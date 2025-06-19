from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum
from drf_spectacular.utils import extend_schema_field
from .models import Category, Product, SalesmanStock, StockMovement, Delivery, DeliveryItem, CentralStock
from accounts.models import Salesman

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'product_count']
        read_only_fields = ['id', 'created_at', 'product_count']
    
    @extend_schema_field(serializers.IntegerField)
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_quantity = serializers.SerializerMethodField()
    owner_stock = serializers.SerializerMethodField()
    total_salesman_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'category', 'category_name',
            'image_url', 'cost_price', 'base_price', 'unit', 'stock_quantity',
            'owner_stock', 'total_salesman_stock', 'min_stock_level', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name', 
                          'stock_quantity', 'owner_stock', 'total_salesman_stock']

    @extend_schema_field(serializers.IntegerField)
    def get_stock_quantity(self, obj):
        """Get appropriate stock quantity based on user role"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'salesman':
                # For salesmen, show their available stock
                try:
                    central_stock = CentralStock.objects.get(
                        product=obj,
                        location_type='salesman',
                        location_id=request.user.salesman_profile.id
                    )
                    return central_stock.quantity
                except CentralStock.DoesNotExist:
                    return 0
        
        # For owners and others, show total owner stock
        try:
            owner_stock = CentralStock.objects.get(
                product=obj, 
                location_type='owner',
                location_id__isnull=True
            )
            return owner_stock.quantity
        except CentralStock.DoesNotExist:
            return 0

    @extend_schema_field(serializers.IntegerField)
    def get_owner_stock(self, obj):
        """Get owner stock quantity"""
        try:
            owner_stock = CentralStock.objects.get(
                product=obj, 
                location_type='owner',
                location_id__isnull=True
            )
            return owner_stock.quantity
        except CentralStock.DoesNotExist:
            return 0

    @extend_schema_field(serializers.IntegerField)
    def get_total_salesman_stock(self, obj):
        """Get total stock with all salesmen"""
        return CentralStock.objects.filter(
            product=obj, 
            location_type='salesman'
        ).aggregate(total=Sum('quantity'))['total'] or 0


class SalesmanStockSerializer(serializers.ModelSerializer):
    """Serializer for salesman stock using CentralStock"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=2, read_only=True)
    salesman_name = serializers.SerializerMethodField()
    allocated_quantity = serializers.IntegerField(source='quantity', read_only=True)
    available_quantity = serializers.IntegerField(source='quantity', read_only=True)
    
    class Meta:
        model = CentralStock
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'product_base_price', 'salesman_name', 'allocated_quantity', 'available_quantity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'product_name', 'product_sku', 'product_base_price', 'salesman_name']
    
    def get_salesman_name(self, obj):
        """Get salesman name from location_id"""
        if obj.location_type == 'salesman' and obj.location_id:
            try:
                salesman = Salesman.objects.get(id=obj.location_id)
                return salesman.user.get_full_name()
            except Salesman.DoesNotExist:
                return "Unknown Salesman"
        return "Owner"


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    performed_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'salesman', 'salesman_name',
            'movement_type', 'quantity', 'notes', 'reference_id',
            'created_by', 'performed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'product_name', 'salesman_name', 'performed_by_name']


class ProductStockSummarySerializer(serializers.Serializer):
    """Serializer for product stock summary across all salesmen"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    total_stock = serializers.IntegerField()
    allocated_stock = serializers.IntegerField()
    available_stock = serializers.IntegerField()
    salesmen_count = serializers.IntegerField()


class SalesmanStockSummarySerializer(serializers.Serializer):
    """Serializer for salesman stock summary"""
    salesman_id = serializers.IntegerField()
    salesman_name = serializers.CharField()
    total_products = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    products = ProductSerializer(many=True, read_only=True)


class DeliveryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=2, read_only=True)
    total_value = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = DeliveryItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_base_price',
            'quantity', 'unit_price', 'total_value'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'product_base_price', 'total_value']
    
    @extend_schema_field(serializers.DecimalField)
    def get_total_value(self, obj):
        return obj.total_value


class DeliverySerializer(serializers.ModelSerializer):
    items = DeliveryItemSerializer(many=True, read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    total_items = serializers.SerializerMethodField(read_only=True)
    total_value = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'delivery_number', 'salesman', 'salesman_name', 'status',
            'delivery_date', 'notes', 'created_by', 'created_by_name',
            'total_items', 'total_value', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'delivery_number', 'salesman_name', 'created_by_name',
            'total_items', 'total_value', 'created_at', 'updated_at'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_total_items(self, obj):
        return obj.total_items
    
    @extend_schema_field(serializers.DecimalField)
    def get_total_value(self, obj):
        return obj.total_value


class CreateDeliverySerializer(serializers.ModelSerializer):
    items = DeliveryItemSerializer(many=True)
    
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
        
        # Validate quantities
        for item in items:
            if item['quantity'] <= 0:
                raise serializers.ValidationError("Quantity must be greater than 0.")
        
        return items
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        delivery = Delivery.objects.create(**validated_data)
        
        for item_data in items_data:
            DeliveryItem.objects.create(delivery=delivery, **item_data)
        
        return delivery

class CentralStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    salesman_name = serializers.CharField(source='salesman.name', read_only=True)
    
    class Meta:
        model = CentralStock
        fields = [
            'id', 'product', 'product_name', 'product_sku', 
            'location', 'salesman', 'salesman_name', 'quantity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'product_name', 'product_sku', 'salesman_name']

class DeliverySettlementItemSerializer(serializers.Serializer):
    """Serializer for individual items in delivery settlement"""
    delivery_item_id = serializers.IntegerField()
    product_id = serializers.IntegerField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    delivered_quantity = serializers.IntegerField(read_only=True)
    sold_quantity = serializers.IntegerField(read_only=True)
    remaining_quantity = serializers.IntegerField()
    margin_earned = serializers.DecimalField(max_digits=10, decimal_places=2)


class DeliverySettlementSerializer(serializers.Serializer):
    """Serializer for delivery settlement data"""
    delivery_id = serializers.IntegerField(read_only=True)
    delivery_number = serializers.CharField(read_only=True)
    salesman_name = serializers.CharField(read_only=True)
    delivery_date = serializers.DateField(read_only=True)
    settlement_notes = serializers.CharField(required=False, allow_blank=True)
    items = DeliverySettlementItemSerializer(many=True)


class SettleDeliverySerializer(serializers.Serializer):
    """Serializer for settling a delivery"""
    settlement_notes = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of items with delivery_item_id, remaining_quantity, and margin_earned"
    )
