from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, F
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

from .models import Category, Product, SalesmanStock, StockMovement
from .serializers import (
    CategorySerializer, ProductSerializer, SalesmanStockSerializer,
    StockMovementSerializer, ProductStockSummarySerializer,
    SalesmanStockSummarySerializer
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
        Get current user's stock (for salesmen)
        """
        if request.user.role != 'salesman':
            return Response(
                {'error': 'This endpoint is only for salesmen'},
                status=status.HTTP_403_FORBIDDEN
            )

        stocks = self.get_queryset().filter(salesman=request.user.salesman_profile)
        serializer = self.get_serializer(stocks, many=True)
        
        # Calculate summary
        total_products = stocks.count()
        total_value = sum(stock.allocated_quantity * stock.product.cost_price for stock in stocks)
        
        return Response({
            'stocks': serializer.data,
            'summary': {
                'total_products': total_products,
                'total_stock_value': total_value
            }
        })

    @extend_schema(
        summary="Get stock summary by salesman",
        description="Get comprehensive stock summary for all salesmen (Owner/Developer only)",
        responses={
            200: OpenApiResponse(
                response=SalesmanStockSummarySerializer(many=True),
                description="Stock summary by salesman",
                examples=[
                    OpenApiExample(
                        "Salesman Summary Response",
                        value=[
                            {
                                "salesman_id": 1,
                                "salesman_name": "John Smith",
                                "total_products": 5,
                                "total_stock_value": 2500.00,
                                "products": []
                            }
                        ]
                    )
                ]
            ),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'])
    def salesman_summary(self, request):
        """
        Get stock summary by salesman
        """
        if request.user.role not in ['owner', 'developer']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        from accounts.models import Salesman
        
        salesmen = Salesman.objects.select_related('user').prefetch_related(
            'stock_allocations__product'
        ).all()

        summary_data = []
        for salesman in salesmen:
            stocks = salesman.stock_allocations.all()
            total_value = sum(stock.allocated_quantity * stock.product.cost_price for stock in stocks)
            
            summary_data.append({
                'salesman_id': salesman.id,
                'salesman_name': salesman.user.get_full_name(),
                'total_products': stocks.count(),
                'total_stock_value': total_value,
                'products': [stock.product for stock in stocks]
            })

        serializer = SalesmanStockSummarySerializer(summary_data, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List stock movements",
        description="Get a paginated list of stock movement history based on user permissions",
        parameters=[
            OpenApiParameter(
                name='movement_type',
                description='Filter by movement type',
                required=False,
                type=str,
                enum=['IN', 'OUT', 'TRANSFER', 'ADJUSTMENT']
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
                description='Search by product name/SKU or reason',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['created_at', '-created_at', 'quantity', '-quantity']
            )
        ],
        responses={200: StockMovementSerializer(many=True)},
        tags=['Product Management']
    ),
    retrieve=extend_schema(
        summary="Get stock movement details",
        description="Retrieve detailed information about a specific stock movement",
        responses={
            200: StockMovementSerializer,
            404: OpenApiResponse(description="Stock movement not found")
        },
        tags=['Product Management']
    )
)
class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing stock movement history (read-only) with role-based filtering
    """
    queryset = StockMovement.objects.select_related(
        'product', 'salesman__user', 'performed_by'
    ).all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['movement_type', 'salesman', 'product']
    search_fields = ['product__name', 'product__sku', 'reason']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'salesman':
            # Salesmen can only see their own stock movements
            return queryset.filter(salesman=user.salesman_profile)
        elif user.role == 'shop':
            # Shops can see movements of salesmen assigned to them
            return queryset.filter(salesman__assigned_shops=user.shop_profile)
        else:
            # Owners and Developers can see all movements
            return queryset

    @extend_schema(
        summary="Get recent stock movements",
        description="Get the last 50 stock movements based on user permissions",
        responses={
            200: OpenApiResponse(
                response=StockMovementSerializer(many=True),
                description="Recent stock movements",
                examples=[
                    OpenApiExample(
                        "Recent Movements Response",
                        value=[
                            {
                                "id": 1,
                                "product": 1,
                                "product_name": "Aloe Vera Gel",
                                "salesman": 1,
                                "salesman_name": "John Smith",
                                "movement_type": "OUT",
                                "quantity": 10,
                                "reason": "Sale to customer",
                                "performed_by": 1,
                                "performed_by_name": "Admin User",
                                "created_at": "2025-06-01T10:00:00Z"
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'])
    def recent_movements(self, request):
        """
        Get recent stock movements (last 50)
        """
        movements = self.get_queryset()[:50]
        serializer = self.get_serializer(movements, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get stock movement summary",
        description="Get summary statistics of stock movements by type and quantities",
        responses={
            200: OpenApiResponse(
                description="Stock movement summary",
                examples=[
                    OpenApiExample(
                        "Movement Summary Response",
                        value={
                            "movements_count": {
                                "IN": 25,
                                "OUT": 40,
                                "TRANSFER": 5,
                                "ADJUSTMENT": 3
                            },
                            "quantities_total": {
                                "IN": 500,
                                "OUT": 320,
                                "TRANSFER": 50,
                                "ADJUSTMENT": 10
                            },
                            "total_movements": 73
                        }
                    )
                ]
            )
        },
        tags=['Product Management']
    )
    @action(detail=False, methods=['get'])
    def movement_summary(self, request):
        """
        Get stock movement summary
        """
        queryset = self.get_queryset()
        
        # Count movements by type
        movements_by_type = {}
        for movement_type in StockMovement.MOVEMENT_TYPES:
            movements_by_type[movement_type[0]] = queryset.filter(
                movement_type=movement_type[0]
            ).count()

        # Get total quantities by type
        quantities_by_type = {}
        for movement_type in StockMovement.MOVEMENT_TYPES:
            total_qty = queryset.filter(
                movement_type=movement_type[0]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            quantities_by_type[movement_type[0]] = total_qty

        return Response({
            'movements_count': movements_by_type,
            'quantities_total': quantities_by_type,
            'total_movements': queryset.count()
        })
