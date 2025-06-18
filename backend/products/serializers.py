from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from .models import Category, Product, SalesmanStock, StockMovement, Delivery, DeliveryItem, Delivery, DeliveryItem

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
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'category', 'category_name',
            'image_url', 'cost_price', 'base_price', 'unit', 'stock_quantity',
            'min_stock_level', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name']

    def get_stock_quantity_for_user(self, obj):
        """Get appropriate stock quantity based on user role"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'salesman':
                stock = SalesmanStock.objects.filter(
                    salesman=request.user.salesman_profile,
                    product=obj
                ).first()
                return stock.available_quantity if stock else 0
        return obj.stock_quantity

    def to_representation(self, instance):
        """Customize the serialized representation"""
        representation = super().to_representation(instance)
        request = self.context.get('request')
        
        # For salesmen, show their available quantity instead of total stock
        if request and request.user.is_authenticated and request.user.role == 'salesman':
            representation['stock_quantity'] = self.get_stock_quantity_for_user(instance)
        
        return representation


class SalesmanStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=2, read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    
    class Meta:
        model = SalesmanStock
        fields = [
            'id', 'salesman', 'salesman_name', 'product', 'product_name', 'product_sku',
            'product_base_price', 'allocated_quantity', 'available_quantity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'product_name', 'product_sku', 'product_base_price', 'salesman_name']
    
    def validate(self, data):
        if data.get('allocated_quantity', 0) < data.get('available_quantity', 0):
            raise serializers.ValidationError(
                "Available quantity cannot be greater than allocated quantity"
            )
        return data


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
