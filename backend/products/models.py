from django.db import models
from django.contrib.auth import get_user_model
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
