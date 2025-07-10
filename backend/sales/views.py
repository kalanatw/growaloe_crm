import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, F, Avg
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample

# Setup logger
logger = logging.getLogger(__name__)

from .models import Invoice, InvoiceItem, Transaction, Return, InvoiceSettlement, SettlementPayment, Commission
from products.models import Batch, BatchAssignment
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceItemSerializer,
    TransactionSerializer, ReturnSerializer, InvoiceSummarySerializer,
    SalesPerformanceSerializer, InvoiceSettlementSerializer, 
    SettlementPaymentSerializer, MultiPaymentSettlementSerializer,
    BatchInvoiceCreateSerializer, AutoBatchInvoiceCreateSerializer,
    CommissionSerializer,
    BatchReturnSerializer, BatchSearchSerializer, BatchTraceabilitySerializer, 
    InvoiceSettlementWithReturnsSerializer, BatchReturnCreateSerializer
)
from accounts.permissions import IsOwnerOrDeveloper, IsAuthenticated
from products.models import StockMovement, BatchAssignment, Batch

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="List invoices",
        description="Get a paginated list of invoices based on user permissions",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by invoice status',
                required=False,
                type=str,
                enum=['DRAFT', 'PENDING', 'PAID', 'PARTIAL', 'CANCELLED']
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
                name='invoice_date',
                description='Filter by invoice date (YYYY-MM-DD)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search by invoice number, customer name, or phone',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['invoice_date', '-invoice_date', 'total_amount', '-total_amount', 'created_at', '-created_at']
            )
        ],
        responses={200: InvoiceSerializer(many=True)},
        tags=['Sales Management']
    ),
    create=extend_schema(
        summary="Create invoice",
        description="Create a new invoice with items",
        request=InvoiceCreateSerializer,
        responses={
            201: InvoiceSerializer,
            400: OpenApiResponse(description="Invalid data provided")
        },
        tags=['Sales Management']
    ),
    retrieve=extend_schema(
        summary="Get invoice details",
        description="Retrieve detailed information about a specific invoice",
        responses={
            200: InvoiceSerializer,
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    ),
    update=extend_schema(
        summary="Update invoice",
        description="Update invoice information",
        request=InvoiceSerializer,
        responses={
            200: InvoiceSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    ),
    partial_update=extend_schema(
        summary="Partially update invoice",
        description="Partially update invoice information",
        request=InvoiceSerializer,
        responses={
            200: InvoiceSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    ),
    destroy=extend_schema(
        summary="Delete invoice",
        description="Delete an invoice (soft delete)",
        responses={
            204: OpenApiResponse(description="Invoice deleted successfully"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    )
)
class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales invoices with comprehensive invoice operations
    """
    queryset = Invoice.objects.select_related('salesman__user', 'shop').prefetch_related('items__product').all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'salesman', 'shop', 'invoice_date']
    search_fields = ['invoice_number', 'customer_name', 'customer_phone']
    ordering_fields = ['invoice_date', 'total_amount', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'SALESMAN':
            # Salesmen can only see their own invoices
            return queryset.filter(salesman=user.salesman_profile)
        elif user.role == 'SHOP':
            # Shops can see invoices from their assigned salesmen
            return queryset.filter(shop=user.shop_profile)
        else:
            # Owners and Developers can see all invoices
            return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            # Use simplified auto-batch serializer for salesmen
            if self.request.user.role == 'salesman':
                return AutoBatchInvoiceCreateSerializer
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def perform_create(self, serializer):
        # Set salesman if user is a salesman
        if self.request.user.role == 'SALESMAN':
            serializer.save(salesman=self.request.user.salesman_profile)
        else:
            serializer.save()

    @extend_schema(
        summary="Generate invoice PDF",
        description="Generate a PDF document for the specified invoice",
        responses={
            200: OpenApiResponse(
                description="PDF generation initiated",
                examples=[
                    OpenApiExample(
                        'Success',
                        value={
                            'message': 'PDF generation will be implemented',
                            'invoice_id': 1,
                            'invoice_number': 'INV-2025-1001'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    )
    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """
        Generate Receipt-style PDF for portable bill printer
        """
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch, mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from reportlab.lib import colors
        import io
        from decimal import Decimal
        from core.models import CompanySettings
        
        invoice = self.get_object()
        
        # Get company settings
        company_settings = CompanySettings.get_settings()
        currency = company_settings.currency_symbol
        
        try:
            # Create PDF buffer - smaller page size for receipt printer
            buffer = io.BytesIO()
            
            # Receipt-style page size (80mm width x variable height)
            page_width = 80 * mm
            page_height = 297 * mm  # A4 height for now, will adjust based on content
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=(page_width, page_height),
                rightMargin=5 * mm,
                leftMargin=5 * mm,
                topMargin=5 * mm,
                bottomMargin=5 * mm
            )
            
            # Custom styles for receipt printer
            styles = getSampleStyleSheet()
            
            # Header style - bold and centered
            header_style = ParagraphStyle(
                'ReceiptHeader',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                spaceAfter=2
            )
            
            # Sub-header style
            subheader_style = ParagraphStyle(
                'ReceiptSubHeader',
                parent=styles['Normal'],
                fontSize=8,
                fontName='Helvetica',
                alignment=TA_CENTER,
                spaceAfter=1
            )
            
            # Normal text style
            normal_style = ParagraphStyle(
                'ReceiptNormal',
                parent=styles['Normal'],
                fontSize=8,
                fontName='Helvetica',
                alignment=TA_LEFT,
                spaceAfter=1
            )
            
            # Amount style - right aligned
            amount_style = ParagraphStyle(
                'ReceiptAmount',
                parent=styles['Normal'],
                fontSize=8,
                fontName='Helvetica',
                alignment=TA_RIGHT,
                spaceAfter=1
            )
            
            # Total style - bold
            total_style = ParagraphStyle(
                'ReceiptTotal',
                parent=styles['Normal'],
                fontSize=9,
                fontName='Helvetica-Bold',
                alignment=TA_RIGHT,
                spaceAfter=2
            )
            
            # Story to hold content
            story = []
            
            # Company Header
            story.append(Paragraph(company_settings.company_name, header_style))
            if company_settings.company_address:
                story.append(Paragraph(company_settings.company_address, subheader_style))
            if company_settings.company_phone:
                story.append(Paragraph(f"Tel: {company_settings.company_phone}", subheader_style))
            
            # Separator line
            story.append(Spacer(1, 3))
            story.append(Paragraph("="*30, subheader_style))
            story.append(Spacer(1, 3))
            
            # Invoice details
            story.append(Paragraph(f"INVOICE #{invoice.invoice_number}", header_style))
            story.append(Paragraph(f"Date: {invoice.invoice_date.strftime('%d/%m/%Y %H:%M')}", normal_style))
            story.append(Paragraph(f"Shop: {invoice.shop.name}", normal_style))
            story.append(Paragraph(f"Salesman: {invoice.salesman.user.first_name or invoice.salesman.name}", normal_style))
            
            # Separator
            story.append(Spacer(1, 2))
            story.append(Paragraph("-"*30, subheader_style))
            story.append(Spacer(1, 2))
            
            # Items - compact format
            for item in invoice.items.all():
                # Product name
                story.append(Paragraph(item.product.name, normal_style))
                
                # Quantity x Unit Price = Total
                item_line = f"{item.quantity} x {currency}{item.unit_price:.2f} = {currency}{item.total_price:.2f}"
                story.append(Paragraph(item_line, amount_style))
                
                story.append(Spacer(1, 1))
            
            # Separator before totals
            story.append(Paragraph("-"*30, subheader_style))
            story.append(Spacer(1, 2))
            
            # Calculate totals according to new logic
            # Total Product Price (sum of all item totals)
            product_total = sum(item.total_price for item in invoice.items.all())
            
            # Shop margin calculation - use invoice-level shop margin
            shop_margin_percent = invoice.shop_margin or Decimal('0.00')
            
            shop_margin_amount = product_total * (shop_margin_percent / Decimal('100'))
            after_margin = product_total - shop_margin_amount
            
            # Final total with tax and discount
            final_total = after_margin + invoice.tax_amount - invoice.discount_amount
            
            # Show totals
            story.append(Paragraph(f"Total Products: {currency}{product_total:.2f}", amount_style))
            
            if shop_margin_percent > 0:
                story.append(Paragraph(f"Shop Margin ({shop_margin_percent}%): -{currency}{shop_margin_amount:.2f}", amount_style))
                story.append(Paragraph(f"After Margin: {currency}{after_margin:.2f}", amount_style))
            
            # Only show tax if it's not zero
            if invoice.tax_amount > 0:
                story.append(Paragraph(f"Tax: {currency}{invoice.tax_amount:.2f}", amount_style))
            
            # Only show discount if it's not zero
            if invoice.discount_amount > 0:
                story.append(Paragraph(f"Discount: -{currency}{invoice.discount_amount:.2f}", amount_style))
            
            # Final separator
            story.append(Paragraph("="*30, subheader_style))
            
            # Final total
            story.append(Paragraph(f"TOTAL: {currency}{final_total:.2f}", total_style))
            
            # Footer
            story.append(Spacer(1, 5))
            story.append(Paragraph("Thank you for your business!", subheader_style))
            story.append(Paragraph(f"Status: {invoice.status}", subheader_style))
            
            if invoice.due_date:
                story.append(Paragraph(f"Due: {invoice.due_date.strftime('%d/%m/%Y')}", subheader_style))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF data
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Create HTTP response
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{invoice.invoice_number}.pdf"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate receipt PDF: {str(e)}',
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Update invoice status",
        description="Update the status of an invoice (Owner/Developer only)",
        request={
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                    'enum': ['DRAFT', 'PENDING', 'PAID', 'PARTIAL', 'CANCELLED'],
                    'description': 'New status for the invoice'
                }
            },
            'required': ['status']
        },
        responses={
            200: InvoiceSerializer,
            400: OpenApiResponse(description="Invalid status provided"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    )
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update invoice status
        """
        invoice = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Invoice.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only certain users can change status
        if request.user.role not in ['OWNER', 'DEVELOPER']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice.status = new_status
        invoice.save()
        
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get invoice summary statistics
        """
        queryset = self.get_queryset()
        
        total_invoices = queryset.count()
        total_amount = queryset.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
        
        # Calculate paid and outstanding amounts
        paid_amount = Decimal('0')
        outstanding_amount = Decimal('0')
        
        for invoice in queryset:
            paid_amount += invoice.paid_amount
            outstanding_amount += invoice.balance_due
        
        overdue_invoices = queryset.filter(
            due_date__lt=timezone.now().date(),
            status__in=['SENT', 'PARTIAL']
        ).count()
        
        draft_invoices = queryset.filter(status='DRAFT').count()
        
        summary_data = {
            'total_invoices': total_invoices,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'outstanding_amount': outstanding_amount,
            'overdue_invoices': overdue_invoices,
            'draft_invoices': draft_invoices
        }
        
        serializer = InvoiceSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent invoices (last 20)
        """
        recent_invoices = self.get_queryset()[:20]
        serializer = self.get_serializer(recent_invoices, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get overdue invoices
        """
        overdue_invoices = self.get_queryset().filter(
            due_date__lt=timezone.now().date(),
            status__in=['SENT', 'PARTIAL']
        )
        serializer = self.get_serializer(overdue_invoices, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List invoice items",
        description="Get a paginated list of invoice line items based on user permissions",
        parameters=[
            OpenApiParameter(
                name='invoice',
                description='Filter by invoice ID',
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
                description='Search by product name or SKU',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['quantity', '-quantity', 'unit_price', '-unit_price']
            )
        ],
        responses={200: InvoiceItemSerializer(many=True)},
        tags=['Sales Management']
    ),
    create=extend_schema(
        summary="Create invoice item",
        description="Add a new item to an invoice",
        request=InvoiceItemSerializer,
        responses={
            201: InvoiceItemSerializer,
            400: OpenApiResponse(description="Invalid data provided")
        },
        tags=['Sales Management']
    ),
    retrieve=extend_schema(
        summary="Get invoice item details",
        description="Retrieve detailed information about a specific invoice item",
        responses={
            200: InvoiceItemSerializer,
            404: OpenApiResponse(description="Invoice item not found")
        },
        tags=['Sales Management']
    ),
    update=extend_schema(
        summary="Update invoice item",
        description="Update invoice item information",
        request=InvoiceItemSerializer,
        responses={
            200: InvoiceItemSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Invoice item not found")
        },
        tags=['Sales Management']
    ),
    partial_update=extend_schema(
        summary="Partially update invoice item",
        description="Partially update invoice item information",
        request=InvoiceItemSerializer,
        responses={
            200: InvoiceItemSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Invoice item not found")
        },
        tags=['Sales Management']
    ),
    destroy=extend_schema(
        summary="Delete invoice item",
        description="Remove an item from an invoice",
        responses={
            204: OpenApiResponse(description="Invoice item deleted successfully"),
            404: OpenApiResponse(description="Invoice item not found")
        },
        tags=['Sales Management']
    )
)
class InvoiceItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoice line items with role-based filtering
    """
    queryset = InvoiceItem.objects.select_related('invoice', 'product').all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['invoice', 'product']
    search_fields = ['product__name', 'product__sku']
    ordering_fields = ['quantity', 'unit_price']
    ordering = ['id']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'SALESMAN':
            # Salesmen can only see items from their invoices
            return queryset.filter(invoice__salesman=user.salesman_profile)
        elif user.role == 'SHOP':
            # Shops can see items from their invoices
            return queryset.filter(invoice__shop=user.shop_profile)
        else:
            # Owners and Developers can see all items
            return queryset


@extend_schema_view(
    list=extend_schema(
        summary="List transactions",
        description="Get a paginated list of payment transactions based on user permissions",
        parameters=[
            OpenApiParameter(
                name='transaction_type',
                description='Filter by transaction type',
                required=False,
                type=str,
                enum=['SALE', 'RETURN', 'ADJUSTMENT']
            ),
            OpenApiParameter(
                name='payment_method',
                description='Filter by payment method',
                required=False,
                type=str,
                enum=['CASH', 'CHEQUE', 'BILL_TO_BILL']
            ),
            OpenApiParameter(
                name='status',
                description='Filter by transaction status',
                required=False,
                type=str,
                enum=['PENDING', 'COMPLETED', 'FAILED', 'CANCELLED']
            ),
            OpenApiParameter(
                name='invoice',
                description='Filter by invoice ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='search',
                description='Search by reference number or invoice number',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['transaction_date', '-transaction_date', 'amount', '-amount', 'created_at', '-created_at']
            )
        ],
        responses={200: TransactionSerializer(many=True)},
        tags=['Sales Management']
    ),
    create=extend_schema(
        summary="Create transaction",
        description="Record a new payment transaction",
        request=TransactionSerializer,
        responses={
            201: TransactionSerializer,
            400: OpenApiResponse(description="Invalid data provided")
        },
        tags=['Sales Management']
    ),
    retrieve=extend_schema(
        summary="Get transaction details",
        description="Retrieve detailed information about a specific transaction",
        responses={
            200: TransactionSerializer,
            404: OpenApiResponse(description="Transaction not found")
        },
        tags=['Sales Management']
    ),
    update=extend_schema(
        summary="Update transaction",
        description="Update transaction information",
        request=TransactionSerializer,
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Transaction not found")
        },
        tags=['Sales Management']
    ),
    partial_update=extend_schema(
        summary="Partially update transaction",
        description="Partially update transaction information",
        request=TransactionSerializer,
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Transaction not found")
        },
        tags=['Sales Management']
    ),
    destroy=extend_schema(
        summary="Delete transaction",
        description="Cancel/delete a transaction",
        responses={
            204: OpenApiResponse(description="Transaction deleted successfully"),
            404: OpenApiResponse(description="Transaction not found")
        },
        tags=['Sales Management']
    )
)
class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payment transactions with comprehensive filtering and summary capabilities
    """
    queryset = Transaction.objects.select_related('invoice', 'created_by').all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['payment_method', 'invoice']
    search_fields = ['reference_number', 'invoice__invoice_number']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'SALESMAN':
            # Salesmen can only see transactions for their invoices
            return queryset.filter(invoice__salesman=user.salesman_profile)
        elif user.role == 'SHOP':
            # Shops can see transactions for their invoices
            return queryset.filter(invoice__shop=user.shop_profile)
        else:
            # Owners and Developers can see all transactions
            return queryset

    def perform_create(self, serializer):
        serializer.save(processed_by=self.request.user)

    @extend_schema(
        summary="Get transaction summary",
        description="Get comprehensive transaction summary by type and payment method",
        responses={
            200: OpenApiResponse(
                description="Transaction summary statistics",
                examples=[
                    OpenApiExample(
                        "Transaction Summary Response",
                        value={
                            "sale_total": 15000.00,
                            "return_total": 500.00,
                            "adjustment_total": 200.00,
                            "payment_methods": {
                                "cash": 12000.00,
                                "cheque": 3000.00,
                                "bill_to_bill": 700.00
                            },
                            "total_transactions": 45
                        }
                    )
                ]
            )
        },
        tags=['Sales Management']
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get transaction summary by type and method
        """
        queryset = self.get_queryset()
        
        summary = {}
        
        # Summary by transaction type
        for trans_type in Transaction.TRANSACTION_TYPES:
            type_code = trans_type[0]
            amount = queryset.filter(
                transaction_type=type_code,
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            summary[f'{type_code.lower()}_total'] = amount
        
        # Summary by payment method
        payment_methods = {}
        for method in Transaction.PAYMENT_METHODS:
            method_code = method[0]
            amount = queryset.filter(
                payment_method=method_code,
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            payment_methods[method_code.lower()] = amount
        
        summary['payment_methods'] = payment_methods
        summary['total_transactions'] = queryset.count()
        
        return Response(summary)

    @extend_schema(
        summary="Get outstanding invoices by shop",
        description="Get list of unpaid or partially paid invoices for a specific shop",
        parameters=[
            OpenApiParameter(
                name='shop_id',
                description='Shop ID to get invoices for',
                required=True,
                type=int
            )
        ],
        responses={
            200: OpenApiResponse(
                description="List of outstanding invoices",
                examples=[
                    OpenApiExample(
                        "Outstanding Invoices Response",
                        value={
                            "invoices": [
                                {
                                    "id": 1,
                                    "invoice_number": "INV-2025-0001",
                                    "invoice_date": "2025-06-17T10:00:00Z",
                                    "net_total": 1500.00,
                                    "paid_amount": 500.00,
                                    "balance_due": 1000.00,
                                    "status": "partial"
                                }
                            ],
                            "total_outstanding": 1000.00
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="Shop not found")
        },
        tags=['Sales Management']
    )
    @action(detail=False, methods=['get'])
    def outstanding_invoices(self, request):
        """
        Get outstanding invoices for a specific shop
        """
        shop_id = request.query_params.get('shop_id')
        if not shop_id:
            return Response(
                {'error': 'shop_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from accounts.models import Shop
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return Response(
                {'error': 'Shop not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get invoices that have outstanding balance
        outstanding_invoices = Invoice.objects.filter(
            shop=shop,
            status__in=['pending', 'partial', 'overdue']
        ).order_by('-invoice_date')
        
        invoices_data = []
        total_outstanding = Decimal('0.00')
        
        for invoice in outstanding_invoices:
            if invoice.balance_due > 0:
                invoices_data.append({
                    'id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'invoice_date': invoice.invoice_date,
                    'net_total': invoice.net_total,
                    'paid_amount': invoice.paid_amount,
                    'balance_due': invoice.balance_due,
                    'status': invoice.status,
                    'due_date': invoice.due_date,
                })
                total_outstanding += invoice.balance_due
        
        return Response({
            'shop': {
                'id': shop.id,
                'name': shop.name,
                'contact_person': shop.contact_person
            },
            'invoices': invoices_data,
            'total_outstanding': total_outstanding
        })
    
    @extend_schema(
        summary="Get total debits summary",
        description="Get total outstanding amount across all invoices",
        responses={
            200: OpenApiResponse(
                description="Total debits summary",
                examples=[
                    OpenApiExample(
                        "Debits Summary Response",
                        value={
                            "total_debits": 25000.00,
                            "invoices_count": 15,
                            "by_status": {
                                "pending": 15000.00,
                                "partial": 8000.00,
                                "overdue": 2000.00
                            },
                            "by_shop": [
                                {
                                    "shop_id": 1,
                                    "shop_name": "Shop ABC",
                                    "outstanding_amount": 5000.00,
                                    "invoices_count": 3
                                }
                            ]
                        }
                    )
                ]
            )
        },
        tags=['Sales Management']
    )
    @action(detail=False, methods=['get'])
    def total_debits(self, request):
        """
        Get total debits (outstanding invoice amounts) summary
        """
        base_queryset = self.get_base_invoice_queryset()
        
        # Get all unpaid invoices
        outstanding_invoices = base_queryset.filter(
            status__in=['pending', 'partial', 'overdue']
        ).select_related('shop')
        
        total_debits = outstanding_invoices.aggregate(
            total=Sum('balance_due')
        )['total'] or Decimal('0.00')
        
        invoices_count = outstanding_invoices.count()
        
        # Summary by status
        by_status = {}
        for status_choice in ['pending', 'partial', 'overdue']:
            amount = outstanding_invoices.filter(status=status_choice).aggregate(
                total=Sum('balance_due')
            )['total'] or Decimal('0.00')
            by_status[status_choice] = amount
        
        # Summary by shop
        from django.db.models import Count
        by_shop = outstanding_invoices.values(
            'shop__id', 'shop__name'
        ).annotate(
            outstanding_amount=Sum('balance_due'),
            invoices_count=Count('id')
        ).order_by('-outstanding_amount')
        
        return Response({
            'total_debits': total_debits,
            'invoices_count': invoices_count,
            'by_status': by_status,
            'by_shop': list(by_shop)
        })
    
    @extend_schema(
        summary="Settle invoice",
        description="Process payment for a specific invoice (full or partial settlement)",
        request=OpenApiExample(
            "Settlement Request",
            value={
                "invoice_id": 1,
                "amount": 1000.00,
                "payment_method": "cash",
                "reference_number": "REF123",
                "notes": "Full payment received"
            }
        ),
        responses={
            201: OpenApiResponse(
                description="Payment processed successfully",
                examples=[
                    OpenApiExample(
                        "Settlement Response",
                        value={
                            "transaction_id": 15,
                            "invoice": {
                                "id": 1,
                                "invoice_number": "INV-2025-0001",
                                "previous_balance": 1000.00,
                                "payment_amount": 1000.00,
                                "new_balance": 0.00,
                                "status": "paid"
                            },
                            "message": "Invoice settled successfully"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid payment amount or invoice"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    )
    @action(detail=False, methods=['post'])
    def settle_invoice(self, request):
        """
        Settle an invoice with payment (full or partial)
        """
        invoice_id = request.data.get('invoice_id')
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'cash')
        reference_number = request.data.get('reference_number', '')
        notes = request.data.get('notes', '')
        
        if not invoice_id or not amount:
            return Response(
                {'error': 'invoice_id and amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response(
                    {'error': 'Amount must be greater than zero'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if payment amount doesn't exceed outstanding balance
        if amount > invoice.balance_due:
            return Response(
                {'error': f'Payment amount ({amount}) exceeds outstanding balance ({invoice.balance_due})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store previous balance for response
        previous_balance = invoice.balance_due
        
        # Create transaction
        transaction = Transaction.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            created_by=request.user
        )
        
        # Transaction save method will update invoice automatically
        invoice.refresh_from_db()
        
        return Response({
            'transaction_id': transaction.id,
            'invoice': {
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'previous_balance': previous_balance,
                'payment_amount': amount,
                'new_balance': invoice.balance_due,
                'status': invoice.status
            },
            'message': 'Invoice settled successfully'
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Settle invoice with multiple payment methods",
        description="Process multiple payments for a single invoice settlement",
        request=MultiPaymentSettlementSerializer,
        responses={
            201: OpenApiResponse(
                description="Multi-payment settlement processed successfully",
                examples=[
                    OpenApiExample(
                        "Multi-Payment Settlement Response",
                        value={
                            "settlement_id": 15,
                            "invoice": {
                                "id": 1,
                                "invoice_number": "INV-2025-0001",
                                "previous_balance": 1000.00,
                                "total_payment_amount": 1000.00,
                                "new_balance": 0.00,
                                "status": "paid"
                            },
                            "payments": [
                                {
                                    "payment_method": "cash",
                                    "amount": 600.00,
                                    "reference_number": ""
                                },
                                {
                                    "payment_method": "cheque", 
                                    "amount": 300.00,
                                    "reference_number": "CHQ123"
                                },
                                {
                                    "payment_method": "return",
                                    "amount": 100.00,
                                    "reference_number": "RET456"
                                }
                            ],
                            "message": "Invoice settled successfully with multiple payments"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid payment data"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Sales Management']
    )
    @action(detail=False, methods=['post'])
    def settle_invoice_multi_payment(self, request):
        """
        Settle an invoice with multiple payment methods
        """
        serializer = MultiPaymentSettlementSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        invoice_id = validated_data['invoice_id']
        payments_data = validated_data['payments']
        notes = validated_data.get('notes', '')
        
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            previous_balance = invoice.balance_due
            
            # Calculate total payment amount
            total_payment_amount = sum(Decimal(str(p['amount'])) for p in payments_data)
            
            # Create settlement
            settlement = InvoiceSettlement.objects.create(
                invoice=invoice,
                total_amount=total_payment_amount,
                notes=notes,
                created_by=request.user
            )
            
            # Create individual payments
            created_payments = []
            for payment_data in payments_data:
                payment = SettlementPayment.objects.create(
                    settlement=settlement,
                    payment_method=payment_data['payment_method'],
                    amount=Decimal(str(payment_data['amount'])),
                    reference_number=payment_data.get('reference_number', ''),
                    bank_name=payment_data.get('bank_name', ''),
                    cheque_date=payment_data.get('cheque_date'),
                    notes=payment_data.get('notes', '')
                )
                created_payments.append({
                    'payment_method': payment.payment_method,
                    'amount': payment.amount,
                    'reference_number': payment.reference_number
                })
            
            # Settlement save method will update invoice automatically
            settlement.save()
            invoice.refresh_from_db()
            
            return Response({
                'settlement_id': settlement.id,
                'invoice': {
                    'id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'previous_balance': previous_balance,
                    'total_payment_amount': total_payment_amount,
                    'new_balance': invoice.balance_due,
                    'status': invoice.status
                },
                'payments': created_payments,
                'message': 'Invoice settled successfully with multiple payments'
            }, status=status.HTTP_201_CREATED)
            
        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to process settlement: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_base_invoice_queryset(self):
        """Get base invoice queryset based on user permissions"""
        user = self.request.user
        
        if user.role == 'SALESMAN':
            return Invoice.objects.filter(salesman=user.salesman_profile)
        elif user.role == 'SHOP':
            return Invoice.objects.filter(shop=user.shop_profile)
        else:
            return Invoice.objects.all()
    

@extend_schema_view(
    list=extend_schema(
        summary="List salesman commissions",
        description="Get a paginated list of salesman commissions",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by commission status',
                required=False,
                type=str,
                enum=['PENDING', 'PAID']
            ),
            OpenApiParameter(
                name='salesman',
                description='Filter by salesman ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='invoice',
                description='Filter by invoice ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='search',
                description='Search by invoice number or salesman name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['created_at', '-created_at', 'commission_amount', '-commission_amount', 'paid_date', '-paid_date']
            )
        ],
        responses={200: CommissionSerializer(many=True)},
        tags=['Sales Management']
    ),
    create=extend_schema(
        summary="Create commission",
        description="Create a new commission record",
        request=CommissionSerializer,
        responses={
            201: CommissionSerializer,
            400: OpenApiResponse(description="Invalid data provided")
        },
        tags=['Sales Management']
    ),
    retrieve=extend_schema(
        summary="Get commission details",
        description="Retrieve detailed information about a specific commission",
        responses={
            200: CommissionSerializer,
            404: OpenApiResponse(description="Commission not found")
        },
        tags=['Sales Management']
    ),
    update=extend_schema(
        summary="Update commission",
        description="Update commission information",
        request=CommissionSerializer,
        responses={
            200: CommissionSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Commission not found")
        },
        tags=['Sales Management']
    ),
    partial_update=extend_schema(
        summary="Partially update commission",
        description="Partially update commission information",
        request=CommissionSerializer,
        responses={
            200: CommissionSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Commission not found")
        },
        tags=['Sales Management']
    ),
    destroy=extend_schema(
        summary="Delete commission",
        description="Delete a commission record",
        responses={
            204: OpenApiResponse(description="Commission deleted successfully"),
            404: OpenApiResponse(description="Commission not found")
        },
        tags=['Sales Management']
    )
)
class CommissionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing salesman commissions"""
    queryset = Commission.objects.all()
    serializer_class = CommissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'salesman', 'invoice']
    search_fields = ['invoice__invoice_number', 'salesman__name']
    ordering_fields = ['created_at', 'commission_amount', 'paid_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter commissions based on user role"""
        user = self.request.user
        
        if user.role == 'SALESMAN':
            # Salesmen can only see their own commissions
            try:
                salesman = user.salesman_profile
                return Commission.objects.filter(salesman=salesman)
            except:
                return Commission.objects.none()
        else:
            # Owners can see all commissions
            return Commission.objects.all()
    
    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        """Get commission dashboard data"""
        try:
            user = request.user
            queryset = self.get_queryset()
            
            # Calculate totals
            pending_total = queryset.filter(status='pending').aggregate(
                total=Sum('commission_amount')
            )['total'] or Decimal('0.00')
            
            paid_total = queryset.filter(status='paid').aggregate(
                total=Sum('commission_amount')
            )['total'] or Decimal('0.00')
            
            # Get per-salesman breakdown (only for owners)
            salesman_data = []
            if user.role != 'SALESMAN':
                from accounts.models import Salesman
                salesmen = Salesman.objects.all()
                
                for salesman in salesmen:
                    salesman_commissions = Commission.objects.filter(salesman=salesman)
                    salesman_pending = salesman_commissions.filter(status='pending').aggregate(
                        total=Sum('commission_amount')
                    )['total'] or Decimal('0.00')
                    
                    salesman_data.append({
                        'salesman_id': salesman.id,
                        'salesman_name': salesman.name,
                        'pending_commission': salesman_pending,
                        'total_invoices': salesman_commissions.count()
                    })
            
            # Get recent commissions
            recent_commissions = queryset.order_by('-created_at')[:10]
            
            dashboard_data = {
                'total_pending_commissions': pending_total,
                'total_paid_commissions': paid_total,
                'salesman_commissions': salesman_data,
                'recent_commissions': CommissionSerializer(recent_commissions, many=True).data
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get commission dashboard data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark a commission as paid"""
        try:
            commission = self.get_object()
            payment_reference = request.data.get('payment_reference', '')
            
            commission.status = 'paid'
            commission.paid_date = timezone.now()
            commission.paid_by = request.user
            commission.payment_reference = payment_reference
            commission.save()
            
            return Response({
                'message': 'Commission marked as paid successfully',
                'commission': CommissionSerializer(commission).data
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to mark commission as paid: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='bulk_mark_paid')
    def bulk_mark_paid(self, request):
        """Bulk mark commissions as paid"""
        commission_ids = request.data.get('commission_ids', [])
        payment_reference = request.data.get('payment_reference', '')
        user = request.user

        if not commission_ids or not isinstance(commission_ids, list):
            return Response({'error': 'commission_ids (list) is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Only allow owners/admins
        if hasattr(user, 'role') and user.role == 'SALESMAN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        updated_commissions = []
        now = timezone.now()
        for commission in Commission.objects.filter(id__in=commission_ids, status='pending'):
            commission.status = 'paid'
            commission.paid_date = now
            commission.paid_by = user
            commission.payment_reference = payment_reference
            commission.save()
            updated_commissions.append(commission)

        return Response({
            'message': f'{len(updated_commissions)} commissions marked as paid',
            'commissions': CommissionSerializer(updated_commissions, many=True).data
        })


class EnhancedReturnViewSet(viewsets.ModelViewSet):
    """Enhanced ViewSet for managing product returns with batch support"""
    queryset = Return.objects.all()
    serializer_class = BatchReturnSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['approved', 'reason', 'batch', 'product']
    search_fields = ['return_number', 'batch__batch_number', 'product__name']
    ordering_fields = ['created_at', 'return_amount']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def batch_return_summary(self, request):
        """Get return summary by batch"""
        try:
            from products.models import Batch
            
            # Get batches with return counts
            batches_with_returns = Batch.objects.annotate(
                total_returns=Sum('returns__quantity', filter=Q(returns__approved=True)),
                return_count=Count('returns', filter=Q(returns__approved=True))
            ).filter(
                Q(total_returns__gt=0) | Q(return_count__gt=0)
            ).select_related('product').order_by('-total_returns')
            
            batch_data = []
            for batch in batches_with_returns:
                batch_data.append({
                    'batch_id': batch.id,
                    'batch_number': batch.batch_number,
                    'product_name': batch.product.name,
                    'original_quantity': batch.initial_quantity,
                    'current_quantity': batch.current_quantity,
                    'total_returns': batch.total_returns or 0,
                    'return_transactions': batch.return_count or 0,
                    'expiry_date': batch.expiry_date
                })
            
            return Response(batch_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get batch return summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get all returns for a specific batch"""
        try:
            batch_id = request.query_params.get('batch_id')
            if not batch_id:
                return Response(
                    {'error': 'batch_id parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get all returns for the specific batch
            returns = Return.objects.filter(batch_id=batch_id).select_related(
                'original_invoice', 'product', 'batch', 'created_by', 'approved_by'
            ).order_by('-created_at')
            
            serializer = BatchReturnSerializer(returns, many=True)
            
            # Calculate summary statistics
            total_returned = returns.filter(approved=True).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            total_return_amount = returns.filter(approved=True).aggregate(
                total=Sum('return_amount')
            )['total'] or Decimal('0')
            
            # Group by return reasons
            return_reasons = returns.filter(approved=True).values('reason').annotate(
                count=Count('id'),
                total_quantity=Sum('quantity')
            ).order_by('-count')
            
            return Response({
                'returns': serializer.data,
                'summary': {
                    'total_returns': returns.count(),
                    'approved_returns': returns.filter(approved=True).count(),
                    'total_returned_quantity': total_returned,
                    'total_return_amount': total_return_amount,
                    'return_reasons': list(return_reasons)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get returns for batch: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get comprehensive return analytics"""
        try:
            from products.models import Batch
            from django.utils import timezone
            from datetime import timedelta
            
            # Get date range parameters
            days = int(request.query_params.get('days', 30))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Overall return statistics
            returns_in_period = Return.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
                approved=True
            )
            
            total_returns = returns_in_period.count()
            total_return_amount = returns_in_period.aggregate(
                total=Sum('return_amount')
            )['total'] or Decimal('0')
            
            # Calculate return rate
            total_sales_in_period = InvoiceItem.objects.filter(
                invoice__invoice_date__date__gte=start_date,
                invoice__invoice_date__date__lte=end_date
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            return_rate = (total_returns / total_sales_in_period * 100) if total_sales_in_period > 0 else 0
            
            # Top return reasons
            top_return_reasons = returns_in_period.values('reason').annotate(
                count=Count('id'),
                percentage=Count('id') * 100.0 / total_returns if total_returns > 0 else 0
            ).order_by('-count')[:5]
            
            # Problematic batches (high return rates)
            problematic_batches = Batch.objects.filter(
                returns__created_at__date__gte=start_date,
                returns__approved=True
            ).annotate(
                total_returned=Sum('returns__quantity'),
                return_count=Count('returns')
            ).filter(
                total_returned__gt=0
            ).order_by('-total_returned')[:10]
            
            batch_analytics = []
            for batch in problematic_batches:
                batch_analytics.append({
                    'batch_id': batch.id,
                    'batch_number': batch.batch_number,
                    'product_name': batch.product.name,
                    'total_produced': batch.initial_quantity,
                    'total_sold': batch.initial_quantity - batch.current_quantity,
                    'total_returned': batch.total_returned or 0,
                    'return_rate': batch.return_rate or 0,
                    'quality_score': batch.quality_score() if hasattr(batch, 'quality_score') else 0,
                    'is_problematic': batch.is_problematic() if hasattr(batch, 'is_problematic') else False,
                    'defect_count': getattr(batch, 'defect_count', 0),
                    'manufacturing_date': batch.manufacturing_date,
                    'expiry_date': batch.expiry_date,
                })
            
            # Return trends (daily counts)
            return_trends = []
            current_date = start_date
            while current_date <= end_date:
                daily_returns = returns_in_period.filter(
                    created_at__date=current_date
                ).count()
                return_trends.append({
                    'date': current_date,
                    'count': daily_returns
                })
                current_date += timedelta(days=1)
            
            # Quality alerts
            quality_alerts = []
            high_return_batches = Batch.objects.filter(
                return_rate__gte=10  # 10% or higher return rate
            ).select_related('product')[:5]
            
            for batch in high_return_batches:
                quality_alerts.append({
                    'type': 'high_return_rate',
                    'batch_number': batch.batch_number,
                    'product_name': batch.product.name,
                    'return_rate': batch.return_rate,
                    'message': f'Batch {batch.batch_number} has a high return rate of {batch.return_rate}%'
                })
            
            analytics_data = {
                'period': f'{days} days',
                'total_returns': total_returns,
                'total_return_amount': total_return_amount,
                'return_rate_percentage': return_rate,
                'top_return_reasons': list(top_return_reasons),
                'problematic_batches': batch_analytics,
                'return_trends': return_trends,
                'quality_alerts': quality_alerts
            }
            
            return Response(analytics_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get return analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnhancedSettlementViewSet(viewsets.ModelViewSet):
    """Enhanced ViewSet for invoice settlements with bill-to-bill support"""
    queryset = InvoiceSettlement.objects.all()
    serializer_class = InvoiceSettlementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['invoice__shop', 'invoice__salesman']
    search_fields = ['invoice__invoice_number', 'invoice__shop__name']
    ordering_fields = ['settlement_date', 'total_amount']
    ordering = ['-settlement_date']
    
    @action(detail=False, methods=['get'])
    def unsettled_invoices(self, request):
        """Get unsettled invoices for a specific shop"""
        try:
            shop_id = request.query_params.get('shop_id')
            
            if not shop_id:
                return Response(
                    {'error': 'shop_id parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get unsettled invoices for the shop
            unsettled_invoices = Invoice.objects.filter(
                shop_id=shop_id,
                balance_due__gt=0
            ).order_by('-invoice_date')
            
            # Calculate total unsettled amount
            total_unsettled = sum(invoice.balance_due for invoice in unsettled_invoices)
            
            serialized_invoices = InvoiceSerializer(unsettled_invoices, many=True).data
            
            return Response({
                'invoices': serialized_invoices,
                'total_unsettled_amount': total_unsettled,
                'invoice_count': len(serialized_invoices)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get unsettled invoices: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        summary="List returns",
        description="Get a list of all returns with filtering and search",
        responses={
            200: OpenApiResponse(description="List of returns"),
        },
        tags=['Returns Management']
    ),
    create=extend_schema(
        summary="Create return",
        description="Create a new product return",
        responses={
            201: OpenApiResponse(description="Return created successfully"),
            400: OpenApiResponse(description="Invalid data")
        },
        tags=['Returns Management']
    ),
    retrieve=extend_schema(
        summary="Get return details",
        description="Get detailed information about a specific return",
        responses={
            200: OpenApiResponse(description="Return details"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Returns Management']
    ),
    update=extend_schema(
        summary="Update return",
        description="Update return information",
        responses={
            200: OpenApiResponse(description="Return updated successfully"),
            400: OpenApiResponse(description="Invalid data"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Returns Management']
    ),
    partial_update=extend_schema(
        summary="Partially update return",
        description="Partially update return information",
        responses={
            200: OpenApiResponse(description="Return updated successfully"),
            400: OpenApiResponse(description="Invalid data"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Returns Management']
    ),
    destroy=extend_schema(
        summary="Delete return",
        description="Delete a return",
        responses={
            204: OpenApiResponse(description="Return deleted successfully"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Returns Management']
    )
)
class BatchReturnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product returns with batch-centric functionality
    """
    queryset = Return.objects.select_related(
        'original_invoice', 'original_invoice__shop', 'original_invoice__salesman', 
        'original_invoice__salesman__user', 'product', 'batch', 'created_by', 'approved_by'
    ).all()
    serializer_class = BatchReturnSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['approved', 'reason', 'batch', 'product', 'original_invoice__shop', 'original_invoice__salesman']
    search_fields = ['return_number', 'product__name', 'batch__batch_number', 'original_invoice__invoice_number']
    ordering_fields = ['created_at', 'return_amount', 'quantity']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'salesman':
            return queryset.filter(original_invoice__salesman=user.salesman_profile)
        elif user.role == 'shop':
            return queryset.filter(original_invoice__shop=user.shop_profile)
        else:
            return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        summary="Search batches",
        description="Search for batches by batch number or product for return processing",
        parameters=[
            OpenApiParameter(name='batch_number', type=str, description='Batch number to search for'),
            OpenApiParameter(name='product_id', type=int, description='Product ID to search batches for'),
            OpenApiParameter(name='salesman_id', type=int, description='Salesman ID to filter batches'),
        ],
        responses={
            200: OpenApiResponse(description="Batch search results"),
            400: OpenApiResponse(description="Invalid search parameters")
        },
        tags=['Returns Management']
    )
    @action(detail=False, methods=['get'])
    def search_batches(self, request):
        """
        Search for batches by batch number or product for return processing
        """
        try:
            batch_number = request.query_params.get('batch_number')
            product_id = request.query_params.get('product_id')
            salesman_id = request.query_params.get('salesman_id')
            
            if not batch_number and not product_id:
                return Response(
                    {'error': 'Either batch_number or product_id must be provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Base query
            batches_query = Batch.objects.select_related('product').filter(is_active=True)
            
            # Filter by batch number
            if batch_number:
                batches_query = batches_query.filter(batch_number__icontains=batch_number)
            
            # Filter by product
            if product_id:
                batches_query = batches_query.filter(product_id=product_id)
            
            # Filter by salesman assignments if specified
            if salesman_id:
                batches_query = batches_query.filter(
                    assignments__salesman_id=salesman_id,
                    assignments__status__in=['delivered', 'partial']
                ).distinct()
            
            # Get batch data with sales information
            batch_results = []
            for batch in batches_query[:20]:  # Limit to 20 results
                # Get invoices that used this batch
                invoices_with_batch = InvoiceItem.objects.filter(
                    batch=batch
                ).select_related('invoice', 'invoice__shop', 'invoice__salesman__user')
                
                # Calculate total sold and returned
                total_sold = invoices_with_batch.aggregate(
                    total=Sum('quantity')
                )['total'] or 0
                
                total_returned = Return.objects.filter(
                    batch=batch,
                    approved=True
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # Get shops that purchased from this batch
                shops_data = []
                for invoice_item in invoices_with_batch:
                    shop_info = {
                        'shop_id': invoice_item.invoice.shop.id,
                        'shop_name': invoice_item.invoice.shop.name,
                        'invoice_id': invoice_item.invoice.id,
                        'invoice_number': invoice_item.invoice.invoice_number,
                        'quantity_sold': invoice_item.quantity,
                        'salesman_name': invoice_item.invoice.salesman.user.get_full_name(),
                        'sale_date': invoice_item.invoice.invoice_date,
                    }
                    shops_data.append(shop_info)
                
                batch_results.append({
                    'batch_id': batch.id,
                    'batch_number': batch.batch_number,
                    'product_id': batch.product.id,
                    'product_name': batch.product.name,
                    'product_sku': batch.product.sku,
                    'manufacturing_date': batch.manufacturing_date,
                    'expiry_date': batch.expiry_date,
                    'initial_quantity': batch.initial_quantity,
                    'current_quantity': batch.current_quantity,
                    'total_sold': total_sold,
                    'total_returned': total_returned,
                    'return_rate': batch.return_rate,
                    'quality_status': batch.quality_status,
                    'is_expired': batch.is_expired,
                    'shops_sold_to': shops_data,
                })
            
            return Response({
                'batches': batch_results,
                'total_found': len(batch_results)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to search batches: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get batch traceability",
        description="Get detailed traceability information for a specific batch including all sales and returns",
        parameters=[
            OpenApiParameter(name='batch_id', type=int, description='Batch ID to get traceability for'),
        ],
        responses={
            200: OpenApiResponse(description="Batch traceability data"),
            404: OpenApiResponse(description="Batch not found")
        },
        tags=['Returns Management']
    )
    @action(detail=False, methods=['get'])
    def batch_traceability(self, request):
        """
        Get detailed traceability information for a specific batch
        """
        try:
            batch_id = request.query_params.get('batch_id')
            
            if not batch_id:
                return Response(
                    {'error': 'batch_id parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                batch = Batch.objects.select_related('product').get(id=batch_id)
            except Batch.DoesNotExist:
                return Response(
                    {'error': 'Batch not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all invoice items for this batch
            invoice_items = InvoiceItem.objects.filter(
                batch=batch
            ).select_related('invoice', 'invoice__shop', 'invoice__salesman__user')
            
            # Get all returns for this batch
            returns = Return.objects.filter(
                batch=batch,
                approved=True
            ).select_related('original_invoice', 'original_invoice__shop')
            
            # Calculate aggregated data
            total_sold = invoice_items.aggregate(total=Sum('quantity'))['total'] or 0
            total_returned = returns.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
            
            # Get shops sold to
            shops_sold_to = []
            for item in invoice_items:
                shops_sold_to.append({
                    'shop_id': item.invoice.shop.id,
                    'shop_name': item.invoice.shop.name,
                    'invoice_id': item.invoice.id,
                    'invoice_number': item.invoice.invoice_number,
                    'quantity_sold': item.quantity,
                    'unit_price': float(item.unit_price),
                    'salesman_name': item.invoice.salesman.user.get_full_name(),
                    'sale_date': item.invoice.invoice_date,
                })
            
            # Get shops returned from
            shops_returned_from = []
            for return_item in returns:
                shops_returned_from.append({
                    'shop_id': return_item.original_invoice.shop.id,
                    'shop_name': return_item.original_invoice.shop.name,
                    'return_id': return_item.id,
                    'return_number': return_item.return_number,
                    'quantity_returned': return_item.quantity,
                    'return_amount': float(return_item.return_amount),
                    'reason': return_item.reason,
                    'return_date': return_item.created_at,
                })
            
            # Get salesmen assigned to this batch
            salesmen_assigned = []
            assignments = BatchAssignment.objects.filter(
                batch=batch
            ).select_related('salesman', 'salesman__user')
            
            for assignment in assignments:
                salesmen_assigned.append({
                    'salesman_id': assignment.salesman.id,
                    'salesman_name': assignment.salesman.user.get_full_name(),
                    'assigned_quantity': assignment.quantity,
                    'delivered_quantity': assignment.delivered_quantity,
                    'returned_quantity': assignment.returned_quantity,
                    'outstanding_quantity': assignment.outstanding_quantity,
                    'assignment_date': assignment.created_at,
                    'status': assignment.status,
                })
            
            traceability_data = {
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'product_name': batch.product.name,
                'product_sku': batch.product.sku,
                'manufacturing_date': batch.manufacturing_date,
                'expiry_date': batch.expiry_date,
                'initial_quantity': batch.initial_quantity,
                'current_quantity': batch.current_quantity,
                'total_sold': total_sold,
                'total_returned': total_returned,
                'shops_sold_to': shops_sold_to,
                'shops_returned_from': shops_returned_from,
                'salesmen_assigned': salesmen_assigned,
                'quality_status': batch.quality_status,
                'return_rate': batch.return_rate,
                'is_expired': batch.is_expired,
            }
            
            return Response(traceability_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get batch traceability: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Process invoice settlement with returns",
        description="Process invoice settlement allowing returns to be recorded simultaneously",
        request=InvoiceSettlementWithReturnsSerializer,
        responses={
            200: OpenApiResponse(description="Settlement processed successfully"),
            400: OpenApiResponse(description="Invalid settlement data"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Returns Management']
    )
    @action(detail=False, methods=['post'])
    def process_settlement_with_returns(self, request):
        """
        Process invoice settlement with returns support
        """
        try:
            serializer = InvoiceSettlementWithReturnsSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            invoice_id = validated_data['invoice_id']
            returns_data = validated_data.get('returns', [])
            payments_data = validated_data.get('payments', [])
            settlement_notes = validated_data.get('settlement_notes', '')
            
            # Get the invoice
            try:
                invoice = Invoice.objects.get(id=invoice_id)
            except Invoice.DoesNotExist:
                return Response(
                    {'error': 'Invoice not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            with transaction.atomic():
                # Process returns first
                created_returns = []
                total_return_amount = Decimal('0')
                
                for return_data in returns_data:
                    return_serializer = BatchReturnCreateSerializer(data=return_data, context={'request': request})
                    if return_serializer.is_valid():
                        return_obj = return_serializer.save()
                        created_returns.append(return_obj)
                        total_return_amount += return_obj.return_amount
                        
                        # Update batch quantities (return stock)
                        batch = return_obj.batch
                        batch.current_quantity += return_obj.quantity
                        batch.save()
                        
                    else:
                        return Response(
                            {'error': 'Invalid return data', 'details': return_serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Calculate total payments
                total_payment_amount = sum(Decimal(str(p['amount'])) for p in payments_data)
                
                # Create settlement record
                settlement = InvoiceSettlement.objects.create(
                    invoice=invoice,
                    total_amount=total_payment_amount,
                    notes=settlement_notes,
                    created_by=request.user
                )
                
                # Process payments
                for payment_data in payments_data:
                    SettlementPayment.objects.create(
                        settlement=settlement,
                        payment_method=payment_data['payment_method'],
                        amount=Decimal(str(payment_data['amount'])),
                        reference_number=payment_data.get('reference_number', ''),
                        bank_name=payment_data.get('bank_name', ''),
                        cheque_date=payment_data.get('cheque_date'),
                        notes=payment_data.get('notes', '')
                    )
                
                # Create return payment if there were returns
                if total_return_amount > 0:
                    SettlementPayment.objects.create(
                        settlement=settlement,
                        payment_method='return',
                        amount=total_return_amount,  # Positive amount for return credit
                        notes=f'Returns: {len(created_returns)} items totaling {total_return_amount}'
                    )
                
                # Update invoice amounts
                invoice.paid_amount += total_payment_amount
                invoice.balance_due -= (total_payment_amount + total_return_amount)
                
                # Update invoice status
                if invoice.balance_due <= 0:
                    invoice.status = 'paid'
                elif invoice.paid_amount > 0:
                    invoice.status = 'partial'
                    
                invoice.save()
                
                return Response({
                    'success': True,
                    'settlement_id': settlement.id,
                    'returns_created': len(created_returns),
                    'total_return_amount': float(total_return_amount),
                    'total_payment_amount': float(total_payment_amount),
                    'settlement_amount': float(total_payment_amount + total_return_amount),
                    'remaining_balance': float(invoice.balance_due),
                    'message': f'Settlement processed successfully with {len(created_returns)} returns'
                })
                
        except Exception as e:
            return Response(
                {'error': f'Failed to process settlement: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Approve return",
        description="Approve a pending return",
        responses={
            200: OpenApiResponse(description="Return approved successfully"),
            400: OpenApiResponse(description="Return cannot be approved"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Returns Management']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrDeveloper])
    def approve(self, request, pk=None):
        """
        Approve a pending return
        """
        try:
            return_obj = self.get_object()
            
            if return_obj.approved:
                return Response(
                    {'error': 'Return is already approved'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Approve the return
            return_obj.approved = True
            return_obj.approved_by = request.user
            return_obj.save()
            
            # Update batch stock through the model's _update_batch_stock method
            return_obj._update_batch_stock()
            
            return Response({
                'success': True,
                'message': 'Return approved successfully',
                'return_id': return_obj.id,
                'return_number': return_obj.return_number
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to approve return: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get returns analytics",
        description="Get comprehensive analytics about returns including trends and batch analysis",
        parameters=[
            OpenApiParameter(name='days', type=int, description='Number of days to analyze (default: 30)'),
            OpenApiParameter(name='shop_id', type=int, description='Filter by shop ID'),
            OpenApiParameter(name='salesman_id', type=int, description='Filter by salesman ID'),
        ],
        responses={
            200: OpenApiResponse(description="Returns analytics data"),
        },
        tags=['Returns Management']
    )
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get comprehensive analytics about returns
        """
        try:
            days = int(request.query_params.get('days', 30))
            shop_id = request.query_params.get('shop_id')
            salesman_id = request.query_params.get('salesman_id')
            
            # Calculate date range
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Base query
            returns_query = Return.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
                approved=True
            )
            
            # Apply filters
            if shop_id:
                returns_query = returns_query.filter(original_invoice__shop_id=shop_id)
            if salesman_id:
                returns_query = returns_query.filter(original_invoice__salesman_id=salesman_id)
            
            # Basic stats
            total_returns = returns_query.count()
            total_return_amount = returns_query.aggregate(
                total=Sum('return_amount')
            )['total'] or Decimal('0')
            
            # Returns by reason
            returns_by_reason = returns_query.values('reason').annotate(
                count=Count('id'),
                amount=Sum('return_amount')
            ).order_by('-count')
            
            # Daily return trends
            daily_trends = []
            current_date = start_date
            while current_date <= end_date:
                daily_count = returns_query.filter(created_at__date=current_date).count()
                daily_amount = returns_query.filter(created_at__date=current_date).aggregate(
                    total=Sum('return_amount')
                )['total'] or Decimal('0')
                
                daily_trends.append({
                    'date': current_date,
                    'count': daily_count,
                    'amount': float(daily_amount)
                })
                current_date += timedelta(days=1)
            
            # Top returned products
            top_products = returns_query.values(
                'product__name', 'product__sku'
            ).annotate(
                count=Count('id'),
                amount=Sum('return_amount')
            ).order_by('-count')[:10]
            
            # Batch analysis
            batch_analysis = returns_query.values(
                'batch__batch_number', 'batch__product__name'
            ).annotate(
                count=Count('id'),
                amount=Sum('return_amount')
            ).order_by('-count')[:10]
            
            analytics_data = {
                'period': f'{days} days',
                'total_returns': total_returns,
                'total_return_amount': float(total_return_amount),
                'returns_by_reason': list(returns_by_reason),
                'daily_trends': daily_trends,
                'top_returned_products': list(top_products),
                'batch_analysis': list(batch_analysis),
            }
            
            return Response(analytics_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get returns analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def calculate_return_amount(self, request):
        """Calculate return amount considering shop margins and original sale price"""
        try:
            batch_id = request.data.get('batch_id')
            quantity = request.data.get('quantity')
            original_invoice_id = request.data.get('original_invoice_id')
            
            if not all([batch_id, quantity, original_invoice_id]):

                return Response(
                    {'error': 'batch_id, quantity, and original_invoice_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from products.models import Batch
            
            # Get the batch
            try:
                batch = Batch.objects.select_related('product').get(id=batch_id)
            except Batch.DoesNotExist:
                return Response(
                    {'error': 'Batch not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get the original invoice
            try:
                invoice = Invoice.objects.select_related('shop').get(id=original_invoice_id)
            except Invoice.DoesNotExist:
                return Response(
                    {'error': 'Invoice not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Find the invoice item for this batch to get the original sale price
            invoice_item = InvoiceItem.objects.filter(
                invoice=invoice,
                batch=batch
            ).first()
            
            if not invoice_item:
                # If no specific batch item found, use product-level pricing
                invoice_item = InvoiceItem.objects.filter(
                    invoice=invoice,
                    product=batch.product
                ).first()
            
            if invoice_item:
                # Use the actual sale price from the invoice
                original_unit_price = invoice_item.unit_price
                shop_margin_percentage = invoice_item.shop_margin or 0
                shop_margin_amount = original_unit_price * (shop_margin_percentage / 100)
            else:
                # Fallback to product base price if no invoice item found
                original_unit_price = batch.product.base_price
                shop_margin_percentage = 0
                shop_margin_amount = 0
            
            # Calculate return amount
            # Return amount = original unit price * quantity
            # Note: We return the full amount to customer, shop margin is handled separately
            return_amount = original_unit_price * quantity
            
            # Check for quality issues that might affect return amount
            quality_deduction = 0
            if batch.quality_status == 'DEFECTIVE':
                quality_deduction = return_amount * 0.1  # 10% deduction for defective items
            elif batch.quality_status == 'WARNING':
                quality_deduction = return_amount * 0.05  # 5% deduction for warning items
            
            final_return_amount = return_amount - quality_deduction
            
            return Response({
                'return_amount': round(final_return_amount, 2),
                'original_unit_price': original_unit_price,
                'shop_margin_percentage': shop_margin_percentage,
                'shop_margin_amount': round(shop_margin_amount, 2),
                'quality_deduction': round(quality_deduction, 2),
                'batch_quality_status': batch.quality_status,
                'calculation_details': {
                    'base_calculation': f"{original_unit_price} × {quantity} = {return_amount}",
                    'quality_deduction': f"{quality_deduction} (due to {batch.quality_status})",
                    'final_amount': final_return_amount
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to calculate return amount: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get invoice batches",
        description="Get all batches that were sold in a specific invoice for easy return processing",
        parameters=[
            OpenApiParameter(name='invoice_id', type=int, description='Invoice ID to get batches for', required=True),
        ],
        responses={
            200: OpenApiResponse(description="Invoice batches data"),
            400: OpenApiResponse(description="Invalid invoice ID"),
            404: OpenApiResponse(description="Invoice not found")
        },
        tags=['Returns Management']
    )
    @action(detail=False, methods=['get'])
    def invoice_batches(self, request):
        """Get all batches that were sold in a specific invoice"""
        try:
            invoice_id = request.query_params.get('invoice_id')
            
            if not invoice_id:
                return Response(
                    {'error': 'Invoice ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify invoice exists
            try:
                invoice = Invoice.objects.get(id=invoice_id)
            except Invoice.DoesNotExist:
                return Response(
                    {'error': 'Invoice not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all batches from invoice items
            invoice_items = InvoiceItem.objects.filter(
                invoice_id=invoice_id
            ).select_related('product', 'batch')
            
            batches_data = []
            for item in invoice_items:
                if not item.batch:
                    continue  # Skip items without batch information
                
                # Calculate already returned quantity for this batch in this invoice
                returned_quantity = Return.objects.filter(
                    original_invoice_id=invoice_id,
                    batch=item.batch,
                    approved=True
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                max_returnable = max(0, item.quantity - returned_quantity)
                
                batch_data = {
                    'id': item.batch.id,
                    'batch_number': item.batch.batch_number,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'product_sku': item.product.sku,
                    'sold_quantity': item.quantity,
                    'already_returned': returned_quantity,
                    'max_returnable_quantity': max_returnable,
                    'unit_price': float(item.unit_price),
                    'total_amount': float(item.total_price),
                    'manufacturing_date': item.batch.manufacturing_date,
                    'expiry_date': item.batch.expiry_date,
                    'quality_status': item.batch.quality_status,
                    'can_return': max_returnable > 0,
                }
                batches_data.append(batch_data)
            
            return Response({
                'invoice_id': int(invoice_id),
                'invoice_number': invoice.invoice_number,
                'shop_name': invoice.shop.name,
                'batches': batches_data,
                'total_batches': len(batches_data)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get invoice batches: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Quick return calculation",
        description="Quick calculation for return amount based on invoice item pricing",
        request=OpenApiExample(
            'Quick Return Calculation',
            value={
                'invoice_id': 123,
                'batch_id': 456,
                'return_quantity': 5
            }
        ),
        responses={
            200: OpenApiResponse(description="Return calculation result"),
            400: OpenApiResponse(description="Invalid request data"),
            404: OpenApiResponse(description="Invoice item not found")
        },
        tags=['Returns Management']
    )
    @action(detail=False, methods=['post'])
    def quick_return_calculation(self, request):
        """Quick calculation for return amount based on invoice item"""
        try:
            invoice_id = request.data.get('invoice_id')
            batch_id = request.data.get('batch_id')
            return_quantity = request.data.get('return_quantity')
            
            if not all([invoice_id, batch_id, return_quantity]):
                return Response(
                    {'error': 'invoice_id, batch_id, and return_quantity are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                return_quantity = int(return_quantity)
                if return_quantity <= 0:
                    raise ValueError("Return quantity must be positive")
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid return quantity'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find the specific invoice item
            try:
                invoice_item = InvoiceItem.objects.select_related('batch').get(
                    invoice_id=invoice_id,
                    batch_id=batch_id
                )
            except InvoiceItem.DoesNotExist:
                return Response(
                    {'error': 'Invoice item not found for this batch'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if return quantity is valid
            already_returned = Return.objects.filter(
                original_invoice_id=invoice_id,
                batch_id=batch_id,
                approved=True
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            max_returnable = invoice_item.quantity - already_returned
            
            if return_quantity > max_returnable:
                return Response({
                    'error': f'Cannot return {return_quantity} items. Maximum returnable: {max_returnable}',
                    'max_returnable_quantity': max_returnable,
                    'already_returned': already_returned,
                    'originally_sold': invoice_item.quantity,
                    'calculation_valid': False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate shop margin and cost price
            # Get shop margin from invoice item or fall back to shop/customer default
            shop_margin_percentage = invoice_item.shop_margin
            
            # If shop margin is zero/None, try to get it from the invoice's shop or customer
            if not shop_margin_percentage or shop_margin_percentage == 0:
                try:
                    if invoice_item.invoice.shop:
                        shop_margin_percentage = invoice_item.invoice.shop.shop_margin
                    elif invoice_item.invoice.customer:
                        shop_margin_percentage = invoice_item.invoice.customer.shop_margin
                except Exception:
                    # Fall back to default margin if all else fails
                    shop_margin_percentage = Decimal('15.00')  # Default margin
                
                # Log the margin source for debugging
                logger.info(
                    f"Shop margin not found in invoice item. Using margin from "
                    f"{'shop' if invoice_item.invoice.shop else 'customer' if invoice_item.invoice.customer else 'default'}: "
                    f"{shop_margin_percentage}%"
                )
            
            # Convert to decimal if it's not already
            if not isinstance(shop_margin_percentage, Decimal):
                shop_margin_percentage = Decimal(str(shop_margin_percentage))
            
            # Calculate cost price using shop margin - correct formula
            # Using multiplication: original_price × (1 - margin_percentage/100)
            original_cost_price = invoice_item.unit_price * (Decimal('1') - (shop_margin_percentage / Decimal('100'))) if shop_margin_percentage > 0 else invoice_item.unit_price
            shop_margin_amount = invoice_item.unit_price - original_cost_price
            
            # Calculate return amount using cost price (without shop margin)
            unit_return_amount = original_cost_price
            base_return_amount = unit_return_amount * return_quantity
            
            # Apply quality deductions if applicable
            quality_deduction = 0
            if invoice_item.batch.quality_status == 'DEFECTIVE':
                quality_deduction = base_return_amount * Decimal('0.10')  # 10% deduction
            elif invoice_item.batch.quality_status == 'WARNING':
                quality_deduction = base_return_amount * Decimal('0.05')  # 5% deduction
            
            final_return_amount = base_return_amount - quality_deduction
            
            # Log the final calculation details
            logger.info(f"Return calculation for invoice {invoice_id}, batch {batch_id}:")
            logger.info(f"- Original unit price: {invoice_item.unit_price}")
            logger.info(f"- Shop margin: {shop_margin_percentage}%")
            logger.info(f"- Original cost price calculation: {invoice_item.unit_price} × (1 - {shop_margin_percentage/100}) = {original_cost_price}")
            logger.info(f"- Return quantity: {return_quantity}")
            logger.info(f"- Base return amount: {base_return_amount}")
            logger.info(f"- Quality deduction: {quality_deduction}")
            logger.info(f"- Total return amount: {final_return_amount}")
            logger.info(f"- Margin source: {'invoice_item' if invoice_item.shop_margin > 0 else ('shop' if getattr(invoice_item.invoice, 'shop', None) else 'customer' if getattr(invoice_item.invoice, 'customer', None) else 'default')}")
            
            return Response({
                'unit_return_amount': float(unit_return_amount),
                'base_return_amount': float(base_return_amount),
                'quality_deduction': float(quality_deduction),
                'total_return_amount': float(final_return_amount),
                'original_unit_price': float(invoice_item.unit_price),
                'original_cost_price': float(original_cost_price),
                'shop_margin_percentage': float(shop_margin_percentage),
                'shop_margin_amount': float(shop_margin_amount),
                'max_returnable_quantity': max_returnable,
                'already_returned': already_returned,
                'calculation_valid': True,
                'batch_quality_status': invoice_item.batch.quality_status,
                'return_quantity': return_quantity,  # Include the return quantity
                'margin_source': 'invoice_item' if invoice_item.shop_margin > 0 else 
                                ('shop' if getattr(invoice_item.invoice, 'shop', None) else 
                                 'customer' if getattr(invoice_item.invoice, 'customer', None) else 'default'),
                'calculation_details': {
                    'base_calculation': f"{float(unit_return_amount)} × {return_quantity} = {float(base_return_amount)}",
                    'quality_impact': f"Quality deduction: -{float(quality_deduction)} ({invoice_item.batch.quality_status})",
                    'final_amount': float(final_return_amount),
                    'margin_calculation': f"Original price {float(invoice_item.unit_price)} × (1 - {float(shop_margin_percentage)}%) = {float(original_cost_price)} per unit"
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to calculate return amount: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
