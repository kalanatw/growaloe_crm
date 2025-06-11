from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Owner, Salesman, Shop
from sales.models import Invoice

User = get_user_model()


class DashboardMetrics(models.Model):
    """Store pre-calculated dashboard metrics for performance"""
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    
    # Sales metrics
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_invoices = models.PositiveIntegerField(default=0)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Product metrics
    products_sold = models.PositiveIntegerField(default=0)
    low_stock_items = models.PositiveIntegerField(default=0)
    
    # Salesman metrics
    active_salesmen = models.PositiveIntegerField(default=0)
    top_salesman_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Shop metrics
    active_shops = models.PositiveIntegerField(default=0)
    shops_with_overdue = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Metrics for {self.owner.business_name} - {self.date}"
    
    class Meta:
        db_table = 'dashboard_metrics'
        unique_together = ['owner', 'date']
        ordering = ['-date']


class SalesReport(models.Model):
    """Generated sales reports"""
    
    REPORT_TYPES = [
        ('daily', 'Daily Sales'),
        ('weekly', 'Weekly Sales'),
        ('monthly', 'Monthly Sales'),
        ('quarterly', 'Quarterly Sales'),
        ('yearly', 'Yearly Sales'),
        ('custom', 'Custom Range'),
    ]
    
    REPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=REPORT_FORMATS, default='pdf')
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Filters
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, null=True, blank=True)
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)
    
    # Report data (stored as JSON)
    report_data = models.JSONField()
    
    # File information
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.PositiveIntegerField(default=0)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.start_date} to {self.end_date}"
    
    class Meta:
        db_table = 'sales_reports'
        ordering = ['-generated_at']


class InventoryReport(models.Model):
    """Generated inventory reports"""
    
    REPORT_TYPES = [
        ('stock_levels', 'Stock Levels'),
        ('low_stock', 'Low Stock Items'),
        ('stock_movements', 'Stock Movements'),
        ('valuation', 'Inventory Valuation'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Date range for movements
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Report data
    report_data = models.JSONField()
    
    # File information
    file_path = models.CharField(max_length=500, blank=True, null=True)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.date()}"
    
    class Meta:
        db_table = 'inventory_reports'
        ordering = ['-generated_at']


class FinancialReport(models.Model):
    """Generated financial reports"""
    
    REPORT_TYPES = [
        ('profit_loss', 'Profit & Loss'),
        ('outstanding', 'Outstanding Payments'),
        ('payment_summary', 'Payment Summary'),
        ('margin_analysis', 'Margin Analysis'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Filters
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, null=True, blank=True)
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, null=True, blank=True)
    
    # Report data
    report_data = models.JSONField()
    
    # File information
    file_path = models.CharField(max_length=500, blank=True, null=True)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.start_date} to {self.end_date}"
    
    class Meta:
        db_table = 'financial_reports'
        ordering = ['-generated_at']
