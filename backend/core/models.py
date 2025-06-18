from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class CompanySettings(models.Model):
    """Company settings for invoice customization"""
    
    # Company Information
    company_name = models.CharField(max_length=200, default="Grow Aloe Business")
    company_address = models.TextField(default="123 Business Street\nCity, State 12345")
    company_phone = models.CharField(max_length=20, default="+1 (555) 123-4567")
    company_email = models.EmailField(default="info@growaloe.com")
    company_website = models.URLField(blank=True, null=True)
    company_tax_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Logo and Branding
    company_logo = models.ImageField(
        upload_to='company/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])]
    )
    primary_color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code (e.g., #007bff)")
    secondary_color = models.CharField(max_length=7, default="#6c757d", help_text="Hex color code (e.g., #6c757d)")
    
    # Invoice Template Settings
    invoice_prefix = models.CharField(max_length=10, default="INV", help_text="Prefix for invoice numbers")
    invoice_footer_text = models.TextField(
        default="Thank you for your business!\nThis is a computer-generated invoice and does not require a signature.",
        help_text="Footer text to appear on invoices"
    )
    show_logo_on_invoice = models.BooleanField(default=True)
    show_company_details = models.BooleanField(default=True)
    
    # Default Invoice Settings
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    default_currency = models.CharField(max_length=3, default="USD")
    currency_symbol = models.CharField(max_length=5, default="$")
    
    # Margin Settings
    max_shop_margin_for_salesmen = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('20.00'),
        help_text="Maximum shop margin percentage that salesmen can set (owners have no restrictions)"
    )
    
    # Payment Terms
    default_payment_terms = models.TextField(
        blank=True,
        null=True,
        help_text="Default payment terms and conditions"
    )
    default_due_days = models.PositiveIntegerField(default=30, help_text="Default days until payment is due")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'company_settings'
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'
    
    def __str__(self):
        return f"Company Settings - {self.company_name}"
    
    @classmethod
    def get_settings(cls):
        """Get or create company settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """Ensure only one settings instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)


class FinancialTransaction(models.Model):
    """
    Represents all business transactions using double-entry accounting principles.
    Every transaction is either a Debit or Credit entry.
    
    Debit entries (increases expenses/assets, decreases income):
    - Invoice creation (accounts receivable)
    - Expenses (rent, utilities, etc.)
    - Agency payments
    
    Credit entries (increases income, decreases expenses/assets):
    - Invoice settlements (cash received)
    - Other income
    
    Net Balance = Total Credits - Total Debits = Profit
    """
    
    TRANSACTION_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    
    CATEGORY_CHOICES = [
        # Credit categories (Income/Revenue)
        ('invoice_settlement', 'Invoice Settlement'),
        ('cash_sale', 'Cash Sale'),
        ('other_income', 'Other Income'),
        ('loan_received', 'Loan Received'),
        ('capital_injection', 'Capital Injection'),
        ('refund_received', 'Refund Received'),
        
        # Debit categories (Expenses/Accounts Receivable)
        ('invoice_created', 'Invoice Created'),
        ('purchase', 'Purchase'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('salaries', 'Salaries'),
        ('transport', 'Transport'),
        ('marketing', 'Marketing'),
        ('office_expenses', 'Office Expenses'),
        ('agency_payment', 'Agency Payment'),
        ('loan_payment', 'Loan Payment'),
        ('tax_payment', 'Tax Payment'),
        ('bank_charges', 'Bank Charges'),
        ('other_expense', 'Other Expense'),
    ]
    
    # Basic transaction info
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Reference information
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_id = models.CharField(max_length=100, blank=True, null=True, help_text="Invoice ID if related to invoice")
    notes = models.TextField(blank=True, null=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Financial Transaction'
        verbose_name_plural = 'Financial Transactions'
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.description} - {self.amount}"
    
    @property
    def is_credit(self):
        """Returns True if this is a credit transaction"""
        return self.transaction_type == 'credit'
    
    @property
    def is_debit(self):
        """Returns True if this is a debit transaction"""
        return self.transaction_type == 'debit'


class FinancialSummary(models.Model):
    """
    Cached financial summary for better performance.
    This will be updated whenever financial transactions are added/modified.
    """
    
    # Date range for this summary
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Financial figures (using accounting principles)
    total_debits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_credits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Credits - Debits = Profit
    
    # Invoice figures
    total_invoices = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_settlements = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Combined figures (actual cash position)
    actual_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # income + settlements
    cash_flow = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # actual_income - expenses
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['start_date', 'end_date']
        ordering = ['-end_date']
        verbose_name = 'Financial Summary'
        verbose_name_plural = 'Financial Summaries'
    
    def __str__(self):
        return f"Financial Summary {self.start_date} to {self.end_date}"
