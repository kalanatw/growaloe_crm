from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import Owner, Salesman

User = get_user_model()


class Category(models.Model):
    """Product category model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'


class Product(models.Model):
    """Product model with stock management"""
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True)
    image_url = models.URLField(blank=True, null=True, help_text="Product image URL")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="MRP - Maximum Retail Price")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Cost price for profit calculation")
    min_stock_level = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50, default='piece')  # piece, kg, liter, etc.
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"
    
    @property
    def total_stock(self):
        """Get total stock across all locations"""
        return CentralStock.objects.filter(product=self).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def owner_stock(self):
        """Get stock with owner"""
        return CentralStock.objects.filter(
            product=self, 
            location_type='owner'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def salesman_stock(self):
        """Get total stock with all salesmen"""
        return CentralStock.objects.filter(
            product=self, 
            location_type='salesman'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def is_low_stock(self):
        """Check if total product stock is below minimum level"""
        return self.total_stock <= self.min_stock_level
    
    def calculate_selling_price(self, salesman_margin=0, shop_margin=0):
        """Calculate selling price with margins"""
        price = self.base_price
        
        # Apply salesman margin
        if salesman_margin > 0:
            price += (price * salesman_margin / 100)
        
        # Apply shop margin
        if shop_margin > 0:
            price += (price * shop_margin / 100)
        
        return round(price, 2)
    
    def calculate_profit_per_unit(self, salesman_margin=0, shop_margin=0):
        """Calculate profit per unit after applying margins"""
        selling_price = self.calculate_selling_price(salesman_margin, shop_margin)
        profit = selling_price - self.cost_price
        
        # Calculate breakdown
        return {
            'cost_price': float(self.cost_price),
            'base_price': float(self.base_price),
            'selling_price': float(selling_price),
            'total_profit': float(profit),
            'salesman_margin_amount': float(self.base_price * salesman_margin / 100) if salesman_margin > 0 else 0,
            'shop_margin_amount': float(self.base_price * shop_margin / 100) if shop_margin > 0 else 0,
            'owner_profit': float(self.base_price - self.cost_price),
            'profit_percentage': float((profit / selling_price) * 100) if selling_price > 0 else 0
        }
    
    def add_stock(self, quantity, user=None, notes=None, batch_number=None, expiry_date=None, cost_per_unit=None):
        """Add stock to owner inventory using batch management"""
        if quantity <= 0:
            raise ValueError("Stock quantity must be positive")
        
        # Create a new batch for the restocked items
        batch = Batch.objects.create(
            product=self,
            batch_number=batch_number or f"BATCH-{self.id}-{timezone.now().strftime('%Y%m%d-%H%M%S')}",
            manufacturing_date=timezone.now().date(),
            initial_quantity=quantity,
            current_quantity=quantity,
            expiry_date=expiry_date,
            unit_cost=cost_per_unit or self.cost_price,
            notes=notes,
            created_by=user
        )
        
        # Create batch transaction record
        BatchTransaction.objects.create(
            batch=batch,
            transaction_type='restock',
            quantity=quantity,
            balance_after=quantity,  # For new batch, balance after = initial quantity
            notes=notes or f"Initial stock added: {quantity} units",
            created_by=user
        )
        
        # Update central stock for backward compatibility
        central_stock = CentralStock.objects.filter(
            product=self,
            location_type='owner',
            location_id=None
        ).first()
        
        if not central_stock:
            central_stock = CentralStock.objects.create(
                product=self,
                location_type='owner',
                location_id=None,
                quantity=0
            )
        
        old_quantity = central_stock.quantity
        central_stock.quantity += quantity
        central_stock.save()
        
        # Create stock movement record
        StockMovement.objects.create(
            product=self,
            movement_type='purchase',
            quantity=quantity,
            notes=notes or f"Stock added: {quantity} units (Batch: {batch.batch_number})",
            created_by=user
        )
        
        return {
            'old_quantity': old_quantity,
            'batch_id': batch.id,
            'batch_number': batch.batch_number,
            'new_quantity': central_stock.quantity,
            'added_quantity': quantity
        }
    
    def reduce_stock(self, quantity, user=None, notes=None, movement_type='adjustment'):
        """Reduce stock from owner inventory"""
        if quantity <= 0:
            raise ValueError("Stock quantity must be positive")
        
        # Get owner stock
        try:
            central_stock = CentralStock.objects.get(
                product=self,
                location_type='owner',
                location_id=None
            )
        except CentralStock.DoesNotExist:
            raise ValueError("No owner stock found for this product")
        
        if central_stock.quantity < quantity:
            raise ValueError(f"Insufficient stock. Available: {central_stock.quantity}, Required: {quantity}")
        
        old_quantity = central_stock.quantity
        central_stock.quantity -= quantity
        central_stock.save()
        
        # Create stock movement record
        StockMovement.objects.create(
            product=self,
            movement_type=movement_type,
            quantity=-quantity,  # Negative for outward movement
            notes=notes or f"Stock reduced: {quantity} units",
            created_by=user
        )
        
        return {
            'old_quantity': old_quantity,
            'new_quantity': central_stock.quantity,
            'reduced_quantity': quantity
        }
    
    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]


class CentralStock(models.Model):
    """Centralized stock management - single source of truth"""
    
    LOCATION_TYPES = [
        ('owner', 'Owner Stock'),
        ('salesman', 'Salesman Stock'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_locations')
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    location_id = models.PositiveIntegerField(null=True, blank=True)  # Salesman ID for salesman stock, None for owner
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.location_type == 'owner':
            return f"{self.product.name} - Owner Stock ({self.quantity})"
        else:
            try:
                salesman = Salesman.objects.get(id=self.location_id)
                return f"{self.product.name} - {salesman.name} ({self.quantity})"
            except Salesman.DoesNotExist:
                return f"{self.product.name} - Unknown Salesman ({self.quantity})"
    
    @property
    def location_name(self):
        """Get human readable location name"""
        if self.location_type == 'owner':
            return "Owner Stock"
        else:
            try:
                salesman = Salesman.objects.get(id=self.location_id)
                return salesman.name
            except Salesman.DoesNotExist:
                return "Unknown Salesman"
    
    class Meta:
        db_table = 'central_stock'
        unique_together = ['product', 'location_type', 'location_id']
        indexes = [
            models.Index(fields=['product', 'location_type']),
            models.Index(fields=['location_type', 'location_id']),
        ]


class SalesmanStock(models.Model):
    """DEPRECATED - keeping for backward compatibility, will be removed"""
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='stock_allocations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='salesman_allocations')
    allocated_quantity = models.PositiveIntegerField(default=0)
    available_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.salesman.name} - {self.product.name} ({self.available_quantity})"
    
    @property
    def sold_quantity(self):
        """Calculate sold quantity"""
        return self.allocated_quantity - self.available_quantity
    
    class Meta:
        db_table = 'salesman_stock'
        unique_together = ['salesman', 'product']
    
    @property
    def sold_quantity(self):
        """Calculate sold quantity"""
        return self.allocated_quantity - self.available_quantity
    
    class Meta:
        db_table = 'salesman_stock'
        unique_together = ['salesman', 'product']


class StockMovement(models.Model):
    """Track all stock movements for audit purposes"""
    
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('allocation', 'Allocation to Salesman'),
        ('return', 'Return'),
        ('adjustment', 'Stock Adjustment'),
        ('damage', 'Damage/Loss'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Positive for inward, negative for outward
    reference_id = models.CharField(max_length=100, blank=True, null=True)  # Invoice ID, PO ID, etc.
    salesman = models.ForeignKey(Salesman, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        direction = "+" if self.quantity >= 0 else ""
        return f"{self.product.name} - {direction}{self.quantity} ({self.get_movement_type_display()})"
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']


class Delivery(models.Model):
    """Track product deliveries from owner to salesmen"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),  # Stock transferred to salesman
        ('settled', 'Settled'),      # Remaining stock returned, margins calculated
        ('cancelled', 'Cancelled'),
    ]
    
    delivery_number = models.CharField(max_length=50, unique=True)
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='deliveries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_date = models.DateField()
    settlement_date = models.DateField(null=True, blank=True)
    total_margin_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    settlement_notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Delivery #{self.delivery_number} - {self.salesman.name}"
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            # Generate delivery number (DEL-YYYYMMDD-XXX)
            today = timezone.now().date()
            date_str = today.strftime('%Y%m%d')
            
            # Find the latest delivery for today
            latest = Delivery.objects.filter(
                delivery_number__startswith=f'DEL-{date_str}'
            ).order_by('-delivery_number').first()
            
            if latest:
                # Extract sequence number and increment
                sequence = int(latest.delivery_number.split('-')[-1]) + 1
            else:
                sequence = 1
                
            self.delivery_number = f'DEL-{date_str}-{sequence:03d}'
        
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        """Get total number of items in this delivery"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def total_value(self):
        """Calculate total value of delivery"""
        return sum(item.total_value for item in self.items.all())
    
    def get_settlement_data(self):
        """Get data needed for settlement modal"""
        from sales.models import InvoiceItem
        
        settlement_data = []
        for item in self.items.all():
            # Get sold quantity for this product by this salesman
            sold_qty = InvoiceItem.objects.filter(
                invoice__salesman=self.salesman,
                product=item.product,
                invoice__created_at__gte=self.created_at,
                invoice__status__in=['SENT', 'PAID', 'PARTIAL']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            remaining_qty = item.quantity - sold_qty
            
            # Calculate margins earned
            total_margin = InvoiceItem.objects.filter(
                invoice__salesman=self.salesman,
                product=item.product,
                invoice__created_at__gte=self.created_at,
                invoice__status__in=['SENT', 'PAID', 'PARTIAL']
            ).aggregate(total=models.Sum('salesman_margin'))['total'] or 0
            
            settlement_data.append({
                'delivery_item_id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'delivered_quantity': item.quantity,
                'sold_quantity': sold_qty,
                'remaining_quantity': remaining_qty,
                'margin_earned': float(total_margin),
            })
        
        return settlement_data
    
    def settle_delivery(self, settlement_data, settlement_notes=""):
        """Settle the delivery by returning remaining stock and calculating margins"""
        if self.status != 'delivered':
            raise ValueError("Only delivered deliveries can be settled")
        
        total_margin_earned = 0
        
        for item_data in settlement_data:
            delivery_item = self.items.get(id=item_data['delivery_item_id'])
            remaining_qty = item_data['remaining_quantity']
            
            # Return remaining stock to owner
            if remaining_qty > 0:
                owner_stock, _ = CentralStock.objects.get_or_create(
                    product=delivery_item.product,
                    location_type='owner',
                    defaults={'quantity': 0}
                )
                owner_stock.quantity += remaining_qty
                owner_stock.save()
                
                # Remove remaining stock from salesman
                try:
                    salesman_stock = CentralStock.objects.get(
                        product=delivery_item.product,
                        location_type='salesman',
                        location_id=self.salesman.id
                    )
                    salesman_stock.quantity -= remaining_qty
                    if salesman_stock.quantity <= 0:
                        salesman_stock.delete()
                    else:
                        salesman_stock.save()
                except CentralStock.DoesNotExist:
                    pass  # Stock already sold/transferred
            
            total_margin_earned += item_data['margin_earned']
        
        # Update delivery status and settlement info
        self.status = 'settled'
        self.settlement_date = timezone.now().date()
        self.total_margin_earned = total_margin_earned
        self.settlement_notes = settlement_notes
        self.save()
        
        return {
            'total_margin_earned': float(total_margin_earned),
            'settlement_date': self.settlement_date.isoformat(),
            'status': self.status
        }
    
    class Meta:
        db_table = 'deliveries'
        ordering = ['-created_at']
        verbose_name_plural = 'Deliveries'


class DeliveryItem(models.Model):
    """Individual items in a delivery"""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.delivery.delivery_number} - {self.product.name} x {self.quantity}"
    
    @property
    def total_value(self):
        """Calculate total value for this item"""
        return float(self.quantity * self.unit_price)
    
    def save(self, *args, **kwargs):
        # Set unit price to product's base price if not provided
        if not self.unit_price:
            self.unit_price = self.product.base_price
        
        is_new = self.pk is None
        old_quantity = 0
        
        if not is_new:
            # Get old quantity for stock adjustment
            old_item = DeliveryItem.objects.get(pk=self.pk)
            old_quantity = old_item.quantity
        
        super().save(*args, **kwargs)
        
        # Stock transfer is now handled by batch assignments in the serializer
        # No need to transfer stock here as it's done via FIFO batch assignment
    
    def delete(self, *args, **kwargs):
        # Return stock to owner when item is deleted
        self._return_stock_to_owner()
        super().delete(*args, **kwargs)
    
    def _transfer_stock_to_salesman(self):
        """Transfer stock from owner to salesman immediately upon delivery creation"""
        try:
            # Get owner stock
            owner_stock = CentralStock.objects.get(
                product=self.product,
                location_type='owner'
            )
            
            # Check if owner has enough stock
            if owner_stock.quantity < self.quantity:
                raise ValueError(f"Insufficient owner stock for {self.product.name}. Available: {owner_stock.quantity}, Required: {self.quantity}")
            
            # Reduce owner stock
            owner_stock.quantity -= self.quantity
            owner_stock.save()
            
            # Add to salesman stock
            salesman_stock, created = CentralStock.objects.get_or_create(
                product=self.product,
                location_type='salesman',
                location_id=self.delivery.salesman.id,
                defaults={'quantity': 0}
            )
            salesman_stock.quantity += self.quantity
            salesman_stock.save()
            
            # Mark delivery as delivered since stock is transferred
            if self.delivery.status == 'pending':
                self.delivery.status = 'delivered'
                self.delivery.save()
                
        except CentralStock.DoesNotExist:
            raise ValueError(f"No owner stock found for {self.product.name}")
    
    def _adjust_stock_for_change(self, old_quantity):
        """Adjust stock when delivery item quantity changes"""
        quantity_diff = self.quantity - old_quantity
        
        if quantity_diff > 0:
            # Increase: need more stock from owner
            owner_stock = CentralStock.objects.get(
                product=self.product,
                location_type='owner'
            )
            if owner_stock.quantity < quantity_diff:
                raise ValueError(f"Insufficient owner stock for {self.product.name}")
            
            owner_stock.quantity -= quantity_diff
            owner_stock.save()
            
            salesman_stock = CentralStock.objects.get(
                product=self.product,
                location_type='salesman',
                location_id=self.delivery.salesman.id
            )
            salesman_stock.quantity += quantity_diff
            salesman_stock.save()
            
        elif quantity_diff < 0:
            # Decrease: return stock to owner
            return_qty = abs(quantity_diff)
            
            owner_stock, _ = CentralStock.objects.get_or_create(
                product=self.product,
                location_type='owner',
                defaults={'quantity': 0}
            )
            owner_stock.quantity += return_qty
            owner_stock.save()
            
            salesman_stock = CentralStock.objects.get(
                product=self.product,
                location_type='salesman',
                location_id=self.delivery.salesman.id
            )
            salesman_stock.quantity -= return_qty
            if salesman_stock.quantity <= 0:
                salesman_stock.delete()
            else:
                salesman_stock.save()
    
    def _return_stock_to_owner(self):
        """Return all stock of this item back to owner"""
        try:
            salesman_stock = CentralStock.objects.get(
                product=self.product,
                location_type='salesman',
                location_id=self.delivery.salesman.id
            )
            
            # Return stock to owner
            owner_stock, _ = CentralStock.objects.get_or_create(
                product=self.product,
                location_type='owner',
                defaults={'quantity': 0}
            )
            owner_stock.quantity += self.quantity
            owner_stock.save()
            
            # Remove from salesman stock
            salesman_stock.quantity -= self.quantity
            if salesman_stock.quantity <= 0:
                salesman_stock.delete()
            else:
                salesman_stock.save()
                
        except CentralStock.DoesNotExist:
            pass  # Stock might have been already sold/transferred
    
    def _update_central_stock(self, old_quantity=0, reverse=False):
        """Update central stock system for delivery"""
        try:
            if reverse:
                # Remove allocation - restore owner stock and remove salesman stock
                quantity_change = -self.quantity
            else:
                # Add or adjust allocation
                quantity_change = self.quantity - old_quantity
            
            if quantity_change == 0:
                return
            
            # Get or create owner stock
            owner_stock, created = CentralStock.objects.get_or_create(
                product=self.product,
                location_type='owner',
                location_id=None,
                defaults={'quantity': 0}
            )
            
            # Check if owner has enough stock for delivery
            if not reverse and quantity_change > 0:
                if owner_stock.quantity < quantity_change:
                    raise ValueError(f"Insufficient owner stock for {self.product.name}. Available: {owner_stock.quantity}, Required: {quantity_change}")
            
            # Update owner stock (reduce for delivery, increase for reversal)
            if reverse:
                owner_stock.quantity += abs(quantity_change)
            else:
                owner_stock.quantity -= quantity_change
            
            owner_stock.quantity = max(0, owner_stock.quantity)
            owner_stock.save()
            
            # Get or create salesman stock
            salesman_stock, created = CentralStock.objects.get_or_create(
                product=self.product,
                location_type='salesman',
                location_id=self.delivery.salesman.id,
                defaults={'quantity': 0}
            )
            
            # Update salesman stock (increase for delivery, decrease for reversal)
            salesman_stock.quantity += quantity_change
            salesman_stock.quantity = max(0, salesman_stock.quantity)
            salesman_stock.save()
            
            # Create stock movement records
            StockMovement.objects.create(
                product=self.product,
                movement_type='allocation',
                quantity=-quantity_change if not reverse else quantity_change,  # Negative for owner reduction
                reference_id=self.delivery.delivery_number,
                notes=f"Owner stock {'reduced' if not reverse else 'restored'} - Delivery: {self.delivery.delivery_number}",
                created_by=self.delivery.created_by
            )
            
            StockMovement.objects.create(
                product=self.product,
                movement_type='allocation',
                quantity=quantity_change,
                reference_id=self.delivery.delivery_number,
                salesman=self.delivery.salesman,
                notes=f"Salesman stock {'allocated' if not reverse else 'removed'} - Delivery: {self.delivery.delivery_number}",
                created_by=self.delivery.created_by
            )
            
        except Exception as e:
            print(f"Error updating central stock: {e}")
            # In production, you might want to raise the exception
            # raise e
    
    class Meta:
        db_table = 'delivery_items'
        unique_together = ['delivery', 'product']


class Batch(models.Model):
    """Product batch model for FIFO inventory management"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100, help_text="User-defined batch number")
    manufacturing_date = models.DateField(help_text="Manufacturing or received date")
    expiry_date = models.DateField(null=True, blank=True, help_text="Expiry date for FIFO")
    initial_quantity = models.PositiveIntegerField(help_text="Initial quantity in this batch")
    current_quantity = models.PositiveIntegerField(help_text="Current available quantity")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Cost per unit for this batch")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about this batch")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_batches'
        unique_together = ['product', 'batch_number']
        ordering = ['manufacturing_date', 'expiry_date']  # FIFO ordering
        
    def __str__(self):
        return f"{self.product.name} - Batch {self.batch_number}"
    
    @property
    def is_expired(self):
        """Check if batch is expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def allocated_quantity(self):
        """Get quantity allocated to salesmen"""
        return BatchAssignment.objects.filter(
            batch=self,
            status__in=['pending', 'delivered']
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def available_quantity(self):
        """Get available quantity (current - allocated)"""
        return self.current_quantity - self.allocated_quantity


class BatchTransaction(models.Model):
    """Track all batch stock movements for audit trail"""
    TRANSACTION_TYPES = (
        ('restock', 'Restock'),
        ('assignment', 'Assignment to Salesman'),
        ('sale', 'Sale'),
        ('return', 'Return from Salesman'),
        ('adjustment', 'Stock Adjustment'),
        ('expired', 'Expired Stock Removal'),
    )
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField(help_text="Positive for stock in, negative for stock out")
    balance_after = models.PositiveIntegerField(help_text="Stock balance after this transaction")
    reference_type = models.CharField(max_length=50, blank=True, help_text="Type of reference (delivery, invoice, etc.)")
    reference_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of related record")
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='batch_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'batch_transactions'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.batch} - {self.transaction_type} ({self.quantity})"


class BatchAssignment(models.Model):
    """Track batch assignments to salesmen"""
    ASSIGNMENT_STATUS = (
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('partial', 'Partially Returned'),
        ('returned', 'Fully Returned'),
        ('cancelled', 'Cancelled'),
    )
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='assignments')
    salesman = models.ForeignKey('accounts.Salesman', on_delete=models.CASCADE, related_name='batch_assignments')
    quantity = models.PositiveIntegerField(help_text="Quantity assigned")
    delivered_quantity = models.PositiveIntegerField(default=0, help_text="Quantity actually delivered")
    returned_quantity = models.PositiveIntegerField(default=0, help_text="Quantity returned")
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='pending')
    delivery_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'batch_assignments'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.batch} -> {self.salesman.user.get_full_name()} ({self.quantity})"
    
    @property
    def outstanding_quantity(self):
        """Get quantity still with salesman (delivered - returned)"""
        return self.delivered_quantity - self.returned_quantity
