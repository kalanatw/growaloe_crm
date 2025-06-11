from django.db import models
from django.core.validators import FileExtensionValidator
from decimal import Decimal


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
