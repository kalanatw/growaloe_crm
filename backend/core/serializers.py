from rest_framework import serializers
from .models import CompanySettings, FinancialTransaction, FinancialSummary
from sales.models import InvoiceSettlement


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


class FinancialTransactionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'id', 'transaction_type', 'date', 'description', 'amount', 'category',
            'reference_number', 'invoice_id', 'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class InvoiceSettlementSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    shop_name = serializers.CharField(source='invoice.shop.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = InvoiceSettlement
        fields = [
            'id', 'invoice', 'invoice_number', 'shop_name', 'settlement_date',
            'total_amount', 'notes', 'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']


class FinancialSummarySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FinancialSummary
        fields = [
            'id', 'start_date', 'end_date', 'total_debits', 'total_credits',
            'net_balance', 'total_invoices', 'total_settlements', 'outstanding_balance',
            'actual_income', 'cash_flow', 'created_at', 'updated_at'
        ]
