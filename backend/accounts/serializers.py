from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.db import models
from .models import User, Owner, Salesman, Shop, MarginPolicy, SalesmanCashCollection, SalesmanCashTransaction


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'phone', 'address', 'is_active', 'date_joined',
            'password', 'confirm_password'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (without password)"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'username', 'role', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Invalid old password")
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'phone', 'address'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class OwnerSerializer(serializers.ModelSerializer):
    """Serializer for Owner model"""
    user = UserProfileSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Owner
        fields = [
            'id', 'user', 'user_id', 'business_name', 'business_license',
            'tax_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SalesmanSerializer(serializers.ModelSerializer):
    """Serializer for Salesman model with balance information"""
    user = UserProfileSerializer(read_only=True)
    owner = OwnerSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    owner_id = serializers.IntegerField(write_only=True)
    
    # Balance fields
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_cash_collected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_cash_settled = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    net_cash_position = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()
    
    # Additional computed fields
    pending_deliveries_value = serializers.SerializerMethodField()
    outstanding_invoices_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Salesman
        fields = [
            'id', 'owner', 'owner_id', 'user', 'user_id', 'name',
            'description', 'profit_margin', 'is_active',
            'current_balance', 'total_cash_collected', 'total_cash_settled',
            'net_cash_position', 'outstanding_balance', 'last_settlement_date',
            'pending_deliveries_value', 'outstanding_invoices_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_balance', 
                          'total_cash_collected', 'total_cash_settled', 'last_settlement_date']
    
    def get_net_cash_position(self, obj):
        """Calculate net cash position"""
        return float(obj.net_cash_position)
    
    def get_outstanding_balance(self, obj):
        """Calculate outstanding balance"""
        return float(obj.outstanding_balance)
    
    def get_pending_deliveries_value(self, obj):
        """Calculate pending deliveries value (outstanding batch assignments)"""
        from products.models import BatchAssignment
        from django.db.models import Sum, F
        from decimal import Decimal
        
        pending_value = BatchAssignment.objects.filter(
            salesman=obj,
            status__in=['delivered', 'partial']
        ).aggregate(
            total=Sum(F('delivered_quantity') - F('returned_quantity'), output_field=models.DecimalField(max_digits=12, decimal_places=2))
        )['total'] or Decimal('0.00')
        
        return float(pending_value)
    
    def get_outstanding_invoices_value(self, obj):
        """Calculate outstanding invoices value for this salesman"""
        from sales.models import Invoice
        from django.db.models import Sum
        from decimal import Decimal
        
        outstanding_value = Invoice.objects.filter(
            salesman=obj,
            status__in=['pending', 'partial']
        ).aggregate(
            total=Sum('balance_due')
        )['total'] or Decimal('0.00')
        
        return float(outstanding_value)


class CreateSalesmanSerializer(serializers.ModelSerializer):
    """Serializer for creating a new salesman with user account"""
    user = UserSerializer(write_only=True)
    
    class Meta:
        model = Salesman
        fields = [
            'user', 'name', 'description', 'profit_margin', 'is_active'
        ]
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'salesman'  # Ensure the user role is set to salesman
        
        # Create the user first
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            
            # Get the owner from the request context
            request = self.context.get('request')
            if request and hasattr(request.user, 'owner_profile'):
                owner = request.user.owner_profile
                
                # Create the salesman with the created user and owner
                salesman = Salesman.objects.create(
                    user=user,
                    owner=owner,
                    **validated_data
                )
                return salesman
            else:
                # Clean up the created user if owner is not found
                user.delete()
                raise serializers.ValidationError("Owner profile not found for the authenticated user")
        else:
            raise serializers.ValidationError(user_serializer.errors)


class ShopSerializer(serializers.ModelSerializer):
    """Serializer for Shop model"""
    salesman = SalesmanSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    salesman_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    user_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'id', 'salesman', 'salesman_id', 'user', 'user_id', 'name',
            'address', 'contact_person', 'phone', 'email', 'shop_margin',
            'credit_limit', 'current_balance', 'latitude', 'longitude', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate shop margin and coordinates"""
        from core.models import CompanySettings
        
        request = self.context.get('request')
        shop_margin = data.get('shop_margin', 0)
        
        # Only validate for salesmen, owners have no restrictions
        if request and request.user.role == 'salesman':
            settings = CompanySettings.get_settings()
            max_margin = settings.max_shop_margin_for_salesmen
            
            if shop_margin > max_margin:
                raise serializers.ValidationError({
                    'shop_margin': f'Salesmen cannot set shop margin above {max_margin}%. Current: {shop_margin}%'
                })
        
        # Validate coordinate ranges (preserve raw Google Maps precision)
        if 'latitude' in data and data['latitude'] is not None:
            if not (-90 <= float(data['latitude']) <= 90):
                raise serializers.ValidationError({
                    'latitude': 'Latitude must be between -90 and 90 degrees'
                })
        
        if 'longitude' in data and data['longitude'] is not None:
            if not (-180 <= float(data['longitude']) <= 180):
                raise serializers.ValidationError({
                    'longitude': 'Longitude must be between -180 and 180 degrees'
                })
        
        return data


class MarginPolicySerializer(serializers.ModelSerializer):
    """Serializer for MarginPolicy model"""
    owner = OwnerSerializer(read_only=True)
    owner_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MarginPolicy
        fields = [
            'id', 'owner', 'owner_id', 'default_salesman_margin',
            'default_shop_margin', 'allow_salesman_override',
            'allow_shop_override', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShopSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for shop summaries"""
    
    class Meta:
        model = Shop
        fields = ['id', 'name', 'contact_person', 'current_balance']


class SalesmanSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for salesman summaries"""
    shops_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Salesman
        fields = ['id', 'name', 'profit_margin', 'shops_count']


class SalesmanCashCollectionSerializer(serializers.ModelSerializer):
    """Serializer for SalesmanCashCollection model"""
    collected_by_name = serializers.CharField(source='collected_by.get_full_name', read_only=True)
    salesman_name = serializers.CharField(source='salesman.user.get_full_name', read_only=True)
    
    class Meta:
        model = SalesmanCashCollection
        fields = [
            'id', 'salesman', 'salesman_name', 'amount', 'collection_date', 
            'collection_method', 'reference_number', 'notes',
            'salesman_balance_before', 'salesman_balance_after',
            'collected_by', 'collected_by_name', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'salesman_name', 'salesman_balance_before', 'salesman_balance_after',
            'collected_by', 'collected_by_name', 'status', 'created_at', 'updated_at'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate(self, data):
        # Additional validation can be added here
        return data


class OutstandingCashSummarySerializer(serializers.Serializer):
    """Serializer for outstanding cash summary"""
    salesman_id = serializers.IntegerField()
    salesman_name = serializers.CharField()
    current_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cash_from_invoices = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cash_collected_by_owner = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_cash_with_salesman = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_collection_date = serializers.DateField(allow_null=True)


class SalesmanCashTransactionSerializer(serializers.ModelSerializer):
    """Serializer for SalesmanCashTransaction model (bank book view)"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = SalesmanCashTransaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display', 'amount', 
            'balance_before', 'balance_after', 'description', 'reference_type', 
            'reference_id', 'notes', 'created_by', 'created_by_name', 
            'invoice', 'cash_collection', 'created_at'
        ]
        read_only_fields = [
            'id', 'transaction_type_display', 'created_by_name', 'created_at'
        ]