from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from accounts.permissions import IsOwnerOrDeveloper
from .models import CompanySettings
from .serializers import CompanySettingsSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Get company settings",
        description="Retrieve current company settings for invoice customization",
        responses={200: CompanySettingsSerializer},
        tags=['Company Settings']
    ),
    partial_update=extend_schema(
        summary="Update company settings",
        description="Update company settings (Owner/Developer only)",
        request=CompanySettingsSerializer,
        responses={
            200: CompanySettingsSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Company Settings']
    ),
)
class CompanySettingsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing company settings
    Only allows retrieving and updating (no create/delete since there's only one instance)
    """
    serializer_class = CompanySettingsSerializer
    permission_classes = [IsOwnerOrDeveloper]
    
    def get_object(self):
        """Always return the single company settings instance"""
        return CompanySettings.get_settings()
    
    def list(self, request):
        """Get company settings"""
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    def partial_update(self, request, pk=None):
        """Update company settings"""
        settings = self.get_object()
        serializer = self.get_serializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Reset to default settings",
        description="Reset company settings to default values (Owner/Developer only)",
        request=None,
        responses={
            200: CompanySettingsSerializer,
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Company Settings']
    )
    @action(detail=False, methods=['post'])
    def reset_defaults(self, request):
        """Reset settings to defaults"""
        settings = CompanySettings.get_settings()
        
        # Reset to default values
        settings.company_name = "Grow Aloe Business"
        settings.company_address = "123 Business Street\nCity, State 12345"
        settings.company_phone = "+1 (555) 123-4567"
        settings.company_email = "info@growaloe.com"
        settings.company_website = ""
        settings.company_tax_id = ""
        settings.company_logo = None
        settings.primary_color = "#007bff"
        settings.secondary_color = "#6c757d"
        settings.invoice_prefix = "INV"
        settings.invoice_footer_text = "Thank you for your business!\nThis is a computer-generated invoice and does not require a signature."
        settings.show_logo_on_invoice = True
        settings.show_company_details = True
        settings.default_tax_rate = 0.00
        settings.default_currency = "USD"
        settings.currency_symbol = "$"
        settings.default_payment_terms = ""
        settings.default_due_days = 30
        
        settings.save()
        
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get invoice template preview",
        description="Preview how the current settings will look in invoice template",
        responses={
            200: OpenApiResponse(description="Template preview data"),
            403: OpenApiResponse(description="Permission denied")
        },
        tags=['Company Settings']
    )
    @action(detail=False, methods=['get'])
    def template_preview(self, request):
        """Get template preview data"""
        settings = self.get_object()
        
        preview_data = {
            'company_info': {
                'name': settings.company_name,
                'address': settings.company_address,
                'phone': settings.company_phone,
                'email': settings.company_email,
                'website': settings.company_website,
                'tax_id': settings.company_tax_id,
            },
            'styling': {
                'primary_color': settings.primary_color,
                'secondary_color': settings.secondary_color,
                'show_logo': settings.show_logo_on_invoice,
                'show_company_details': settings.show_company_details,
            },
            'invoice_settings': {
                'prefix': settings.invoice_prefix,
                'footer_text': settings.invoice_footer_text,
                'currency_symbol': settings.currency_symbol,
                'default_tax_rate': settings.default_tax_rate,
            }
        }
        
        return Response(preview_data)
    
    @extend_schema(
        summary="Get public company settings",
        description="Get basic company settings that are accessible to all authenticated users",
        responses={200: CompanySettingsSerializer},
        tags=['Company Settings']
    )
    @action(detail=False, methods=['get'], permission_classes=[])
    def public(self, request):
        """Get public company settings (no authentication required)"""
        settings = self.get_object()
        public_data = {
            'company_name': settings.company_name,
            'company_address': settings.company_address,
            'company_phone': settings.company_phone,
            'company_email': settings.company_email,
            'currency_symbol': settings.currency_symbol,
            'default_currency': settings.default_currency,
            'max_shop_margin_for_salesmen': settings.max_shop_margin_for_salesmen,
        }
        return Response(public_data)
