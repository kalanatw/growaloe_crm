"""
Simplified serializers for the salesman-centric delivery and settlement workflow.
These serializers present data in a way that's easier for the frontend to consume
and organize by salesman.
"""

from rest_framework import serializers
from django.db.models import Sum, F
from django.utils import timezone
from .models import Delivery, DeliveryItem, BatchAssignment, Product
from sales.models import InvoiceItem
from accounts.models import Salesman


class SalesmanStockItemSerializer(serializers.Serializer):
    """Simplified serializer for individual stock items held by a salesman"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    oldest_batch_date = serializers.DateField(required=False, allow_null=True)
    expiry_warning = serializers.BooleanField(default=False)


class SalesmanOverviewSerializer(serializers.Serializer):
    """Salesman overview for the owner's dashboard"""
    salesman_id = serializers.IntegerField()
    salesman_name = serializers.CharField()
    salesman_phone = serializers.CharField(required=False, allow_null=True)
    total_products = serializers.IntegerField()
    total_stock_quantity = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    stock_by_product = SalesmanStockItemSerializer(many=True)
    today_sales_quantity = serializers.IntegerField()
    today_sales_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_deliveries = serializers.IntegerField()
    last_delivery_date = serializers.DateTimeField(required=False, allow_null=True)


class SettlementItemSerializer(serializers.Serializer):
    """Individual product item in a settlement"""
    delivery_item_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    delivered_quantity = serializers.IntegerField()
    sold_quantity = serializers.IntegerField()
    outstanding_quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_value = serializers.DecimalField(max_digits=12, decimal_places=2)


class SettlementDeliverySerializer(serializers.Serializer):
    """Individual delivery in settlement queue"""
    delivery_id = serializers.IntegerField()
    delivery_number = serializers.CharField()
    delivery_date = serializers.DateTimeField()
    total_items = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_quantity = serializers.IntegerField()
    outstanding_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    items = SettlementItemSerializer(many=True)


class SalesmanSettlementSerializer(serializers.Serializer):
    """Settlement data for a specific salesman"""
    salesman_id = serializers.IntegerField()
    salesman_name = serializers.CharField()
    salesman_phone = serializers.CharField(required=False, allow_null=True)
    deliveries = SettlementDeliverySerializer(many=True)
    total_deliveries = serializers.IntegerField()
    total_outstanding_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    oldest_delivery_date = serializers.DateTimeField(required=False, allow_null=True)


class SettleRequestSerializer(serializers.Serializer):
    """Request serializer for settling a salesman's deliveries"""
    salesman_id = serializers.IntegerField()
    settlement_notes = serializers.CharField(required=False, allow_blank=True)
    return_all_stock = serializers.BooleanField(default=True)
    
    def validate_salesman_id(self, value):
        try:
            salesman = Salesman.objects.get(id=value, is_active=True)
            return value
        except Salesman.DoesNotExist:
            raise serializers.ValidationError("Salesman not found or inactive")


class ReturnedProductSerializer(serializers.Serializer):
    """Products returned during settlement"""
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    value = serializers.DecimalField(max_digits=12, decimal_places=2)


class SettlementResponseSerializer(serializers.Serializer):
    """Response serializer for settlement completion"""
    message = serializers.CharField()
    salesman_name = serializers.CharField()
    settled_deliveries = serializers.IntegerField()
    total_returned_items = serializers.IntegerField()
    total_returned_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    returned_products = ReturnedProductSerializer(many=True)
    settlement_notes = serializers.CharField()


class DailySalesmanSummarySerializer(serializers.Serializer):
    """Daily summary for individual salesman"""
    salesman_id = serializers.IntegerField()
    salesman_name = serializers.CharField()
    deliveries_count = serializers.IntegerField()
    deliveries_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    sales_quantity = serializers.IntegerField()
    sales_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_items = serializers.IntegerField()
    outstanding_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    recommendation = serializers.ChoiceField(
        choices=['no_action', 'review_required', 'settle_recommended']
    )
    efficiency_rate = serializers.DecimalField(max_digits=5, decimal_places=1)


class DailySummarySerializer(serializers.Serializer):
    """Daily settlement summary for owner"""
    date = serializers.DateField()
    summary = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
    salesmen = DailySalesmanSummarySerializer(many=True)


class SimplifiedDeliveryItemSerializer(serializers.ModelSerializer):
    """Simplified delivery item for salesman view"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = DeliveryItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price']
        read_only_fields = ['id', 'product_name', 'product_sku']


class SimplifiedDeliverySerializer(serializers.ModelSerializer):
    """Simplified delivery serializer for salesman-centric views"""
    items = SimplifiedDeliveryItemSerializer(many=True, read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    total_items_count = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'delivery_number', 'salesman', 'salesman_name', 'status',
            'delivery_date', 'notes', 'total_items_count', 'total_value', 'items',
            'created_at'
        ]
        read_only_fields = ['id', 'delivery_number', 'salesman_name', 'total_items_count', 'total_value', 'created_at']
    
    def get_total_items_count(self, obj):
        return obj.total_items
    
    def get_total_value(self, obj):
        return float(obj.total_value)


class CreateSimplifiedDeliverySerializer(serializers.ModelSerializer):
    """Simplified delivery creation - just products and quantities"""
    items = SimplifiedDeliveryItemSerializer(many=True)
    
    class Meta:
        model = Delivery
        fields = ['salesman', 'delivery_date', 'notes', 'items']
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required for a delivery.")
        
        # Check for duplicate products
        product_ids = [item['product'].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products are not allowed in a delivery.")
        
        return items
    
    def create(self, validated_data):
        from django.db import transaction
        
        items_data = validated_data.pop('items')
        delivery = Delivery.objects.create(**validated_data)
        
        with transaction.atomic():
            for item_data in items_data:
                DeliveryItem.objects.create(delivery=delivery, **item_data)
        
        return delivery


class QuickStockCheckSerializer(serializers.Serializer):
    """Quick stock check for a specific salesman"""
    salesman_id = serializers.IntegerField()
    products = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        help_text="List of {product_id: quantity} pairs to check availability"
    )


class StockAvailabilitySerializer(serializers.Serializer):
    """Stock availability response"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    requested_quantity = serializers.IntegerField()
    available_quantity = serializers.IntegerField()
    sufficient = serializers.BooleanField()
    shortage = serializers.IntegerField()


class BulkDeliveryStatusSerializer(serializers.Serializer):
    """Bulk delivery status update"""
    delivery_ids = serializers.ListField(child=serializers.IntegerField())
    new_status = serializers.ChoiceField(
        choices=['pending', 'delivered', 'cancelled', 'settled']
    )
    notes = serializers.CharField(required=False, allow_blank=True)
