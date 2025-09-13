from rest_framework import serializers
from django.db import models
from .models import Delivery, AgentReturn, Product, Batch
from accounts.models import Salesman


class AgentReturnSerializer(serializers.ModelSerializer):
    """Serializer for AgentReturn model"""
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    delivery_number = serializers.CharField(source='original_delivery.delivery_number', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AgentReturn
        fields = [
            'id', 'return_number', 'agent', 'agent_name', 'original_delivery', 'delivery_number',
            'product', 'product_name', 'product_sku', 'batch', 'batch_number',
            'quantity', 'unit_price', 'return_amount', 'reason', 'reason_display',
            'status', 'status_display', 'approved_by', 'approved_by_name',
            'approved_date', 'processed_date', 'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'return_number', 'return_amount', 'agent_name', 'product_name', 
            'product_sku', 'batch_number', 'delivery_number', 'approved_by_name',
            'created_by_name', 'reason_display', 'status_display', 'approved_date',
            'processed_date', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validate agent return data"""
        agent = data.get('agent')
        original_delivery = data.get('original_delivery')
        product = data.get('product')
        quantity = data.get('quantity', 0)
        
        # Ensure agent is actually an agent type
        if agent and agent.salesman_type != 'agent':
            raise serializers.ValidationError("Returns can only be created for agents")
        
        # Ensure delivery belongs to the agent
        if original_delivery and original_delivery.salesman != agent:
            raise serializers.ValidationError("Delivery does not belong to this agent")
        
        # Ensure delivery is an agent delivery
        if original_delivery and not original_delivery.is_agent_delivery:
            raise serializers.ValidationError("Can only return products from agent deliveries")
        
        # Check if product was in the original delivery
        if original_delivery and product:
            delivery_item = original_delivery.items.filter(product=product).first()
            if not delivery_item:
                raise serializers.ValidationError(
                    f"Product {product.name} was not in delivery {original_delivery.delivery_number}"
                )
            
            # Check return quantity doesn't exceed purchased quantity
            if quantity > delivery_item.quantity:
                raise serializers.ValidationError(
                    f"Return quantity ({quantity}) exceeds purchased quantity ({delivery_item.quantity})"
                )
            
            # Check for existing returns
            existing_returns = AgentReturn.objects.filter(
                original_delivery=original_delivery,
                product=product,
                status__in=['approved', 'processed']
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            
            if existing_returns + quantity > delivery_item.quantity:
                raise serializers.ValidationError(
                    f"Total return quantity would exceed purchased quantity. "
                    f"Already returned: {existing_returns}, Requesting: {quantity}, "
                    f"Purchased: {delivery_item.quantity}"
                )
        
        return data


class AgentDeliverySerializer(serializers.ModelSerializer):
    """Serializer for agent-specific delivery information"""
    salesman_name = serializers.CharField(source='salesman.name', read_only=True)
    salesman_type = serializers.CharField(source='salesman.salesman_type', read_only=True)
    agent_payment_status_display = serializers.CharField(source='get_agent_payment_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'delivery_number', 'salesman', 'salesman_name', 'salesman_type',
            'status', 'delivery_date', 'settlement_date', 'is_agent_delivery',
            'agent_purchase_amount', 'agent_payment_status', 'agent_payment_status_display',
            'agent_payment_date', 'items_count', 'total_items', 'notes', 'settlement_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'delivery_number', 'salesman_name', 'salesman_type', 
            'agent_payment_status_display', 'items_count', 'total_items',
            'created_at', 'updated_at'
        ]
    
    def get_items_count(self, obj):
        """Get number of different products in delivery"""
        return obj.items.count()
    
    def get_total_items(self, obj):
        """Get total quantity of all items in delivery"""
        return sum(item.quantity for item in obj.items.all())


class CreateAgentDeliverySerializer(serializers.ModelSerializer):
    """Serializer for creating agent deliveries with immediate payment requirement"""
    items = serializers.ListField(write_only=True)
    
    class Meta:
        model = Delivery
        fields = [
            'salesman', 'delivery_date', 'notes', 'items'
        ]
    
    def validate(self, data):
        """Validate agent delivery creation"""
        salesman = data.get('salesman')
        items = data.get('items', [])
        
        # Ensure salesman is an agent
        if salesman and salesman.salesman_type != 'agent':
            raise serializers.ValidationError("This endpoint is only for agent deliveries")
        
        # Validate items
        if not items:
            raise serializers.ValidationError("At least one item is required")
        
        for item in items:
            if not all(key in item for key in ['product', 'quantity', 'unit_price']):
                raise serializers.ValidationError("Each item must have product, quantity, and unit_price")
            
            if item['quantity'] <= 0:
                raise serializers.ValidationError("Item quantity must be positive")
            
            if item['unit_price'] <= 0:
                raise serializers.ValidationError("Item unit price must be positive")
        
        return data
    
    def create(self, validated_data):
        """Create agent delivery with immediate stock transfer"""
        from django.db import transaction
        from .models import DeliveryItem
        
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            # Create delivery as agent delivery
            delivery = Delivery.objects.create(
                is_agent_delivery=True,
                agent_payment_status='pending',
                **validated_data
            )
            
            # Create delivery items
            total_amount = 0
            for item_data in items_data:
                delivery_item = DeliveryItem.objects.create(
                    delivery=delivery,
                    product_id=item_data['product'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price']
                )
                total_amount += delivery_item.quantity * delivery_item.unit_price
            
            # Set the total purchase amount
            delivery.agent_purchase_amount = total_amount
            delivery.status = 'delivered'  # Agent deliveries are immediately delivered
            delivery.save()
            
            return delivery