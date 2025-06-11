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

from .models import Invoice, InvoiceItem, Transaction, Return
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceItemSerializer,
    TransactionSerializer, ReturnSerializer, InvoiceSummarySerializer,
    SalesPerformanceSerializer
)
from accounts.permissions import IsOwnerOrDeveloper, IsAuthenticated
from products.models import SalesmanStock, StockMovement

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
        Generate PDF for an invoice using ReportLab
        """
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor
        import io
        from decimal import Decimal
        from core.models import CompanySettings
        
        invoice = self.get_object()
        
        # Get company settings for customization
        company_settings = CompanySettings.get_settings()
        
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles with company colors
            primary_color = HexColor(company_settings.primary_color)
            secondary_color = HexColor(company_settings.secondary_color)
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=primary_color,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=primary_color,
                spaceAfter=12
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
            
            # Story to hold all content
            story = []
            
            # Company Header
            if company_settings.show_company_details:
                company_name = Paragraph(company_settings.company_name, title_style)
                story.append(company_name)
                
                if company_settings.company_address:
                    address = Paragraph(company_settings.company_address, normal_style)
                    story.append(address)
                
                contact_info = []
                if company_settings.company_phone:
                    contact_info.append(f"Phone: {company_settings.company_phone}")
                if company_settings.company_email:
                    contact_info.append(f"Email: {company_settings.company_email}")
                if company_settings.company_website:
                    contact_info.append(f"Website: {company_settings.company_website}")
                
                if contact_info:
                    contact_para = Paragraph(" | ".join(contact_info), normal_style)
                    story.append(contact_para)
                
                story.append(Spacer(1, 20))
            
            # Invoice Title
            invoice_title = Paragraph(f"INVOICE #{invoice.invoice_number}", heading_style)
            story.append(invoice_title)
            story.append(Spacer(1, 12))
            
            # Invoice Details Table
            invoice_data = [
                ['Invoice Number:', invoice.invoice_number],
                ['Date:', invoice.invoice_date.strftime('%B %d, %Y')],
                ['Due Date:', invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else 'N/A'],
                ['Status:', invoice.status],
                ['Salesman:', f"{invoice.salesman.user.first_name} {invoice.salesman.user.last_name}" if invoice.salesman.user.first_name else invoice.salesman.name],
                ['Shop:', invoice.shop.name if invoice.shop else 'N/A'],
            ]
            
            invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
            invoice_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), primary_color),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(invoice_table)
            story.append(Spacer(1, 20))
            
            # Items Table
            items_title = Paragraph("Invoice Items", heading_style)
            story.append(items_title)
            
            # Prepare items data
            items_data = [['Item', 'Quantity', 'Unit Price', 'Salesman Margin', 'Shop Margin', 'Total']]
            
            for item in invoice.items.all():
                currency = company_settings.currency_symbol
                items_data.append([
                    item.product.name,
                    str(item.quantity),
                    f"{currency}{item.unit_price:.2f}",
                    f"{item.salesman_margin:.1f}%",
                    f"{item.shop_margin:.1f}%",
                    f"{currency}{item.total_price:.2f}"
                ])
            
            items_table = Table(items_data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), secondary_color),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(items_table)
            story.append(Spacer(1, 20))
            
            # Totals Section
            currency = company_settings.currency_symbol
            totals_data = [
                ['Subtotal:', f"{currency}{invoice.subtotal:.2f}"],
                ['Tax:', f"{currency}{invoice.tax_amount:.2f}"],
                ['Total Amount:', f"{currency}{invoice.total_amount:.2f}"],
            ]
            
            totals_table = Table(totals_data, colWidths=[2*inch, 1.5*inch])
            totals_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (0, -1), (-1, -1), primary_color),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            # Right align the totals table
            totals_table.hAlign = 'RIGHT'
            story.append(totals_table)
            story.append(Spacer(1, 30))
            
            # Footer
            if company_settings.invoice_footer_text:
                footer_style = ParagraphStyle(
                    'Footer',
                    parent=styles['Normal'],
                    fontSize=8,
                    textColor=secondary_color,
                    alignment=TA_CENTER
                )
                footer = Paragraph(company_settings.invoice_footer_text, footer_style)
                story.append(footer)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF data
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Create HTTP response
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate PDF: {str(e)}',
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


@extend_schema_view(
    list=extend_schema(
        summary="List returns",
        description="Get a paginated list of product returns based on user permissions",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by return status',
                required=False,
                type=str,
                enum=['PENDING', 'APPROVED', 'REJECTED']
            ),
            OpenApiParameter(
                name='reason',
                description='Filter by return reason',
                required=False,
                type=str
            ),
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
                description='Search by invoice number, product name, or reason',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order results by field (prefix with - for descending)',
                required=False,
                type=str,
                enum=['return_date', '-return_date', 'quantity_returned', '-quantity_returned', 'created_at', '-created_at']
            )
        ],
        responses={200: ReturnSerializer(many=True)},
        tags=['Sales Management']
    ),
    create=extend_schema(
        summary="Create return",
        description="Create a new product return request",
        request=ReturnSerializer,
        responses={
            201: ReturnSerializer,
            400: OpenApiResponse(description="Invalid data provided")
        },
        tags=['Sales Management']
    ),
    retrieve=extend_schema(
        summary="Get return details",
        description="Retrieve detailed information about a specific return",
        responses={
            200: ReturnSerializer,
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Sales Management']
    ),
    update=extend_schema(
        summary="Update return",
        description="Update return information",
        request=ReturnSerializer,
        responses={
            200: ReturnSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Sales Management']
    ),
    partial_update=extend_schema(
        summary="Partially update return",
        description="Partially update return information",
        request=ReturnSerializer,
        responses={
            200: ReturnSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Sales Management']
    ),
    destroy=extend_schema(
        summary="Delete return",
        description="Cancel/delete a return request",
        responses={
            204: OpenApiResponse(description="Return deleted successfully"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Sales Management']
    )
)
class ReturnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product returns with approval workflow and role-based access
    """
    queryset = Return.objects.select_related('original_invoice', 'product', 'created_by').all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['reason', 'original_invoice', 'product', 'approved']
    search_fields = ['original_invoice__invoice_number', 'product__name', 'reason']
    ordering_fields = ['quantity', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'SALESMAN':
            # Salesmen can only see returns for their invoices
            return queryset.filter(invoice__salesman=user.salesman_profile)
        elif user.role == 'SHOP':
            # Shops can see returns for their invoices
            return queryset.filter(invoice__shop=user.shop_profile)
        else:
            # Owners and Developers can see all returns
            return queryset

    def perform_create(self, serializer):
        serializer.save(processed_by=self.request.user)

    @extend_schema(
        summary="Approve return request",
        description="Approve a pending return request and update stock (Owner/Developer only)",
        request=None,
        responses={
            200: OpenApiResponse(
                response=ReturnSerializer,
                description="Return approved successfully",
                examples=[
                    OpenApiExample(
                        "Approve Return Response",
                        value={
                            "id": 1,
                            "status": "APPROVED",
                            "invoice": 1,
                            "product": 1,
                            "quantity_returned": 5,
                            "reason": "Damaged product",
                            "return_date": "2025-06-01",
                            "processed_by": 1
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Only pending returns can be approved"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Return not found")
        },
        tags=['Sales Management']
    )
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        """
        Approve a return request
        """
        return_obj = self.get_object()
        
        if request.user.role not in ['OWNER', 'DEVELOPER']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if return_obj.status != 'PENDING':
            return Response(
                {'error': 'Only pending returns can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return_obj.status = 'APPROVED'
        return_obj.save()
        
        # Update stock - add returned items back to salesman's stock
        try:
            stock = SalesmanStock.objects.get(
                salesman=return_obj.invoice.salesman,
                product=return_obj.product
            )
            stock.available_quantity += return_obj.quantity_returned
            stock.save()
            
            # Create stock movement record
            StockMovement.objects.create(
                product=return_obj.product,
                salesman=return_obj.invoice.salesman,
                movement_type='return',
                quantity=return_obj.quantity_returned,
                notes=f'Return approved: {return_obj.reason}',
                reference_id=str(return_obj.invoice.id),
                created_by=request.user
            )
        except SalesmanStock.DoesNotExist:
            # Create new stock entry if it doesn't exist
            SalesmanStock.objects.create(
                salesman=return_obj.invoice.salesman,
                product=return_obj.product,
                available_quantity=return_obj.quantity_returned,
                allocated_quantity=0
            )
        
        serializer = self.get_serializer(return_obj)
        return Response(serializer.data)

    @extend_schema(
        summary="Get pending returns",
        description="Get all pending return requests based on user permissions",
        responses={
            200: OpenApiResponse(
                response=ReturnSerializer(many=True),
                description="List of pending returns",
                examples=[
                    OpenApiExample(
                        "Pending Returns Response",
                        value=[
                            {
                                "id": 1,
                                "status": "PENDING",
                                "invoice": 1,
                                "product": 1,
                                "quantity_returned": 3,
                                "reason": "Wrong size",
                                "return_date": "2025-06-01",
                                "processed_by": 1
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Sales Management']
    )
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get pending returns
        """
        pending_returns = self.get_queryset().filter(status='PENDING')
        serializer = self.get_serializer(pending_returns, many=True)
        return Response(serializer.data)


@extend_schema_view(
    sales_performance=extend_schema(
        summary="Get sales performance by salesman",
        description="Get comprehensive sales performance metrics for all salesmen (Owner/Developer only)",
        responses={
            200: OpenApiResponse(
                response=SalesPerformanceSerializer(many=True),
                description="Sales performance data",
                examples=[
                    OpenApiExample(
                        "Sales Performance Response",
                        value=[
                            {
                                "salesman_id": 1,
                                "salesman_name": "John Smith",
                                "total_sales": 15000.00,
                                "total_invoices": 45,
                                "average_sale": 333.33,
                                "commission_earned": 750.00
                            }
                        ]
                    )
                ]
            ),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Sales Analytics']
    ),
    monthly_trends=extend_schema(
        summary="Get monthly sales trends",
        description="Get sales trends for the last 12 months based on user permissions",
        responses={
            200: OpenApiResponse(
                description="Monthly sales trend data",
                examples=[
                    OpenApiExample(
                        "Monthly Trends Response",
                        value=[
                            {
                                "month": "2025-05",
                                "month_name": "May 2025",
                                "total_sales": 12000.00,
                                "invoice_count": 35
                            },
                            {
                                "month": "2025-06",
                                "month_name": "June 2025",
                                "total_sales": 15000.00,
                                "invoice_count": 42
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Sales Analytics']
    ),
    top_products=extend_schema(
        summary="Get top selling products",
        description="Get top 10 products by quantity sold based on user permissions",
        responses={
            200: OpenApiResponse(
                description="Top selling products data",
                examples=[
                    OpenApiExample(
                        "Top Products Response",
                        value=[
                            {
                                "product__id": 1,
                                "product__name": "Aloe Vera Gel",
                                "product__sku": "ALV001",
                                "total_quantity": 150,
                                "total_revenue": 7500.00
                            }
                        ]
                    )
                ]
            )
        },
        tags=['Sales Analytics']
    )
)
class SalesAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for sales analytics and reports with role-based data filtering
    """
    permission_classes = [IsAuthenticated]

    def get_base_queryset(self):
        """Get base queryset based on user role"""
        user = self.request.user
        
        if user.role == 'SALESMAN':
            return Invoice.objects.filter(salesman=user.salesman_profile)
        elif user.role == 'SHOP':
            return Invoice.objects.filter(shop=user.shop_profile)
        else:
            return Invoice.objects.all()

    @action(detail=False, methods=['get'])
    def sales_performance(self, request):
        """
        Get sales performance by salesman
        """
        if request.user.role not in ['OWNER', 'DEVELOPER']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from accounts.models import Salesman
        
        salesmen = Salesman.objects.select_related('user').all()
        performance_data = []
        
        for salesman in salesmen:
            invoices = Invoice.objects.filter(salesman=salesman, status__in=['PAID', 'PARTIAL'])
            
            total_sales = invoices.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
            total_invoices = invoices.count()
            average_sale = total_sales / total_invoices if total_invoices > 0 else Decimal('0')
            
            # Calculate commission (assuming 5% commission rate)
            commission_rate = salesman.commission_rate or Decimal('0.05')
            commission_earned = total_sales * commission_rate
            
            performance_data.append({
                'salesman_id': salesman.id,
                'salesman_name': salesman.user.get_full_name(),
                'total_sales': total_sales,
                'total_invoices': total_invoices,
                'average_sale': average_sale,
                'commission_earned': commission_earned
            })
        
        serializer = SalesPerformanceSerializer(performance_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def monthly_trends(self, request):
        """
        Get monthly sales trends
        """
        queryset = self.get_base_queryset()
        
        # Get data for last 12 months
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        monthly_data = []
        current_date = start_date
        
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            month_invoices = queryset.filter(
                invoice_date__gte=month_start,
                invoice_date__lte=month_end,
                status__in=['PAID', 'PARTIAL']
            )
            
            monthly_sales = month_invoices.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
            invoice_count = month_invoices.count()
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'total_sales': monthly_sales,
                'invoice_count': invoice_count
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return Response(monthly_data)

    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """
        Get top selling products
        """
        queryset = self.get_base_queryset()
        
        # Get top products by quantity sold
        top_products = InvoiceItem.objects.filter(
            invoice__in=queryset,
            invoice__status__in=['PAID', 'PARTIAL']
        ).values(
            'product__id', 'product__name', 'product__sku'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total_quantity')[:10]
        
        return Response(list(top_products))
