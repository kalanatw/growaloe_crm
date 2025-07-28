from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, F
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
import logging

from .models import Category, Product, StockMovement, Delivery, DeliveryItem, Batch, BatchTransaction, BatchAssignment, DeliveryExpense, ProductReturn
from .serializers import (
    CategorySerializer, ProductSerializer, ProductCreateSerializer, SalesmanStockSerializer,
    StockMovementSerializer, ProductStockSummarySerializer,
    SalesmanStockSummarySerializer, DeliverySerializer, CreateDeliverySerializer,
    DeliveryItemSerializer, DeliverySettlementSerializer,
    BatchSerializer, BatchTransactionSerializer, BatchAssignmentSerializer, CreateBatchAssignmentSerializer,
    DeliveryExpenseSerializer, ProductReturnSerializer, CreateProductReturnSerializer, ProcessReturnSerializer, StockOverviewSerializer
)
from sales.serializers import BatchRecallSerializer
from accounts.permissions import IsOwnerOrDeveloper, IsAuthenticated

User = get_user_model()
db_logger = logging.getLogger('db_logger')


@extend_schema_view(
    list=extend_schema(
        summary="List categories",
        description="Get a paginated list of product categories",
        parameters=[
            OpenApiParameter(
                name='is_active',
                description='Filter by active status',
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name='search',
                description='Search by category name or description',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['name', '-name', 'created_at', '-created_at']
            )
        ],
        responses={200: CategorySerializer(many=True)},
        tags=['Product Management']
    ),
    create=extend_schema(
        summary="Create category",
        description="Create a new product category (Owner/Developer only)",
        request=CategorySerializer,
        responses={
            201: CategorySerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Product Management']
    ),
    retrieve=extend_schema(
        summary="Get category details",
        description="Retrieve detailed information about a specific category",
        responses={
            200: CategorySerializer,
            404: OpenApiResponse(description="Category not found")
        },
        tags=['Product Management']
    ),
    update=extend_schema(
        summary="Update category",
        description="Update category information (Owner/Developer only)",
        request=CategorySerializer,
        responses={
            200: CategorySerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Category not found")
        },
        tags=['Product Management']
    ),
    partial_update=extend_schema(
        summary="Partially update category",
        description="Partially update category information (Owner/Developer only)",
        request=CategorySerializer,
        responses={
            200: CategorySerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Category not found")
        },
        tags=['Product Management']
    ),
    destroy=extend_schema(
        summary="Delete category",
        description="Delete a category (Owner/Developer only)",
        responses={
            204: OpenApiResponse(description="Category deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Category not found")
        },
        tags=['Product Management']
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product categories with role-based permissions
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        # All roles can view categories
        return queryset

    def get_permissions(self):
        """
        Different permissions for different actions
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Get a paginated list of products with category information",
        parameters=[
            OpenApiParameter(
                name='category',
                description='Filter by category ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='is_active',
                description='Filter by active status',
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name='search',
                description='Search by product name, description, or SKU',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['name', '-name', 'cost_price', '-cost_price', 'base_price', '-base_price', 'created_at', '-created_at']
            )
        ],
        responses={200: ProductSerializer(many=True)},
        tags=['Product Management']
    ),
    create=extend_schema(
        summary="Create product",
        description="Create a new product (Owner/Developer only)",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Product Management']
    ),
    retrieve=extend_schema(
        summary="Get product details",
        description="Retrieve detailed information about a specific product",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Product not found")
        },
        tags=['Product Management']
    ),
    update=extend_schema(
        summary="Update product",
        description="Update product information (Owner/Developer only)",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Product not found")
        },
        tags=['Product Management']
    ),
    partial_update=extend_schema(
        summary="Partially update product",
        description="Partially update product information (Owner/Developer only)",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Product not found")
        },
        tags=['Product Management']
    ),
    destroy=extend_schema(
        summary="Delete product",
        description="Delete a product (Owner/Developer only)",
        responses={
            204: OpenApiResponse(description="Product deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Product not found")
        },
        tags=['Product Management']
    )
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products with comprehensive product operations
    """
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['name', 'cost_price', 'base_price', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """
        Return different serializers based on action
        """
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter products by owner for owner role
        if self.request.user.role == 'owner':
            try:
                owner = self.request.user.owner_profile
                queryset = queryset.filter(owner=owner)
            except:
                # If owner profile doesn't exist, return empty queryset
                queryset = queryset.none()
        elif self.request.user.role == 'salesman':
            try:
                # Salesmen can only see products from their owner
                salesman = self.request.user.salesman_profile
                queryset = queryset.filter(owner=salesman.owner)
            except:
                queryset = queryset.none()
        elif self.request.user.role == 'shop':
            try:
                # Shops can only see products from their salesman's owner
                shop = self.request.user.shop_profile
                queryset = queryset.filter(owner=shop.salesman.owner)
            except:
                queryset = queryset.none()
        # Developers can see all products (no filtering)
        
        return queryset

    def get_permissions(self):
        """
        Different permissions for different actions
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Handle product creation with enhanced logging and owner assignment
        """
        db_logger.info(f"Creating new product by user: {self.request.user.username}")
        db_logger.info(f"Product data: {serializer.validated_data}")
        
        # Get the owner for the current user
        owner = None
        if self.request.user.role == 'owner':
            try:
                owner = self.request.user.owner_profile
            except:
                raise serializers.ValidationError("Owner profile not found for user")
        else:
            raise serializers.ValidationError("Only owners can create products")
        
        product = serializer.save(created_by=self.request.user, owner=owner)
        
        db_logger.info(f"Product created successfully: ID={product.id}, SKU={product.sku}, Name={product.name}")
        db_logger.info(f"Owner: {owner.business_name}, Category: {product.category.name if product.category else 'None'}")
        
        # No initial stock creation - stock will be managed via batch system

    def perform_update(self, serializer):
        """
        Handle product updates with enhanced logging
        """
        original_product = self.get_object()
        db_logger.info(f"Updating product: ID={original_product.id}, SKU={original_product.sku}")
        db_logger.info(f"Updated data: {serializer.validated_data}")
        
        product = serializer.save()
        
        db_logger.info(f"Product updated successfully: ID={product.id}, SKU={product.sku}")

    def perform_destroy(self, instance):
        """
        Handle product deletion with enhanced logging
        """
        db_logger.info(f"Deleting product: ID={instance.id}, SKU={instance.sku}, Name={instance.name}")
        
        # Check if product has stock
        total_stock = instance.total_stock
        
        if total_stock > 0:
            db_logger.warning(f"Attempting to delete product with existing stock: {total_stock}")
            raise serializers.ValidationError(
                f"Cannot delete product with existing stock. Current stock: {total_stock}"
            )
        
        super().perform_destroy(instance)
        db_logger.info(f"Product deleted successfully: ID={instance.id}")

    @extend_schema(
        summary="Get stock summary for all products",
        description="Get comprehensive stock summary across all products and salesmen",
        responses={
            200: OpenApiResponse(
                response=ProductStockSummarySerializer(many=True),
                description="Stock summary for all products",
                examples=[
                    OpenApiExample(
                        "Stock Summary Response",
                        value=[
                            {
                                "product_id": 1,
                                "product_name": "Aloe Vera Gel",
                                "product_sku": "ALV001",
                                "total_stock": 100,
                                "allocated_stock": 20,
                                "available_stock": 80,
                                "salesmen_count": 3
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'])
    def stock_summary(self, request):
        """
        Get stock summary for all products using Batch system (NEW)
        """
        db_logger.info(f"Stock summary requested by user: {request.user.username}")
        
        # Use the same filtering logic as get_queryset
        products = self.get_queryset().filter(is_active=True)

        summary_data = []
        for product in products:
            # Get total available stock from Batches (NEW APPROACH)
            total_stock = Batch.objects.filter(
                product=product,
                is_active=True
            ).aggregate(total=Sum('current_quantity'))['total'] or 0
            
            # Get allocated stock (assigned to salesmen via BatchAssignments)
            allocated_stock = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['delivered', 'partial']
            ).aggregate(total=Sum('delivered_quantity'))['total'] or 0
            
            # Get returned stock (returned by salesmen)
            returned_stock = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['delivered', 'partial']
            ).aggregate(total=Sum('returned_quantity'))['total'] or 0
            
            # Get pending returns (not yet approved/disposed) - include all assignment statuses
            pending_returns = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['pending', 'delivered', 'partial']  # Include 'pending' for settlement returns
            ).aggregate(total=Sum('pending_return_quantity'))['total'] or 0
            
            # Calculate available stock - since total_stock uses current_quantity (already reduced by allocations)
            # we don't need to subtract allocations again (that would be double subtraction)
            net_allocated = (allocated_stock or 0) - (returned_stock or 0)
            available_stock = total_stock  # current_quantity already reflects allocations
            
            # Count unique salesmen with active assignments for this product
            salesmen_count = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['delivered', 'partial']
            ).values('salesman').distinct().count()

            summary_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_sku': product.sku,
                'total_stock': total_stock,  # Total in all batches
                'allocated_stock': net_allocated,  # Net allocated to salesmen  
                'available_stock': available_stock,  # Available for delivery creation
                'pending_returns': pending_returns,  # Returns awaiting approval/disposal
                'salesmen_count': salesmen_count
            })

        db_logger.info(f"Stock summary generated for {len(summary_data)} products using Batch system")
        serializer = ProductStockSummarySerializer(summary_data, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get detailed stock overview for a product",
        description="Get detailed stock breakdown including returns and sales data",
        responses={
            200: OpenApiResponse(
                response=StockOverviewSerializer,
                description="Detailed stock overview",
            )
        }
    )
    @action(detail=True, methods=['get'])
    def stock_overview(self, request, pk=None):
        """Get detailed stock overview for a specific product"""
        try:
            product = self.get_object()
            today = timezone.now().date()
            
            # Get basic stock data
            total_stock = Batch.objects.filter(
                product=product,
                is_active=True
            ).aggregate(total=Sum('current_quantity'))['total'] or 0
            
            allocated_stock = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['delivered', 'partial']
            ).aggregate(total=Sum('delivered_quantity'))['total'] or 0
            
            returned_stock = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['delivered', 'partial']
            ).aggregate(total=Sum('returned_quantity'))['total'] or 0
            
            pending_returns = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['pending', 'delivered', 'partial']  # Include 'pending' for settlement returns
            ).aggregate(total=Sum('pending_return_quantity'))['total'] or 0
            
            # Get today's return data
            approved_returns_today = ProductReturn.objects.filter(
                batch_assignment__batch__product=product,
                status='approved',
                processed_date__date=today
            ).aggregate(total=Sum('return_quantity'))['total'] or 0
            
            disposed_returns_today = ProductReturn.objects.filter(
                batch_assignment__batch__product=product,
                status='disposed',
                processed_date__date=today
            ).aggregate(total=Sum('return_quantity'))['total'] or 0
            
            # Get today's sales (this would need to be implemented based on your sales model)
            sales_today = 0  # Placeholder - implement based on your sales tracking
            
            # Calculate available stock (total - net allocated, pending returns don't affect this)
            net_allocated = allocated_stock - returned_stock
            available_stock = total_stock - net_allocated
            
            # Get salesman breakdown
            salesman_breakdown = []
            assignments = BatchAssignment.objects.filter(
                batch__product=product,
                status__in=['delivered', 'partial']
            ).select_related('salesman', 'salesman__user').values(
                'salesman__id', 'salesman__user__first_name', 'salesman__user__last_name'
            ).annotate(
                outstanding=Sum('delivered_quantity') - Sum('returned_quantity'),
                pending_returns=Sum('pending_return_quantity')
            )
            
            for assignment in assignments:
                if assignment['outstanding'] > 0 or assignment['pending_returns'] > 0:
                    salesman_breakdown.append({
                        'salesman_id': assignment['salesman__id'],
                        'salesman_name': f"{assignment['salesman__user__first_name']} {assignment['salesman__user__last_name']}",
                        'outstanding_quantity': assignment['outstanding'],
                        'pending_returns': assignment['pending_returns']
                    })
            
            overview_data = {
                'product_id': product.id,
                'product_name': product.name,
                'product_sku': product.sku,
                'total_stock': total_stock,
                'allocated_stock': net_allocated,
                'available_stock': available_stock,
                'pending_returns': pending_returns,
                'approved_returns_today': approved_returns_today,
                'disposed_returns_today': disposed_returns_today,
                'sales_today': sales_today,
                'salesmen_count': len(salesman_breakdown),
                'low_stock_alert': available_stock <= product.min_stock_level,
                'salesman_breakdown': salesman_breakdown
            }
            
            serializer = StockOverviewSerializer(overview_data)
            return Response(serializer.data)
            
        except Exception as e:
            db_logger.error(f"Error getting stock overview for product {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to get stock overview'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get stock distribution by salesman",
        description="Get stock distribution for a specific product across all salesmen",
        responses={
            200: OpenApiResponse(
                response=SalesmanStockSerializer(many=True),
                description="Stock distribution by salesman",
                examples=[
                    OpenApiExample(
                        "Stock Distribution Response",
                        value=[
                            {
                                "id": 1,
                                "salesman": 1,
                                "salesman_name": "John Smith",
                                "product": 1,
                                "product_name": "Aloe Vera Gel",
                                "quantity": 50,
                                "allocated_quantity": 10
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Product Management']
    )
    @action(detail=True, methods=['get'])
    def stock_by_salesman(self, request, pk=None):
        """
        Get stock distribution for a specific product across salesmen using batch assignments
        """
        product = self.get_object()
        
        # Get batch assignments for this product
        assignments = BatchAssignment.objects.filter(
            batch__product=product,
            status__in=['delivered', 'partial']
        ).select_related('salesman__user', 'batch')
        
        # Group by salesman and aggregate
        salesman_stocks = {}
        for assignment in assignments:
            salesman_id = assignment.salesman.id
            if salesman_id not in salesman_stocks:
                salesman_stocks[salesman_id] = {
                    'salesman': assignment.salesman,
                    'total_outstanding': 0,
                    'assignments': []
                }
            
            outstanding = assignment.outstanding_quantity
            salesman_stocks[salesman_id]['total_outstanding'] += outstanding
            salesman_stocks[salesman_id]['assignments'].append({
                'batch_number': assignment.batch.batch_number,
                'outstanding_quantity': outstanding
            })
        
        # Create response
        stock_data = []
        for salesman_id, data in salesman_stocks.items():
            if data['total_outstanding'] > 0:
                stock_data.append({
                    'salesman_id': salesman_id,
                    'salesman_name': data['salesman'].user.get_full_name(),
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_sku': product.sku,
                    'total_outstanding_quantity': data['total_outstanding'],
                    'batch_assignments': data['assignments']
                })
        
        return Response(stock_data)

    @extend_schema(
        summary="Get all products for invoice creation (owners only)",
        description="Get all active products with stock information for owners to create invoices directly",
        responses={
            200: OpenApiResponse(
                description="Products available for invoice creation",
                examples=[
                    OpenApiExample(
                        "Products for Invoice Response",
                        value={
                            "stocks": [
                                {
                                    "id": "product_1",
                                    "product": 1,
                                    "product_name": "Aloe Vera Gel",
                                    "product_sku": "ALV001",
                                    "product_base_price": 25.00,
                                    "available_quantity": 100,
                                    "category": "Skincare"
                                }
                            ],
                            "summary": {
                                "total_products": 1,
                                "total_available_quantity": 100,
                                "total_stock_value": 2500.00
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'])
    def for_invoice_creation(self, request):
        """
        Get all products available for invoice creation (owners only)
        Owners can create invoices directly from product stock without delivery restrictions
        """
        if request.user.role not in ['owner', 'developer']:
            return Response(
                {'error': 'Permission denied. Only owners can access direct product stock.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all active products with available batch stock (NEW APPROACH)
        from decimal import Decimal
        from django.db.models import DecimalField
        
        # Use the same filtering logic as get_queryset to filter by owner
        products_with_stock = self.get_queryset().filter(
            is_active=True,
            batches__current_quantity__gt=0,
            batches__is_active=True
        ).distinct().prefetch_related('batches', 'category')
        
        stock_data = []
        for product in products_with_stock:
            # Calculate total available quantity from all active batches
            total_available = Batch.objects.filter(
                product=product,
                current_quantity__gt=0,
                is_active=True
            ).aggregate(total=Sum('current_quantity'))['total'] or 0
            
            if total_available > 0:
                # Calculate total stock value based on batch costs
                total_value = Batch.objects.filter(
                    product=product,
                    current_quantity__gt=0,
                    is_active=True
                ).aggregate(
                    value=Sum(F('current_quantity') * F('unit_cost'), output_field=DecimalField())
                )['value'] or Decimal('0.00')
                
                stock_data.append({
                    'id': f"product_{product.id}",
                    'product': product.id,
                    'product_name': product.name,
                    'product_sku': product.sku,
                    'product_base_price': float(product.base_price),
                    'available_quantity': total_available,
                    'category': product.category.name if product.category else 'Uncategorized',
                    # Add fields to match SalesmanStock interface
                    'salesman': None,
                    'salesman_name': 'Batch Stock',
                    'allocated_quantity': total_available,
                    'total_value': float(total_value),
                    'created_at': product.created_at.isoformat(),
                    'updated_at': product.updated_at.isoformat(),
                })
        
        return Response({
            'stocks': stock_data,
            'summary': {
                'total_products': len(stock_data),
                'total_available_quantity': sum(item['available_quantity'] for item in stock_data),
                'total_stock_value': sum(item.get('total_value', 0) for item in stock_data)
            }
        })

    @extend_schema(
        summary="Add stock to product",
        description="Add stock to a product with batch management (Owner/Developer only)",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'quantity': {'type': 'integer', 'minimum': 1, 'description': 'Quantity to add'},
                    'notes': {'type': 'string', 'description': 'Optional notes for the stock addition'},
                    'batch_number': {'type': 'string', 'description': 'Optional batch number (auto-generated if not provided)'},
                    'expiry_date': {'type': 'string', 'format': 'date', 'description': 'Optional expiry date for the batch'},
                    'cost_per_unit': {'type': 'number', 'description': 'Optional cost per unit (uses product cost_price if not provided)'}
                },
                'required': ['quantity']
            }
        },
        responses={
            200: OpenApiResponse(
                description="Stock added successfully",
                response={
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean'},
                        'message': {'type': 'string'},
                        'old_quantity': {'type': 'integer'},
                        'new_quantity': {'type': 'integer'},
                        'added_quantity': {'type': 'integer'},
                        'batch_id': {'type': 'integer'},
                        'batch_number': {'type': 'string'}
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Product not found")
        },
        tags=['Product Management']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrDeveloper])
    def add_stock(self, request, pk=None):
        """
        Add stock to a product with batch management
        """
        product = self.get_object()
        quantity = request.data.get('quantity')
        notes = request.data.get('notes')
        batch_number = request.data.get('batch_number')
        expiry_date = request.data.get('expiry_date')
        cost_per_unit = request.data.get('cost_per_unit')
        
        if not quantity or quantity <= 0:
            return Response(
                {'error': 'Quantity must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse expiry_date if provided
        parsed_expiry_date = None
        if expiry_date:
            try:
                from datetime import datetime
                parsed_expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid expiry_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Parse cost_per_unit if provided
        parsed_cost_per_unit = None
        if cost_per_unit:
            try:
                parsed_cost_per_unit = float(cost_per_unit)
                if parsed_cost_per_unit < 0:
                    return Response(
                        {'error': 'Cost per unit must be non-negative'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid cost_per_unit format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            result = product.add_stock(
                quantity=int(quantity),
                user=request.user,
                notes=notes,
                batch_number=batch_number,
                expiry_date=parsed_expiry_date,
                cost_per_unit=parsed_cost_per_unit
            )
            
            return Response({
                'success': True,
                'message': f'Successfully added {quantity} units to {product.name} (Batch: {result["batch_number"]})',
                **result
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Reduce stock from product",
        description="Reduce stock quantity from a product (Owner/Developer only)",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'quantity': {'type': 'integer', 'minimum': 1, 'description': 'Quantity to reduce'},
                    'notes': {'type': 'string', 'description': 'Optional notes for the stock reduction'},
                    'reason': {'type': 'string', 'enum': ['adjustment', 'damage', 'return'], 'description': 'Reason for stock reduction'}
                },
                'required': ['quantity']
            }
        },
        responses={
            200: OpenApiResponse(
                description="Stock reduced successfully",
                response={
                    'type': 'object',
                    'properties': {
                        'success': {'type': 'boolean'},
                        'message': {'type': 'string'},
                        'old_quantity': {'type': 'integer'},
                        'new_quantity': {'type': 'integer'},
                        'reduced_quantity': {'type': 'integer'}
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid data or insufficient stock"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Product not found")
        },
        tags=['Product Management']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrDeveloper])
    def reduce_stock(self, request, pk=None):
        """
        Reduce stock from a product
        """
        product = self.get_object()
        quantity = request.data.get('quantity')
        notes = request.data.get('notes')
        reason = request.data.get('reason', 'adjustment')
        
        if not quantity or quantity <= 0:
            return Response(
                {'error': 'Quantity must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = product.reduce_stock(
                quantity=int(quantity),
                user=request.user,
                notes=notes,
                movement_type=reason
            )
            
            return Response({
                'success': True,
                'message': f'Successfully reduced {quantity} units from {product.name}',
                **result
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Get real-time stock status",
        description="Get current stock levels including owner stock and salesman allocations",
        responses={
            200: OpenApiResponse(
                description="Stock status retrieved successfully",
                response={
                    'type': 'object',
                    'properties': {
                        'owner_stock': {'type': 'integer'},
                        'total_allocated': {'type': 'integer'},
                        'total_available': {'type': 'integer'},
                        'low_stock_alert': {'type': 'boolean'},
                        'salesman_allocations': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'salesman_name': {'type': 'string'},
                                    'allocated': {'type': 'integer'},
                                    'available': {'type': 'integer'},
                                    'sold': {'type': 'integer'}
                                }
                            }
                        }
                    }
                }
            ),
            404: OpenApiResponse(description="Product not found")
        },
        tags=['Product Management']
    )
    @action(detail=True, methods=['get'])
    def stock_status(self, request, pk=None):
        """
        Get real-time stock status for a product using batch system
        """
        product = self.get_object()
        
        # Get salesman allocations from batch assignments
        assignments = BatchAssignment.objects.filter(
            batch__product=product,
            status__in=['delivered', 'partial']
        ).select_related('salesman__user')
        
        # Group by salesman
        salesman_data = {}
        total_allocated = 0
        
        for assignment in assignments:
            salesman_id = assignment.salesman.id
            if salesman_id not in salesman_data:
                salesman_data[salesman_id] = {
                    'salesman_name': assignment.salesman.user.get_full_name(),
                    'allocated': 0,
                    'available': 0,
                    'sold': 0
                }
            
            outstanding = assignment.outstanding_quantity
            salesman_data[salesman_id]['allocated'] += assignment.delivered_quantity
            salesman_data[salesman_id]['available'] += outstanding
            salesman_data[salesman_id]['sold'] += (assignment.delivered_quantity - outstanding)
            total_allocated += outstanding
        
        # Get owner stock (unallocated batches)
        owner_stock_quantity = product.total_stock - total_allocated
        
        return Response({
            'owner_stock': owner_stock_quantity,
            'total_allocated': total_allocated,
            'total_available': total_allocated,
            'low_stock_alert': product.is_low_stock,
            'salesman_allocations': list(salesman_data.values())
        })

    @extend_schema(
        summary="Get available products for salesman",
        description="Get products with total available quantities for the authenticated salesman",
        responses={
            200: OpenApiResponse(
                description="List of available products with quantities",
                examples=[
                    OpenApiExample(
                        name="Available products",
                        value=[
                            {
                                "product_id": 1,
                                "product_name": "Aloevera Drink 200ml",
                                "product_sku": "ALS001",
                                "total_available_quantity": 1061,
                                "base_price": 180.00,
                                "cost_price": 150.00,
                                "unit": "pcs"
                            }
                        ]
                    )
                ]
            ),
            403: OpenApiResponse(description="Only salesmen can access this endpoint")
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'], url_path='salesman-available-products')
    def salesman_available_products(self, request):
        """Get products with total available quantities for the authenticated salesman"""
        if request.user.role != 'salesman':
            return Response(
                {'error': 'Only salesmen can access this endpoint'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            salesman = request.user.salesman_profile
        except AttributeError:
            return Response(
                {'error': 'Salesman profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get products with available quantities
        from collections import defaultdict
        
        # Get batch assignments for this salesman
        assignments = BatchAssignment.objects.filter(
            salesman=salesman,
            status__in=['delivered', 'partial'],
            batch__is_active=True
        ).exclude(
            batch__expiry_date__lt=timezone.now().date()
        ).select_related('batch__product').annotate(
            available_qty=F('delivered_quantity') - F('returned_quantity')
        ).filter(available_qty__gt=0)
        
        # Aggregate by product
        product_quantities = defaultdict(int)
        product_info = {}
        
        for assignment in assignments:
            product = assignment.batch.product
            
            # For delivered assignments, the salesman can sell what was delivered to them
            # The batch current quantity constraint only applies when creating new assignments from the batch
            assignment_available = assignment.available_qty
            
            if assignment_available > 0:
                product_quantities[product.id] += assignment_available
                
                if product.id not in product_info:
                    product_info[product.id] = {
                        'product_id': product.id,
                        'product_name': product.name,
                        'product_sku': product.sku,
                        'base_price': float(product.base_price),
                        'cost_price': float(product.cost_price),
                        'unit': product.unit,
                    }
        
        # Build response
        available_products = []
        for product_id, total_qty in product_quantities.items():
            if total_qty > 0:  # Only include products with available stock
                product_data = product_info[product_id].copy()
                product_data['total_available_quantity'] = total_qty
                available_products.append(product_data)
        
        # Sort by product name
        available_products.sort(key=lambda x: x['product_name'])
        
        return Response(available_products, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List salesman stock allocations",
        description="Get a paginated list of stock allocations to salesmen based on user permissions",
        parameters=[
            OpenApiParameter(
                name='salesman',
                description='Filter by salesman ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='product',
                description='Filter by product ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='search',
                description='Search by product name/SKU or salesman name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['quantity', '-quantity', 'allocated_quantity', '-allocated_quantity', 'last_updated', '-last_updated']
            )
        ],
        responses={200: SalesmanStockSerializer(many=True)},
        tags=['Product Management']
    ),
    create=extend_schema(
        summary="Create stock allocation",
        description="Allocate stock to a salesman (Owner/Developer only)",
        request=SalesmanStockSerializer,
        responses={
            201: SalesmanStockSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Product Management']
    ),
    retrieve=extend_schema(
        summary="Get stock allocation details",
        description="Retrieve detailed information about a specific stock allocation",
        responses={
            200: SalesmanStockSerializer,
            404: OpenApiResponse(description="Stock allocation not found")
        },
        tags=['Product Management']
    ),
    update=extend_schema(
        summary="Update stock allocation",
        description="Update stock allocation information (Owner/Developer only)",
        request=SalesmanStockSerializer,
        responses={
            200: SalesmanStockSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Stock allocation not found")
        },
        tags=['Product Management']
    ),
    partial_update=extend_schema(
        summary="Partially update stock allocation",
        description="Partially update stock allocation information (Owner/Developer only)",
        request=SalesmanStockSerializer,
        responses={
            200: SalesmanStockSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Stock allocation not found")
        },
        tags=['Product Management']
    ),
    destroy=extend_schema(
        summary="Delete stock allocation",
        description="Remove stock allocation (Owner/Developer only)",
        responses={
            204: OpenApiResponse(description="Stock allocation deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Stock allocation not found")
        },
        tags=['Product Management']
    )
)
class SalesmanStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing salesman stock allocations using Batch Assignments
    """
    queryset = BatchAssignment.objects.filter(status__in=['delivered', 'partial']).select_related('batch__product', 'salesman__user').all()
    serializer_class = BatchAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['salesman', 'batch__product']
    search_fields = ['batch__product__name', 'batch__product__sku', 'salesman__user__first_name', 'salesman__user__last_name']
    ordering_fields = ['delivered_quantity', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'salesman':
            # Salesmen can only see their own stock
            return queryset.filter(salesman=user.salesman_profile)
        elif user.role == 'shop':
            # Shops can see stock of salesmen assigned to them - this will need adjustment
            # For now, return empty queryset since shops don't directly manage stock
            return queryset.none()
        else:
            # Owners and Developers can see all stock
            return queryset

    def get_permissions(self):
        """
        Different permissions for different actions
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Get current user's stock",
        description="Get stock allocations for the currently authenticated salesman",
        responses={
            200: OpenApiResponse(
                description="Salesman's stock with summary",
                examples=[
                    OpenApiExample(
                        "My Stock Response",
                        value={
                            "stocks": [
                                {
                                    "id": 1,
                                    "product": 1,
                                    "product_name": "Aloe Vera Gel",
                                    "quantity": 50,
                                    "allocated_quantity": 10
                                }
                            ],
                            "summary": {
                                "total_products": 3,
                                "total_stock_value": 1500.00
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(description="This endpoint is only for salesmen")
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'])
    def my_stock(self, request):
        """
        Get current user's stock from batch assignments (for salesmen)
        """
        if request.user.role != 'salesman':
            return Response(
                {'error': 'This endpoint is only for salesmen'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get salesman's batch assignments
        assignments = BatchAssignment.objects.filter(
            salesman=request.user.salesman_profile,
            status__in=['delivered', 'partial']
        ).select_related('batch__product')

        # Group by product and aggregate
        product_stocks = {}
        total_stock_value = 0
        
        for assignment in assignments:
            product = assignment.batch.product
            outstanding_qty = assignment.outstanding_quantity
            
            if outstanding_qty > 0:
                if product.id not in product_stocks:
                    product_stocks[product.id] = {
                        'product': product,
                        'total_outstanding': 0,
                        'batch_assignments': []
                    }
                
                product_stocks[product.id]['total_outstanding'] += outstanding_qty
                product_stocks[product.id]['batch_assignments'].append({
                    'assignment_id': assignment.id,
                    'batch_number': assignment.batch.batch_number,
                    'outstanding_quantity': outstanding_qty,
                    'expiry_date': assignment.batch.expiry_date.isoformat() if assignment.batch.expiry_date else None
                })
        
        # Convert to response format
        stock_data_list = []
        for product_id, data in product_stocks.items():
            product = data['product']
            total_outstanding = data['total_outstanding']
            stock_value = total_outstanding * product.base_price
            total_stock_value += stock_value
            
            stock_data_list.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_sku': product.sku,
                'product_base_price': float(product.base_price),
                'total_outstanding_quantity': total_outstanding,
                'available_quantity': total_outstanding,
                'batch_assignments': data['batch_assignments'],
                'stock_value': float(stock_value)
            })

        return Response({
            'stocks': stock_data_list,
            'summary': {
                'total_products': len(stock_data_list),
                'total_stock_value': float(total_stock_value),
            }
        })

    @extend_schema(
        summary="Get all available stock",
        description="Get all available stock across all salesmen for invoice creation (Owner/Developer only)",
        responses={
            200: OpenApiResponse(
                description="All available stock with summary",
                examples=[
                    OpenApiExample(
                        "All Stock Response",
                        value={
                            "stocks": [
                                {
                                    "id": 1,
                                    "product": 1,
                                    "product_name": "Aloe Vera Gel",
                                    "available_quantity": 50,
                                    "allocated_quantity": 60,
                                    "salesman_name": "John Smith"
                                }
                            ],
                            "summary": {
                                "total_products": 10,
                                "total_available_quantity": 150
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'])
    def all_available_stock(self, request):
        """
        Get all available stock across all salesmen from deliveries (for owners/developers)
        """
        if request.user.role not in ['owner', 'developer']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all delivery items for salesmen under this owner
        from .models import DeliveryItem
        from accounts.models import Salesman, Owner
        
        # Get the Owner instance for this user
        try:
            owner = Owner.objects.get(user=request.user)
        except Owner.DoesNotExist:
            return Response(
                {'error': 'Owner profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all salesmen under this owner
        salesmen = Salesman.objects.filter(owner=owner)
        
        # Get all delivery items for these salesmen
        delivery_items = DeliveryItem.objects.filter(
            delivery__salesman__in=salesmen
        ).select_related('product', 'delivery__salesman__user')
        
        # Group by salesman and product
        stock_data = {}
        for item in delivery_items:
            salesman_id = item.delivery.salesman.id
            product_id = item.product.id
            key = f"{salesman_id}_{product_id}"
            
            if key not in stock_data:
                stock_data[key] = {
                    'salesman': item.delivery.salesman,
                    'product': item.product,
                    'delivered_quantity': 0,
                    'sold_quantity': 0,
                    'remaining_quantity': 0
                }
            stock_data[key]['delivered_quantity'] += item.quantity
        
        # Calculate sold quantities
        from sales.models import InvoiceItem
        for key, data in stock_data.items():
            sold_qty = InvoiceItem.objects.filter(
                invoice__salesman=data['salesman'],
                product=data['product']
            ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
            
            data['sold_quantity'] = sold_qty
            data['remaining_quantity'] = data['delivered_quantity'] - sold_qty
        
        # Convert to response format
        stocks = []
        for key, data in stock_data.items():
            if data['remaining_quantity'] > 0:  # Only show items with remaining stock
                stocks.append({
                    'id': f"delivery_{key}",
                    'product_id': data['product'].id,
                    'product_name': data['product'].name,
                    'product': {
                        'id': data['product'].id,
                        'name': data['product'].name,
                        'cost_price': str(data['product'].cost_price),
                        'selling_price': str(data['product'].base_price),
                        'category': {
                            'id': data['product'].category.id,
                            'name': data['product'].category.name
                        } if data['product'].category else None
                    },
                    'allocated_quantity': data['remaining_quantity'],
                    'delivered_quantity': data['delivered_quantity'],
                    'sold_quantity': data['sold_quantity'],
                    'salesman_name': data['salesman'].user.get_full_name()
                })
        
        # Calculate summary
        total_products = len(set(stock['product_id'] for stock in stocks))
        total_available = sum(stock['allocated_quantity'] for stock in stocks)
        
        return Response({
            'stocks': stocks,
            'summary': {
                'total_products': total_products,
                'total_available_quantity': total_available
            }
        })


@extend_schema_view(
    list=extend_schema(
        summary="List stock movements",
        description="Get a paginated list of all stock movements for audit and tracking",
        parameters=[
            OpenApiParameter(
                name='product',
                description='Filter by product ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='salesman',
                description='Filter by salesman ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='movement_type',
                description='Filter by movement type',
                required=False,
                type=str,
                enum=['purchase', 'sale', 'allocation', 'return', 'adjustment', 'damage']
            ),
            OpenApiParameter(
                name='search',
                description='Search by product name, notes, or reference ID',
                required=False,
                type=str
            )
        ],
        responses={200: StockMovementSerializer(many=True)},
        tags=['Stock Management']
    ),
    create=extend_schema(
        summary="Create stock movement",
        description="Record a new stock movement (purchase, sale, allocation, etc.)",
        request=StockMovementSerializer,
        responses={201: StockMovementSerializer},
        tags=['Stock Management']
    ),
    retrieve=extend_schema(
        summary="Get stock movement details",
        description="Get detailed information about a specific stock movement",
        responses={200: StockMovementSerializer},
        tags=['Stock Management']
    ),
    update=extend_schema(
        summary="Update stock movement",
        description="Update stock movement details (limited to certain fields)",
        request=StockMovementSerializer,
        responses={200: StockMovementSerializer},
        tags=['Stock Management']
    ),
    partial_update=extend_schema(
        summary="Partially update stock movement",
        description="Partially update stock movement details",
        request=StockMovementSerializer,
        responses={200: StockMovementSerializer},
        tags=['Stock Management']
    ),
    destroy=extend_schema(
        summary="Delete stock movement",
        description="Delete a stock movement record (admin only)",
        responses={204: None},
        tags=['Stock Management']
    )
)
class StockMovementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock movements.
    
    - Owners/Developers: Can view all stock movements
    - Salesmen: Can only view their own stock movements
    - Create: Automatically sets created_by to current user
    """
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'salesman', 'movement_type']
    search_fields = ['product__name', 'notes', 'reference_id']
    ordering_fields = ['created_at', 'quantity', 'movement_type']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter queryset based on user role
        """
        user = self.request.user
        queryset = StockMovement.objects.select_related(
            'product', 'salesman__user', 'created_by'
        )
        
        if user.role in ['owner', 'developer']:
            return queryset
        elif user.role == 'salesman':
            # Salesmen can only see movements related to their stock
            try:
                salesman = user.salesman
                return queryset.filter(salesman=salesman)
            except:
                return queryset.none()
        else:
            return queryset.none()

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user
        """
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get stock movement summary statistics
        """
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_movements = queryset.count()
        inward_movements = queryset.filter(quantity__gt=0).aggregate(
            count=Count('id'), total=Sum('quantity')
        )
        outward_movements = queryset.filter(quantity__lt=0).aggregate(
            count=Count('id'), total=Sum('quantity')
        )
        
        by_type = queryset.values('movement_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('movement_type')
        
        return Response({
            'total_movements': total_movements,
            'inward_movements': {
                'count': inward_movements['count'] or 0,
                'total_quantity': inward_movements['total'] or 0
            },
            'outward_movements': {
                'count': outward_movements['count'] or 0,
                'total_quantity': abs(outward_movements['total'] or 0)  # Make positive for display
            },
            'by_movement_type': list(by_type)
        })

    @action(detail=False, methods=['get'])
    def product_history(self, request):
        """
        Get stock movement history for a specific product
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movements = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(movements, many=True)
        
        # Calculate running totals
        running_total = 0
        history_data = []
        for movement_data in serializer.data:
            running_total += movement_data['quantity']
            movement_data['running_total'] = running_total
            history_data.append(movement_data)
        
        return Response({
            'movements': history_data,
            'current_total': running_total
        })


@extend_schema_view(
    list=extend_schema(
        summary="List deliveries",
        description="Get a paginated list of product deliveries to salesmen",
        parameters=[
            OpenApiParameter(name='salesman', description='Filter by salesman ID', required=False, type=int),
            OpenApiParameter(name='status', description='Filter by delivery status', required=False, type=str),
            OpenApiParameter(name='delivery_date', description='Filter by delivery date (YYYY-MM-DD)', required=False, type=str),
        ]
    ),
    create=extend_schema(
        summary="Create delivery",
        description="Create a new product delivery to a salesman",
        request=CreateDeliverySerializer,
        responses={201: DeliverySerializer}
    ),
    retrieve=extend_schema(
        summary="Get delivery details",
        description="Get detailed information about a specific delivery"
    ),
    update=extend_schema(
        summary="Update delivery",
        description="Update delivery information (only status and notes can be updated after creation)"
    ),
    destroy=extend_schema(
        summary="Delete delivery",
        description="Delete a delivery (only allowed if status is 'pending')"
    )
)
class DeliveryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product deliveries to salesmen.
    
    Owners can create deliveries and assign products to salesmen.
    Salesmen can view their assigned deliveries.
    """
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['salesman', 'status', 'delivery_date']
    search_fields = ['delivery_number', 'salesman__user__first_name', 'salesman__user__last_name', 'notes']
    ordering_fields = ['delivery_date', 'created_at', 'delivery_number']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter deliveries based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'salesman':
            # Salesmen can only see their own deliveries
            return queryset.filter(salesman=user.salesman_profile)
        elif user.role in ['owner', 'developer']:
            # Owners and developers can see all deliveries
            if user.role == 'owner':
                # Filter by salesmen under this owner
                return queryset.filter(salesman__owner=user.owner_profile)
            return queryset
        else:
            return queryset.none()
    
    def get_serializer_class(self):
        """Use different serializers for create and other actions"""
        if self.action == 'create':
            return CreateDeliverySerializer
        return DeliverySerializer
    
    def perform_create(self, serializer):
        """Set the creator when creating a delivery"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Limit what can be updated based on delivery status"""
        instance = self.get_object()
        
        # Only allow status and notes to be updated
        allowed_fields = ['status', 'notes']
        validated_data = serializer.validated_data
        
        # Remove fields that shouldn't be updated
        for field in list(validated_data.keys()):
            if field not in allowed_fields:
                validated_data.pop(field)
        
        # Handle status changes
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        if old_status != new_status:
            if new_status == 'delivered' and old_status == 'pending':
                # When marking as delivered, update central stock
                for item in instance.items.all():
                    item._update_central_stock()
            elif old_status == 'delivered' and new_status in ['pending', 'cancelled']:
                # When changing from delivered, reverse stock allocation
                for item in instance.items.all():
                    item._update_central_stock(reverse=True)
        
        serializer.save()
    
    def perform_destroy(self, serializer):
        """Only allow deletion of pending deliveries"""
        instance = self.get_object()
        if instance.status != 'pending':
            raise serializers.ValidationError(
                "Only pending deliveries can be deleted"
            )
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark a delivery as delivered"""
        delivery = self.get_object()
        
        if delivery.status != 'pending':
            return Response(
                {'error': 'Only pending deliveries can be marked as delivered'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        delivery.status = 'delivered'
        delivery.save()
        
        # Stock is already transferred when DeliveryItem is created
        # No need to update stock here
        
        serializer = self.get_serializer(delivery)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a delivery"""
        delivery = self.get_object()
        
        if delivery.status == 'delivered':
            # Reverse stock allocation if delivery was already delivered
            for item in delivery.items.all():
                item._update_salesman_stock(reverse=True)
        
        delivery.status = 'cancelled'
        delivery.save()
        
        serializer = self.get_serializer(delivery)
        return Response(serializer.data)

    @extend_schema(
        summary="Get settlement data for delivery",
        description="Get data needed for settling a delivery - shows sold and remaining quantities",
        responses={
            200: OpenApiResponse(
                description="Settlement data with sold and remaining quantities",
                examples=[
                    OpenApiExample(
                        "Settlement Data",
                        value={
                            "delivery_id": 1,
                            "delivery_number": "DEL-20250619-001",
                            "salesman_name": "Mike Johnson",
                            "items": [
                                {
                                    "delivery_item_id": 1,
                                    "product_id": 1,
                                    "product_name": "Aloe Vera Gel",
                                    "delivered_quantity": 100,
                                    "sold_quantity": 75,
                                    "remaining_quantity": 25,
                                    "margin_earned": 50.00
                                }
                            ]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Only delivered deliveries can be settled")
        }
    )
    @action(detail=True, methods=['get'])
    def settlement_data(self, request, pk=None):
        """Get settlement data for a delivery"""
        delivery = self.get_object()
        
        if delivery.status != 'delivered':
            return Response(
                {'error': 'Only delivered deliveries can be settled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settlement_data = delivery.get_settlement_data()
        
        return Response({
            'delivery_id': delivery.id,
            'delivery_number': delivery.delivery_number,
            'salesman_name': delivery.salesman.user.get_full_name(),
            'delivery_date': delivery.delivery_date.isoformat(),
            'items': settlement_data
        })

    @extend_schema(
        summary="Settle delivery",
        description="Settle a delivery by confirming remaining stock and calculating margins",
        request={
            "type": "object",
            "properties": {
                "settlement_notes": {"type": "string", "description": "Notes for the settlement"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "delivery_item_id": {"type": "integer"},
                            "remaining_quantity": {"type": "integer"},
                            "margin_earned": {"type": "number"}
                        },
                        "required": ["delivery_item_id", "remaining_quantity", "margin_earned"]
                    }
                }
            },
            "required": ["items"]
        },
        responses={
            200: OpenApiResponse(
                description="Settlement completed successfully",
                examples=[
                    OpenApiExample(
                        "Settlement Result",
                        value={
                            "status": "settled",
                            "settlement_date": "2025-06-19",
                            "total_margin_earned": 75.50,
                            "message": "Delivery settled successfully"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Settlement validation errors")
        }
    )
    @action(detail=True, methods=['post'])
    def settle(self, request, pk=None):
        """Settle a delivery"""
        delivery = self.get_object()
        
        if delivery.status != 'delivered':
            return Response(
                {'error': 'Only delivered deliveries can be settled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settlement_notes = request.data.get('settlement_notes', '')
        settlement_items = request.data.get('items', [])
        
        if not settlement_items:
            return Response(
                {'error': 'Settlement items are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = delivery.settle_delivery(settlement_items, settlement_notes, settled_by=request.user)
            return Response({
                **result,
                'message': 'Delivery settled successfully'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Settlement failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get delivery settlement preview for salesman",
        description="Get comprehensive settlement preview including cash flow for a salesman's deliveries",
        responses={
            200: OpenApiResponse(
                description="Settlement preview data",
                examples=[
                    OpenApiExample(
                        "Settlement Preview",
                        value={
                            "delivery": {
                                "id": 1,
                                "delivery_number": "DEL-20250619-001",
                                "salesman_name": "John Doe",
                                "delivery_date": "2025-06-19"
                            },
                            "products": [
                                {
                                    "product_name": "Aloe Vera Gel",
                                    "delivered_quantity": 100,
                                    "sold_quantity": 75,
                                    "returned_quantity": 5,
                                    "outstanding_quantity": 20,
                                    "unit_price": 25.00,
                                    "delivered_value": 2500.00,
                                    "sold_value": 1875.00,
                                    "outstanding_value": 500.00
                                }
                            ],
                            "cash_breakdown": {
                                "invoice_collections": 1875.00,
                                "delivery_expenses": 100.00,
                                "return_value": 125.00,
                                "net_cash_available": 1900.00,
                                "payment_methods": [
                                    {
                                        "method": "cash",
                                        "amount": 1500.00
                                    },
                                    {
                                        "method": "cheque",
                                        "amount": 375.00,
                                        "reference": "CHQ001",
                                        "bank": "Commercial Bank"
                                    }
                                ]
                            },
                            "salesman_balance": {
                                "current_balance": 500.00,
                                "balance_after_settlement": -1400.00
                            }
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="Salesman not found")
        }
    )
    @action(detail=False, methods=['get'])
    def settlement_preview(self, request):
        """Get settlement preview for a salesman"""
        salesman_id = request.query_params.get('salesman_id')
        if not salesman_id:
            return Response(
                {'error': 'salesman_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from accounts.models import Salesman
            from sales.models import Invoice, InvoiceItem, Transaction
            from decimal import Decimal
            
            salesman = Salesman.objects.get(id=salesman_id)
            
            # Get the most recent active delivery for this salesman
            recent_delivery = Delivery.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'pending']
            ).order_by('-created_at').first()
            
            if not recent_delivery:
                return Response(
                    {'error': 'No active deliveries found for this salesman'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get product settlement data
            products_data = []
            for item in recent_delivery.items.all():
                # Get sold quantity from invoices since delivery
                sold_qty = InvoiceItem.objects.filter(
                    invoice__salesman=salesman,
                    product=item.product,
                    invoice__invoice_date__gte=recent_delivery.created_at,
                    invoice__status__in=['paid', 'partial', 'pending']
                ).aggregate(total=models.Sum('quantity'))['total'] or 0
                
                # Get returned quantity from batch assignments
                returned_qty = BatchAssignment.objects.filter(
                    salesman=salesman,
                    batch__product=item.product,
                    created_at__gte=recent_delivery.created_at
                ).aggregate(total=models.Sum('returned_quantity'))['total'] or 0
                
                outstanding_qty = item.quantity - sold_qty - returned_qty
                
                products_data.append({
                    'product_name': item.product.name,
                    'delivered_quantity': item.quantity,
                    'sold_quantity': sold_qty,
                    'returned_quantity': returned_qty,
                    'outstanding_quantity': max(0, outstanding_qty),
                    'unit_price': float(item.unit_price),
                    'delivered_value': float(item.total_value),
                    'sold_value': float(sold_qty * item.unit_price),
                    'outstanding_value': float(max(0, outstanding_qty) * item.unit_price)
                })
            
            # Get cash breakdown
            # Invoice collections since delivery
            invoice_collections = Transaction.objects.filter(
                invoice__salesman=salesman,
                invoice__invoice_date__gte=recent_delivery.created_at,
                transaction_date__gte=recent_delivery.created_at
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            # Delivery expenses (only unsettled ones)
            delivery_expenses = recent_delivery.expenses.filter(
                is_settled=False
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0.00')
            
            # Return value (products returned)
            return_value = sum(p['returned_quantity'] * p['unit_price'] for p in products_data)
            
            # Net cash available
            net_cash_available = float(invoice_collections) - float(delivery_expenses) + return_value
            
            # Get payment methods breakdown
            payment_methods = []
            transactions = Transaction.objects.filter(
                invoice__salesman=salesman,
                invoice__invoice_date__gte=recent_delivery.created_at,
                transaction_date__gte=recent_delivery.created_at
            ).values('payment_method').annotate(
                total_amount=models.Sum('amount')
            )
            
            for transaction in transactions:
                payment_methods.append({
                    'method': transaction['payment_method'],
                    'amount': float(transaction['total_amount'])
                })
            
            # Salesman balance
            current_balance = float(salesman.current_balance)
            balance_after_settlement = current_balance - net_cash_available
            
            return Response({
                'delivery': {
                    'id': recent_delivery.id,
                    'delivery_number': recent_delivery.delivery_number,
                    'salesman_name': salesman.user.get_full_name(),
                    'delivery_date': recent_delivery.delivery_date.isoformat()
                },
                'products': products_data,
                'cash_breakdown': {
                    'invoice_collections': float(invoice_collections),
                    'delivery_expenses': float(delivery_expenses),
                    'return_value': return_value,
                    'net_cash_available': net_cash_available,
                    'payment_methods': payment_methods
                },
                'salesman_balance': {
                    'current_balance': current_balance,
                    'balance_after_settlement': balance_after_settlement
                }
            })
            
        except Salesman.DoesNotExist:
            return Response(
                {'error': 'Salesman not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get settlement preview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Process delivery settlement with cash management",
        description="Complete delivery settlement including cash collection and balance updates",
        request={
            "type": "object",
            "properties": {
                "salesman_id": {"type": "integer", "description": "ID of the salesman"},
                "settlement_notes": {"type": "string", "description": "Notes for the settlement"},
                "cash_settlement_amount": {"type": "number", "description": "Amount of cash collected"},
                "settlement_method": {
                    "type": "string", 
                    "enum": ["full_cash", "partial_cash", "balance_carry"],
                    "description": "Settlement method"
                },
                "return_all_stock": {"type": "boolean", "description": "Whether to return all remaining stock"},
                "create_settlement_record": {"type": "boolean", "description": "Whether to create settlement record"}
            },
            "required": ["salesman_id", "cash_settlement_amount", "settlement_method"]
        },
        responses={
            200: OpenApiResponse(
                description="Settlement processed successfully",
                examples=[
                    OpenApiExample(
                        "Settlement Result",
                        value={
                            "success": True,
                            "message": "Settlement completed successfully",
                            "settlement_id": 123,
                            "cash_collected": 1500.00,
                            "new_balance": -1000.00,
                            "delivery_status": "settled"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid settlement data"),
            404: OpenApiResponse(description="Salesman or delivery not found")
        }
    )
    @action(detail=False, methods=['post'])
    def process_settlement(self, request):
        """Process complete delivery settlement with cash management"""
        try:
            from accounts.models import Salesman
            from accounts.services import SalesmanBalanceService
            from decimal import Decimal
            
            salesman_id = request.data.get('salesman_id')
            settlement_notes = request.data.get('settlement_notes', '')
            cash_settlement_amount = Decimal(str(request.data.get('cash_settlement_amount', 0)))
            settlement_method = request.data.get('settlement_method', 'full_cash')
            return_all_stock = request.data.get('return_all_stock', True)
            create_settlement_record = request.data.get('create_settlement_record', True)
            
            if not salesman_id:
                return Response(
                    {'error': 'salesman_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            salesman = Salesman.objects.get(id=salesman_id)
            
            # Get the most recent active delivery
            delivery = Delivery.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'pending']
            ).order_by('-created_at').first()
            
            if not delivery:
                return Response(
                    {'error': 'No active delivery found for settlement'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            with transaction.atomic():
                # 1. Record cash collection if amount > 0
                cash_transaction = None
                if cash_settlement_amount > 0:
                    cash_transaction = SalesmanBalanceService.record_cash_settlement(
                        salesman=salesman,
                        amount=cash_settlement_amount,
                        settlement_method=settlement_method,
                        notes=settlement_notes,
                        reference_type='delivery_settlement',
                        reference_id=delivery.id,
                        created_by=request.user
                    )
                
                # 2. Handle stock returns if requested
                if return_all_stock:
                    for item in delivery.items.all():
                        # Get outstanding quantity for this product
                        assignments = BatchAssignment.objects.filter(
                            salesman=salesman,
                            batch__product=item.product,
                            status__in=['delivered', 'partial']
                        )
                        
                        for assignment in assignments:
                            if assignment.outstanding_quantity > 0:
                                # Return remaining stock
                                assignment.returned_quantity += assignment.outstanding_quantity
                                assignment.status = 'returned'
                                assignment.save()
                
                # 3. Mark all unsettled expenses for this delivery as settled
                from products.models import DeliveryExpense
                unsettled_expenses = DeliveryExpense.objects.filter(
                    delivery=delivery,
                    is_settled=False
                )
                
                expense_count = unsettled_expenses.count()
                if expense_count > 0:
                    unsettled_expenses.update(
                        is_settled=True,
                        settled_at=timezone.now(),
                        settled_by=request.user
                    )
                    print(f"Marked {expense_count} expenses as settled for delivery {delivery.delivery_number}")
                
                # 4. Create settlement record if requested
                settlement_record = None
                if create_settlement_record:
                    from products.models import DeliverySettlement
                    settlement_record = DeliverySettlement.objects.create(
                        salesman=salesman,
                        settlement_date=timezone.now().date(),
                        total_delivered_value=delivery.total_value,
                        total_sold_value=0,  # Calculate based on invoices
                        total_returned_value=0,  # Calculate based on returns
                        status='completed',
                        settlement_notes=settlement_notes,
                        settled_by=request.user
                    )
                
                # 5. Update delivery status
                delivery.status = 'settled'
                delivery.settlement_date = timezone.now().date()
                delivery.settlement_notes = settlement_notes
                delivery.save()
                
                # 6. Refresh salesman balance
                salesman.refresh_from_db()
                
                return Response({
                    'success': True,
                    'message': 'Settlement completed successfully',
                    'settlement_id': settlement_record.id if settlement_record else None,
                    'cash_transaction_id': cash_transaction.id if cash_transaction else None,
                    'cash_collected': float(cash_settlement_amount),
                    'new_balance': float(salesman.current_balance),
                    'delivery_status': delivery.status,
                    'delivery_id': delivery.id
                })
                
        except Salesman.DoesNotExist:
            return Response(
                {'error': 'Salesman not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Settlement failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get detailed invoice settlement breakdown for delivery",
        description="Get comprehensive invoice settlement breakdown showing payment methods, collection rates, and recent transactions",
        responses={
            200: OpenApiResponse(
                description="Detailed settlement breakdown",
                examples=[
                    OpenApiExample(
                        "Settlement Breakdown",
                        value={
                            "delivery_info": {
                                "id": 1,
                                "delivery_number": "DEL-20250619-001",
                                "salesman_name": "John Doe",
                                "delivery_date": "2025-06-19",
                                "total_value": 5000.00
                            },
                            "settlement_summary": {
                                "total_invoice_amount": 4500.00,
                                "total_collected": 3200.00,
                                "outstanding_balance": 1300.00,
                                "collection_rate": 71.11,
                                "invoice_count": 8
                            },
                            "payment_methods": [
                                {
                                    "method": "cash",
                                    "total_amount": 2000.00,
                                    "transaction_count": 5,
                                    "settlement_count": 2,
                                    "percentage": 62.5
                                },
                                {
                                    "method": "cheque",
                                    "total_amount": 800.00,
                                    "transaction_count": 2,
                                    "settlement_count": 1,
                                    "percentage": 25.0
                                },
                                {
                                    "method": "bank_transfer",
                                    "total_amount": 400.00,
                                    "transaction_count": 1,
                                    "settlement_count": 0,
                                    "percentage": 12.5
                                }
                            ],
                            "recent_settlements": [
                                {
                                    "type": "transaction",
                                    "id": 123,
                                    "date": "2025-06-20T10:30:00Z",
                                    "amount": 500.00,
                                    "payment_method": "cash",
                                    "invoice_number": "INV-001",
                                    "shop_name": "ABC Store",
                                    "reference": None,
                                    "notes": "Cash payment"
                                }
                            ]
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="Delivery not found")
        }
    )
    @action(detail=True, methods=['get'])
    def settlement_breakdown(self, request, pk=None):
        """Get detailed invoice settlement breakdown for a specific delivery"""
        try:
            delivery = self.get_object()
            
            # Get the settlement breakdown from the serializer method
            serializer = self.get_serializer(delivery)
            settlement_data = serializer.get_settlement_breakdown(delivery)
            
            # Add delivery info
            response_data = {
                'delivery_info': {
                    'id': delivery.id,
                    'delivery_number': delivery.delivery_number,
                    'salesman_name': delivery.salesman.user.get_full_name(),
                    'delivery_date': delivery.delivery_date.isoformat(),
                    'total_value': float(delivery.total_value),
                    'status': delivery.status
                },
                'settlement_summary': settlement_data['summary'],
                'payment_methods': [
                    {
                        **pm,
                        'percentage': (pm['total_amount'] / settlement_data['summary']['total_collected'] * 100) if settlement_data['summary']['total_collected'] > 0 else 0
                    }
                    for pm in settlement_data['payment_methods']
                ],
                'recent_settlements': settlement_data['recent_settlements']
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get settlement breakdown: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get delivery settlement summary",
        description="Get comprehensive settlement summary for owner cash flow tracking",
        responses={
            200: OpenApiResponse(
                description="Settlement summary with cash flow metrics",
                examples=[
                    OpenApiExample(
                        "Settlement Summary",
                        value={
                            "delivery_id": 1,
                            "delivery_number": "DEL-20250725-001",
                            "salesman_name": "John Doe",
                            "settlement_summary": {
                                "delivery_metrics": {
                                    "delivery_value": 170000.00,
                                    "delivery_date": "2025-07-25",
                                    "delivery_status": "delivered",
                                    "total_items": 3
                                },
                                "cash_flow": {
                                    "total_cash_collected": 71000.00,
                                    "cash_to_settle_to_owner": 71000.00,
                                    "outstanding_from_customers": 8000.00,
                                    "collection_rate_percentage": 41.76
                                },
                                "product_tracking": {
                                    "product_value_in_circulation": 99000.00,
                                    "circulation_percentage": 58.24,
                                    "conversion_rate": 41.76
                                }
                            }
                        }
                    )
                ]
            )
        }
    )
    @action(detail=True, methods=['get'])
    def settlement_summary(self, request, pk=None):
        """
        Get comprehensive settlement summary for delivery.
        
        This endpoint provides owners with detailed cash flow analysis,
        product value tracking, and settlement obligations.
        """
        try:
            delivery = self.get_object()
            serializer = self.get_serializer(delivery)
            settlement_data = serializer.get_settlement_summary(delivery)
            
            return Response({
                'delivery_id': delivery.id,
                'delivery_number': delivery.delivery_number,
                'salesman_name': delivery.salesman.user.get_full_name(),
                'settlement_summary': settlement_data
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get settlement summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Collect physical cash from salesman",
        description="Owner physically collects cash from salesman and resets balance",
        request={
            "type": "object",
            "properties": {
                "settlement_id": {"type": "integer", "description": "Delivery settlement ID"},
                "amount_collected": {"type": "number", "description": "Amount of cash physically collected"},
                "collection_notes": {"type": "string", "description": "Notes about cash collection"},
                "collection_method": {
                    "type": "string",
                    "enum": ["full_amount", "partial_amount", "excess_returned"],
                    "description": "How the cash was collected"
                }
            },
            "required": ["settlement_id", "amount_collected"]
        },
        responses={
            200: OpenApiResponse(
                description="Cash collected successfully",
                examples=[
                    OpenApiExample(
                        "Cash Collection Result",
                        value={
                            "success": True,
                            "message": "Cash collected successfully",
                            "settlement_id": 41,
                            "amount_collected": 19800.00,
                            "salesman_name": "Roshan Padukka",
                            "new_balance": 0.00,
                            "collection_date": "2025-07-27T16:30:00Z",
                            "next_delivery_ready": True
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid collection data or cash already collected"),
            404: OpenApiResponse(description="Settlement not found")
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsOwnerOrDeveloper])
    def collect_physical_cash(self, request):
        """
        Owner physically collects cash from salesman after delivery settlement.
        This resets the salesman's cash balance and creates audit trail.
        """
        from decimal import Decimal
        from products.models import DeliverySettlement, BatchAssignment
        
        try:
            settlement_id = request.data.get('settlement_id')
            amount_collected = Decimal(str(request.data.get('amount_collected', 0)))
            collection_notes = request.data.get('collection_notes', '')
            collection_method = request.data.get('collection_method', 'full_amount')
            
            if not settlement_id:
                return Response(
                    {'error': 'settlement_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if amount_collected <= 0:
                return Response(
                    {'error': 'amount_collected must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get settlement record
            try:
                settlement = DeliverySettlement.objects.get(id=settlement_id)
            except DeliverySettlement.DoesNotExist:
                return Response(
                    {'error': 'Settlement not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if owner has permission for this salesman
            if request.user.role == 'owner' and settlement.salesman.owner != request.user.owner_profile:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate amount against salesman's current balance
            if amount_collected > settlement.salesman.current_balance:
                return Response(
                    {'error': f'Amount collected ({amount_collected}) exceeds salesman balance ({settlement.salesman.current_balance})'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Collect the cash
            result = settlement.collect_physical_cash(
                collected_by=request.user,
                amount_collected=amount_collected,
                notes=f"{collection_method}: {collection_notes}"
            )
            
            # Check if salesman is ready for next delivery
            next_delivery_ready = (
                settlement.salesman.current_balance == 0 and
                not BatchAssignment.objects.filter(
                    salesman=settlement.salesman,
                    status__in=['delivered', 'partial']
                ).exists()
            )
            
            return Response({
                'success': True,
                'message': f'Cash collected successfully from {settlement.salesman.user.get_full_name()}',
                'settlement_id': settlement.id,
                'amount_collected': float(amount_collected),
                'salesman_name': settlement.salesman.user.get_full_name(),
                'new_balance': float(settlement.salesman.current_balance),
                'collection_date': result['collection_date'].isoformat(),
                'collection_method': collection_method,
                'next_delivery_ready': next_delivery_ready,
                'audit_trail': {
                    'collected_by': request.user.get_full_name(),
                    'collection_notes': collection_notes,
                    'transaction_created': True
                }
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Cash collection failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        summary="List delivery items",
        description="Get a list of items in deliveries",
        parameters=[
            OpenApiParameter(name='delivery', description='Filter by delivery ID', required=False, type=int),
            OpenApiParameter(name='product', description='Filter by product ID', required=False, type=int),
        ]
    ),
    create=extend_schema(
        summary="Add item to delivery",
        description="Add a product item to an existing delivery"
    ),
    update=extend_schema(
        summary="Update delivery item",
        description="Update quantity or unit price of a delivery item"
    ),
    destroy=extend_schema(
        summary="Remove item from delivery",
        description="Remove a product item from a delivery"
    )
)
class DeliveryItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual items in deliveries.
    
    Allows adding, updating, and removing products from deliveries.
    """
    queryset = DeliveryItem.objects.all()
    serializer_class = DeliveryItemSerializer
    permission_classes = [IsOwnerOrDeveloper]  # Only owners can manage delivery items
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['delivery', 'product']
    
    def get_queryset(self):
        """Filter delivery items based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'owner':
            # Filter by deliveries under this owner's salesmen
            return queryset.filter(delivery__salesman__owner=user.owner_profile)
        elif user.role == 'developer':
            return queryset
        else:
            return queryset.none()
    
    def perform_create(self, serializer):
        """Validate delivery item creation"""
        delivery = serializer.validated_data['delivery']
        
        if delivery.status != 'pending':
            raise serializers.ValidationError(
                "Cannot add items to a delivery that is not pending"
            )
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Validate delivery item updates"""
        instance = self.get_object()
        
        if instance.delivery.status != 'pending':
            raise serializers.ValidationError(
                "Cannot update items in a delivery that is not pending"
            )
        
        serializer.save()
    
    def perform_destroy(self, serializer):
        """Validate delivery item deletion"""
        instance = self.get_object()
        
        if instance.delivery.status != 'pending':
            raise serializers.ValidationError(
                "Cannot remove items from a delivery that is not pending"
            )
        
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="List product batches",
        description="Get a paginated list of product batches with FIFO ordering",
        parameters=[
            OpenApiParameter('product', description='Filter by product ID', required=False, type=int),
            OpenApiParameter('is_active', description='Filter by active status', required=False, type=bool),
            OpenApiParameter('expired', description='Filter expired batches', required=False, type=bool),
        ],
        tags=['Batch Management']
    ),
    create=extend_schema(
        summary="Create new batch",
        description="Create a new product batch (Owner/Developer only)",
        tags=['Batch Management']
    ),
    retrieve=extend_schema(
        summary="Get batch details",
        description="Retrieve detailed information about a specific batch",
        tags=['Batch Management']
    ),
    update=extend_schema(
        summary="Update batch",
        description="Update batch information (Owner/Developer only)",
        tags=['Batch Management']
    ),
    destroy=extend_schema(
        summary="Delete batch",
        description="Delete a batch (Owner/Developer only)",
        tags=['Batch Management']
    )
)
class BatchViewSet(viewsets.ModelViewSet):
    """ViewSet for managing product batches"""
    queryset = Batch.objects.select_related('product').all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'is_active']
    search_fields = ['batch_number', 'product__name', 'product__sku']
    ordering_fields = ['manufacturing_date', 'expiry_date', 'created_at']
    ordering = ['manufacturing_date', 'expiry_date']  # FIFO ordering
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter expired batches if requested
        expired = self.request.query_params.get('expired')
        if expired is not None:
            current_date = timezone.now().date()
            if expired.lower() == 'true':
                queryset = queryset.filter(expiry_date__lt=current_date)
            else:
                queryset = queryset.exclude(expiry_date__lt=current_date)
        
        return queryset
    
    def perform_create(self, serializer):
        """Handle batch creation with logging"""
        db_logger.info(f"Creating new batch by user: {self.request.user.username}")
        
        batch = serializer.save(created_by=self.request.user)
        
        # Create initial transaction record
        BatchTransaction.objects.create(
            batch=batch,
            transaction_type='restock',
            quantity=batch.initial_quantity,
            balance_after=batch.current_quantity,
            reference_type='batch_creation',
            reference_id=batch.id,
            notes="Initial batch creation",
            created_by=self.request.user
        )
        
        db_logger.info(f"Batch created: {batch.batch_number} for product {batch.product.name}")
    
    @extend_schema(
        summary="Get batch transactions",
        description="Get transaction history for a specific batch",
        responses={200: BatchTransactionSerializer(many=True)},
        tags=['Batch Management']
    )
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get transaction history for a batch"""
        batch = self.get_object()
        transactions = batch.transactions.all()
        serializer = BatchTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get FIFO suggestions",
        description="Get oldest batches first for FIFO compliance",
        parameters=[
            OpenApiParameter('product_id', description='Product ID to get FIFO suggestions for', required=True, type=int),
            OpenApiParameter('quantity', description='Required quantity', required=True, type=int),
        ],
        tags=['Batch Management']
    )
    @action(detail=False, methods=['get'])
    def fifo_suggestions(self, request):
        """Get FIFO batch suggestions for a product"""
        product_id = request.query_params.get('product_id')
        required_quantity = request.query_params.get('quantity')
        
        if not product_id or not required_quantity:
            return Response(
                {'error': 'product_id and quantity parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            required_quantity = int(required_quantity)
            product = Product.objects.get(id=product_id)
        except (ValueError, Product.DoesNotExist):
            return Response(
                {'error': 'Invalid product_id or quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get available batches in FIFO order
        available_batches = Batch.objects.filter(
            product=product,
            is_active=True,
            current_quantity__gt=0
        ).exclude(
            expiry_date__lt=timezone.now().date()
        ).order_by('manufacturing_date', 'expiry_date')
        
        suggestions = []
        remaining_quantity = required_quantity
        
        for batch in available_batches:
            if remaining_quantity <= 0:
                break
            
            available_qty = batch.available_quantity
            if available_qty > 0:
                take_quantity = min(available_qty, remaining_quantity)
                suggestions.append({
                    'batch_id': batch.id,
                    'batch_number': batch.batch_number,
                    'available_quantity': available_qty,
                    'suggested_quantity': take_quantity,
                    'manufacturing_date': batch.manufacturing_date,
                    'expiry_date': batch.expiry_date,
                    'days_until_expiry': batch.days_until_expiry
                })
                remaining_quantity -= take_quantity
        
        return Response({
            'suggestions': suggestions,
            'total_available': sum(s['suggested_quantity'] for s in suggestions),
            'shortage': max(0, remaining_quantity)
        })
    
    @extend_schema(
        summary="Get salesman's available batches for invoice creation",
        description="Get batches assigned to the authenticated salesman that are available for invoicing",
        parameters=[
            OpenApiParameter(
                name='product_id',
                description='Filter by specific product ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='min_quantity',
                description='Only show batches with at least this quantity available',
                required=False,
                type=int
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Available batches for salesman",
                examples=[
                    OpenApiExample(
                        'Success',
                        value=[
                            {
                                'batch_id': 1,
                                'batch_number': 'BATCH-001',
                                'product_id': 1,
                                'product_name': 'Sample Product',
                                'product_sku': 'SKU001',
                                'available_quantity': 50,
                                'unit_cost': '10.00',
                                'expiry_date': '2025-12-31',
                                'days_until_expiry': 365,
                                'assignment_id': 1,
                                'assignment_status': 'delivered'
                            }
                        ]
                    )
                ]
            ),
            403: OpenApiResponse(description="Only salesmen can access this endpoint")
        },
        tags=['Batch Management']
    )
    @action(detail=False, methods=['get'], url_path='salesman-available-batches')
    def salesman_available_batches(self, request):
        """Get batches available to the authenticated salesman for invoice creation"""
        if request.user.role != 'salesman':
            return Response(
                {'error': 'Only salesmen can access this endpoint'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            salesman = request.user.salesman_profile
        except AttributeError:
            return Response(
                {'error': 'Salesman profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get query parameters
        product_id = request.query_params.get('product_id')
        min_quantity = request.query_params.get('min_quantity', 1)
        
        try:
            min_quantity = int(min_quantity)
        except (ValueError, TypeError):
            min_quantity = 1
        
        # Get batch assignments for this salesman
        assignments_filter = {
            'salesman': salesman,
            'status__in': ['delivered', 'partial']  # Only delivered or partially returned batches
        }
        
        if product_id:
            try:
                product_id = int(product_id)
                assignments_filter['batch__product_id'] = product_id
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid product_id'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get assignments with available quantity
        assignments = BatchAssignment.objects.filter(
            **assignments_filter
        ).select_related(
            'batch__product'
        ).annotate(
            available_qty=F('delivered_quantity') - F('returned_quantity')
        ).filter(
            available_qty__gte=min_quantity,
            batch__is_active=True
        ).exclude(
            batch__expiry_date__lt=timezone.now().date()
        ).order_by('batch__expiry_date', 'batch__manufacturing_date')
        
        # Format response
        available_batches = []
        for assignment in assignments:
            batch = assignment.batch
            available_batches.append({
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'product_id': batch.product.id,
                'product_name': batch.product.name,
                'product_sku': batch.product.sku,
                'available_quantity': assignment.outstanding_quantity,
                'unit_cost': str(batch.unit_cost),
                'expiry_date': batch.expiry_date,
                'days_until_expiry': batch.days_until_expiry,
                'assignment_id': assignment.id,
                'assignment_status': assignment.status,
                'manufacturing_date': batch.manufacturing_date
            })
        
        return Response(available_batches, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List batch assignments",
        description="Get list of batch assignments to salesmen",
        parameters=[
            OpenApiParameter('batch', description='Filter by batch ID', required=False, type=int),
            OpenApiParameter('salesman', description='Filter by salesman ID', required=False, type=int),
            OpenApiParameter('status', description='Filter by status', required=False, type=str),
        ],
        tags=['Batch Management']
    ),
    create=extend_schema(
        summary="Create batch assignment",
        description="Assign batch stock to a salesman (Owner/Developer only)",
        tags=['Batch Management']
    )
)
class BatchAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing batch assignments to salesmen"""
    queryset = BatchAssignment.objects.select_related('batch', 'salesman', 'created_by').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['batch', 'salesman', 'status']
    search_fields = ['batch__batch_number', 'salesman__user__first_name', 'salesman__user__last_name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateBatchAssignmentSerializer
        return BatchAssignmentSerializer
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # If user is salesman, only show their assignments
        if self.request.user.role == 'salesman':
            queryset = queryset.filter(salesman=self.request.user.salesman_profile)
        
        return queryset
    
    def perform_create(self, serializer):
        """Handle batch assignment creation"""
        with transaction.atomic():
            assignment = serializer.save(created_by=self.request.user)
            
            db_logger.info(f"Batch assigned: {assignment.batch.batch_number} to {assignment.salesman.user.get_full_name()}")
    
    @extend_schema(
        summary="Mark assignment as delivered",
        description="Mark batch assignment as delivered to salesman",
        tags=['Batch Management']
    )
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark assignment as delivered"""
        assignment = self.get_object()
        
        if assignment.status != 'pending':
            return Response(
                {'error': 'Only pending assignments can be marked as delivered'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            assignment.status = 'delivered'
            assignment.delivered_quantity = assignment.quantity
            assignment.delivery_date = timezone.now()
            assignment.save()
            
            # Create transaction record
            BatchTransaction.objects.create(
                batch=assignment.batch,
                transaction_type='assignment',
                quantity=0,  # No quantity change, just status change
                balance_after=assignment.batch.current_quantity,
                reference_type='delivery_confirmation',
                reference_id=assignment.id,
                notes=f"Delivered to {assignment.salesman.user.get_full_name()}",
                created_by=request.user
            )
        
        serializer = BatchAssignmentSerializer(assignment)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Process return",
        description="Process return of batch items from salesman",
        tags=['Batch Management']
    )
    @action(detail=True, methods=['post'])
    def process_return(self, request, pk=None):
        """Process return of batch items"""
        assignment = self.get_object()
        return_quantity = request.data.get('return_quantity', 0)
        
        if not return_quantity or return_quantity <= 0:
            return Response(
                {'error': 'return_quantity must be greater than 0'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        max_returnable = assignment.delivered_quantity - assignment.returned_quantity
        if return_quantity > max_returnable:
            return Response(
                {'error': f'Cannot return more than {max_returnable} items'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create ProductReturn in pending state instead of directly adding to stock
            product_return = ProductReturn.objects.create(
                batch_assignment=assignment,
                return_quantity=return_quantity,
                return_reason='unsold',  # Default reason for salesman returns
                return_notes=request.data.get('notes', f'Return from salesman {assignment.salesman.user.get_full_name()}'),
                status='pending',
                created_by=request.user
            )
            
            # Update assignment pending return quantity (not returned_quantity yet)
            assignment.pending_return_quantity += return_quantity
            assignment.save()
            
            # DO NOT update batch quantity here - it will be updated when owner approves the return
            # The stock will only be updated when owner approves the ProductReturn via approve_return method
            
            # Create transaction record for pending return
            BatchTransaction.objects.create(
                batch=assignment.batch,
                transaction_type='return_pending',
                quantity=return_quantity,
                balance_after=assignment.batch.current_quantity,  # No change to current quantity yet
                reference_type='product_return',
                reference_id=product_return.id,
                notes=f"Pending return from {assignment.salesman.user.get_full_name()}",
                created_by=request.user
            )
        
        serializer = BatchAssignmentSerializer(assignment)
        return Response(serializer.data)

    @extend_schema(
        summary="Mark batch as defective",
        description="Mark an entire batch as defective and initiate recall process",
        request=BatchRecallSerializer,
        responses={
            200: OpenApiResponse(description="Batch marked as defective successfully"),
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Batch not found")
        },
        tags=['Batch Management']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrDeveloper])
    def mark_defective(self, request, pk=None):
        """Mark a batch as defective and initiate recall"""
        try:
            batch = self.get_object()
            
            # Get recall data from request
            recall_reason = request.data.get('recall_reason', 'Quality issue detected')
            severity = request.data.get('severity', 'medium')
            recall_all_stock = request.data.get('recall_all_stock', True)
            notify_customers = request.data.get('notify_customers', True)
            
            # Mark batch as defective
            batch.quality_status = 'defective'
            batch.recall_initiated_at = timezone.now()
            batch.recall_reason = recall_reason
            batch.is_active = False  # Deactivate the batch
            batch.save()
            
            # Create defect record if BatchDefect model exists
            try:
                from products.models import BatchDefect
                BatchDefect.objects.create(
                    batch=batch,
                    defect_type='quality_issue',
                    severity=severity,
                    description=recall_reason,



                    reported_by=request.user
                )
           
            except ImportError:
                # BatchDefect model doesn't exist, log the defect info
                db_logger.warning(f"BatchDefect model not found. Batch {batch.batch_number} marked defective: {recall_reason}")
            
            # Update batch assignments to recalled status if recalling all stock
            if recall_all_stock:
                from products.models import BatchAssignment
                BatchAssignment.objects.filter(
                    batch=batch,
                    status__in=['delivered', 'partial']
                ).update(status='recalled')
            
            # Create transaction record for the recall
            BatchTransaction.objects.create(
                batch=batch,
                transaction_type='recall',
                quantity=batch.current_quantity,
                balance_after=0 if recall_all_stock else batch.current_quantity,
                reference_type='batch_recall',
                reference_id=batch.id,
                notes=f"Batch recall initiated: {recall_reason}",
                created_by=request.user
            )
            
            # If recalling all stock, set current quantity to 0
            if recall_all_stock:
                batch.current_quantity = 0
                batch.save()
            
            # Log the recall
            db_logger.info(f"Batch {batch.batch_number} marked as defective by {request.user.username}. Reason: {recall_reason}")
            
            # Prepare response data
            response_data = {
                'message': f'Batch {batch.batch_number} has been marked as defective and recall initiated',
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'recall_reason': recall_reason,
                'severity': severity,
                'recall_initiated_at': batch.recall_initiated_at,
                'stock_recalled': recall_all_stock,
                'notify_customers': notify_customers
            }
            
            # Add affected assignments info
            if recall_all_stock:
                affected_assignments = BatchAssignment.objects.filter(
                    batch=batch,
                    status='recalled'
                ).select_related('salesman__user')
                
                response_data['affected_salesmen'] = [
                    {
                        'salesman_id': assignment.salesman.id,
                        'salesman_name': assignment.salesman.user.get_full_name(),
                        'recalled_quantity': assignment.delivered_quantity - assignment.returned_quantity
                    }
                    for assignment in affected_assignments
                ]
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to mark batch as defective: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get batch quality analytics",
        description="Get comprehensive quality analytics for a specific batch",
        responses={
            200: OpenApiResponse(description="Batch quality analytics retrieved successfully"),
            404: OpenApiResponse(description="Batch not found")
        },
        tags=['Batch Management']
    )
    @action(detail=True, methods=['get'])
    def quality_analytics(self, request, pk=None):
        """Get quality analytics for a batch"""
        try:
            batch = self.get_object()
            from sales.models import Return, InvoiceItem
            
            # Get all returns for this batch
            returns = Return.objects.filter(batch=batch, approved=True)
            total_returned = returns.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Get all sales for this batch
            sales = InvoiceItem.objects.filter(batch=batch)
            total_sold = sales.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Calculate return rate
            return_rate = (total_returned / total_sold * 100) if total_sold > 0 else 0
            
            # Group returns by reason
            return_reasons = returns.values('reason').annotate(
                count=Count('id'),
                quantity=Sum('quantity')
            ).order_by('-quantity')
            
            # Get defect records if available
            defects = []
            try:
                from products.models import BatchDefect
                defect_records = BatchDefect.objects.filter(batch=batch)
                defects = [
                    {
                        'defect_type': defect.defect_type,
                        'severity': defect.severity,
                        'description': defect.description,
                        'reported_by': defect.reported_by.get_full_name(),
                        'created_at': defect.created_at
                    }
                    for defect in defect_records
                ]
            except ImportError:
                pass
            
            analytics_data = {
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'product_name': batch.product.name,
                'quality_status': batch.quality_status,
                'quality_score': batch.quality_score() if hasattr(batch, 'quality_score') else None,
                'is_problematic': batch.is_problematic() if hasattr(batch, 'is_problematic') else False,
                'manufacturing_date': batch.manufacturing_date,
                'expiry_date': batch.expiry_date,
                'initial_quantity': batch.initial_quantity,
                'current_quantity': batch.current_quantity,
                'total_sold': total_sold,
                'total_returned': total_returned,
                'return_rate': return_rate,
                'return_reasons': list(return_reasons),
                'defects': defects,
                'recall_info': {
                    'is_recalled': batch.recall_initiated_at is not None,
                    'recall_date': batch.recall_initiated_at,
                    'recall_reason': getattr(batch, 'recall_reason', None)
                }
            }
            
            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get batch quality analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get batch expiry alerts",
        description="Get batches that are expiring within the specified number of days",
        parameters=[
            OpenApiParameter(
                name='days',
                description='Number of days ahead to check for expiry (default: 30)',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='urgency',
                description='Filter by urgency level (critical, warning, normal)',
                required=False,
                type=str
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="List of batches expiring soon",
                examples=[
                    OpenApiExample(
                        'Success',
                        value=[
                            {
                                'batch_id': 1,
                                'batch_number': 'BATCH-001',
                                'product_name': 'Sample Product',
                                'product_sku': 'SKU001',
                                'current_quantity': 50,
                                'expiry_date': '2025-08-05',
                                'days_to_expiry': 30,
                                'urgency_level': 'warning',
                                'manufacturing_date': '2025-01-01'
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Batch Management']
    )
    @action(detail=False, methods=['get'], url_path='expiry-alerts')
    def expiry_alerts(self, request):
        """Get batches that are expiring within the specified number of days"""
        days_ahead = int(request.query_params.get('days', 30))
        urgency_filter = request.query_params.get('urgency', None)
        
        cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
        
        # Get batches expiring within the specified timeframe
        expiring_batches = Batch.objects.filter(
            is_active=True,
            expiry_date__isnull=False,
            expiry_date__lte=cutoff_date,
            expiry_date__gt=timezone.now().date(),  # Not already expired
            current_quantity__gt=0
        ).select_related('product').order_by('expiry_date')
        
        # Format response with urgency levels
        alerts = []
        for batch in expiring_batches:
            days_to_expiry = batch.days_until_expiry
            
            # Determine urgency level
            if days_to_expiry <= 7:
                urgency_level = 'critical'
            elif days_to_expiry <= 14:
                urgency_level = 'warning'
            else:
                urgency_level = 'normal'
            
            # Apply urgency filter if specified
            if urgency_filter and urgency_level != urgency_filter:
                continue
            
            alerts.append({
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'product_id': batch.product.id,
                'product_name': batch.product.name,
                'product_sku': batch.product.sku,
                'current_quantity': batch.current_quantity,
                'expiry_date': batch.expiry_date,
                'days_to_expiry': days_to_expiry,
                'urgency_level': urgency_level,
                'manufacturing_date': batch.manufacturing_date,
                'unit_cost': str(batch.unit_cost)
            })
        
        return Response({
            'alerts': alerts,
            'total_count': len(alerts),
            'summary': {
                'critical': len([a for a in alerts if a['urgency_level'] == 'critical']),
                'warning': len([a for a in alerts if a['urgency_level'] == 'warning']),
                'normal': len([a for a in alerts if a['urgency_level'] == 'normal'])
            }
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get batch low stock alerts",
        description="Get batches that have stock below the specified threshold",
        parameters=[
            OpenApiParameter(
                name='threshold',
                description='Minimum stock threshold (default: 10)',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='percentage_threshold',
                description='Percentage of initial quantity threshold (default: 20)',
                required=False,
                type=int
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="List of batches with low stock",
                examples=[
                    OpenApiExample(
                        'Success',
                        value=[
                            {
                                'batch_id': 1,
                                'batch_number': 'BATCH-001',
                                'product_name': 'Sample Product',
                                'product_sku': 'SKU001',
                                'current_quantity': 5,
                                'initial_quantity': 100,
                                'threshold': 10,
                                'percentage_remaining': 5.0,
                                'severity': 'critical'
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Batch Management']
    )
    @action(detail=False, methods=['get'], url_path='low-stock-alerts')
    def low_stock_alerts(self, request):
        """Get batches with stock below the specified threshold"""
        absolute_threshold = int(request.query_params.get('threshold', 10))
        percentage_threshold = int(request.query_params.get('percentage_threshold', 20))
        
        # Get active batches with stock
        batches = Batch.objects.filter(
            is_active=True,
            current_quantity__gt=0
        ).exclude(
            expiry_date__lt=timezone.now().date()
        ).select_related('product')
        
        low_stock_alerts = []
        for batch in batches:
            current_qty = batch.current_quantity
            initial_qty = batch.initial_quantity
            
            # Calculate percentage remaining
            percentage_remaining = (current_qty / initial_qty * 100) if initial_qty > 0 else 0
            
            # Check if batch meets low stock criteria
            is_low_absolute = current_qty <= absolute_threshold
            is_low_percentage = percentage_remaining <= percentage_threshold
            
            if is_low_absolute or is_low_percentage:
                # Determine severity
                if current_qty <= 5 or percentage_remaining <= 10:
                    severity = 'critical'
                elif current_qty <= absolute_threshold * 0.5 or percentage_remaining <= percentage_threshold * 0.5:
                    severity = 'high'
                else:
                    severity = 'medium'
                
                low_stock_alerts.append({
                    'batch_id': batch.id,
                    'batch_number': batch.batch_number,
                    'product_id': batch.product.id,
                    'product_name': batch.product.name,
                    'product_sku': batch.product.sku,
                    'current_quantity': current_qty,
                    'initial_quantity': initial_qty,
                    'available_quantity': batch.available_quantity,
                    'threshold': absolute_threshold,
                    'percentage_remaining': round(percentage_remaining, 2),
                    'percentage_threshold': percentage_threshold,
                    'severity': severity,
                    'expiry_date': batch.expiry_date,
                    'days_to_expiry': batch.days_until_expiry
                })
        
        # Sort by severity and current quantity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2}
        low_stock_alerts.sort(key=lambda x: (severity_order[x['severity']], x['current_quantity']))
        
        return Response({
            'alerts': low_stock_alerts,
            'total_count': len(low_stock_alerts),
            'summary': {
                'critical': len([a for a in low_stock_alerts if a['severity'] == 'critical']),
                'high': len([a for a in low_stock_alerts if a['severity'] == 'high']),
                'medium': len([a for a in low_stock_alerts if a['severity'] == 'medium'])
            }
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get batch quality alerts",
        description="Get batches with quality issues or defects",
        parameters=[
            OpenApiParameter(
                name='severity',
                description='Filter by severity level (critical, high, medium, low)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='quality_status',
                description='Filter by quality status (DEFECTIVE, WARNING, RECALLED)',
                required=False,
                type=str
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="List of batches with quality issues",
                examples=[
                    OpenApiExample(
                        'Success',
                        value=[
                            {
                                'batch_id': 1,
                                'batch_number': 'BATCH-001',
                                'product_name': 'Sample Product',
                                'product_sku': 'SKU001',
                                'quality_status': 'WARNING',
                                'quality_score': 75,
                                'return_rate': 15.5,
                                'defect_count': 2,
                                'severity': 'medium'
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Batch Management']
    )
    @action(detail=False, methods=['get'], url_path='quality-alerts')
    def quality_alerts(self, request):
        """Get batches with quality issues or defects"""
        severity_filter = request.query_params.get('severity', None)
        quality_status_filter = request.query_params.get('quality_status', None)
        
        # Get batches with potential quality issues
        batches = Batch.objects.filter(
            is_active=True
        ).select_related('product').prefetch_related('defects')
        
        # Filter by quality status if specified
        if quality_status_filter:
            batches = batches.filter(quality_status=quality_status_filter)
        else:
            # Only include batches with quality concerns
            batches = batches.filter(
                models.Q(quality_status__in=['WARNING', 'DEFECTIVE', 'RECALLED']) |
                models.Q(return_rate__gt=5) |
                models.Q(defects__isnull=False)
            ).distinct()
        
        quality_alerts = []
        for batch in batches:
            defect_count = batch.defects.count()
            critical_defects = batch.defects.filter(severity='CRITICAL').count()
            high_defects = batch.defects.filter(severity='HIGH').count()
            
            # Determine overall severity
            if batch.quality_status == 'RECALLED' or critical_defects > 0:
                severity = 'critical'
            elif batch.quality_status == 'DEFECTIVE' or high_defects > 0 or batch.return_rate > 15:
                severity = 'high'
            elif batch.quality_status == 'WARNING' or batch.return_rate > 5:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Apply severity filter if specified
            if severity_filter and severity != severity_filter:
                continue
            
            # Get latest defect for additional context
            latest_defect = batch.defects.order_by('-created_at').first()
            
            quality_alerts.append({
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'product_id': batch.product.id,
                'product_name': batch.product.name,
                'product_sku': batch.product.sku,
                'quality_status': batch.quality_status,
                'quality_score': batch.quality_score,
                'return_rate': float(batch.return_rate),
                'total_returned': float(batch.total_returned),
                'defect_count': defect_count,
                'critical_defects': critical_defects,
                'high_defects': high_defects,
                'severity': severity,
                'current_quantity': batch.current_quantity,
                'expiry_date': batch.expiry_date,
                'recall_initiated_at': batch.recall_initiated_at,
                'recall_reason': batch.recall_reason,
                'latest_defect': {
                    'type': latest_defect.defect_type,
                    'severity': latest_defect.severity,
                    'description': latest_defect.description,
                    'created_at': latest_defect.created_at
                } if latest_defect else None
            })
        
        # Sort by severity and return rate
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        quality_alerts.sort(key=lambda x: (severity_order[x['severity']], -x['return_rate']))
        
        return Response({
            'alerts': quality_alerts,
            'total_count': len(quality_alerts),
            'summary': {
                'critical': len([a for a in quality_alerts if a['severity'] == 'critical']),
                'high': len([a for a in quality_alerts if a['severity'] == 'high']),
                'medium': len([a for a in quality_alerts if a['severity'] == 'medium']),
                'low': len([a for a in quality_alerts if a['severity'] == 'low'])
            }
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Validate batch number availability",
        description="Check if a batch number is available for use",
        parameters=[
            OpenApiParameter(
                name='batch_number',
                description='Batch number to validate',
                required=True,
                type=str
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Batch number validation result",
                examples=[
                    OpenApiExample(
                        'Available',
                        value={
                            'is_available': True,
                            'message': 'Batch number is available'
                        }
                    ),
                    OpenApiExample(
                        'Not Available',
                        value={
                            'is_available': False,
                            'message': 'Batch number already exists'
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Missing batch_number parameter")
        },
        tags=['Batch Management']
    )
    @action(detail=False, methods=['get'], url_path='validate-batch-number')
    def validate_batch_number(self, request):
        """Validate if batch number is available"""
        batch_number = request.query_params.get('batch_number')
        
        if not batch_number:
            return Response(
                {'error': 'batch_number parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = Batch.objects.filter(batch_number=batch_number).exists()
        
        return Response({
            'is_available': not exists,
            'message': 'Batch number already exists' if exists else 'Batch number is available'
        }, status=status.HTTP_200_OK)


class DeliveryExpenseViewSet(viewsets.ModelViewSet):
    queryset = DeliveryExpense.objects.all()
    serializer_class = DeliveryExpenseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['delivery', 'category', 'is_settled']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = DeliveryExpense.objects.select_related('delivery__salesman', 'settled_by')
        delivery_id = self.request.query_params.get('delivery', None)
        if delivery_id is not None:
            queryset = queryset.filter(delivery=delivery_id)
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Create expense - balance will be updated when delivery is settled
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()
        
        print(f"Created expense {expense.id} for LKR {expense.amount}")
        print(f"Expense will be settled when delivery {expense.delivery.delivery_number} is settled")
        
        # Return expense data
        headers = self.get_success_headers(serializer.data)
        return Response({
            'expense': serializer.data,
            'message': f'Expense created. Will be settled when delivery is settled.'
        }, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update expense - balance will be updated when delivery is settled
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_amount = instance.amount
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()
        
        print(f"Updated expense {expense.id} from LKR {old_amount} to LKR {expense.amount}")
        print(f"Balance will be adjusted when delivery {expense.delivery.delivery_number} is settled")
        
        return Response({
            'expense': serializer.data,
            'message': f'Expense updated. Will be settled when delivery is settled.'
        })

    def destroy(self, request, *args, **kwargs):
        """
        Delete expense and restore salesman balance - return updated balance
        """
        instance = self.get_object()
        expense_amount = instance.amount
        
        with transaction.atomic():
            # Restore salesman balance - add back expense amount
            salesman = instance.delivery.salesman
            salesman.current_balance += expense_amount
            salesman.save()
            
            print(f"Deleted expense {instance.id} for LKR {expense_amount}")
            print(f"Updated salesman {salesman.name} balance: LKR {salesman.current_balance}")
            
            instance.delete()
            
            return Response({
                'salesman_balance': float(salesman.current_balance),
                'message': f'Expense deleted. Salesman balance updated to LKR {salesman.current_balance}'
            }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='mark-settled')
    def mark_settled(self, request, pk=None):
        """
        Mark an expense as settled - Only available for individual expense settlement
        Note: Expenses are automatically settled when the delivery is settled
        """
        expense = self.get_object()
        
        if expense.is_settled:
            return Response(
                {'error': 'Expense is already settled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if delivery is already settled
        if expense.delivery.status == 'settled':
            return Response(
                {'error': 'Cannot settle individual expenses for a settled delivery'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only owners can mark expenses as settled
        if not hasattr(request.user, 'owner_profile'):
            return Response(
                {'error': 'Only owners can mark expenses as settled'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            expense.is_settled = True
            expense.settled_at = timezone.now()
            expense.settled_by = request.user
            expense.save()
            
            # Reduce salesman balance when expense is settled individually
            # (This is already done during creation, but we ensure consistency)
            # No additional balance adjustment needed since expense amount was already deducted during creation
        
        serializer = self.get_serializer(expense)
        return Response({
            'message': 'Expense marked as settled',
            'expense': serializer.data
        })




@extend_schema_view(
    list=extend_schema(
        summary="List product returns",
        description="Get a paginated list of product returns with filtering options",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by return status',
                required=False,
                type=str,
                enum=['pending', 'approved', 'disposed']
            ),
            OpenApiParameter(
                name='return_reason',
                description='Filter by return reason',
                required=False,
                type=str,
                enum=['unsold', 'damaged', 'expired', 'defective', 'customer_return', 'other']
            ),
            OpenApiParameter(
                name='salesman',
                description='Filter by salesman ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='product',
                description='Filter by product ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='search',
                description='Search by product name, salesman name, or notes',
                required=False,
                type=str
            )
        ],
        responses={200: ProductReturnSerializer(many=True)},
        tags=['Return Management']
    ),
    create=extend_schema(
        summary="Create product return",
        description="Create a new product return request",
        request=CreateProductReturnSerializer,
        responses={
            201: ProductReturnSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Return Management']
    ),
    retrieve=extend_schema(
        summary="Get return details",
        description="Retrieve detailed information about a specific return",
        responses={
            200: ProductReturnSerializer,
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Return Management']
    )
)
class ProductReturnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product returns with approval workflow
    """
    queryset = ProductReturn.objects.select_related(
        'batch_assignment__batch__product',
        'batch_assignment__salesman__user',
        'batch_assignment__delivery',
        'processed_by',
        'created_by'
    ).all()
    serializer_class = ProductReturnSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'return_reason', 'batch_assignment__salesman', 'batch_assignment__batch__product']
    search_fields = ['batch_assignment__batch__product__name', 'batch_assignment__salesman__user__first_name', 
                    'batch_assignment__salesman__user__last_name', 'return_notes', 'processing_notes']
    ordering_fields = ['return_date', 'processed_date', 'return_quantity']
    ordering = ['-return_date']

    def get_serializer_class(self):
        """Return different serializers based on action"""
        if self.action == 'create':
            return CreateProductReturnSerializer
        elif self.action in ['approve_return', 'dispose_return']:
            return ProcessReturnSerializer
        return ProductReturnSerializer

    def get_queryset(self):
        """Filter returns based on user role"""
        queryset = super().get_queryset()
        
        if self.request.user.role == 'owner':
            try:
                owner = self.request.user.owner_profile
                queryset = queryset.filter(batch_assignment__batch__product__owner=owner)
            except:
                queryset = queryset.none()
        elif self.request.user.role == 'salesman':
            try:
                salesman = self.request.user.salesman_profile
                # Salesmen can only see their own returns
                queryset = queryset.filter(batch_assignment__salesman=salesman)
            except:
                queryset = queryset.none()
        elif self.request.user.role == 'shop':
            # Shops cannot access returns directly
            queryset = queryset.none()
        # Developers can see all returns
        
        return queryset

    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ['approve_return', 'dispose_return']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Handle return creation with logging"""
        db_logger.info(f"Creating product return by user: {self.request.user.username}")
        
        return_obj = serializer.save(created_by=self.request.user)
        
        db_logger.info(f"Product return created: ID={return_obj.id}, Product={return_obj.product.name}, "
                      f"Quantity={return_obj.return_quantity}, Reason={return_obj.return_reason}")

    @extend_schema(
        summary="Approve product return",
        description="Approve a pending return and add stock back to inventory",
        request=ProcessReturnSerializer,
        responses={
            200: OpenApiResponse(description="Return approved successfully"),
            400: OpenApiResponse(description="Invalid request or return cannot be approved"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Return Management']
    )
    @action(detail=True, methods=['post'])
    def approve_return(self, request, pk=None):
        """Approve a pending return"""
        try:
            return_obj = self.get_object()
            
            if return_obj.status != 'pending':
                return Response(
                    {'error': 'Only pending returns can be approved'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = ProcessReturnSerializer(data=request.data)
            if serializer.is_valid():
                processing_notes = serializer.validated_data.get('processing_notes', '')
                
                # Approve the return
                return_obj.approve_return(
                    processed_by=request.user,
                    processing_notes=processing_notes
                )
                
                db_logger.info(f"Return approved: ID={return_obj.id}, Product={return_obj.product.name}, "
                              f"Quantity={return_obj.return_quantity}, Processed by={request.user.username}")
                
                return Response({
                    'message': 'Return approved successfully',
                    'return_id': return_obj.id,
                    'status': return_obj.status,
                    'processed_date': return_obj.processed_date
                })
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            db_logger.error(f"Error approving return {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to approve return'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Dispose product return",
        description="Dispose a pending return (permanently remove from system)",
        request=ProcessReturnSerializer,
        responses={
            200: OpenApiResponse(description="Return disposed successfully"),
            400: OpenApiResponse(description="Invalid request or return cannot be disposed"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Return Management']
    )
    @action(detail=True, methods=['post'])
    def dispose_return(self, request, pk=None):
        """Dispose a pending return"""
        try:
            return_obj = self.get_object()
            
            if return_obj.status != 'pending':
                return Response(
                    {'error': 'Only pending returns can be disposed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = ProcessReturnSerializer(data=request.data)
            if serializer.is_valid():
                processing_notes = serializer.validated_data.get('processing_notes', '')
                
                # Dispose the return
                return_obj.dispose_return(
                    processed_by=request.user,
                    processing_notes=processing_notes
                )
                
                db_logger.info(f"Return disposed: ID={return_obj.id}, Product={return_obj.product.name}, "
                              f"Quantity={return_obj.return_quantity}, Processed by={request.user.username}")
                
                return Response({
                    'message': 'Return disposed successfully',
                    'return_id': return_obj.id,
                    'status': return_obj.status,
                    'processed_date': return_obj.processed_date
                })
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            db_logger.error(f"Error disposing return {pk}: {str(e)}")
            return Response(
                {'error': 'Failed to dispose return'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get pending returns summary",
        description="Get summary of all pending returns for dashboard",
        responses={
            200: OpenApiResponse(
                description="Pending returns summary",
                examples=[
                    OpenApiExample(
                        "Pending Returns Summary",
                        value={
                            "total_pending": 15,
                            "total_quantity": 150,
                            "by_reason": {
                                "unsold": 10,
                                "damaged": 3,
                                "expired": 2
                            },
                            "by_salesman": [
                                {
                                    "salesman_id": 1,
                                    "salesman_name": "John Doe",
                                    "pending_count": 5,
                                    "pending_quantity": 50
                                }
                            ]
                        }
                    )
                ]
            )
        },
        tags=['Return Management']
    )
    @action(detail=False, methods=['get'])
    def pending_summary(self, request):
        """Get summary of pending returns and salesman balances"""
        try:
            # Filter by user permissions
            queryset = self.get_queryset().filter(status='pending')
            
            # Total counts
            total_pending = queryset.count()
            total_quantity = queryset.aggregate(total=Sum('return_quantity'))['total'] or 0
            
            # Group by reason
            by_reason = {}
            reason_counts = queryset.values('return_reason').annotate(
                count=Count('id'),
                quantity=Sum('return_quantity')
            )
            for item in reason_counts:
                by_reason[item['return_reason']] = {
                    'count': item['count'],
                    'quantity': item['quantity']
                }
            
            # Group by salesman
            by_salesman = []
            salesman_counts = queryset.values(
                'batch_assignment__salesman__id',
                'batch_assignment__salesman__user__first_name',
                'batch_assignment__salesman__user__last_name'
            ).annotate(
                count=Count('id'),
                quantity=Sum('return_quantity')
            )
            
            for item in salesman_counts:
                by_salesman.append({
                    'salesman_id': item['batch_assignment__salesman__id'],
                    'salesman_name': f"{item['batch_assignment__salesman__user__first_name']} {item['batch_assignment__salesman__user__last_name']}",
                    'pending_count': item['count'],
                    'pending_quantity': item['quantity']
                })
            
            # Get salesman balance summary
            from accounts.models import Salesman
            from sales.models import Invoice
            from decimal import Decimal
            
            salesman_balances = []
            
            # Get all salesmen for the current owner
            if request.user.role == 'owner':
                try:
                    owner = request.user.owner_profile
                    salesmen = Salesman.objects.filter(owner=owner, is_active=True)
                except:
                    salesmen = Salesman.objects.none()
            elif request.user.role == 'developer':
                salesmen = Salesman.objects.filter(is_active=True)
            else:
                salesmen = Salesman.objects.none()
            
            for salesman in salesmen:
                # Calculate pending deliveries value (outstanding batch assignments)
                pending_deliveries_value = BatchAssignment.objects.filter(
                    salesman=salesman,
                    status__in=['delivered', 'partial']
                ).aggregate(
                    total=Sum(F('delivered_quantity') - F('returned_quantity'), output_field=models.DecimalField())
                )['total'] or Decimal('0.00')
                
                # Calculate outstanding invoices value for this salesman
                outstanding_invoices_value = Invoice.objects.filter(
                    salesman=salesman,
                    status__in=['pending', 'partial']
                ).aggregate(
                    total=Sum('balance_due')
                )['total'] or Decimal('0.00')
                
                salesman_balances.append({
                    'salesman_id': salesman.id,
                    'salesman_name': salesman.user.get_full_name(),
                    'current_balance': float(salesman.current_balance),
                    'total_cash_collected': float(salesman.total_cash_collected),
                    'total_cash_settled': float(salesman.total_cash_settled),
                    'net_cash_position': float(salesman.net_cash_position),
                    'last_settlement_date': salesman.last_settlement_date.isoformat() if salesman.last_settlement_date else None,
                    'pending_deliveries_value': float(pending_deliveries_value),
                    'outstanding_invoices_value': float(outstanding_invoices_value)
                })
            
            return Response({
                'pending_returns': {
                    'total_pending': total_pending,
                    'total_quantity': total_quantity,
                    'by_reason': by_reason,
                    'by_salesman': by_salesman
                },
                'salesman_balances': salesman_balances
            })
            
        except Exception as e:
            db_logger.error(f"Error getting pending returns summary: {str(e)}")
            return Response(
                {'error': 'Failed to get pending returns summary'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Bulk process returns",
        description="Approve or dispose multiple returns at once",
        request=OpenApiExample(
            "Bulk Process Request",
            value={
                "return_ids": [1, 2, 3],
                "action": "approve",
                "processing_notes": "Bulk approval of unsold stock"
            }
        ),
        responses={
            200: OpenApiResponse(description="Returns processed successfully"),
            400: OpenApiResponse(description="Invalid request data"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Return Management']
    )
    @action(detail=False, methods=['post'])
    def bulk_process(self, request):
        """Bulk approve or dispose returns"""
        try:
            return_ids = request.data.get('return_ids', [])
            action = request.data.get('action')
            processing_notes = request.data.get('processing_notes', '')
            
            if not return_ids or action not in ['approve', 'dispose']:
                return Response(
                    {'error': 'Invalid request. Provide return_ids and action (approve/dispose)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get returns that can be processed
            returns = self.get_queryset().filter(
                id__in=return_ids,
                status='pending'
            )
            
            if not returns.exists():
                return Response(
                    {'error': 'No pending returns found with provided IDs'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            processed_count = 0
            errors = []
            
            for return_obj in returns:
                try:
                    if action == 'approve':
                        return_obj.approve_return(
                            processed_by=request.user,
                            processing_notes=processing_notes
                        )
                    else:  # dispose
                        return_obj.dispose_return(
                            processed_by=request.user,
                            processing_notes=processing_notes
                        )
                    processed_count += 1
                except Exception as e:
                    errors.append(f"Return {return_obj.id}: {str(e)}")
            
            db_logger.info(f"Bulk {action} processed {processed_count} returns by {request.user.username}")
            
            response_data = {
                'message': f'Successfully {action}d {processed_count} returns',
                'processed_count': processed_count,
                'total_requested': len(return_ids)
            }
            
            if errors:
                response_data['errors'] = errors
            
            return Response(response_data)
            
        except Exception as e:
            db_logger.error(f"Error in bulk process returns: {str(e)}")
            return Response(
                {'error': 'Failed to process returns'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )