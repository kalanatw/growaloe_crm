from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

from .models import User, Owner, Salesman, Shop, MarginPolicy, SalesmanCashTransaction
from .serializers import (
    UserSerializer, UserProfileSerializer, ChangePasswordSerializer,
    RegisterSerializer, OwnerSerializer, SalesmanSerializer, CreateSalesmanSerializer,
    ShopSerializer, MarginPolicySerializer, ShopSummarySerializer,
    SalesmanSummarySerializer
)
from .permissions import IsOwnerOrReadOnly, IsSalesmanOrReadOnly
from .services import SalesmanBalanceService
from sales.models import Invoice


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
    
    @action(detail=True, methods=['post'], url_path='collect-cash')
    def collect_cash(self, request, pk=None):
        """Record physical cash collection from salesman"""
        from django.db import transaction
        from .serializers import SalesmanCashCollectionSerializer
        from .models import SalesmanCashTransaction
        
        salesman = self.get_object()
        
        # Only owners can collect cash from their salesmen
        if request.user.role != 'owner':
            return Response(
                {'error': 'Only owners can collect cash from salesmen'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify the salesman belongs to this owner
        try:
            owner = request.user.owner_profile
            if salesman.owner != owner:
                return Response(
                    {'error': 'You can only collect cash from your own salesmen'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except:
            return Response(
                {'error': 'Owner profile not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SalesmanCashCollectionSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            
            # Check if salesman has sufficient balance
            if salesman.current_balance < amount:
                return Response(
                    {
                        'error': f'Insufficient balance. Salesman has LKR {salesman.current_balance}, but trying to collect LKR {amount}',
                        'current_balance': float(salesman.current_balance),
                        'requested_amount': float(amount)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                # Calculate the balance after collection
                balance_before = salesman.current_balance
                balance_after = balance_before - amount
                
                # Record cash collection with all balance fields
                collection = serializer.save(
                    salesman=salesman,
                    collected_by=request.user,
                    salesman_balance_before=balance_before,
                    salesman_balance_after=balance_after
                )
                
                # Update salesman balance (reduce by collected amount)
                salesman.current_balance = balance_after
                salesman.save()
                
                # Create cash transaction record
                SalesmanCashTransaction.objects.create(
                    salesman=salesman,
                    transaction_type='settlement',
                    amount=-collection.amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    description=f'Cash collected by {request.user.get_full_name()}',
                    reference_id=collection.reference_number,
                    cash_collection=collection,
                    created_by=request.user
                )
                
                return Response({
                    'collection': SalesmanCashCollectionSerializer(collection).data,
                    'salesman_balance_after': float(salesman.current_balance),
                    'message': f'Cash collection recorded. Salesman balance updated to LKR {salesman.current_balance}'
                }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='cash-collections')
    def cash_collections(self, request, pk=None):
        """Get cash collection history for salesman"""
        from .serializers import SalesmanCashCollectionSerializer
        
        salesman = self.get_object()
        collections = salesman.cash_collections.all()
        serializer = SalesmanCashCollectionSerializer(collections, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='outstanding-cash')
    def outstanding_cash(self, request, pk=None):
        """Get outstanding cash summary for salesman"""
        from django.db.models import Sum
        from .serializers import OutstandingCashSummarySerializer
        
        salesman = self.get_object()
        
        # Calculate cash from invoices (paid invoices)
        from sales.models import Invoice
        invoices = Invoice.objects.filter(
            salesman=salesman,
            status__in=['paid', 'partial']
        )
        
        total_cash_from_invoices = sum(float(invoice.paid_amount or 0) for invoice in invoices)
        total_cash_collected = float(salesman.cash_collections.aggregate(
            total=Sum('amount')
        )['total'] or 0)
        
        outstanding_cash = total_cash_from_invoices - total_cash_collected
        
        summary_data = {
            'salesman_id': salesman.id,
            'salesman_name': salesman.user.get_full_name(),
            'current_balance': float(salesman.current_balance),
            'total_cash_from_invoices': total_cash_from_invoices,
            'total_cash_collected_by_owner': total_cash_collected,
            'outstanding_cash_with_salesman': outstanding_cash,
            'last_collection_date': salesman.cash_collections.first().collection_date if salesman.cash_collections.exists() else None
        }
        
        serializer = OutstandingCashSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='cash-transactions')
    def cash_transactions(self, request, pk=None):
        """Get cash transaction history for salesman (bank book view)"""
        from .models import SalesmanCashTransaction
        from .serializers import SalesmanCashTransactionSerializer
        
        salesman = self.get_object()
        transactions = SalesmanCashTransaction.objects.filter(
            salesman=salesman
        ).select_related('invoice', 'cash_collection', 'created_by').order_by('-created_at')
        
        serializer = SalesmanCashTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get salesmen summary for current owner"""
        queryset = self.get_queryset()
        serializer = SalesmanSummarySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def agents(self, request):
        """Get all agents (salesman_type='agent')"""
        queryset = self.get_queryset().filter(salesman_type='agent')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def employees(self, request):
        """Get all employees (salesman_type='employee')"""
        queryset = self.get_queryset().filter(salesman_type='employee')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def agent_balance(self, request, pk=None):
        """Get agent balance summary"""
        salesman = self.get_object()
        
        if salesman.salesman_type != 'agent':
            return Response(
                {'error': 'This endpoint is only for agents'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate agent-specific balance data
        from products.models import Delivery, AgentReturn
        from django.db.models import Sum
        
        # Get total purchases (agent deliveries)
        total_purchases = Delivery.objects.filter(
            salesman=salesman,
            is_agent_delivery=True,
            status__in=['delivered', 'settled']
        ).aggregate(total=Sum('agent_purchase_amount'))['total'] or 0
        
        # Get total returns
        total_returns = AgentReturn.objects.filter(
            agent=salesman,
            status__in=['approved', 'processed']
        ).aggregate(total=Sum('return_amount'))['total'] or 0
        
        # Get pending deliveries
        pending_deliveries = Delivery.objects.filter(
            salesman=salesman,
            is_agent_delivery=True,
            agent_payment_status='pending'
        ).count()
        
        # Get pending returns
        pending_returns = AgentReturn.objects.filter(
            agent=salesman,
            status='pending'
        ).count()
        
        # Calculate net position
        net_position = float(total_purchases) - float(total_returns) - float(salesman.current_balance)
        
        balance_data = {
            'agent_id': salesman.id,
            'agent_name': salesman.name,
            'salesman_type': salesman.salesman_type,
            'current_balance': float(salesman.current_balance),
            'total_purchases': float(total_purchases),
            'total_returns': float(total_returns),
            'total_payments_made': float(salesman.total_cash_settled),
            'net_position': net_position,
            'pending_deliveries_count': pending_deliveries,
            'pending_returns_count': pending_returns,
            'last_purchase_date': salesman.deliveries.filter(
                is_agent_delivery=True
            ).order_by('-created_at').first().created_at if salesman.deliveries.filter(
                is_agent_delivery=True
            ).exists() else None,
            'last_payment_date': salesman.last_settlement_date,
        }
        
        from .serializers import AgentBalanceSummarySerializer
        serializer = AgentBalanceSummarySerializer(balance_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def process_agent_payment(self, request, pk=None):
        """Process payment for agent delivery"""
        salesman = self.get_object()
        
        if salesman.salesman_type != 'agent':
            return Response(
                {'error': 'This endpoint is only for agents'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        delivery_id = request.data.get('delivery_id')
        payment_amount = request.data.get('payment_amount', 0)
        payment_method = request.data.get('payment_method', 'cash')
        notes = request.data.get('notes', '')
        
        try:
            from products.models import Delivery
            delivery = Delivery.objects.get(
                id=delivery_id,
                salesman=salesman,
                is_agent_delivery=True
            )
            
            if delivery.agent_payment_status == 'paid':
                return Response(
                    {'error': 'Delivery is already fully paid'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate payment amount
            if payment_amount <= 0:
                return Response(
                    {'error': 'Payment amount must be greater than zero'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if payment_amount > delivery.agent_purchase_amount:
                return Response(
                    {'error': f'Payment amount cannot exceed purchase amount of {delivery.agent_purchase_amount}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process payment
            with transaction.atomic():
                # Update agent balance (increase debt to owner)
                salesman.current_balance += payment_amount
                salesman.save()
                
                # Update delivery payment status
                if payment_amount >= delivery.agent_purchase_amount:
                    delivery.agent_payment_status = 'paid'
                    delivery.agent_payment_date = timezone.now()
                else:
                    delivery.agent_payment_status = 'partial'
                
                delivery.save()
                
                # Create cash transaction record
                SalesmanCashTransaction.objects.create(
                    salesman=salesman,
                    transaction_type='collection',
                    amount=payment_amount,
                    balance_before=salesman.current_balance - payment_amount,
                    balance_after=salesman.current_balance,
                    description=f'Agent payment for delivery {delivery.delivery_number}',
                    reference_type='agent_delivery',
                    reference_id=delivery.id,
                    notes=notes,
                    created_by=request.user
                )
            
            return Response({
                'message': 'Payment processed successfully',
                'delivery_id': delivery.id,
                'payment_amount': float(payment_amount),
                'payment_status': delivery.agent_payment_status,
                'agent_balance': float(salesman.current_balance),
                'remaining_amount': float(delivery.agent_purchase_amount - payment_amount) if delivery.agent_payment_status == 'partial' else 0
            })
            
        except Delivery.DoesNotExist:
            return Response(
                {'error': 'Delivery not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


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
        return Response({'message': 'Balance history endpoint - implementation pending'})
    
    @action(detail=False, methods=['post'])
    def optimize_route(self, request):
        """Calculate optimized route for visiting multiple shops"""
        shop_ids = request.data.get('shop_ids', [])
        start_location = request.data.get('start_location')  # {lat, lng}
        
        if not shop_ids:
            return Response({'error': 'shop_ids is required'}, status=400)
        
        if not start_location or 'lat' not in start_location or 'lng' not in start_location:
            return Response({'error': 'start_location with lat and lng is required'}, status=400)
        
        # Get shops with location data
        queryset = self.get_queryset()
        shops = queryset.filter(
            id__in=shop_ids,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        if not shops.exists():
            return Response({'error': 'No shops found with location data'}, status=400)
        
        # Prepare shop data for route optimization
        shop_locations = []
        for shop in shops:
            shop_locations.append({
                'id': shop.id,
                'name': shop.name,
                'lat': float(shop.latitude),
                'lng': float(shop.longitude),
                'address': shop.address
            })
        
        # For now, return the shops in order (basic implementation)
        # In a production environment, you might want to integrate with
        # Google Maps Directions API or implement a TSP algorithm
        response_data = {
            'start_location': start_location,
            'shops': shop_locations,
            'total_shops': len(shop_locations),
            'message': 'Route optimization data prepared. Use Google Maps API on frontend for actual route calculation.'
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def search_places(self, request):
        """Search for places using Google Places API"""
        import requests
        from django.conf import settings
        
        query = request.data.get('query', '')
        location = request.data.get('location')  # {lat, lng}
        search_type = request.data.get('type', 'establishment')  # restaurant, store, etc.
        
        if not query and not location:
            return Response({'error': 'Query or location is required'}, status=400)
        
        # Get Google Maps API key from environment
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)      
        
        try:
            if query:
                # Text search
                url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
                params = {
                    'query': query,
                    'key': api_key
                }
            else:
                # Nearby search
                url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    'location': f"{location['lat']},{location['lng']}",
                    'radius': 2000,
                    'type': search_type,
                    'key': api_key
                }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'OK':
                # Format results for frontend
                places = []
                for place in data.get('results', []):
                    places.append({
                        'place_id': place.get('place_id'),
                        'name': place.get('name'),
                        'formatted_address': place.get('formatted_address'),
                        'types': place.get('types', []),
                        'rating': place.get('rating'),
                        'location': {
                            'lat': place.get('geometry', {}).get('location', {}).get('lat'),
                            'lng': place.get('geometry', {}).get('location', {}).get('lng')
                        },
                        'business_status': place.get('business_status'),
                        'price_level': place.get('price_level')
                    })
                
                return Response({
                    'status': 'success',
                    'places': places,
                    'total': len(places)
                })
            else:
                return Response({
                    'error': f"Google Places API error: {data.get('status')}",
                    'details': data.get('error_message', '')
                }, status=400)
                
        except Exception as e:
            return Response({
                'error': f"Failed to search places: {str(e)}"
            }, status=500)
    
    @action(detail=False, methods=['post'])
    def geocode_address(self, request):
        """Geocode an address using Google Geocoding API"""
        import requests
        from django.conf import settings
        
        address = request.data.get('address', '')
        
        if not address:
            return Response({'error': 'Address is required'}, status=400)
        
        # Get Google Maps API key from environment
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)

        if not api_key:
            return Response({'error': 'Google Maps API key is not configured'}, status=500)

        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'OK':
                results = []
                for result in data.get('results', []):
                    results.append({
                        'formatted_address': result.get('formatted_address'),
                        'location': {
                            'lat': result.get('geometry', {}).get('location', {}).get('lat'),
                            'lng': result.get('geometry', {}).get('location', {}).get('lng')
                        },
                        'place_id': result.get('place_id'),
                        'types': result.get('types', [])
                    })
                
                return Response({
                    'status': 'success',
                    'results': results,
                    'total': len(results)
                })
            else:
                return Response({
                    'error': f"Geocoding API error: {data.get('status')}",
                    'details': data.get('error_message', '')
                }, status=400)
                
        except Exception as e:
            return Response({
                'error': f"Failed to geocode address: {str(e)}"
            }, status=500)


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


# Cash Flow Management API Endpoints

@extend_schema(
    summary="Get salesman cash summary",
    description="Get cash flow summary for a specific salesman",
    parameters=[
        OpenApiParameter(
            name='days',
            description='Number of days to include in summary (default: 30)',
            required=False,
            type=int
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Cash flow summary",
            examples=[
                OpenApiExample(
                    'Cash Summary',
                    value={
                        'total_collections': 5000.00,
                        'total_settlements': 4500.00,
                        'total_expenses': 200.00,
                        'current_balance': 300.00,
                        'net_cash_position': 500.00,
                        'transaction_count': 15,
                        'period_days': 30
                    }
                )
            ]
        ),
        404: OpenApiResponse(description="Salesman not found")
    },
    tags=['Cash Flow Management']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def salesman_cash_summary(request, salesman_id):
    """Get salesman cash flow summary"""
    try:
        salesman = Salesman.objects.get(id=salesman_id)
        
        # Check permission
        if request.user.role == 'owner' and salesman.owner != request.user.owner_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'salesman' and salesman != request.user.salesman_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        days = int(request.GET.get('days', 30))
        summary = SalesmanBalanceService.get_salesman_cash_summary(salesman, days)
        
        return Response(summary)
    except Salesman.DoesNotExist:
        return Response({'error': 'Salesman not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({'error': 'Invalid days parameter'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Record cash collection",
    description="Record cash collection from invoice settlement",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'invoice_id': {'type': 'integer', 'description': 'Invoice ID'},
                'amount': {'type': 'number', 'description': 'Collection amount'},
                'notes': {'type': 'string', 'description': 'Collection notes'}
            },
            'required': ['invoice_id', 'amount']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Cash collection recorded successfully",
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'message': 'Cash collection recorded successfully',
                        'transaction_id': 123,
                        'new_balance': 1500.00
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="Invalid data provided")
    },
    tags=['Cash Flow Management']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_cash_collection(request):
    """Record cash collection from invoice settlement"""
    try:
        invoice_id = request.data.get('invoice_id')
        amount = request.data.get('amount')
        notes = request.data.get('notes', '')
        
        if not invoice_id or not amount:
            return Response({'error': 'invoice_id and amount are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        invoice = Invoice.objects.get(id=invoice_id)
        
        # Check permission
        if request.user.role == 'owner' and invoice.salesman.owner != request.user.owner_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'salesman' and invoice.salesman != request.user.salesman_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        cash_transaction = SalesmanBalanceService.record_cash_collection(
            salesman=invoice.salesman,
            invoice=invoice,
            amount=amount,
            notes=notes,
            created_by=request.user
        )
        
        return Response({
            'message': 'Cash collection recorded successfully',
            'transaction_id': cash_transaction.id,
            'new_balance': float(invoice.salesman.current_balance)
        })
        
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Get cash transaction history",
    description="Get recent cash transaction history for a salesman",
    parameters=[
        OpenApiParameter(
            name='limit',
            description='Number of transactions to return (default: 50)',
            required=False,
            type=int
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Transaction history",
            examples=[
                OpenApiExample(
                    'Transaction History',
                    value=[
                        {
                            'id': 1,
                            'transaction_type': 'collection',
                            'amount': 500.00,
                            'balance_before': 1000.00,
                            'balance_after': 1500.00,
                            'description': 'Cash collection from Shop ABC - Invoice INV202501001',
                            'created_at': '2025-01-15T10:30:00Z'
                        }
                    ]
                )
            ]
        ),
        404: OpenApiResponse(description="Salesman not found")
    },
    tags=['Cash Flow Management']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cash_transaction_history(request, salesman_id):
    """Get cash transaction history for salesman"""
    try:
        salesman = Salesman.objects.get(id=salesman_id)
        
        # Check permission
        if request.user.role == 'owner' and salesman.owner != request.user.owner_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'salesman' and salesman != request.user.salesman_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        limit = int(request.GET.get('limit', 50))
        transactions = SalesmanBalanceService.get_cash_transaction_history(salesman, limit)
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'id': transaction.id,
                'transaction_type': transaction.transaction_type,
                'transaction_type_display': transaction.get_transaction_type_display(),
                'amount': float(transaction.amount),
                'balance_before': float(transaction.balance_before),
                'balance_after': float(transaction.balance_after),
                'description': transaction.description,
                'notes': transaction.notes,
                'reference_type': transaction.reference_type,
                'reference_id': transaction.reference_id,
                'invoice_number': transaction.invoice.invoice_number if transaction.invoice else None,
                'created_at': transaction.created_at.isoformat(),
                'created_by': transaction.created_by.get_full_name() if transaction.created_by else None
            })
        
        return Response(transaction_data)
        
    except Salesman.DoesNotExist:
        return Response({'error': 'Salesman not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Calculate settlement cash flow",
    description="Calculate available cash flow for settlement",
    responses={
        200: OpenApiResponse(
            description="Settlement cash flow data",
            examples=[
                OpenApiExample(
                    'Cash Flow Data',
                    value={
                        'total_collections': 5000.00,
                        'total_expenses': 200.00,
                        'net_cash_available': 4800.00,
                        'current_balance': 1200.00,
                        'last_settlement_date': '2025-01-10T15:30:00Z'
                    }
                )
            ]
        ),
        404: OpenApiResponse(description="Salesman not found")
    },
    tags=['Cash Flow Management']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def settlement_cash_flow(request, salesman_id):
    """Calculate settlement cash flow for salesman"""
    try:
        salesman = Salesman.objects.get(id=salesman_id)
        
        # Check permission
        if request.user.role == 'owner' and salesman.owner != request.user.owner_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'salesman' and salesman != request.user.salesman_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        cash_flow = SalesmanBalanceService.calculate_settlement_cash_flow(salesman)
        
        # Convert Decimal to float for JSON serialization
        response_data = {
            'total_collections': float(cash_flow['total_collections']),
            'total_expenses': float(cash_flow['total_expenses']),
            'net_cash_available': float(cash_flow['net_cash_available']),
            'current_balance': float(cash_flow['current_balance']),
            'last_settlement_date': cash_flow['last_settlement_date'].isoformat() if cash_flow['last_settlement_date'] else None
        }
        
        return Response(response_data)
        
    except Salesman.DoesNotExist:
        return Response({'error': 'Salesman not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Record advance payment",
    description="Record advance payment from owner to salesman",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'amount': {'type': 'number', 'description': 'Advance amount'},
                'notes': {'type': 'string', 'description': 'Advance notes'}
            },
            'required': ['amount']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Advance payment recorded successfully",
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'message': 'Advance payment recorded successfully',
                        'transaction_id': 124,
                        'new_balance': 800.00
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="Invalid data provided")
    },
    tags=['Cash Flow Management']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_advance_payment(request, salesman_id):
    """Record advance payment from owner to salesman"""
    try:
        salesman = Salesman.objects.get(id=salesman_id)
        
        # Only owners can give advances
        if request.user.role != 'owner' or salesman.owner != request.user.owner_profile:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        amount = request.data.get('amount')
        notes = request.data.get('notes', '')
        
        if not amount or float(amount) <= 0:
            return Response({'error': 'Valid amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        cash_transaction = SalesmanBalanceService.record_advance_payment(
            salesman=salesman,
            amount=amount,
            notes=notes,
            created_by=request.user
        )
        
        return Response({
            'message': 'Advance payment recorded successfully',
            'transaction_id': cash_transaction.id,
            'new_balance': float(salesman.current_balance)
        })
        
    except Salesman.DoesNotExist:
        return Response({'error': 'Salesman not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)