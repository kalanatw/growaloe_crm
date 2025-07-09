from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class TransactionCategory(models.Model):
    """Categories for financial transactions"""
    
    TRANSACTION_TYPES = [
        ('income', 'Additional Income'),
        ('expense', 'Expense'),
    ]
    
    name = models.CharField(max_length=100)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_transaction_type_display()})"
    
    class Meta:
        db_table = 'finance_transaction_categories'
        ordering = ['transaction_type', 'name']
        verbose_name_plural = 'Transaction Categories'


class FinancialTransaction(models.Model):
    """Model for recording income and expense transactions"""
    
    TRANSACTION_TYPES = [
        ('income', 'Additional Income'),
        ('expense', 'Expense'),
    ]
    
    transaction_date = models.DateField(default=timezone.now)
    category = models.ForeignKey(
        TransactionCategory, 
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(
        upload_to='finance/attachments/', 
        null=True, 
        blank=True
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='created_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def transaction_type(self):
        return self.category.transaction_type if self.category else None
    
    def __str__(self):
        return f"{self.category.name} - {self.amount} ({self.transaction_date})"
    
    class Meta:
        db_table = 'finance_transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['category']),
            models.Index(fields=['created_by']),
        ]


class DescriptionSuggestion(models.Model):
    """Cache for frequently used transaction descriptions"""
    
    description = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(
        TransactionCategory, 
        on_delete=models.CASCADE,
        related_name='suggestions'
    )
    frequency = models.PositiveIntegerField(default=1)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.description} (used {self.frequency} times)"
    
    class Meta:
        db_table = 'finance_description_suggestions'
        ordering = ['-frequency', '-last_used']
        indexes = [
            models.Index(fields=['description']),
            models.Index(fields=['category']),
            models.Index(fields=['frequency']),
        ]


class ProfitSummary(models.Model):
    """Periodic profit summaries for financial reporting"""
    
    PERIOD_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Invoice metrics
    total_invoices = models.IntegerField(default=0)
    settled_invoices = models.IntegerField(default=0)
    unsettled_invoices = models.IntegerField(default=0)
    
    # Amount metrics
    invoice_total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unsettled_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cost metrics
    cost_of_goods_settled = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_of_goods_unsettled = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Commission metrics
    commission_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_pending = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Income and expense metrics
    additional_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Profit metrics
    realized_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unrealized_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    spendable_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Efficiency metrics
    collection_efficiency = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )  # percentage
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_period_type_display()}: {self.start_date} to {self.end_date}"
    
    class Meta:
        db_table = 'finance_profit_summaries'
        ordering = ['-start_date']
        unique_together = ['period_type', 'start_date', 'end_date']
        indexes = [
            models.Index(fields=['period_type', 'start_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]


class CommissionRecord(models.Model):
    """Track commission calculations and payments"""
    
    STATUS_CHOICES = [
        ('calculated', 'Calculated'),
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Foreign key to sales models
    invoice = models.ForeignKey(
        'sales.Invoice', 
        on_delete=models.CASCADE,
        related_name='commission_records'
    )
    settlement = models.ForeignKey(
        'sales.InvoiceSettlement', 
        on_delete=models.CASCADE,
        related_name='commission_records',
        null=True,
        blank=True
    )
    salesman = models.ForeignKey(
        'accounts.Salesman', 
        on_delete=models.CASCADE,
        related_name='commission_records'
    )
    
    # Commission details
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    calculation_basis = models.CharField(
        max_length=20,
        choices=[
            ('total_sales', 'Total Sales'),
            ('profit_margin', 'Profit Margin'),
            ('cash_collected', 'Cash Collected'),
        ],
        default='cash_collected'
    )
    
    # Payment tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='calculated')
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional fields
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Commission for {self.salesman.user.get_full_name()} - {self.commission_amount}"
    
    class Meta:
        db_table = 'finance_commission_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['salesman']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_date']),
        ]
