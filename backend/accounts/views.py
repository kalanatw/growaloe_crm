from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

from .models import User, Owner, Salesman, Shop, MarginPolicy
from .serializers import (
    UserSerializer, UserProfileSerializer, ChangePasswordSerializer,
    RegisterSerializer, OwnerSerializer, SalesmanSerializer, CreateSalesmanSerializer,
    ShopSerializer, MarginPolicySerializer, ShopSummarySerializer,
    SalesmanSummarySerializer
)
from .permissions import IsOwnerOrReadOnly, IsSalesmanOrReadOnly


@extend_schema_view(
    post=extend_schema(
        summary="Register new user",
        description="Create a new user account with the specified role (OWNER, SALESMAN, SHOP)",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                response=UserProfileSerializer,
                description="User created successfully",
                examples=[
                    OpenApiExample(
                        'Successful Registration',
                        value={
                            'message': 'User created successfully',
                            'user': {
                                'id': 1,
                                'username': 'john_doe',
                                'email': 'john@example.com',
                                'first_name': 'John',
                                'last_name': 'Doe',
                                'role': 'OWNER'
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid data provided")
        },
        tags=['Authentication']
    )
)
class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User created successfully',
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="Get user profile",
        description="Retrieve the current authenticated user's profile information",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Authentication']
    ),
    patch=extend_schema(
        summary="Update user profile",
        description="Update the current authenticated user's profile information",
        request=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Authentication']
    )
)
class ProfileView(APIView):
    """User profile management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        summary="Change password",
        description="Change the current authenticated user's password",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password changed successfully",
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'message': 'Password changed successfully'}
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid data provided"),
            401: OpenApiResponse(description="Authentication required")
        },
        tags=['Authentication']
    )
)
class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Get a paginated list of all users in the system",
        parameters=[
            OpenApiParameter(
                name='role',
                description='Filter by user role',
                required=False,
                type=str,
                enum=['OWNER', 'SALESMAN', 'SHOP']
            ),
            OpenApiParameter(
                name='is_active',
                description='Filter by active status',
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name='search',
                description='Search by username, email, first name, or last name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['username', '-username', 'date_joined', '-date_joined']
            )
        ],
        responses={200: UserProfileSerializer(many=True)},
        tags=['User Management']
    ),
    create=extend_schema(
        summary="Create user",
        description="Create a new user account",
        request=UserSerializer,
        responses={
            201: UserProfileSerializer,
            400: OpenApiResponse(description="Invalid data provided")
        },
        tags=['User Management']
    ),
    retrieve=extend_schema(
        summary="Get user details",
        description="Retrieve detailed information about a specific user",
        responses={
            200: UserProfileSerializer,
            404: OpenApiResponse(description="User not found")
        },
        tags=['User Management']
    ),
    update=extend_schema(
        summary="Update user",
        description="Update user information",
        request=UserSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="User not found")
        },
        tags=['User Management']
    ),
    partial_update=extend_schema(
        summary="Partially update user",
        description="Partially update user information",
        request=UserSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="User not found")
        },
        tags=['User Management']
    ),
    destroy=extend_schema(
        summary="Delete user",
        description="Delete a user account",
        responses={
            204: OpenApiResponse(description="User deleted successfully"),
            404: OpenApiResponse(description="User not found")
        },
        tags=['User Management']
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model with comprehensive user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserProfileSerializer
        return UserSerializer
    
    @extend_schema(
        summary="Activate user",
        description="Activate a user account to allow login and access",
        responses={
            200: OpenApiResponse(
                description="User activated successfully",
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'message': 'User activated successfully'}
                    )
                ]
            ),
            404: OpenApiResponse(description="User not found")
        },
        tags=['User Management']
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'User activated successfully'})
    
    @extend_schema(
        summary="Deactivate user",
        description="Deactivate a user account to prevent login and access",
        responses={
            200: OpenApiResponse(
                description="User deactivated successfully",
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'message': 'User deactivated successfully'}
                    )
                ]
            ),
            404: OpenApiResponse(description="User not found")
        },
        tags=['User Management']
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated successfully'})


class OwnerViewSet(viewsets.ModelViewSet):
    """ViewSet for Owner model"""
    queryset = Owner.objects.select_related('user').all()
    serializer_class = OwnerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['business_name', 'user__username', 'tax_id']
    ordering_fields = ['business_name', 'created_at']
    ordering = ['-created_at']


class SalesmanViewSet(viewsets.ModelViewSet):
    """ViewSet for Salesman model"""
    queryset = Salesman.objects.select_related('owner', 'user').annotate(
        shops_count=Count('shops')
    ).all()
    serializer_class = SalesmanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['owner', 'is_active']
    search_fields = ['name', 'user__username', 'owner__business_name']
    ordering_fields = ['name', 'profit_margin', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return CreateSalesmanSerializer
        return SalesmanSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'owner':
            try:
                owner = user.owner_profile
                queryset = queryset.filter(owner=owner)
            except Owner.DoesNotExist:
                queryset = queryset.none()
        elif user.role == 'salesman':
            try:
                salesman = user.salesman_profile
                queryset = queryset.filter(id=salesman.id)
            except Salesman.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def perform_create(self, serializer):
        """Ensure the owner is set to the authenticated user's owner profile"""
        if self.request.user.role != 'owner':
            raise PermissionDenied("Only owners can create salesmen")
        
        try:
            owner = self.request.user.owner_profile
            serializer.save()
        except Owner.DoesNotExist:
            raise ValidationError("Owner profile not found for the authenticated user")
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get salesmen summary for current owner"""
        queryset = self.get_queryset()
        serializer = SalesmanSummarySerializer(queryset, many=True)
        return Response(serializer.data)


class ShopViewSet(viewsets.ModelViewSet):
    """ViewSet for Shop model"""
    queryset = Shop.objects.select_related('salesman', 'salesman__owner', 'user').all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['salesman', 'is_active']
    search_fields = ['name', 'contact_person', 'phone', 'salesman__name']
    ordering_fields = ['name', 'contact_person', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'owner':
            # Owners can access all shops regardless of who created them
            queryset = queryset.all()
        elif user.role == 'developer':
            # Developers can access all shops
            queryset = queryset.all()
        elif user.role == 'salesman':
            try:
                salesman = user.salesman_profile
                queryset = queryset.filter(salesman=salesman)
            except Salesman.DoesNotExist:
                queryset = queryset.none()
        elif user.role == 'shop':
            try:
                shop = user.shop_profile
                queryset = queryset.filter(id=shop.id)
            except Shop.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def perform_create(self, serializer):
        """Automatically set the salesman when a salesman creates a shop"""
        if self.request.user.role == 'salesman':
            try:
                salesman = self.request.user.salesman_profile
                serializer.save(salesman=salesman)
            except Salesman.DoesNotExist:
                # This shouldn't happen for authenticated salesmen, but handle gracefully
                raise ValidationError({'detail': 'Salesman profile not found'})
        elif self.request.user.role == 'owner':
            # For owners, auto-assign to first salesman if not specified
            salesman_id = serializer.validated_data.get('salesman_id')
            if not salesman_id:
                try:
                    owner = self.request.user.owner_profile
                    # Get the first active salesman under this owner
                    first_salesman = Salesman.objects.filter(owner=owner, is_active=True).first()
                    if first_salesman:
                        serializer.save(salesman=first_salesman)
                    else:
                        raise ValidationError({'detail': 'No active salesmen found under this owner. Please create a salesman first or specify salesman_id.'})
                except Owner.DoesNotExist:
                    raise ValidationError({'detail': 'Owner profile not found'})
            else:
                # Owner specified a salesman_id, validate it belongs to them
                try:
                    owner = self.request.user.owner_profile
                    salesman = Salesman.objects.get(id=salesman_id, owner=owner)
                    serializer.save(salesman=salesman)
                except (Owner.DoesNotExist, Salesman.DoesNotExist):
                    raise ValidationError({'salesman_id': 'Invalid salesman or salesman does not belong to this owner'})
        else:
            # For other roles, require salesman_id to be provided
            salesman_id = serializer.validated_data.get('salesman_id')
            if not salesman_id:
                raise ValidationError({'salesman_id': 'This field is required for non-salesman users'})
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get shops summary for current user"""
        queryset = self.get_queryset()
        serializer = ShopSummarySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def balance_history(self, request, pk=None):
        """Get balance history for a shop"""
        shop = self.get_object()
        # This would include transaction history
        # Implementation depends on Transaction model
        return Response({'message': 'Balance history endpoint'})


class MarginPolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for MarginPolicy model"""
    queryset = MarginPolicy.objects.select_related('owner').all()
    serializer_class = MarginPolicySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Only owners can see their margin policies
        if user.role == 'owner':
            try:
                owner = user.owner_profile
                queryset = queryset.filter(owner=owner)
            except Owner.DoesNotExist:
                queryset = queryset.none()
        else:
            queryset = queryset.none()
        
        return queryset
