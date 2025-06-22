from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from .models import Category, Product, SalesmanStock, StockMovement, Delivery, DeliveryItem, CentralStock, Batch, BatchTransaction, BatchAssignment
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

    def validate(self, data):
        """
        Custom validation for product creation/update
        """
        # Category is now optional - no validation needed
        # Initial quantity is not required anymore
        return data

    @extend_schema_field(serializers.IntegerField)
    def get_stock_quantity(self, obj):
        """Get appropriate stock quantity based on user role"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'salesman':
                # For salesmen, show their available stock
                try:
                    central_stock = CentralStock.objects.filter(
                        product=obj,
                        location_type='salesman',
                        location_id=request.user.salesman_profile.id
                    ).first()
                    return central_stock.quantity if central_stock else 0
                except Exception:
                    return 0
        
        # For owners and others, show total owner stock
        owner_stock_total = CentralStock.objects.filter(
            product=obj, 
            location_type='owner'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        return owner_stock_total

    @extend_schema_field(serializers.IntegerField)
    def get_owner_stock(self, obj):
        """Get owner stock quantity"""
        owner_stock_total = CentralStock.objects.filter(
            product=obj, 
            location_type='owner'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        return owner_stock_total

    @extend_schema_field(serializers.IntegerField)
    def get_total_salesman_stock(self, obj):
        """Get total stock with all salesmen"""
        return CentralStock.objects.filter(
            product=obj, 
            location_type='salesman'
        ).aggregate(total=Sum('quantity'))['total'] or 0


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for product creation without category and initial quantity requirements
    """
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'sku', 'category', 'image_url', 
            'cost_price', 'base_price', 'unit', 'min_stock_level', 'is_active'
        ]
        extra_kwargs = {
            'category': {'required': False, 'allow_null': True},
            'description': {'required': False},
            'image_url': {'required': False},
            'unit': {'default': 'piece'},
            'min_stock_level': {'default': 0},
            'is_active': {'default': True}
        }
    
    def validate_sku(self, value):
        """Ensure SKU is unique"""
        if Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Product with this SKU already exists.")
        return value
    
    def validate_base_price(self, value):
        """Ensure base price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Base price must be greater than 0.")
        return value
    
    def validate_cost_price(self, value):
        """Ensure cost price is not negative"""
        if value < 0:
            raise serializers.ValidationError("Cost price cannot be negative.")
        return value


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


class DeliveryBatchAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for batch assignments related to a delivery"""
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    product_name = serializers.CharField(source='batch.product.name', read_only=True)
    unit_cost = serializers.DecimalField(source='batch.unit_cost', max_digits=10, decimal_places=2, read_only=True)
    manufacturing_date = serializers.DateField(source='batch.manufacturing_date', read_only=True)
    expiry_date = serializers.DateField(source='batch.expiry_date', read_only=True)
    
    class Meta:
        model = BatchAssignment
        fields = [
            'id', 'batch_number', 'product_name', 'quantity', 'delivered_quantity',
            'returned_quantity', 'outstanding_quantity', 'unit_cost',
            'manufacturing_date', 'expiry_date', 'status', 'notes'
        ]
        read_only_fields = ['id', 'outstanding_quantity']


class DeliverySerializer(serializers.ModelSerializer):
    items = DeliveryItemSerializer(many=True, read_only=True)
    batch_assignments = serializers.SerializerMethodField(read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    total_items = serializers.SerializerMethodField(read_only=True)
    total_value = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'delivery_number', 'salesman', 'salesman_name', 'status',
            'delivery_date', 'notes', 'created_by', 'created_by_name',
            'total_items', 'total_value', 'items', 'batch_assignments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'delivery_number', 'salesman_name', 'created_by_name',
            'total_items', 'total_value', 'batch_assignments', 'created_at', 'updated_at'
        ]
    
    @extend_schema_field(DeliveryBatchAssignmentSerializer(many=True))
    def get_batch_assignments(self, obj):
        """Get all batch assignments for this delivery"""
        # Get batch assignments related to this delivery's salesman
        # that were created around the same time as the delivery
        from datetime import timedelta
        
        # For simplicity, get all batch assignments for this salesman
        # In a more refined version, we could track delivery-batch relationships more explicitly
        assignments = BatchAssignment.objects.filter(
            salesman=obj.salesman,
            created_at__gte=obj.created_at - timedelta(minutes=5),
            created_at__lte=obj.created_at + timedelta(minutes=5)
        ).select_related('batch', 'batch__product')
        
        return DeliveryBatchAssignmentSerializer(assignments, many=True).data
    
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
        
        with transaction.atomic():
            for item_data in items_data:
                product = item_data['product']
                requested_quantity = item_data['quantity']
                
                # Create the delivery item
                delivery_item = DeliveryItem.objects.create(delivery=delivery, **item_data)
                
                # Find available batches using FIFO (First In, First Out)
                available_batches = Batch.objects.filter(
                    product=product,
                    current_quantity__gt=0,
                    is_active=True
                ).order_by('manufacturing_date', 'expiry_date')
                
                remaining_to_assign = requested_quantity
                
                for batch in available_batches:
                    if remaining_to_assign <= 0:
                        break
                    
                    # Determine how much we can take from this batch
                    quantity_to_assign = min(batch.current_quantity, remaining_to_assign)
                    
                    if quantity_to_assign > 0:
                        # Create batch assignment
                        assignment = BatchAssignment.objects.create(
                            batch=batch,
                            salesman=delivery.salesman,  # Use the Salesman instance, not User
                            quantity=quantity_to_assign,  # Use 'quantity', not 'assigned_quantity'
                            delivered_quantity=quantity_to_assign,  # Mark as delivered immediately
                            status='delivered',  # Set status to delivered since this is for delivery
                            delivery_date=delivery.delivery_date,
                            notes=f"Assigned via delivery {delivery.delivery_number}",
                            created_by=delivery.created_by
                        )
                        
                        # Update batch current quantity
                        batch.current_quantity -= quantity_to_assign
                        batch.save()
                        
                        # Create batch transaction record
                        BatchTransaction.objects.create(
                            batch=batch,
                            transaction_type='assignment',
                            quantity=-quantity_to_assign,  # Negative for stock out
                            balance_after=batch.current_quantity,
                            reference_type='delivery',
                            reference_id=delivery.id,
                            notes=f"Assigned to {delivery.salesman.user.get_full_name()} via delivery {delivery.delivery_number}",
                            created_by=delivery.created_by
                        )
                        
                        remaining_to_assign -= quantity_to_assign
                
                # Check if we couldn't fulfill the complete request
                if remaining_to_assign > 0:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name}. "
                        f"Requested: {requested_quantity}, Available: {requested_quantity - remaining_to_assign}"
                    )
        
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


class BatchSerializer(serializers.ModelSerializer):
    """Serializer for product batches"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    allocated_quantity = serializers.SerializerMethodField()
    available_quantity = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Batch
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'batch_number',
            'manufacturing_date', 'expiry_date', 'initial_quantity', 'current_quantity',
            'allocated_quantity', 'available_quantity', 'unit_cost', 'notes',
            'is_active', 'is_expired', 'days_until_expiry', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'product_name', 'product_sku',
                          'allocated_quantity', 'available_quantity', 'is_expired', 'days_until_expiry']
    
    @extend_schema_field(serializers.IntegerField)
    def get_allocated_quantity(self, obj):
        return obj.allocated_quantity
    
    @extend_schema_field(serializers.IntegerField)
    def get_available_quantity(self, obj):
        return obj.available_quantity
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_expired(self, obj):
        return obj.is_expired
    
    @extend_schema_field(serializers.IntegerField)
    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry
    
    def validate(self, data):
        # Ensure manufacturing date is not in the future
        if data.get('manufacturing_date') and data['manufacturing_date'] > timezone.now().date():
            raise serializers.ValidationError("Manufacturing date cannot be in the future")
        
        # Ensure expiry date is after manufacturing date
        if (data.get('expiry_date') and data.get('manufacturing_date') and 
            data['expiry_date'] <= data['manufacturing_date']):
            raise serializers.ValidationError("Expiry date must be after manufacturing date")
        
        return data


class BatchTransactionSerializer(serializers.ModelSerializer):
    """Serializer for batch transactions"""
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    product_name = serializers.CharField(source='batch.product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = BatchTransaction
        fields = [
            'id', 'batch', 'batch_number', 'product_name', 'transaction_type',
            'quantity', 'balance_after', 'reference_type', 'reference_id',
            'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'batch_number', 'product_name', 'created_by_name']


class BatchAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for batch assignments to salesmen"""
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    product_name = serializers.CharField(source='batch.product.name', read_only=True)
    product_sku = serializers.CharField(source='batch.product.sku', read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    outstanding_quantity = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = BatchAssignment
        fields = [
            'id', 'batch', 'batch_number', 'product_name', 'product_sku',
            'salesman', 'salesman_name', 'quantity', 'delivered_quantity',
            'returned_quantity', 'outstanding_quantity', 'status',
            'delivery_date', 'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'batch_number', 'product_name',
                          'product_sku', 'salesman_name', 'outstanding_quantity', 'created_by_name']
    
    @extend_schema_field(serializers.IntegerField)
    def get_outstanding_quantity(self, obj):
        return obj.outstanding_quantity
    
    def validate(self, data):
        # Ensure delivered_quantity doesn't exceed assigned quantity
        if data.get('delivered_quantity', 0) > data.get('quantity', 0):
            raise serializers.ValidationError("Delivered quantity cannot exceed assigned quantity")
        
        # Ensure returned_quantity doesn't exceed delivered quantity
        if data.get('returned_quantity', 0) > data.get('delivered_quantity', 0):
            raise serializers.ValidationError("Returned quantity cannot exceed delivered quantity")
        
        return data


class CreateBatchAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for creating batch assignments"""
    
    class Meta:
        model = BatchAssignment
        fields = ['batch', 'salesman', 'quantity', 'notes']
    
    def validate(self, data):
        batch = data['batch']
        quantity = data['quantity']
        
        # Check if batch has enough available quantity
        if batch.available_quantity < quantity:
            raise serializers.ValidationError(
                f"Insufficient batch stock. Available: {batch.available_quantity}, Requested: {quantity}"
            )
        
        return data
    
    def create(self, validated_data):
        # Create the assignment
        assignment = BatchAssignment.objects.create(**validated_data)
        
        # Create batch transaction
        BatchTransaction.objects.create(
            batch=assignment.batch,
            transaction_type='assignment',
            quantity=-assignment.quantity,
            balance_after=assignment.batch.current_quantity,
            reference_type='batch_assignment',
            reference_id=assignment.id,
            notes=f"Assigned to {assignment.salesman.user.get_full_name()}",
            created_by=self.context['request'].user
        )
        
        return assignment
