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
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50, default='piece')  # piece, kg, liter, etc.
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"
    
    @property
    def is_low_stock(self):
        """Check if product is below minimum stock level"""
        return self.stock_quantity <= self.min_stock_level
    
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
    
    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]


class SalesmanStock(models.Model):
    """Track stock allocated to each salesman"""
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
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    delivery_number = models.CharField(max_length=50, unique=True)
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='deliveries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
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
        
        # Update salesman stock when delivery item is saved
        if self.delivery.status == 'delivered':
            self._update_salesman_stock(old_quantity)
    
    def delete(self, *args, **kwargs):
        # Reverse stock allocation when item is deleted
        if self.delivery.status == 'delivered':
            self._update_salesman_stock(0, reverse=True)
        super().delete(*args, **kwargs)
    
    def _update_salesman_stock(self, old_quantity=0, reverse=False):
        """Update salesman stock allocation"""
        try:
            salesman_stock, created = SalesmanStock.objects.get_or_create(
                salesman=self.delivery.salesman,
                product=self.product,
                defaults={
                    'allocated_quantity': 0,
                    'available_quantity': 0
                }
            )
            
            if reverse:
                # Remove allocation
                quantity_change = -self.quantity
            else:
                # Add or adjust allocation
                quantity_change = self.quantity - old_quantity
            
            salesman_stock.allocated_quantity += quantity_change
            salesman_stock.available_quantity += quantity_change
            
            # Ensure quantities don't go negative
            salesman_stock.allocated_quantity = max(0, salesman_stock.allocated_quantity)
            salesman_stock.available_quantity = max(0, salesman_stock.available_quantity)
            
            salesman_stock.save()
            
            # Create stock movement record
            StockMovement.objects.create(
                product=self.product,
                movement_type='allocation',
                quantity=quantity_change,
                reference_id=self.delivery.delivery_number,
                salesman=self.delivery.salesman,
                notes=f"Delivery allocation: {self.delivery.delivery_number}",
                created_by=self.delivery.created_by
            )
            
        except Exception as e:
            print(f"Error updating salesman stock: {e}")
    
    class Meta:
        db_table = 'delivery_items'
        unique_together = ['delivery', 'product']
