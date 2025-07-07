from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, F, Avg
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

from .models import DashboardMetrics, SalesReport, InventoryReport, FinancialReport
from .serializers import (
    DashboardMetricsSerializer, SalesReportSerializer, InventoryReportSerializer,
    FinancialReportSerializer, ReportSummarySerializer, SalesAnalyticsSerializer,
    ProductPerformanceSerializer, CustomerAnalyticsSerializer, RegionalPerformanceSerializer
)
from accounts.permissions import IsOwnerOrDeveloper, IsAuthenticated
from sales.models import Invoice, InvoiceItem, Transaction
from products.models import Product, Batch, BatchAssignment

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="List dashboard metrics",
        description="Get a paginated list of dashboard metrics",
        parameters=[
            OpenApiParameter(
                name='date',
                description='Filter by date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search by owner business name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['date', '-date', 'created_at', '-created_at']
            )
        ],
        responses={200: DashboardMetricsSerializer(many=True)},
        tags=['Reports Management']
    ),
    create=extend_schema(
        summary="Create dashboard metrics",
        description="Generate new dashboard metrics (Owner/Developer only)",
        request=DashboardMetricsSerializer,
        responses={
            201: DashboardMetricsSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Reports Management']
    ),
    retrieve=extend_schema(
        summary="Get dashboard metrics details",
        description="Retrieve detailed information about specific dashboard metrics",
        responses={
            200: DashboardMetricsSerializer,
            404: OpenApiResponse(description="Dashboard metrics not found")
        },
        tags=['Reports Management']
    ),
    update=extend_schema(
        summary="Update dashboard metrics",
        description="Update dashboard metrics information (Owner/Developer only)",
        request=DashboardMetricsSerializer,
        responses={
            200: DashboardMetricsSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Dashboard metrics not found")
        },
        tags=['Reports Management']
    ),
    partial_update=extend_schema(
        summary="Partially update dashboard metrics",
        description="Partially update dashboard metrics information (Owner/Developer only)",
        request=DashboardMetricsSerializer,
        responses={
            200: DashboardMetricsSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Dashboard metrics not found")
        },
        tags=['Reports Management']
    ),
    destroy=extend_schema(
        summary="Delete dashboard metrics",
        description="Delete dashboard metrics (Owner/Developer only)",
        responses={
            204: OpenApiResponse(description="Dashboard metrics deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Dashboard metrics not found")
        },
        tags=['Reports Management']
    )
)
class DashboardMetricsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard metrics with role-based permissions
    """
    queryset = DashboardMetrics.objects.select_related('owner').all()
    serializer_class = DashboardMetricsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['date']
    search_fields = ['owner__business_name', 'owner__user__first_name', 'owner__user__last_name']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def get_permissions(self):
        """
        Only owners and developers can create/modify dashboard metrics
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)

    @extend_schema(
        summary="Generate current dashboard metrics",
        description="Generate dashboard metrics for the current date (Owner/Developer only)",
        request=None,
        responses={
            200: OpenApiResponse(
                response=DashboardMetricsSerializer,
                description="Dashboard metrics generated successfully",
                examples=[
                    OpenApiExample(
                        "Generated Metrics Response",
                        value={
                            "id": 1,
                            "report_date": "2025-06-01",
                            "total_sales": 25000.00,
                            "total_invoices": 85,
                            "total_customers": 45,
                            "total_products": 15,
                            "total_inventory_value": 50000.00,
                            "outstanding_amount": 5000.00,
                            "generated_by": 1
                        }
                    )
                ]
            ),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Reports Management']
    )
    @action(detail=False, methods=['post'])
    def generate_current(self, request):
        """
        Generate dashboard metrics for current date
        """
        if request.user.role not in ['OWNER', 'DEVELOPER']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        today = timezone.now().date()
        
        # Calculate metrics
        total_sales = Invoice.objects.filter(
            status__in=['PAID', 'PARTIAL']
        ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
        
        total_invoices = Invoice.objects.count()
        
        # Count unique customers
        total_customers = Invoice.objects.values('customer_name').distinct().count()
        
        total_products = Product.objects.filter(is_active=True).count()
        
        # Calculate total inventory value from all active batches
        total_inventory_value = Decimal('0')
        batches = Batch.objects.filter(is_active=True, current_quantity__gt=0).select_related('product')
        for batch in batches:
            total_inventory_value += batch.current_quantity * batch.unit_cost
        
        # Calculate outstanding amount
        outstanding_amount = Decimal('0')
        for invoice in Invoice.objects.filter(status__in=['SENT', 'PARTIAL']):
            outstanding_amount += invoice.get_outstanding_balance()
        
        # Create or update dashboard metrics
        # Get the owner for the current user
        from accounts.models import Owner
        try:
            owner = request.user.owner_profile
        except AttributeError:
            # If user is not an owner, use the first owner or create one
            owner = Owner.objects.first()
            if not owner:
                return Response(
                    {'error': 'No owner found in system'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        metrics, created = DashboardMetrics.objects.update_or_create(
            owner=owner,
            date=today,
            defaults={
                'total_sales': total_sales,
                'total_invoices': total_invoices,
                'outstanding_amount': outstanding_amount,
                'products_sold': total_products,
                'low_stock_items': 0,  # TODO: Calculate actual low stock items
                'active_salesmen': 0,  # TODO: Calculate active salesmen
                'top_salesman_sales': Decimal('0'),
                'active_shops': 0,  # TODO: Calculate active shops
                'shops_with_overdue': 0,  # TODO: Calculate shops with overdue
            }
        )
        
        serializer = self.get_serializer(metrics)
        return Response(serializer.data)

    @extend_schema(
        summary="Get latest dashboard metrics",
        description="Retrieve the most recent dashboard metrics",
        responses={
            200: OpenApiResponse(
                response=DashboardMetricsSerializer,
                description="Latest dashboard metrics",
                examples=[
                    OpenApiExample(
                        "Latest Metrics Response",
                        value={
                            "id": 1,
                            "report_date": "2025-06-01",
                            "total_sales": 25000.00,
                            "total_invoices": 85,
                            "total_customers": 45,
                            "total_products": 15,
                            "total_inventory_value": 50000.00,
                            "outstanding_amount": 5000.00,
                            "generated_by": 1
                        }
                    )
                ]
            ),
            200: OpenApiResponse(
                description="No metrics found",
                examples=[
                    OpenApiExample(
                        "No Metrics Response",
                        value={"message": "No metrics found"}
                    )
                ]
            )
        },
        tags=['Reports Management']
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get latest dashboard metrics
        """
        latest_metrics = self.get_queryset().first()
        if latest_metrics:
            serializer = self.get_serializer(latest_metrics)
            return Response(serializer.data)
        return Response({'message': 'No metrics found'})


@extend_schema_view(
    list=extend_schema(
        summary="List sales reports",
        description="Get a paginated list of sales reports based on user permissions",
        parameters=[
            OpenApiParameter(
                name='report_type',
                description='Filter by report type',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='salesman',
                description='Filter by salesman ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='shop',
                description='Filter by shop ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='start_date',
                description='Filter by start date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='end_date',
                description='Filter by end date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search by salesman or shop name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['start_date', '-start_date', 'end_date', '-end_date', 'total_sales', '-total_sales', 'created_at', '-created_at']
            )
        ],
        responses={200: SalesReportSerializer(many=True)},
        tags=['Reports Management']
    ),
    create=extend_schema(
        summary="Create sales report",
        description="Generate a new sales report (Owner/Developer only)",
        request=SalesReportSerializer,
        responses={
            201: SalesReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Reports Management']
    ),
    retrieve=extend_schema(
        summary="Get sales report details",
        description="Retrieve detailed information about a specific sales report",
        responses={
            200: SalesReportSerializer,
            404: OpenApiResponse(description="Sales report not found")
        },
        tags=['Reports Management']
    ),
    update=extend_schema(
        summary="Update sales report",
        description="Update sales report information (Owner/Developer only)",
        request=SalesReportSerializer,
        responses={
            200: SalesReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Sales report not found")
        },
        tags=['Reports Management']
    ),
    partial_update=extend_schema(
        summary="Partially update sales report",
        description="Partially update sales report information (Owner/Developer only)",
        request=SalesReportSerializer,
        responses={
            200: SalesReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Sales report not found")
        },
        tags=['Reports Management']
    ),
    destroy=extend_schema(
        summary="Delete sales report",
        description="Delete a sales report (Owner/Developer only)",
        responses={
            204: OpenApiResponse(description="Sales report deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Sales report not found")
        },
        tags=['Reports Management']
    )
)
class SalesReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales reports with role-based filtering and comprehensive analytics
    """
    queryset = SalesReport.objects.select_related('generated_by', 'salesman__user', 'shop').all()
    serializer_class = SalesReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'salesman', 'shop', 'start_date', 'end_date']
    search_fields = ['salesman__user__first_name', 'salesman__user__last_name', 'shop__name']
    ordering_fields = ['start_date', 'end_date', 'total_sales', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'SALESMAN':
            # Salesmen can only see their own reports
            return queryset.filter(salesman=user.salesman_profile)
        elif user.role == 'SHOP':
            # Shops can see reports for their salesmen
            return queryset.filter(shop=user.shop_profile)
        else:
            # Owners and Developers can see all reports
            return queryset

    def get_permissions(self):
        """
        Only owners and developers can create/modify sales reports
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List inventory reports",
        description="Get a paginated list of inventory reports based on user permissions",
        parameters=[
            OpenApiParameter(
                name='report_type',
                description='Filter by report type',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='start_date',
                description='Filter by start date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='end_date',
                description='Filter by end date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search by title or generator name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['start_date', '-start_date', 'end_date', '-end_date', 'generated_at', '-generated_at']
            )
        ],
        responses={200: InventoryReportSerializer(many=True)},
        tags=['Reports Management']
    ),
    create=extend_schema(
        summary="Create inventory report",
        description="Generate a new inventory report (Owner/Developer only)",
        request=InventoryReportSerializer,
        responses={
            201: InventoryReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Reports Management']
    ),
    retrieve=extend_schema(
        summary="Get inventory report details",
        description="Retrieve detailed information about a specific inventory report",
        responses={
            200: InventoryReportSerializer,
            404: OpenApiResponse(description="Inventory report not found")
        },
        tags=['Reports Management']
    ),
    update=extend_schema(
        summary="Update inventory report",
        description="Update inventory report information (Owner/Developer only)",
        request=InventoryReportSerializer,
        responses={
            200: InventoryReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Inventory report not found")
        },
        tags=['Reports Management']
    ),
    partial_update=extend_schema(
        summary="Partially update inventory report",
        description="Partially update inventory report information (Owner/Developer only)",
        request=InventoryReportSerializer,
        responses={
            200: InventoryReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Inventory report not found")
        },
        tags=['Reports Management']
    ),
    destroy=extend_schema(
        summary="Delete inventory report",
        description="Delete an inventory report (Owner/Developer only)",
        responses={
            204: OpenApiResponse(description="Inventory report deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Inventory report not found")
        },
        tags=['Reports Management']
    )
)
class InventoryReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing inventory reports with role-based access control
    """
    queryset = InventoryReport.objects.select_related('generated_by').all()
    serializer_class = InventoryReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'start_date', 'end_date']
    search_fields = ['title', 'generated_by__first_name', 'generated_by__last_name']
    ordering_fields = ['start_date', 'end_date', 'generated_at']
    ordering = ['-generated_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        # All authenticated users can see inventory reports
        return queryset

    def get_permissions(self):
        """
        Only owners and developers can create/modify inventory reports
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrDeveloper]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List financial reports",
        description="Get a paginated list of financial reports (Owner/Developer only)",
        parameters=[
            OpenApiParameter(
                name='report_type',
                description='Filter by report type',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='start_date',
                description='Filter by start date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='end_date',
                description='Filter by end date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search by generator name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['start_date', '-start_date', 'end_date', '-end_date', 'total_revenue', '-total_revenue', 'created_at', '-created_at']
            )
        ],
        responses={200: FinancialReportSerializer(many=True)},
        tags=['Reports Management']
    ),
    create=extend_schema(
        summary="Create financial report",
        description="Generate a new financial report (Owner/Developer only)",
        request=FinancialReportSerializer,
        responses={
            201: FinancialReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Reports Management']
    ),
    retrieve=extend_schema(
        summary="Get financial report details",
        description="Retrieve detailed information about a specific financial report",
        responses={
            200: FinancialReportSerializer,
            404: OpenApiResponse(description="Financial report not found")
        },
        tags=['Reports Management']
    ),
    update=extend_schema(
        summary="Update financial report",
        description="Update financial report information (Owner/Developer only)",
        request=FinancialReportSerializer,
        responses={
            200: FinancialReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Financial report not found")
        },
        tags=['Reports Management']
    ),
    partial_update=extend_schema(
        summary="Partially update financial report",
        description="Partially update financial report information (Owner/Developer only)",
        request=FinancialReportSerializer,
        responses={
            200: FinancialReportSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Financial report not found")
        },
        tags=['Reports Management']
    ),
    destroy=extend_schema(
        summary="Delete financial report",
        description="Delete a financial report (Owner/Developer only)",
        responses={
            204: OpenApiResponse(description="Financial report deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Financial report not found")
        },
        tags=['Reports Management']
    )
)
class FinancialReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financial reports with strict role-based permissions (Owner/Developer only)
    """
    queryset = FinancialReport.objects.select_related('generated_by').all()
    serializer_class = FinancialReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'start_date', 'end_date']
    search_fields = ['generated_by__first_name', 'generated_by__last_name']
    ordering_fields = ['start_date', 'end_date', 'total_revenue', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Only owners and developers can access financial reports
        """
        permission_classes = [IsOwnerOrDeveloper]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


class ReportsAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for advanced analytics and reporting with comprehensive business intelligence features
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get reports summary",
        description="Get overview statistics of all report types",
        responses={
            200: OpenApiResponse(
                response=ReportSummarySerializer,
                description="Reports summary data",
                examples=[
                    OpenApiExample(
                        "Reports Summary Response",
                        value={
                            "dashboard_metrics_count": 30,
                            "sales_reports_count": 15,
                            "inventory_reports_count": 8,
                            "financial_reports_count": 5,
                            "last_generated": "2025-06-01T10:00:00Z"
                        }
                    )
                ]
            )
        },
        tags=['Reports Analytics']
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get reports summary
        """
        summary_data = {
            'dashboard_metrics_count': DashboardMetrics.objects.count(),
            'sales_reports_count': SalesReport.objects.count(),
            'inventory_reports_count': InventoryReport.objects.count(),
            'financial_reports_count': FinancialReport.objects.count(),
            'last_generated': DashboardMetrics.objects.order_by('-created_at').first().created_at if DashboardMetrics.objects.exists() else None
        }
        
        serializer = ReportSummarySerializer(summary_data)
        return Response(serializer.data)

    @extend_schema(
        summary="Get sales analytics data",
        description="Get comprehensive sales analytics with period comparison and growth metrics",
        parameters=[
            OpenApiParameter(
                name='period',
                description='Analytics period',
                required=False,
                type=str,
                enum=['daily', 'weekly', 'monthly', 'yearly'],
                default='monthly'
            )
        ],
        responses={
            200: OpenApiResponse(
                response=SalesAnalyticsSerializer,
                description="Sales analytics data",
                examples=[
                    OpenApiExample(
                        "Sales Analytics Response",
                        value={
                            "period": "monthly",
                            "total_sales": 25000.00,
                            "total_invoices": 85,
                            "average_sale": 294.12,
                            "growth_rate": 15.5
                        }
                    )
                ]
            )
        },
        tags=['Reports Analytics']
    )
    @action(detail=False, methods=['get'])
    def sales_analytics(self, request):
        """
        Get sales analytics data
        """
        period = request.query_params.get('period', 'monthly')  # daily, weekly, monthly, yearly
        
        # Get current period data
        end_date = timezone.now().date()
        
        if period == 'daily':
            start_date = end_date
            previous_start = end_date - timedelta(days=1)
            previous_end = end_date - timedelta(days=1)
        elif period == 'weekly':
            start_date = end_date - timedelta(days=7)
            previous_start = start_date - timedelta(days=7)
            previous_end = start_date - timedelta(days=1)
        elif period == 'yearly':
            start_date = end_date.replace(month=1, day=1)
            previous_start = start_date.replace(year=start_date.year - 1)
            previous_end = end_date.replace(year=end_date.year - 1)
        else:  # monthly
            start_date = end_date.replace(day=1)
            if start_date.month == 1:
                previous_start = start_date.replace(year=start_date.year - 1, month=12, day=1)
                previous_end = start_date.replace(day=1) - timedelta(days=1)
            else:
                previous_start = start_date.replace(month=start_date.month - 1, day=1)
                previous_end = start_date - timedelta(days=1)
        
        # Calculate current period metrics
        current_invoices = Invoice.objects.filter(
            invoice_date__gte=start_date,
            invoice_date__lte=end_date,
            status__in=['PAID', 'PARTIAL']
        )
        
        current_sales = current_invoices.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
        current_count = current_invoices.count()
        current_average = current_sales / current_count if current_count > 0 else Decimal('0')
        
        # Calculate previous period metrics
        previous_invoices = Invoice.objects.filter(
            invoice_date__gte=previous_start,
            invoice_date__lte=previous_end,
            status__in=['PAID', 'PARTIAL']
        )
        
        previous_sales = previous_invoices.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
        
        # Calculate growth rate
        if previous_sales > 0:
            growth_rate = ((current_sales - previous_sales) / previous_sales) * 100
        else:
            growth_rate = Decimal('0') if current_sales == 0 else Decimal('100')
        
        analytics_data = {
            'period': period,
            'total_sales': current_sales,
            'total_invoices': current_count,
            'average_sale': current_average,
            'growth_rate': growth_rate
        }
        
        serializer = SalesAnalyticsSerializer(analytics_data)
        return Response(serializer.data)

    @extend_schema(
        summary="Get product performance analytics",
        description="Get top 10 products performance with sales metrics and profit analysis",
        responses={
            200: OpenApiResponse(
                response=ProductPerformanceSerializer(many=True),
                description="Product performance data",
                examples=[
                    OpenApiExample(
                        "Product Performance Response",
                        value=[
                            {
                                "product_id": 1,
                                "product_name": "Aloe Vera Gel",
                                "product_sku": "ALV001",
                                "total_sold": 150,
                                "total_revenue": 7500.00,
                                "average_price": 50.00,
                                "profit_margin": 25.5
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Reports Analytics']
    )
    @action(detail=False, methods=['get'])
    def product_performance(self, request):
        """
        Get product performance analytics
        """
        # Get top 10 products by sales
        top_products = InvoiceItem.objects.filter(
            invoice__status__in=['PAID', 'PARTIAL']
        ).values(
            'product__id', 'product__name', 'product__sku'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
            average_price=Avg('unit_price')
        ).order_by('-total_revenue')[:10]
        
        # Calculate profit margins
        performance_data = []
        for product_data in top_products:
            try:
                product = Product.objects.get(id=product_data['product__id'])
                if product.cost_price > 0:
                    profit_margin = ((product_data['average_price'] - product.cost_price) / product_data['average_price']) * 100
                else:
                    profit_margin = Decimal('0')
            except Product.DoesNotExist:
                profit_margin = Decimal('0')
            
            performance_data.append({
                'product_id': product_data['product__id'],
                'product_name': product_data['product__name'],
                'product_sku': product_data['product__sku'],
                'total_sold': product_data['total_sold'],
                'total_revenue': product_data['total_revenue'],
                'average_price': product_data['average_price'],
                'profit_margin': profit_margin
            })
        
        serializer = ProductPerformanceSerializer(performance_data, many=True)
        return Response(serializer.data)
