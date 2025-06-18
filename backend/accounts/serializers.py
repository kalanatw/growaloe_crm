from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, Owner, Salesman, Shop, MarginPolicy


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
    """Serializer for Salesman model"""
    user = UserProfileSerializer(read_only=True)
    owner = OwnerSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    owner_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Salesman
        fields = [
            'id', 'owner', 'owner_id', 'user', 'user_id', 'name',
            'description', 'profit_margin', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
            'credit_limit', 'current_balance', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate shop margin based on user permissions"""
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
