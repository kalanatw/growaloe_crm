from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class FinancialTransaction(models.Model):
    """
    Represents actual business income and expense transactions (cash flow).
    This is separate from invoice settlements and represents real money movement.
    """
    
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    CATEGORY_CHOICES = [
        # Income categories
        ('sales_cash', 'Sales - Cash'),
        ('sales_collection', 'Sales - Collection'),
        ('other_income', 'Other Income'),
        ('loan_received', 'Loan Received'),
        ('capital_injection', 'Capital Injection'),
        
        # Expense categories
        ('purchase', 'Purchase'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('salaries', 'Salaries'),
        ('transport', 'Transport'),
        ('marketing', 'Marketing'),
        ('office_expenses', 'Office Expenses'),
        ('loan_payment', 'Loan Payment'),
        ('tax_payment', 'Tax Payment'),
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


class InvoiceSettlement(models.Model):
    """
    Represents settlements/payments against invoices.
    This tracks how much has been collected against each invoice.
    """
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_note', 'Credit Note'),
    ]
    
    invoice = models.ForeignKey('sales.Invoice', on_delete=models.CASCADE, related_name='settlements')
    settlement_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    # Payment details
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-settlement_date', '-created_at']
        verbose_name = 'Invoice Settlement'
        verbose_name_plural = 'Invoice Settlements'
    
    def __str__(self):
        return f"Settlement - {self.invoice.invoice_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update invoice paid amount and balance
        from django.db.models import Sum
        total_settlements = self.invoice.settlements.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        self.invoice.paid_amount = total_settlements
        self.invoice.balance_due = self.invoice.net_total - self.invoice.paid_amount
        
        # Update invoice status
        if self.invoice.balance_due <= 0:
            self.invoice.status = 'paid'
        elif self.invoice.paid_amount > 0:
            self.invoice.status = 'partial'
        else:
            self.invoice.status = 'pending'
            
        self.invoice.save()


class FinancialSummary(models.Model):
    """
    Cached financial summary for better performance.
    This will be updated whenever financial transactions are added/modified.
    """
    
    # Date range for this summary
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Financial figures
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
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
