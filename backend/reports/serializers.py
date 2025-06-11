from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import DashboardMetrics, SalesReport, InventoryReport, FinancialReport

User = get_user_model()


class DashboardMetricsSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.business_name', read_only=True)
    
    class Meta:
        model = DashboardMetrics
        fields = [
            'id', 'owner', 'owner_name', 'date', 'total_sales', 'total_invoices', 
            'paid_amount', 'outstanding_amount', 'products_sold', 'low_stock_items',
            'active_salesmen', 'top_salesman_sales', 'active_shops', 'shops_with_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_name']


class SalesReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    owner_name = serializers.CharField(source='owner.business_name', read_only=True)
    
    class Meta:
        model = SalesReport
        fields = [
            'id', 'title', 'report_type', 'format', 'start_date', 'end_date', 
            'owner', 'owner_name', 'salesman', 'salesman_name', 'shop', 'shop_name',
            'report_data', 'file_path', 'file_size', 'generated_by', 'generated_by_name', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at', 'salesman_name', 'shop_name', 'owner_name', 'generated_by_name']
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                "End date cannot be earlier than start date"
            )
        
        return data


class InventoryReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    
    class Meta:
        model = InventoryReport
        fields = [
            'id', 'title', 'report_type', 'start_date', 'end_date', 'report_data',
            'file_path', 'generated_by', 'generated_by_name', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at', 'generated_by_name']


class FinancialReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    owner_name = serializers.CharField(source='owner.business_name', read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    
    class Meta:
        model = FinancialReport
        fields = [
            'id', 'title', 'report_type', 'start_date', 'end_date', 
            'owner', 'owner_name', 'salesman', 'salesman_name',
            'report_data', 'file_path', 'generated_by', 'generated_by_name', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at', 'owner_name', 'salesman_name', 'generated_by_name']
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                "End date cannot be earlier than start date"
            )
        
        return data


class ReportSummarySerializer(serializers.Serializer):
    """Serializer for report summary data"""
    dashboard_metrics_count = serializers.IntegerField()
    sales_reports_count = serializers.IntegerField()
    inventory_reports_count = serializers.IntegerField()
    financial_reports_count = serializers.IntegerField()
    last_generated = serializers.DateTimeField()


class SalesAnalyticsSerializer(serializers.Serializer):
    """Serializer for sales analytics data"""
    period = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_invoices = serializers.IntegerField()
    average_sale = serializers.DecimalField(max_digits=15, decimal_places=2)
    growth_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class ProductPerformanceSerializer(serializers.Serializer):
    """Serializer for product performance data"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2)


class CustomerAnalyticsSerializer(serializers.Serializer):
    """Serializer for customer analytics data"""
    total_customers = serializers.IntegerField()
    new_customers = serializers.IntegerField()
    repeat_customers = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    customer_lifetime_value = serializers.DecimalField(max_digits=15, decimal_places=2)


class RegionalPerformanceSerializer(serializers.Serializer):
    """Serializer for regional/shop performance data"""
    shop_id = serializers.IntegerField()
    shop_name = serializers.CharField()
    shop_location = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_invoices = serializers.IntegerField()
    active_salesmen = serializers.IntegerField()
    average_sale = serializers.DecimalField(max_digits=10, decimal_places=2)
