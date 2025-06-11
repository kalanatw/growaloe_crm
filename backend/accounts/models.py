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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.owner.business_name}"
    
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
