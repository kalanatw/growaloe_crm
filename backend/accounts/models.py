from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with role-based access control"""
    
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('owner', 'Owner'),
        ('salesman', 'Salesman'),
        ('shop', 'Shop'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='shop')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    class Meta:
        db_table = 'users'


class Owner(models.Model):
    """Owner profile extending User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
    business_name = models.CharField(max_length=200)
    business_license = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.business_name} - {self.user.username}"
    
    class Meta:
        db_table = 'owners'


class Salesman(models.Model):
    """Salesman model with owner relationship and margin settings"""
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='salesmen')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salesman_profile')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    is_active = models.BooleanField(default=True)
    
    # New balance tracking fields
    current_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Current cash balance with salesman (positive = salesman owes owner, negative = owner owes salesman)"
    )
    total_cash_collected = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Total cash collected by salesman from customers"
    )
    total_cash_settled = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Total cash settled with owner"
    )
    last_settlement_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.owner.business_name}"
    
    @property
    def outstanding_balance(self):
        """Calculate outstanding balance (positive = salesman owes owner)"""
        return self.current_balance
    
    @property
    def net_cash_position(self):
        """Calculate net cash position"""
        return self.total_cash_collected - self.total_cash_settled
    
    class Meta:
        db_table = 'salesmen'
        unique_together = ['owner', 'user']


class Shop(models.Model):
    """Shop model managed by salesmen"""
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='shops')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_profile', null=True, blank=True)
    name = models.CharField(max_length=200)
    address = models.TextField()
    contact_person = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    shop_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    # Location fields for mapping - increased precision for Google Maps coordinates
    latitude = models.DecimalField(max_digits=20, decimal_places=16, null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=16, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.salesman.name}"
    
    @property
    def current_balance(self):
        """Calculate current outstanding balance"""
        from sales.models import Invoice
        total_invoices = Invoice.objects.filter(shop=self).aggregate(
            total=models.Sum('balance_due')
        )['total'] or 0
        return total_invoices
    
    class Meta:
        db_table = 'shops'


class SalesmanCashCollection(models.Model):
    """Track physical cash collections from salesmen to owners"""
    COLLECTION_METHODS = [
        ('physical_handover', 'Physical Handover'),
        ('bank_deposit', 'Bank Deposit'),
        ('digital_transfer', 'Digital Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='cash_collections')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    collection_date = models.DateField()
    collection_method = models.CharField(max_length=20, choices=COLLECTION_METHODS, default='physical_handover')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Balance tracking
    salesman_balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    salesman_balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Audit fields
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cash_collections_made')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'salesman_cash_collections'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cash Collection: {self.salesman.name} - LKR {self.amount} on {self.collection_date}"


class SalesmanCashTransaction(models.Model):
    """Track all cash transactions between salesman and owner"""
    
    TRANSACTION_TYPES = [
        ('collection', 'Cash Collection from Customer'),
        ('settlement', 'Settlement with Owner'),
        ('expense', 'Delivery Expense'),
        ('advance', 'Advance from Owner'),
        ('adjustment', 'Balance Adjustment'),
    ]
    
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='cash_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Reference information
    reference_type = models.CharField(max_length=50, null=True, blank=True)  # 'invoice', 'delivery_settlement', 'expense'
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    invoice = models.ForeignKey('sales.Invoice', on_delete=models.CASCADE, null=True, blank=True, related_name='salesman_cash_transactions')
    cash_collection = models.ForeignKey(SalesmanCashCollection, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    description = models.TextField()
    notes = models.TextField(blank=True, null=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.salesman.name} - {self.get_transaction_type_display()} - {self.amount}"
    
    class Meta:
        db_table = 'salesman_cash_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['salesman', 'transaction_type']),
            models.Index(fields=['salesman', 'created_at']),
        ]


class MarginPolicy(models.Model):
    """Margin policy configuration for owners"""
    owner = models.OneToOneField(Owner, on_delete=models.CASCADE, related_name='margin_policy')
    default_salesman_margin = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    default_shop_margin = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    allow_salesman_override = models.BooleanField(default=True)
    allow_shop_override = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Margin Policy - {self.owner.business_name}"
    
    class Meta:
        db_table = 'margin_policies'
