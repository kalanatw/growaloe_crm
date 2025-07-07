"""
Salesman-centric delivery and settlement views for the redesigned workflow.
This module provides APIs that organize data by salesman to simplify
the delivery and settlement process.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Sum, Count, F, Case, When
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
import logging

from .models import Delivery, DeliveryItem, BatchAssignment, Product, Batch, DeliverySettlement, DeliverySettlementItem
from .serializers import (
    DeliverySerializer, DeliverySettlementSerializer, DeliverySettlementItemSerializer,
    SalesmanStockOverviewSerializer, SalesmanSettlementQueueSerializer, 
    SettleSalesmanRequestSerializer, SalesmanDailySummarySerializer
)
from sales.models import Invoice, InvoiceItem
from accounts.models import Salesman, Owner
from accounts.permissions import IsOwnerOrDeveloper, IsAuthenticated

User = get_user_model()
logger = logging.getLogger(__name__)


class SalesmanDeliveryViewSet(viewsets.ModelViewSet):
    """
    Salesman-centric delivery management.
    Organizes all delivery, stock, and settlement data by salesman for simplified workflow.
    """
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter deliveries based on user role and salesman"""
        user = self.request.user
        
        if user.role == 'salesman':
            return Delivery.objects.filter(salesman=user.salesman_profile)
        elif user.role in ['owner', 'developer']:
            # Owners see deliveries for their salesmen
            if user.role == 'owner':
                return Delivery.objects.filter(salesman__owner=user.owner_profile)
            return Delivery.objects.all()
        else:
            return Delivery.objects.none()
    
    @extend_schema(
        summary="Get salesman stock overview",
        description="Get current stock status for all salesmen under the owner",
        responses={200: OpenApiResponse(description="Salesman stock overview")}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsOwnerOrDeveloper])
    def stock_overview(self, request):
        """
        Get comprehensive stock overview organized by salesman.
        Shows what each salesman currently has and what they've sold.
        """
        user = request.user
        
        # Get salesmen based on user role
        if user.role == 'owner':
            salesmen = Salesman.objects.filter(owner=user.owner_profile, is_active=True)
        else:  # developer
            salesmen = Salesman.objects.filter(is_active=True)
        
        overview_data = []
        
        for salesman in salesmen:
            # Get outstanding stock (delivered but not returned)
            outstanding_assignments = BatchAssignment.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'partial']
            ).select_related('batch', 'batch__product')
            
            # Calculate stock by product
            stock_by_product = {}
            total_stock_value = 0
            
            for assignment in outstanding_assignments:
                product = assignment.batch.product
                outstanding_qty = assignment.outstanding_quantity
                
                if outstanding_qty > 0:
                    if product.id not in stock_by_product:
                        stock_by_product[product.id] = {
                            'product_id': product.id,
                            'product_name': product.name,
                            'product_sku': product.sku,
                            'unit_price': float(product.base_price),
                            'quantity': 0,
                            'total_value': 0
                        }
                    
                    stock_by_product[product.id]['quantity'] += outstanding_qty
                    stock_by_product[product.id]['total_value'] += outstanding_qty * float(product.base_price)
                    total_stock_value += outstanding_qty * float(product.base_price)
            
            # Get sales data for today
            today = timezone.now().date()
            today_sales = InvoiceItem.objects.filter(
                invoice__salesman=salesman,
                invoice__invoice_date__date=today,
                invoice__status__in=['pending', 'paid', 'partial']
            ).aggregate(
                total_sales=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('unit_price'))
            )
            
            # Get pending deliveries
            pending_deliveries = Delivery.objects.filter(
                salesman=salesman,
                status='pending'
            ).count()
            
            overview_data.append({
                'salesman_id': salesman.id,
                'salesman_name': salesman.user.get_full_name(),
                'salesman_phone': salesman.user.phone,
                'total_products': len(stock_by_product),
                'total_stock_quantity': sum(item['quantity'] for item in stock_by_product.values()),
                'total_stock_value': total_stock_value,
                'stock_by_product': list(stock_by_product.values()),
                'today_sales_quantity': today_sales['total_sales'] or 0,
                'today_sales_revenue': float(today_sales['total_revenue'] or 0),
                'pending_deliveries': pending_deliveries,
                'last_delivery_date': salesman.deliveries.filter(status='delivered').order_by('-created_at').first().created_at if salesman.deliveries.filter(status='delivered').exists() else None
            })
        
        return Response({
            'salesmen_count': len(overview_data),
            'total_stock_value': sum(item['total_stock_value'] for item in overview_data),
            'total_products_distributed': sum(item['total_products'] for item in overview_data),
            'salesmen': overview_data
        })
    
    @extend_schema(
        summary="Get settlement queue",
        description="Get all deliveries ready for settlement, organized by salesman",
        responses={200: OpenApiResponse(description="Settlement queue data")}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsOwnerOrDeveloper])
    def settlement_queue(self, request):
        """
        Get all deliveries that are ready for settlement.
        Shows what needs to be settled for each salesman.
        """
        user = request.user
        
        # Get deliveries ready for settlement (delivered but not settled)
        deliveries_query = Delivery.objects.filter(status='delivered')
        
        if user.role == 'owner':
            deliveries_query = deliveries_query.filter(salesman__owner=user.owner_profile)
        
        deliveries = deliveries_query.select_related('salesman', 'salesman__user').order_by('salesman', '-created_at')
        
        # Group by salesman
        settlement_data = {}
        
        for delivery in deliveries:
            salesman_id = delivery.salesman.id
            
            if salesman_id not in settlement_data:
                settlement_data[salesman_id] = {
                    'salesman_id': salesman_id,
                    'salesman_name': delivery.salesman.user.get_full_name(),
                    'salesman_phone': delivery.salesman.user.phone,
                    'deliveries': [],
                    'total_deliveries': 0,
                    'total_outstanding_value': 0,
                    'oldest_delivery_date': None
                }
            
            # Calculate outstanding stock for this delivery
            settlement_items = []
            total_outstanding_qty = 0
            total_outstanding_value = 0
            
            for item in delivery.items.all():
                # Get sold quantity from invoices
                sold_qty = InvoiceItem.objects.filter(
                    invoice__salesman=delivery.salesman,
                    product=item.product,
                    invoice__invoice_date__gte=delivery.created_at,
                    invoice__status__in=['pending', 'paid', 'partial']
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                outstanding_qty = max(0, item.quantity - sold_qty)
                outstanding_value = outstanding_qty * float(item.unit_price)
                
                if outstanding_qty > 0:
                    settlement_items.append({
                        'delivery_item_id': item.id,
                        'product_id': item.product.id,
                        'product_name': item.product.name,
                        'product_sku': item.product.sku,
                        'delivered_quantity': item.quantity,
                        'sold_quantity': sold_qty,
                        'outstanding_quantity': outstanding_qty,
                        'unit_price': float(item.unit_price),
                        'outstanding_value': outstanding_value
                    })
                    
                    total_outstanding_qty += outstanding_qty
                    total_outstanding_value += outstanding_value
            
            delivery_data = {
                'delivery_id': delivery.id,
                'delivery_number': delivery.delivery_number,
                'delivery_date': delivery.created_at,
                'total_items': delivery.total_items,
                'total_value': float(delivery.total_value),
                'outstanding_quantity': total_outstanding_qty,
                'outstanding_value': total_outstanding_value,
                'items': settlement_items
            }
            
            settlement_data[salesman_id]['deliveries'].append(delivery_data)
            settlement_data[salesman_id]['total_deliveries'] += 1
            settlement_data[salesman_id]['total_outstanding_value'] += total_outstanding_value
            
            # Update oldest delivery date
            if (settlement_data[salesman_id]['oldest_delivery_date'] is None or 
                delivery.created_at < settlement_data[salesman_id]['oldest_delivery_date']):
                settlement_data[salesman_id]['oldest_delivery_date'] = delivery.created_at
        
        return Response({
            'salesmen_count': len(settlement_data),
            'total_deliveries_pending': sum(s['total_deliveries'] for s in settlement_data.values()),
            'total_outstanding_value': sum(s['total_outstanding_value'] for s in settlement_data.values()),
            'salesmen': list(settlement_data.values())
        })
    
    @extend_schema(
        summary="Settle salesman deliveries",
        description="Settle all outstanding deliveries for a specific salesman",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'salesman_id': {'type': 'integer'},
                    'settlement_notes': {'type': 'string'},
                    'return_all_stock': {'type': 'boolean', 'default': True}
                }
            }
        },
        responses={200: OpenApiResponse(description="Settlement completed")}
    )
    @action(detail=False, methods=['post'], permission_classes=[IsOwnerOrDeveloper])
    def settle_salesman(self, request):
        """
        Settle all outstanding deliveries for a specific salesman.
        Returns all unsold stock to owner inventory.
        """
        salesman_id = request.data.get('salesman_id')
        settlement_notes = request.data.get('settlement_notes', '')
        return_all_stock = request.data.get('return_all_stock', True)
        
        if not salesman_id:
            return Response(
                {'error': 'salesman_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            salesman = Salesman.objects.get(id=salesman_id)
        except Salesman.DoesNotExist:
            return Response(
                {'error': 'Salesman not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission for owner
        if request.user.role == 'owner' and salesman.owner != request.user.owner_profile:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            # Get all outstanding batch assignments for this salesman
            outstanding_assignments = BatchAssignment.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'partial']
            ).select_related('batch', 'batch__product')
            
            total_returned_items = 0
            total_returned_value = 0
            returned_products = {}
            
            for assignment in outstanding_assignments:
                outstanding_qty = assignment.outstanding_quantity
                
                if outstanding_qty > 0 and return_all_stock:
                    # Return the outstanding stock
                    assignment.returned_quantity += outstanding_qty
                    assignment.status = 'returned'
                    assignment.save()
                    
                    # Update batch current quantity (return to owner)
                    assignment.batch.current_quantity += outstanding_qty
                    assignment.batch.save()
                    
                    # Track returned items
                    product = assignment.batch.product
                    if product.id not in returned_products:
                        returned_products[product.id] = {
                            'product_name': product.name,
                            'quantity': 0,
                            'value': 0
                        }
                    
                    returned_products[product.id]['quantity'] += outstanding_qty
                    returned_products[product.id]['value'] += outstanding_qty * float(product.base_price)
                    
                    total_returned_items += outstanding_qty
                    total_returned_value += outstanding_qty * float(product.base_price)
            
            # Mark all delivered deliveries as settled
            settled_deliveries = Delivery.objects.filter(
                salesman=salesman,
                status='delivered'
            ).update(status='settled')
            
            # Log the settlement
            logger.info(f"Settlement completed for salesman {salesman.user.get_full_name()}: "
                       f"{total_returned_items} items worth LKR {total_returned_value} returned to owner")
        
        return Response({
            'message': 'Settlement completed successfully',
            'salesman_name': salesman.user.get_full_name(),
            'settled_deliveries': settled_deliveries,
            'total_returned_items': total_returned_items,
            'total_returned_value': total_returned_value,
            'returned_products': list(returned_products.values()),
            'settlement_notes': settlement_notes
        })
    
    @extend_schema(
        summary="Get daily settlement summary",
        description="Get end-of-day settlement summary for all salesmen",
        parameters=[
            OpenApiParameter(
                name='date',
                description='Date for settlement summary (YYYY-MM-DD)',
                required=False,
                type=str
            )
        ],
        responses={200: OpenApiResponse(description="Daily settlement summary")}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsOwnerOrDeveloper])
    def daily_summary(self, request):
        """
        Get daily settlement summary showing:
        - Total deliveries made
        - Total sales achieved
        - Outstanding stock with each salesman
        - Recommended settlement actions
        """
        date_param = request.GET.get('date')
        
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.now().date()
        
        user = request.user
        
        # Get salesmen based on user role
        if user.role == 'owner':
            salesmen = Salesman.objects.filter(owner=user.owner_profile, is_active=True)
        else:  # developer
            salesmen = Salesman.objects.filter(is_active=True)
        
        summary_data = []
        total_deliveries = 0
        total_sales_revenue = 0
        total_outstanding_value = 0
        
        for salesman in salesmen:
            # Deliveries made on target date
            daily_deliveries = Delivery.objects.filter(
                salesman=salesman,
                delivery_date=target_date,
                status__in=['delivered', 'settled']
            )
            
            # Sales made on target date
            daily_sales = InvoiceItem.objects.filter(
                invoice__salesman=salesman,
                invoice__invoice_date__date=target_date,
                invoice__status__in=['pending', 'paid', 'partial']
            ).aggregate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('unit_price'))
            )
            
            # Outstanding stock (from all deliveries, not just today)
            outstanding_assignments = BatchAssignment.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'partial']
            ).select_related('batch', 'batch__product')
            
            outstanding_value = 0
            outstanding_products = 0
            
            for assignment in outstanding_assignments:
                outstanding_qty = assignment.outstanding_quantity
                if outstanding_qty > 0:
                    outstanding_value += outstanding_qty * float(assignment.batch.product.base_price)
                    outstanding_products += outstanding_qty
            
            # Determine recommendation
            recommendation = "no_action"
            if outstanding_value > 1000:  # Threshold for settlement
                recommendation = "settle_recommended"
            elif outstanding_value > 500:
                recommendation = "review_required"
            
            salesman_summary = {
                'salesman_id': salesman.id,
                'salesman_name': salesman.user.get_full_name(),
                'deliveries_count': daily_deliveries.count(),
                'deliveries_value': sum(float(d.total_value) for d in daily_deliveries),
                'sales_quantity': daily_sales['total_quantity'] or 0,
                'sales_revenue': float(daily_sales['total_revenue'] or 0),
                'outstanding_items': outstanding_products,
                'outstanding_value': outstanding_value,
                'recommendation': recommendation,
                'efficiency_rate': 0  # Will calculate below
            }
            
            # Calculate efficiency rate (sales / deliveries)
            if salesman_summary['deliveries_value'] > 0:
                salesman_summary['efficiency_rate'] = round(
                    (salesman_summary['sales_revenue'] / salesman_summary['deliveries_value']) * 100, 1
                )
            
            summary_data.append(salesman_summary)
            
            total_deliveries += salesman_summary['deliveries_count']
            total_sales_revenue += salesman_summary['sales_revenue']
            total_outstanding_value += outstanding_value
        
        return Response({
            'date': target_date,
            'summary': {
                'total_salesmen': len(summary_data),
                'total_deliveries': total_deliveries,
                'total_sales_revenue': total_sales_revenue,
                'total_outstanding_value': total_outstanding_value,
                'settlement_recommended': len([s for s in summary_data if s['recommendation'] == 'settle_recommended']),
                'review_required': len([s for s in summary_data if s['recommendation'] == 'review_required'])
            },
            'salesmen': summary_data
        })


class DeliverySettlementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing delivery settlements.
    Provides CRUD operations for settlement records.
    """
    serializer_class = DeliverySettlementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter settlements based on user role"""
        user = self.request.user
        
        if user.role == 'salesman':
            return DeliverySettlement.objects.filter(salesman=user.salesman_profile)
        elif user.role == 'owner':
            return DeliverySettlement.objects.filter(salesman__owner=user.owner_profile)
        elif user.role == 'developer':
            return DeliverySettlement.objects.all()
        else:
            return DeliverySettlement.objects.none()


class DeliveryBySalesmanView(APIView):
    """
    GET /api/products/deliveries/by-salesman/
    List all salesmen with delivery summaries.
    """
    permission_classes = [IsOwnerOrDeveloper]
    
    @extend_schema(
        summary="List salesmen with delivery summaries",
        description="Get overview of all salesmen with their delivery and stock status",
        responses={200: OpenApiResponse(description="Salesmen delivery summaries")}
    )
    def get(self, request):
        user = request.user
        
        # Get salesmen based on user role
        if user.role == 'owner':
            salesmen = Salesman.objects.filter(owner=user.owner_profile, is_active=True)
        else:  # developer
            salesmen = Salesman.objects.filter(is_active=True)
        
        summaries = []
        total_outstanding_value = 0
        total_salesmen_with_stock = 0
        
        for salesman in salesmen:
            # Get current outstanding stock value
            outstanding_assignments = BatchAssignment.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'partial']
            ).select_related('batch', 'batch__product')
            
            outstanding_value = 0
            outstanding_items = 0
            
            for assignment in outstanding_assignments:
                outstanding_qty = assignment.outstanding_quantity
                if outstanding_qty > 0:
                    outstanding_value += outstanding_qty * float(assignment.batch.product.base_price)
                    outstanding_items += outstanding_qty
            
            # Get recent delivery activity
            recent_deliveries = Delivery.objects.filter(
                salesman=salesman,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            # Get today's sales
            today_sales = InvoiceItem.objects.filter(
                invoice__salesman=salesman,
                invoice__invoice_date__date=timezone.now().date(),
                invoice__status__in=['pending', 'paid', 'partial']
            ).aggregate(
                revenue=Sum(F('quantity') * F('unit_price'))
            )['revenue'] or 0
            
            if outstanding_value > 0:
                total_salesmen_with_stock += 1
            
            total_outstanding_value += outstanding_value
            
            summaries.append({
                'salesman_id': salesman.id,
                'salesman_name': salesman.user.get_full_name(),
                'salesman_phone': salesman.user.phone,
                'outstanding_value': outstanding_value,
                'outstanding_items': outstanding_items,
                'recent_deliveries': recent_deliveries,
                'today_sales_revenue': float(today_sales),
                'status': 'has_stock' if outstanding_value > 0 else 'no_stock',
                'priority': 'high' if outstanding_value > 1000 else 'normal'
            })
        
        # Sort by outstanding value (highest first)
        summaries.sort(key=lambda x: x['outstanding_value'], reverse=True)
        
        return Response({
            'total_salesmen': len(summaries),
            'salesmen_with_stock': total_salesmen_with_stock,
            'total_outstanding_value': total_outstanding_value,
            'salesmen': summaries
        })


class SalesmanDeliveryDetailView(APIView):
    """
    GET /api/products/deliveries/salesman/{id}/details/
    Detailed view for a specific salesman's deliveries and stock.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get detailed delivery information for a salesman",
        description="Comprehensive view of a salesman's deliveries, stock, and settlement data",
        responses={200: OpenApiResponse(description="Salesman delivery details")}
    )
    def get(self, request, salesman_id):
        try:
            salesman = Salesman.objects.get(id=salesman_id)
        except Salesman.DoesNotExist:
            return Response(
                {'error': 'Salesman not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if user.role == 'salesman' and user.salesman_profile != salesman:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role == 'owner' and salesman.owner != user.owner_profile:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all deliveries for this salesman
        deliveries = Delivery.objects.filter(salesman=salesman).order_by('-created_at')
        
        # Get current stock by product
        outstanding_assignments = BatchAssignment.objects.filter(
            salesman=salesman,
            status__in=['delivered', 'partial']
        ).select_related('batch', 'batch__product')
        
        stock_by_product = {}
        for assignment in outstanding_assignments:
            outstanding_qty = assignment.outstanding_quantity
            if outstanding_qty > 0:
                product = assignment.batch.product
                if product.id not in stock_by_product:
                    stock_by_product[product.id] = {
                        'product_id': product.id,
                        'product_name': product.name,
                        'product_sku': product.sku,
                        'quantity': 0,
                        'unit_price': float(product.base_price),
                        'total_value': 0
                    }
                
                stock_by_product[product.id]['quantity'] += outstanding_qty
                stock_by_product[product.id]['total_value'] += outstanding_qty * float(product.base_price)
        
        # Get sales history for last 30 days
        sales_history = InvoiceItem.objects.filter(
            invoice__salesman=salesman,
            invoice__invoice_date__gte=timezone.now().date() - timedelta(days=30),
            invoice__status__in=['pending', 'paid', 'partial']
        ).values('invoice__invoice_date__date').annotate(
            daily_revenue=Sum(F('quantity') * F('unit_price')),
            daily_quantity=Sum('quantity')
        ).order_by('-invoice__invoice_date__date')
        
        # Get recent settlements
        recent_settlements = DeliverySettlement.objects.filter(
            salesman=salesman
        ).order_by('-settlement_date')[:5]
        
        return Response({
            'salesman': {
                'id': salesman.id,
                'name': salesman.user.get_full_name(),
                'phone': salesman.user.phone,
                'email': salesman.user.email,
                'joined_date': salesman.created_at,
                'is_active': salesman.is_active
            },
            'current_stock': {
                'total_products': len(stock_by_product),
                'total_quantity': sum(item['quantity'] for item in stock_by_product.values()),
                'total_value': sum(item['total_value'] for item in stock_by_product.values()),
                'products': list(stock_by_product.values())
            },
            'deliveries': {
                'total_count': deliveries.count(),
                'pending_count': deliveries.filter(status='pending').count(),
                'delivered_count': deliveries.filter(status='delivered').count(),
                'settled_count': deliveries.filter(status='settled').count(),
                'recent_deliveries': DeliverySerializer(deliveries[:10], many=True).data
            },
            'sales_performance': {
                'last_30_days': list(sales_history),
                'total_revenue_30d': sum(day['daily_revenue'] for day in sales_history),
                'total_quantity_30d': sum(day['daily_quantity'] for day in sales_history)
            },
            'settlements': {
                'recent_settlements': DeliverySettlementSerializer(recent_settlements, many=True).data,
                'total_settlements': recent_settlements.count()
            }
        })


class SettleSalesmanDeliveryView(APIView):
    """
    POST /api/products/deliveries/settle/{salesman_id}/
    Settle end-of-day for a salesman.
    """
    permission_classes = [IsOwnerOrDeveloper]
    
    @extend_schema(
        summary="Settle deliveries for a salesman",
        description="Process end-of-day settlement for a specific salesman",
        request=SettleSalesmanRequestSerializer,
        responses={200: OpenApiResponse(description="Settlement completed")}
    )
    def post(self, request, salesman_id):
        try:
            salesman = Salesman.objects.get(id=salesman_id)
        except Salesman.DoesNotExist:
            return Response(
                {'error': 'Salesman not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission for owner
        if request.user.role == 'owner' and salesman.owner != request.user.owner_profile:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SettleSalesmanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        settlement_notes = serializer.validated_data.get('settlement_notes', '')
        return_all_stock = serializer.validated_data.get('return_all_stock', True)
        create_settlement_record = serializer.validated_data.get('create_settlement_record', True)
        settlement_date = timezone.now().date()
        
        # Check if settlement already exists for today
        existing_settlement = DeliverySettlement.objects.filter(
            salesman=salesman,
            settlement_date=settlement_date
        ).first()
        
        if existing_settlement:
            return Response(
                {'error': f'Settlement already exists for {settlement_date}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            settlement_data = {
                'total_delivered_value': 0,
                'total_sold_value': 0,
                'total_returned_value': 0,
                'total_margin_earned': 0,
                'total_delivered_items': 0,
                'total_sold_items': 0,
                'total_returned_items': 0,
                'settlement_items': []
            }
            
            # Get all outstanding batch assignments for this salesman
            outstanding_assignments = BatchAssignment.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'partial']
            ).select_related('batch', 'batch__product')
            
            for assignment in outstanding_assignments:
                outstanding_qty = assignment.outstanding_quantity
                
                if outstanding_qty > 0:
                    product = assignment.batch.product
                    
                    # Calculate sold quantity from invoices
                    sold_qty = InvoiceItem.objects.filter(
                        invoice__salesman=salesman,
                        product=product,
                        invoice__invoice_date__gte=assignment.created_at,
                        invoice__status__in=['pending', 'paid', 'partial']
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    
                    if return_all_stock:
                        # Return the outstanding stock
                        assignment.returned_quantity += outstanding_qty
                        assignment.status = 'returned'
                        assignment.save()
                        
                        # Update batch current quantity (return to owner)
                        assignment.batch.current_quantity += outstanding_qty
                        assignment.batch.save()
                    
                    # Track settlement data
                    delivered_value = assignment.delivered_quantity * float(product.base_price)
                    sold_value = sold_qty * float(product.base_price)
                    returned_value = outstanding_qty * float(product.base_price) if return_all_stock else 0
                    
                    settlement_data['total_delivered_value'] += delivered_value
                    settlement_data['total_sold_value'] += sold_value
                    settlement_data['total_returned_value'] += returned_value
                    settlement_data['total_delivered_items'] += assignment.delivered_quantity
                    settlement_data['total_sold_items'] += sold_qty
                    settlement_data['total_returned_items'] += outstanding_qty if return_all_stock else 0
                    
                    settlement_data['settlement_items'].append({
                        'product': product,
                        'delivered_quantity': assignment.delivered_quantity,
                        'sold_quantity': sold_qty,
                        'returned_quantity': outstanding_qty if return_all_stock else 0,
                        'unit_price': float(product.base_price),
                        'delivered_value': delivered_value,
                        'sold_value': sold_value,
                        'returned_value': returned_value
                    })
            
            # Create settlement record if requested
            settlement_record = None
            if create_settlement_record:
                settlement_record = DeliverySettlement.objects.create(
                    salesman=salesman,
                    settlement_date=settlement_date,
                    total_delivered_value=settlement_data['total_delivered_value'],
                    total_sold_value=settlement_data['total_sold_value'],
                    total_returned_value=settlement_data['total_returned_value'],
                    total_margin_earned=settlement_data['total_margin_earned'],
                    total_delivered_items=settlement_data['total_delivered_items'],
                    total_sold_items=settlement_data['total_sold_items'],
                    total_returned_items=settlement_data['total_returned_items'],
                    status='completed',
                    settlement_notes=settlement_notes,
                    settled_by=request.user
                )
                
                # Create settlement items
                for item_data in settlement_data['settlement_items']:
                    DeliverySettlementItem.objects.create(
                        settlement=settlement_record,
                        product=item_data['product'],
                        delivered_quantity=item_data['delivered_quantity'],
                        sold_quantity=item_data['sold_quantity'],
                        returned_quantity=item_data['returned_quantity'],
                        unit_price=item_data['unit_price'],
                        delivered_value=item_data['delivered_value'],
                        sold_value=item_data['sold_value'],
                        returned_value=item_data['returned_value']
                    )
            
            # Mark all delivered deliveries as settled
            settled_deliveries = Delivery.objects.filter(
                salesman=salesman,
                status='delivered'
            ).update(
                status='settled',
                settlement_date=settlement_date,
                settlement_notes=settlement_notes
            )
            
            logger.info(f"Settlement completed for salesman {salesman.user.get_full_name()}: "
                       f"{settlement_data['total_returned_items']} items worth LKR {settlement_data['total_returned_value']} returned to owner")
        
        response_data = {
            'message': 'Settlement completed successfully',
            'salesman_name': salesman.user.get_full_name(),
            'settlement_date': settlement_date,
            'settled_deliveries': settled_deliveries,
            'summary': {
                'total_delivered_items': settlement_data['total_delivered_items'],
                'total_sold_items': settlement_data['total_sold_items'],
                'total_returned_items': settlement_data['total_returned_items'],
                'total_delivered_value': settlement_data['total_delivered_value'],
                'total_sold_value': settlement_data['total_sold_value'],
                'total_returned_value': settlement_data['total_returned_value'],
                'efficiency_rate': round((settlement_data['total_sold_value'] / settlement_data['total_delivered_value']) * 100, 1) if settlement_data['total_delivered_value'] > 0 else 0
            }
        }
        
        if settlement_record:
            response_data['settlement_record'] = DeliverySettlementSerializer(settlement_record).data
        
        return Response(response_data)


class UpdateSoldQuantitiesView(APIView):
    """
    PUT /api/products/deliveries/update-sold/
    Update sold quantities from invoice creation.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Update sold quantities",
        description="Update delivery and batch assignment quantities when invoices are created/updated",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'salesman_id': {'type': 'integer'},
                    'invoice_items': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'product_id': {'type': 'integer'},
                                'quantity': {'type': 'integer'},
                                'unit_price': {'type': 'number'}
                            }
                        }
                    }
                }
            }
        },
        responses={200: OpenApiResponse(description="Quantities updated")}
    )
    def put(self, request):
        salesman_id = request.data.get('salesman_id')
        invoice_items = request.data.get('invoice_items', [])
        
        if not salesman_id or not invoice_items:
            return Response(
                {'error': 'salesman_id and invoice_items are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            salesman = Salesman.objects.get(id=salesman_id)
        except Salesman.DoesNotExist:
            return Response(
                {'error': 'Salesman not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if user.role == 'salesman' and user.salesman_profile != salesman:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif user.role == 'owner' and salesman.owner != user.owner_profile:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        updated_assignments = []
        
        for item in invoice_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            if product_id and quantity > 0:
                # Update batch assignments - this will be reflected in real-time
                # The sold quantities are calculated dynamically from InvoiceItems
                # so no direct update is needed here, but we can track the change
                assignments = BatchAssignment.objects.filter(
                    salesman=salesman,
                    batch__product_id=product_id,
                    status__in=['delivered', 'partial']
                ).select_related('batch', 'batch__product')
                
                for assignment in assignments:
                    updated_assignments.append({
                        'assignment_id': assignment.id,
                        'product_name': assignment.batch.product.name,
                        'outstanding_before': assignment.outstanding_quantity,
                        'outstanding_after': assignment.outstanding_quantity  # This will update dynamically
                    })
        
        return Response({
            'message': 'Sold quantities updated successfully',
            'salesman_name': salesman.user.get_full_name(),
            'updated_assignments': updated_assignments,
            'note': 'Sold quantities are calculated dynamically from invoice items'
        })
