from rest_framework import serializers
from .models import CompanySettings


class CompanySettingsSerializer(serializers.ModelSerializer):
    """Serializer for Company Settings"""
    
    class Meta:
        model = CompanySettings
        fields = [
            'id', 'company_name', 'company_address', 'company_phone', 
            'company_email', 'company_website', 'company_tax_id',
            'company_logo', 'primary_color', 'secondary_color',
            'invoice_prefix', 'invoice_footer_text', 'show_logo_on_invoice',
            'show_company_details', 'default_tax_rate', 'default_currency',
            'currency_symbol', 'default_payment_terms', 'default_due_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_primary_color(self, value):
        """Validate hex color format"""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be in hex format (e.g., #007bff)")
        return value
    
    def validate_secondary_color(self, value):
        """Validate hex color format"""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be in hex format (e.g., #6c757d)")
        return value
