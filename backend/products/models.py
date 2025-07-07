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
        """Get total stock from all batches"""
        return self.batches.filter(is_active=True).aggregate(
            total=models.Sum('current_quantity')
        )['total'] or 0
    
    @property
    def owner_stock(self):
        """Get stock available with owner (unallocated batches)"""
        total_batch_stock = self.batches.filter(
            is_active=True
        ).aggregate(
            total=models.Sum('current_quantity')
        )['total'] or 0
        
        return max(0, total_batch_stock - self.allocated_stock)

    @property
    def allocated_stock(self):
        """Get total stock allocated to salesmen"""
        delivered_quantity = BatchAssignment.objects.filter(
            batch__product=self,
            status__in=['pending', 'delivered', 'partial']
        ).aggregate(
            total=models.Sum('delivered_quantity')
        )['total'] or 0
        
        returned_quantity = BatchAssignment.objects.filter(
            batch__product=self,
            status__in=['delivered', 'partial', 'returned']
        ).aggregate(
            total=models.Sum('returned_quantity')
        )['total'] or 0
        
        return max(0, delivered_quantity - returned_quantity)

    @property
    def salesman_stock(self):
        """Get total stock with all salesmen (outstanding allocations)"""
        return self.allocated_stock
    
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
        
        # Create stock movement record for audit
        StockMovement.objects.create(
            product=self,
            movement_type='purchase',
            quantity=quantity,
            notes=notes or f"Stock added: {quantity} units (Batch: {batch.batch_number})",
            created_by=user
        )
        
        return {
            'batch_id': batch.id,
            'batch_number': batch.batch_number,
            'new_quantity': batch.current_quantity,
            'added_quantity': quantity
        }
    
    def reduce_stock(self, quantity, user=None, notes=None, movement_type='adjustment'):
        """Reduce stock from owner inventory using FIFO batch management"""
        if quantity <= 0:
            raise ValueError("Stock quantity must be positive")
        
        # Get available batches ordered by FIFO (manufacturing date, expiry date)
        available_batches = self.batches.filter(
            is_active=True,
            current_quantity__gt=0
        ).order_by('manufacturing_date', 'expiry_date')
        
        # Check if enough stock is available
        total_available = sum(batch.current_quantity for batch in available_batches)
        if total_available < quantity:
            raise ValueError(f"Insufficient stock. Available: {total_available}, Required: {quantity}")
        
        remaining_to_reduce = quantity
        reduced_batches = []
        
        # Reduce from batches using FIFO
        for batch in available_batches:
            if remaining_to_reduce <= 0:
                break
                
            if batch.current_quantity > 0:
                reduce_from_batch = min(batch.current_quantity, remaining_to_reduce)
                
                # Update batch quantity
                batch.current_quantity -= reduce_from_batch
                batch.save()
                
                # Create batch transaction
                BatchTransaction.objects.create(
                    batch=batch,
                    transaction_type=movement_type,
                    quantity=-reduce_from_batch,
                    balance_after=batch.current_quantity,
                    notes=notes or f"Stock reduced: {reduce_from_batch} units",
                    created_by=user
                )
                
                reduced_batches.append({
                    'batch_id': batch.id,
                    'batch_number': batch.batch_number,
                    'reduced_quantity': reduce_from_batch
                })
                
                remaining_to_reduce -= reduce_from_batch
        
        # Create stock movement record
        StockMovement.objects.create(
            product=self,
            movement_type=movement_type,
            quantity=-quantity,  # Negative for outward movement
            notes=notes or f"Stock reduced: {quantity} units",
            created_by=user
        )
        
        return {
            'reduced_quantity': quantity,
            'affected_batches': reduced_batches
        }
    
    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]





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
    
    def get_real_time_settlement_data(self):
        """
        Get real-time settlement data with updated sold quantities from invoices.
        This replaces the old get_settlement_data method with more accurate calculations.
        """
        from sales.models import InvoiceItem
        
        settlement_data = []
        for item in self.items.all():
            # Get sold quantity for this exact product by this salesman since delivery
            sold_qty = InvoiceItem.objects.filter(
                invoice__salesman=self.salesman,
                product=item.product,
                invoice__invoice_date__gte=self.created_at,
                invoice__status__in=['pending', 'paid', 'partial']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            remaining_qty = max(0, item.quantity - sold_qty)
            
            # Calculate actual margins earned from invoices (not estimated)
            total_margin = InvoiceItem.objects.filter(
                invoice__salesman=self.salesman,
                product=item.product,
                invoice__invoice_date__gte=self.created_at,
                invoice__status__in=['pending', 'paid', 'partial']
            ).aggregate(
                total=models.Sum(
                    models.F('quantity') * (models.F('unit_price') - models.F('product__base_price'))
                )
            )['total'] or 0
            
            settlement_data.append({
                'delivery_item_id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'delivered_quantity': item.quantity,
                'sold_quantity': sold_qty,
                'remaining_quantity': remaining_qty,
                'unit_price': float(item.unit_price),
                'outstanding_value': remaining_qty * float(item.unit_price),
                'margin_earned': float(total_margin),
            })
        
        return settlement_data
    
    def can_be_settled(self):
        """Check if this delivery can be settled"""
        return self.status == 'delivered'
    
    def get_settlement_summary(self):
        """Get a quick summary for settlement decisions"""
        settlement_data = self.get_real_time_settlement_data()
        
        total_delivered = sum(item['delivered_quantity'] for item in settlement_data)
        total_sold = sum(item['sold_quantity'] for item in settlement_data)
        total_remaining = sum(item['remaining_quantity'] for item in settlement_data)
        total_margin = sum(item['margin_earned'] for item in settlement_data)
        total_outstanding_value = sum(item['outstanding_value'] for item in settlement_data)
        
        return {
            'delivery_id': self.id,
            'delivery_number': self.delivery_number,
            'salesman_name': self.salesman.user.get_full_name(),
            'delivery_date': self.created_at,
            'can_settle': self.can_be_settled(),
            'total_delivered': total_delivered,
            'total_sold': total_sold,
            'total_remaining': total_remaining,
            'total_margin_earned': total_margin,
            'total_outstanding_value': total_outstanding_value,
            'sale_completion_rate': (total_sold / total_delivered * 100) if total_delivered > 0 else 0,
            'settlement_priority': 'high' if total_outstanding_value > 1000 else 'medium' if total_outstanding_value > 500 else 'low'
        }
    
    def settle_delivery(self, settlement_data, settlement_notes=""):
        """Settle the delivery by processing returned stock through batch assignments"""
        if self.status != 'delivered':
            raise ValueError("Only delivered deliveries can be settled")
        
        total_margin_earned = 0
        
        for item_data in settlement_data:
            delivery_item = self.items.get(id=item_data['delivery_item_id'])
            remaining_qty = item_data['remaining_quantity']
            
            # Process returns through batch assignments
            if remaining_qty > 0:
                # Find batch assignments for this salesman and product
                assignments = BatchAssignment.objects.filter(
                    batch__product=delivery_item.product,
                    salesman=self.salesman,
                    status__in=['delivered', 'partial']
                ).order_by('created_at')
                
                # Return stock by updating assignment returned_quantity
                remaining_to_return = remaining_qty
                for assignment in assignments:
                    if remaining_to_return <= 0:
                        break
                    
                    outstanding = assignment.outstanding_quantity
                    if outstanding > 0:
                        return_qty = min(outstanding, remaining_to_return)
                        assignment.returned_quantity += return_qty
                        
                        # Update assignment status
                        if assignment.returned_quantity >= assignment.delivered_quantity:
                            assignment.status = 'returned'
                        elif assignment.returned_quantity > 0:
                            assignment.status = 'partial'
                        
                        assignment.save()
                        
                        # Create batch transaction for return
                        BatchTransaction.objects.create(
                            batch=assignment.batch,
                            transaction_type='return',
                            quantity=return_qty,
                            balance_after=assignment.batch.current_quantity,
                            reference_type='delivery_settlement',
                            reference_id=self.id,
                            notes=f"Settlement return from {self.salesman.user.get_full_name()}",
                            created_by=self.created_by
                        )
                        
                        remaining_to_return -= return_qty
            
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
        
        # Handle batch allocation when delivery item is created/updated
        if is_new and self.delivery.status == 'pending':
            self._allocate_stock_to_salesman()
    
    def delete(self, *args, **kwargs):
        # Return allocated stock when item is deleted
        self._deallocate_stock_from_salesman()
        super().delete(*args, **kwargs)
    
    def _allocate_stock_to_salesman(self):
        """Allocate stock from owner's batches to salesman using FIFO"""
        # Check if allocation already exists for this delivery item
        existing_assignments = BatchAssignment.objects.filter(
            delivery=self.delivery,
            salesman=self.delivery.salesman,
            notes__contains=f"Delivery: {self.delivery.delivery_number}"
        )
        
        if existing_assignments.exists():
            # Allocation already exists, skip to prevent duplication
            return
            
        # Get available batches ordered by FIFO
        available_batches = self.product.batches.filter(
            is_active=True,
            current_quantity__gt=0
        ).order_by('manufacturing_date', 'expiry_date')
        
        # Check if enough stock is available
        total_available = sum(batch.available_quantity for batch in available_batches)
        if total_available < self.quantity:
            raise ValueError(f"Insufficient stock for {self.product.name}. Available: {total_available}, Required: {self.quantity}")
        
        remaining_to_allocate = self.quantity
        
        # Allocate from batches using FIFO
        for batch in available_batches:
            if remaining_to_allocate <= 0:
                break
                
            available_in_batch = batch.available_quantity
            if available_in_batch > 0:
                allocate_from_batch = min(available_in_batch, remaining_to_allocate)
                
                # Create batch assignment
                assignment = BatchAssignment.objects.create(
                    batch=batch,
                    salesman=self.delivery.salesman,
                    delivery=self.delivery,
                    quantity=allocate_from_batch,
                    delivered_quantity=allocate_from_batch,
                    status='delivered',
                    delivery_date=timezone.now(),
                    notes=f"Delivery: {self.delivery.delivery_number}",
                    created_by=self.delivery.created_by
                )
                
                # Update batch current quantity
                batch.current_quantity -= allocate_from_batch
                batch.save()
                
                # Create batch transaction
                BatchTransaction.objects.create(
                    batch=batch,
                    transaction_type='assignment',
                    quantity=-allocate_from_batch,
                    balance_after=batch.current_quantity,
                    reference_type='delivery_item',
                    reference_id=self.id,
                    notes=f"Allocated to {self.delivery.salesman.user.get_full_name()}",
                    created_by=self.delivery.created_by
                )
                
                remaining_to_allocate -= allocate_from_batch
        
        # Mark delivery as delivered since stock is allocated
        if self.delivery.status == 'pending':
            self.delivery.status = 'delivered'
            self.delivery.save()
    
    def _deallocate_stock_from_salesman(self):
        """Deallocate stock assignments when delivery item is deleted"""
        # Find and remove batch assignments for this delivery item
        assignments = BatchAssignment.objects.filter(
            batch__product=self.product,
            salesman=self.delivery.salesman,
            notes__contains=f"Delivery: {self.delivery.delivery_number}"
        )
        
        for assignment in assignments:
            # Create reversal transaction
            BatchTransaction.objects.create(
                batch=assignment.batch,
                transaction_type='return',
                quantity=assignment.delivered_quantity - assignment.returned_quantity,
                balance_after=assignment.batch.current_quantity,
                reference_type='delivery_cancellation',
                reference_id=self.id,
                notes=f"Delivery cancelled: {self.delivery.delivery_number}",
                created_by=self.delivery.created_by
            )
            
            assignment.delete()
    
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
    
    # Quality tracking fields
    quality_status = models.CharField(max_length=20, choices=[
        ('GOOD', 'Good Quality'),
        ('WARNING', 'Quality Warning'),
        ('DEFECTIVE', 'Defective'),
        ('RECALLED', 'Recalled')
    ], default='GOOD', help_text="Quality status of the batch")
    
    recall_initiated_at = models.DateTimeField(null=True, blank=True, help_text="When recall was initiated")
    recall_reason = models.TextField(blank=True, help_text="Reason for batch recall")
    total_returned = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total quantity returned")
    return_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Return rate percentage")
    
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
        """Get available quantity (current - allocated but not returned)"""
        allocated = BatchAssignment.objects.filter(
            batch=self,
            status__in=['pending', 'delivered', 'partial']
        ).aggregate(
            total_delivered=models.Sum('delivered_quantity'),
            total_returned=models.Sum('returned_quantity')
        )
        
        total_allocated = (allocated['total_delivered'] or 0) - (allocated['total_returned'] or 0)
        return max(0, self.current_quantity - total_allocated)
    
    @property
    def quality_score(self):
        """Calculate quality score based on returns and defects"""
        if self.initial_quantity == 0:
            return 100
        
        # Base score starts at 100
        score = 100
        
        # Reduce score based on return rate
        score -= min(self.return_rate, 50)  # Max 50 points reduction for returns
        
        # Reduce score based on defects
        defect_count = self.defects.count()
        critical_defects = self.defects.filter(severity='CRITICAL').count()
        high_defects = self.defects.filter(severity='HIGH').count()
        
        score -= (critical_defects * 30)  # 30 points per critical defect
        score -= (high_defects * 15)     # 15 points per high defect
        score -= (defect_count * 5)      # 5 points per defect
        
        return max(0, score)
    
    @property
    def is_problematic(self):
        """Check if batch has quality issues"""
        return (self.quality_status in ['WARNING', 'DEFECTIVE', 'RECALLED'] or 
                self.return_rate > 10 or 
                self.defects.filter(severity__in=['HIGH', 'CRITICAL']).exists())
    
    def update_return_rate(self):
        """Update the return rate based on actual returns"""
        from sales.models import Return
        
        total_sold = self.assignments.aggregate(
            total=models.Sum('delivered_quantity')
        )['total'] or 0
        
        total_returned = Return.objects.filter(
            batch=self,
            approved=True
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        if total_sold > 0:
            self.return_rate = (total_returned / total_sold) * 100
            self.total_returned = total_returned
        else:
            self.return_rate = 0
            self.total_returned = 0
        
        # Update quality status based on return rate
        if self.return_rate > 20:
            self.quality_status = 'DEFECTIVE'
        elif self.return_rate > 10:
            self.quality_status = 'WARNING'
        elif self.quality_status not in ['RECALLED']:
            self.quality_status = 'GOOD'
        
        self.save()
    
    def initiate_recall(self, reason, user=None):
        """Initiate a recall for this batch"""
        self.quality_status = 'RECALLED'
        self.recall_initiated_at = timezone.now()
        self.recall_reason = reason
        self.save()
        
        # Create a critical defect record
        BatchDefect.objects.create(
            batch=self,
            defect_type='OTHER',
            severity='CRITICAL',
            description=f"Batch recalled: {reason}",
            reported_by=user
        )
    

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
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='batch_assignments', null=True, blank=True)
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
        # Prevent duplicate assignments for the same batch and delivery
        unique_together = [['batch', 'delivery', 'salesman']]
        
    def __str__(self):
        return f"{self.batch} -> {self.salesman.user.get_full_name()} ({self.quantity})"
    
    @property
    def outstanding_quantity(self):
        """Get quantity still with salesman (delivered - returned)"""
        return self.delivered_quantity - self.returned_quantity
    
    @property
    def sold_quantity(self):
        """Get quantity sold (delivered - returned = sold + still with salesman)"""
        # For now, we track outstanding. Sold quantity would come from invoice items
        return 0  # This would be calculated from invoice items if needed


class BatchDefect(models.Model):
    """Track defects and quality issues in batches"""
    DEFECT_TYPES = (
        ('QUALITY', 'Quality Issue'),
        ('CONTAMINATION', 'Contamination'),
        ('EXPIRY', 'Premature Expiry'),
        ('PACKAGING', 'Packaging Defect'),
        ('OTHER', 'Other Issue'),
    )
    
    SEVERITY_LEVELS = (
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical - Immediate Recall'),
    )
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='defects')
    defect_type = models.CharField(max_length=50, choices=DEFECT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    description = models.TextField(help_text="Detailed description of the defect")
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_defects')
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, help_text="Notes on how the defect was resolved")
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_defects')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'batch_defects'
        ordering = ['-reported_at']
        
    def __str__(self):
        return f"{self.batch.batch_number} - {self.defect_type} ({self.severity})"
    
    def save(self, *args, **kwargs):
        if self.resolved and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


class DeliverySettlement(models.Model):
    """
    Track daily settlements for salesmen.
    Provides audit trail and prevents double-settlement.
    """
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='delivery_settlements')
    settlement_date = models.DateField()
    settlement_number = models.CharField(max_length=50, unique=True)
    
    # Settlement totals
    total_delivered_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_sold_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_returned_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_margin_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Item counts
    total_delivered_items = models.PositiveIntegerField(default=0)
    total_sold_items = models.PositiveIntegerField(default=0)
    total_returned_items = models.PositiveIntegerField(default=0)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    
    settlement_notes = models.TextField(blank=True, null=True)
    settled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='settlements_processed')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'delivery_settlements'
        unique_together = [['salesman', 'settlement_date']]
        ordering = ['-settlement_date', '-created_at']
        indexes = [
            models.Index(fields=['salesman', 'settlement_date']),
            models.Index(fields=['settlement_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Settlement {self.settlement_number} - {self.salesman.user.get_full_name()} ({self.settlement_date})"
    
    def save(self, *args, **kwargs):
        if not self.settlement_number:
            # Generate settlement number (SET-YYYYMMDD-XXX)
            date_str = self.settlement_date.strftime('%Y%m%d')
            
            # Find the latest settlement for this date
            latest = DeliverySettlement.objects.filter(
                settlement_number__startswith=f'SET-{date_str}'
            ).order_by('-settlement_number').first()
            
            if latest:
                # Extract sequence number and increment
                sequence = int(latest.settlement_number.split('-')[-1]) + 1
            else:
                sequence = 1
                
            self.settlement_number = f'SET-{date_str}-{sequence:03d}'
        
        super().save(*args, **kwargs)
    
    @property
    def efficiency_rate(self):
        """Calculate efficiency rate (sold value / delivered value * 100)"""
        if self.total_delivered_value > 0:
            return round((self.total_sold_value / self.total_delivered_value) * 100, 1)
        return 0


class DeliverySettlementItem(models.Model):
    """
    Individual items in a delivery settlement.
    Tracks what was delivered, sold, and returned for each product.
    """
    settlement = models.ForeignKey(DeliverySettlement, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Quantities
    delivered_quantity = models.PositiveIntegerField()
    sold_quantity = models.PositiveIntegerField(default=0)
    returned_quantity = models.PositiveIntegerField(default=0)
    
    # Values
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivered_value = models.DecimalField(max_digits=10, decimal_places=2)
    sold_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    returned_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Margin calculation
    margin_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_margin_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'delivery_settlement_items'
        unique_together = [['settlement', 'product']]
        indexes = [
            models.Index(fields=['settlement', 'product']),
        ]
    
    def __str__(self):
        return f"{self.settlement.settlement_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate values
        self.delivered_value = self.delivered_quantity * self.unit_price
        self.sold_value = self.sold_quantity * self.unit_price
        self.returned_value = self.returned_quantity * self.unit_price
        self.total_margin_earned = self.sold_quantity * self.margin_per_unit
        
        super().save(*args, **kwargs)
