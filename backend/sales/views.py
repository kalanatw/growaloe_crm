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

from .models import Invoice, InvoiceItem, Transaction, Return, InvoiceSettlement, SettlementPayment
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceItemSerializer,
    TransactionSerializer, ReturnSerializer, InvoiceSummarySerializer,
    SalesPerformanceSerializer, InvoiceSettlementSerializer, 
    SettlementPaymentSerializer, MultiPaymentSettlementSerializer,
    BatchInvoiceCreateSerializer, AutoBatchInvoiceCreateSerializer
)
from accounts.permissions import IsOwnerOrDeveloper, IsAuthenticated
from products.models import CentralStock, StockMovement

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
            paid_amount += invoice.get_paid_amount()
            outstanding_amount += invoice.get_outstanding_balance()
        
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
