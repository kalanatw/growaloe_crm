from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, F
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

from .models import Category, Product, SalesmanStock, StockMovement, Delivery, DeliveryItem
from .serializers import (
    CategorySerializer, ProductSerializer, SalesmanStockSerializer,
    StockMovementSerializer, ProductStockSummarySerializer,
    SalesmanStockSummarySerializer, DeliverySerializer, CreateDeliverySerializer,
    DeliveryItemSerializer
)
from accounts.permissions import IsOwnerOrDeveloper, IsAuthenticated

User = get_user_model()


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

    def get_queryset(self):
        queryset = super().get_queryset()
        # All roles can view products
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
        Handle product creation with stock tracking
        """
        product = serializer.save(created_by=self.request.user)
        
        # Create stock movement record for initial stock if stock_quantity > 0
        if product.stock_quantity > 0:
            StockMovement.objects.create(
                product=product,
                movement_type='purchase',
                quantity=product.stock_quantity,
                notes=f'Initial stock for product creation',
                created_by=self.request.user
            )

    def perform_update(self, serializer):
        """
        Handle product updates with stock tracking
        """
        old_product = self.get_object()
        old_stock_quantity = old_product.stock_quantity
        
        product = serializer.save()
        new_stock_quantity = product.stock_quantity
        
        # Create stock movement if stock quantity changed
        if new_stock_quantity != old_stock_quantity:
            quantity_diff = new_stock_quantity - old_stock_quantity
            movement_type = 'purchase' if quantity_diff > 0 else 'adjustment'
            
            StockMovement.objects.create(
                product=product,
                movement_type=movement_type,
                quantity=quantity_diff,
                notes=f'Stock quantity updated from {old_stock_quantity} to {new_stock_quantity}',
                created_by=self.request.user
            )

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
        Get stock summary for all products
        """
        products = Product.objects.filter(is_active=True).annotate(
            allocated_stock=Sum('salesman_allocations__allocated_quantity'),
            available_stock=Sum('salesman_allocations__available_quantity'),
            salesmen_count=Count('salesman_allocations__salesman', distinct=True)
        )

        summary_data = []
        for product in products:
            summary_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_sku': product.sku,
                'total_stock': product.allocated_stock or 0,
                'allocated_stock': product.allocated_stock or 0,
                'available_stock': product.available_stock or 0,
                'salesmen_count': product.salesmen_count or 0
            })

        serializer = ProductStockSummarySerializer(summary_data, many=True)
        return Response(serializer.data)

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
        Get stock distribution for a specific product across salesmen
        """
        product = self.get_object()
        stocks = SalesmanStock.objects.filter(product=product).select_related('salesman__user')
        serializer = SalesmanStockSerializer(stocks, many=True)
        return Response(serializer.data)

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

        # Get all active products with stock
        products = Product.objects.filter(is_active=True, stock_quantity__gt=0).select_related('category')
        
        stock_data = []
        for product in products:
            stock_data.append({
                'id': f"product_{product.id}",
                'product': product.id,
                'product_name': product.name,
                'product_sku': product.sku,
                'product_base_price': float(product.base_price),
                'available_quantity': product.stock_quantity,
                'category': product.category.name if product.category else 'Uncategorized',
                # Add fields to match SalesmanStock interface
                'salesman': None,
                'salesman_name': 'Direct Stock',
                'allocated_quantity': product.stock_quantity,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat(),
            })
        
        return Response({
            'stocks': stock_data,
            'summary': {
                'total_products': len(stock_data),
                'total_available_quantity': sum(item['available_quantity'] for item in stock_data),
                'total_stock_value': sum(
                    item['product_base_price'] * item['available_quantity'] 
                    for item in stock_data
                )
            }
        })


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
    ViewSet for managing salesman stock allocations with role-based access control
    """
    queryset = SalesmanStock.objects.select_related('product', 'salesman__user').all()
    serializer_class = SalesmanStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['salesman', 'product']
    search_fields = ['product__name', 'product__sku', 'salesman__user__first_name', 'salesman__user__last_name']
    ordering_fields = ['quantity', 'allocated_quantity', 'last_updated']
    ordering = ['-last_updated']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'salesman':
            # Salesmen can only see their own stock
            return queryset.filter(salesman=user.salesman_profile)
        elif user.role == 'shop':
            # Shops can see stock of salesmen assigned to them
            return queryset.filter(salesman__assigned_shops=user.shop_profile)
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
        Get current user's stock from deliveries (for salesmen)
        """
        if request.user.role != 'salesman':
            return Response(
                {'error': 'This endpoint is only for salesmen'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get salesman's current stock from deliveries
        from .models import DeliveryItem
        
        # Get all delivery items for this salesman
        delivery_items = DeliveryItem.objects.filter(
            delivery__salesman=request.user.salesman_profile
        ).select_related('product', 'delivery')
        
        # Group by product and calculate remaining stock
        stock_data = {}
        for item in delivery_items:
            product_id = item.product.id
            if product_id not in stock_data:
                stock_data[product_id] = {
                    'product': item.product,
                    'delivered_quantity': 0,
                    'sold_quantity': 0,  # Will be calculated from invoices
                    'remaining_quantity': 0
                }
            stock_data[product_id]['delivered_quantity'] += item.quantity
        
        # Calculate sold quantities from invoices
        from sales.models import InvoiceItem
        for product_id in stock_data.keys():
            sold_qty = InvoiceItem.objects.filter(
                invoice__salesman=request.user.salesman_profile,
                product_id=product_id
            ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
            
            stock_data[product_id]['sold_quantity'] = sold_qty
            stock_data[product_id]['remaining_quantity'] = (
                stock_data[product_id]['delivered_quantity'] - sold_qty
            )
        
        # Convert to serializable format matching SalesmanStock interface
        stock_data_list = []
        for product_id, data in stock_data.items():
            if data['remaining_quantity'] > 0:  # Only show products with remaining stock
                stock_data_list.append({
                    'id': f"delivery_{product_id}",
                    'salesman': request.user.salesman_profile.id,
                    'salesman_name': request.user.get_full_name(),
                    'product': data['product'].id,
                    'product_name': data['product'].name,
                    'product_sku': data['product'].sku,
                    'product_base_price': float(data['product'].base_price),
                    'allocated_quantity': data['delivered_quantity'],
                    'available_quantity': data['remaining_quantity'],
                    'created_at': timezone.now().isoformat(),
                    'updated_at': timezone.now().isoformat(),
                })
        
        return Response({
            'stocks': stock_data_list,
            'summary': {
                'total_products': len(stock_data_list),
                'total_stock_value': sum(
                    float(stock['product_base_price']) * stock['available_quantity'] 
                    for stock in stock_data_list
                )
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
                # When marking as delivered, update salesman stock
                for item in instance.items.all():
                    item._update_salesman_stock()
            elif old_status == 'delivered' and new_status in ['pending', 'cancelled']:
                # When changing from delivered, reverse stock allocation
                for item in instance.items.all():
                    item._update_salesman_stock(reverse=True)
        
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
        
        # Update salesman stock for all items
        for item in delivery.items.all():
            item._update_salesman_stock()
        
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
