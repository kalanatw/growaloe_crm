from rest_framework import serializers
from django.db.models import Sum, Count
from decimal import Decimal

from .models import (
    TransactionCategory, 
    FinancialTransaction, 
    DescriptionSuggestion, 
    ProfitSummary,
    CommissionRecord
)


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer for TransactionCategory model"""
    
    transaction_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionCategory
        fields = [
            'id', 'name', 'transaction_type', 'description', 'is_active',
            'transaction_count', 'total_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_transaction_count(self, obj):
        """Get count of transactions for this category"""
        return obj.transactions.count()
    
    def get_total_amount(self, obj):
        """Get total amount of transactions for this category"""
        total = obj.transactions.aggregate(total=Sum('amount'))['total']
        return float(total) if total else 0.0


class FinancialTransactionSerializer(serializers.ModelSerializer):
    """Serializer for FinancialTransaction model"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    transaction_type = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'id', 'transaction_date', 'category', 'category_name', 
            'transaction_type', 'amount', 'description', 'reference_number',
            'notes', 'attachment', 'created_by', 'created_by_name', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'transaction_type']
    
    def create(self, validated_data):
        # Set the current user as created_by
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_amount(self, value):
        """Validate that amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class FinancialTransactionCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating financial transactions"""
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'transaction_date', 'category', 'amount', 'description', 
            'reference_number', 'notes', 'attachment'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSummarySerializer(serializers.Serializer):
    """Serializer for transaction summary data"""
    
    category_name = serializers.CharField()
    transaction_type = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class DescriptionSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for DescriptionSuggestion model"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = DescriptionSuggestion
        fields = [
            'id', 'description', 'category', 'category_name', 
            'frequency', 'last_used', 'created_at'
        ]
        read_only_fields = ['frequency', 'last_used', 'created_at']


class ProfitSummarySerializer(serializers.ModelSerializer):
    """Serializer for ProfitSummary model"""
    
    period_display = serializers.CharField(source='get_period_type_display', read_only=True)
    profit_margin_percentage = serializers.SerializerMethodField()
    expense_ratio = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfitSummary
        fields = [
            'id', 'period_type', 'period_display', 'start_date', 'end_date',
            'total_invoices', 'settled_invoices', 'unsettled_invoices',
            'invoice_total_amount', 'settled_amount', 'unsettled_amount',
            'cost_of_goods_settled', 'cost_of_goods_unsettled',
            'commission_total', 'commission_paid', 'commission_pending',
            'additional_income', 'expenses',
            'realized_profit', 'unrealized_profit', 'spendable_profit',
            'collection_efficiency', 'profit_margin_percentage', 'expense_ratio',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_profit_margin_percentage(self, obj):
        """Calculate profit margin percentage"""
        if obj.settled_amount > 0:
            margin = (obj.realized_profit / obj.settled_amount) * 100
            return float(margin)
        return 0.0
    
    def get_expense_ratio(self, obj):
        """Calculate expense ratio"""
        total_income = obj.settled_amount + obj.additional_income
        if total_income > 0:
            ratio = (obj.expenses / total_income) * 100
            return float(ratio)
        return 0.0


class CommissionRecordSerializer(serializers.ModelSerializer):
    """Serializer for CommissionRecord model"""
    
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    shop_name = serializers.CharField(source='invoice.shop.name', read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    settlement_amount = serializers.DecimalField(
        source='settlement.total_amount', 
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    calculation_basis_display = serializers.CharField(source='get_calculation_basis_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = CommissionRecord
        fields = [
            'id', 'invoice', 'invoice_number', 'settlement', 'salesman', 'salesman_name',
            'shop_name', 'settlement_amount', 'commission_rate', 'commission_amount',
            'calculation_basis', 'calculation_basis_display', 'status', 'status_display',
            'payment_date', 'payment_reference', 'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class FinancialDashboardSerializer(serializers.Serializer):
    """Serializer for financial dashboard data"""
    
    period = serializers.DictField()
    invoice_metrics = serializers.DictField()
    profit_metrics = serializers.DictField()
    financial_transactions = serializers.DictField()
    commission_metrics = serializers.DictField()
    efficiency_metrics = serializers.DictField()


class TransactionFilterSerializer(serializers.Serializer):
    """Serializer for transaction filtering parameters"""
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    transaction_type = serializers.ChoiceField(
        choices=['income', 'expense', 'all'],
        required=False,
        default='all'
    )
    category = serializers.IntegerField(required=False)
    search = serializers.CharField(required=False, max_length=100)
    min_amount = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    max_amount = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    
    def validate(self, data):
        """Validate date range and amount range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        min_amount = data.get('min_amount')
        max_amount = data.get('max_amount')
        
        if min_amount and max_amount and min_amount > max_amount:
            raise serializers.ValidationError("Minimum amount must be less than maximum amount")
        
        return data


class ProfitCalculationRequestSerializer(serializers.Serializer):
    """Serializer for profit calculation requests"""
    
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    period_type = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly', 'yearly'],
        default='monthly'
    )
    
    def validate(self, data):
        """Validate date range"""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before end date")
        return data


class CommissionPaymentSerializer(serializers.Serializer):
    """Serializer for commission payment operations"""
    
    commission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    payment_date = serializers.DateField()
    payment_reference = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False)
    
    def validate_commission_ids(self, value):
        """Validate that commission records exist and are payable"""
        commission_records = CommissionRecord.objects.filter(id__in=value)
        
        if commission_records.count() != len(value):
            raise serializers.ValidationError("Some commission records do not exist")
        
        non_payable = commission_records.exclude(status__in=['calculated', 'pending'])
        if non_payable.exists():
            raise serializers.ValidationError("Some commission records are not in a payable status")
        
        return value


class FinancialReportSerializer(serializers.Serializer):
    """Serializer for financial report data"""
    
    report_type = serializers.CharField()
    period = serializers.DictField()
    summary = serializers.DictField()
    details = serializers.ListField()
    charts = serializers.DictField(required=False)
    
    class Meta:
        fields = ['report_type', 'period', 'summary', 'details', 'charts']
