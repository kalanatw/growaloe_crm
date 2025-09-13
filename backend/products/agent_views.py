from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Sum, Q, Count
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Delivery, AgentReturn, Product, Batch
from accounts.models import Salesman
from .agent_serializers import AgentReturnSerializer, AgentDeliverySerializer, CreateAgentDeliverySerializer


class AgentReturnViewSet(viewsets.ModelViewSet):
    """ViewSet for managing agent returns"""
    queryset = AgentReturn.objects.select_related(
        'agent', 'original_delivery', 'product', 'batch', 'approved_by', 'created_by'
    ).all()
    serializer_class = AgentReturnSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['agent', 'status', 'reason', 'original_delivery']
    search_fields = ['return_number', 'product__name', 'agent__name']
    ordering_fields = ['created_at', 'return_amount', 'quantity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'owner':
            # Owners can see all agent returns
            return queryset
        elif user.role == 'salesman':
            try:
                salesman = user.salesman_profile
                if salesman.salesman_type == 'agent':
                    # Agents can only see their own returns
                    return queryset.filter(agent=salesman)
                else:
                    # Employees cannot access agent returns
                    return queryset.none()
            except Salesman.DoesNotExist:
                return queryset.none()
        elif user.role == 'developer':
            return queryset
        else:
            return queryset.none()
    
    def perform_create(self, serializer):
        """Set the created_by field and validate agent type"""
        user = self.request.user
        
        # If user is an agent, set them as the agent
        if user.role == 'salesman':
            try:
                salesman = user.salesman_profile
                if salesman.salesman_type == 'agent':
                    serializer.save(agent=salesman, created_by=user)
                else:
                    raise ValidationError("Only agents can create returns")
            except Salesman.DoesNotExist:
                raise ValidationError("Salesman profile not found")
        else:
            # Owners/developers can create returns for any agent
            serializer.save(created_by=user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an agent return"""
        agent_return = self.get_object()
        
        # Only owners can approve returns
        if request.user.role != 'owner':
            return Response(
                {'error': 'Only owners can approve returns'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if agent_return.status != 'pending':
            return Response(
                {'error': 'Only pending returns can be approved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                agent_return.approve_return(request.user)
                
                return Response({
                    'message': 'Return approved successfully',
                    'return_number': agent_return.return_number,
                    'return_amount': float(agent_return.return_amount),
                    'agent_balance_after': float(agent_return.agent.current_balance)
                })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an agent return"""
        agent_return = self.get_object()
        
        # Only owners can reject returns
        if request.user.role != 'owner':
            return Response(
                {'error': 'Only owners can reject returns'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if agent_return.status != 'pending':
            return Response(
                {'error': 'Only pending returns can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        agent_return.status = 'rejected'
        agent_return.approved_by = request.user
        agent_return.approved_date = timezone.now()
        agent_return.notes = f"Rejected: {rejection_reason}"
        agent_return.save()
        
        return Response({
            'message': 'Return rejected',
            'return_number': agent_return.return_number,
            'rejection_reason': rejection_reason
        })
    
    @action(detail=False, methods=['get'])
    def pending_summary(self, request):
        """Get summary of pending returns"""
        queryset = self.get_queryset().filter(status='pending')
        
        total_pending = queryset.count()
        total_amount = queryset.aggregate(total=Sum('return_amount'))['total'] or 0
        
        # Group by agent
        by_agent = queryset.values(
            'agent__id', 'agent__name'
        ).annotate(
            pending_count=Count('id'),
            pending_amount=Sum('return_amount')
        ).order_by('-pending_amount')
        
        # Group by reason
        by_reason = queryset.values('reason').annotate(
            count=Count('id'),
            amount=Sum('return_amount')
        ).order_by('-amount')
        
        return Response({
            'total_pending': total_pending,
            'total_amount': float(total_amount),
            'by_agent': list(by_agent),
            'by_reason': list(by_reason)
        })


class AgentDeliveryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing agent deliveries"""
    queryset = Delivery.objects.filter(is_agent_delivery=True).select_related(
        'salesman', 'created_by'
    ).prefetch_related('items__product').all()
    serializer_class = AgentDeliverySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['salesman', 'status', 'agent_payment_status']
    search_fields = ['delivery_number', 'salesman__name']
    ordering_fields = ['delivery_date', 'agent_purchase_amount', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'owner':
            # Owners can see all agent deliveries
            return queryset
        elif user.role == 'salesman':
            try:
                salesman = user.salesman_profile
                if salesman.salesman_type == 'agent':
                    # Agents can only see their own deliveries
                    return queryset.filter(salesman=salesman)
                else:
                    # Employees cannot access agent deliveries
                    return queryset.none()
            except Salesman.DoesNotExist:
                return queryset.none()
        elif user.role == 'developer':
            return queryset
        else:
            return queryset.none()
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process payment for agent delivery"""
        delivery = self.get_object()
        
        # Only owners can process payments
        if request.user.role != 'owner':
            return Response(
                {'error': 'Only owners can process payments'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if delivery.agent_payment_status == 'paid':
            return Response(
                {'error': 'Delivery is already fully paid'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_amount = request.data.get('payment_amount', 0)
        payment_method = request.data.get('payment_method', 'cash')
        notes = request.data.get('notes', '')
        
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
        
        try:
            with transaction.atomic():
                # Update agent balance (increase debt to owner)
                agent = delivery.salesman
                agent.current_balance += payment_amount
                agent.save()
                
                # Update delivery payment status
                if payment_amount >= delivery.agent_purchase_amount:
                    delivery.agent_payment_status = 'paid'
                    delivery.agent_payment_date = timezone.now()
                else:
                    delivery.agent_payment_status = 'partial'
                
                delivery.save()
                
                # Create cash transaction record
                from accounts.models import SalesmanCashTransaction
                SalesmanCashTransaction.objects.create(
                    salesman=agent,
                    transaction_type='collection',
                    amount=payment_amount,
                    balance_before=agent.current_balance - payment_amount,
                    balance_after=agent.current_balance,
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
                'agent_balance': float(agent.current_balance),
                'remaining_amount': float(delivery.agent_purchase_amount - payment_amount) if delivery.agent_payment_status == 'partial' else 0
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def payment_summary(self, request):
        """Get payment summary for agent deliveries"""
        queryset = self.get_queryset()
        
        total_deliveries = queryset.count()
        total_amount = queryset.aggregate(total=Sum('agent_purchase_amount'))['total'] or 0
        
        # Group by payment status
        by_status = queryset.values('agent_payment_status').annotate(
            count=Count('id'),
            amount=Sum('agent_purchase_amount')
        ).order_by('agent_payment_status')
        
        # Group by agent
        by_agent = queryset.values(
            'salesman__id', 'salesman__name'
        ).annotate(
            delivery_count=Count('id'),
            total_amount=Sum('agent_purchase_amount'),
            paid_count=Count('id', filter=Q(agent_payment_status='paid')),
            pending_count=Count('id', filter=Q(agent_payment_status='pending'))
        ).order_by('-total_amount')
        
        return Response({
            'total_deliveries': total_deliveries,
            'total_amount': float(total_amount),
            'by_status': list(by_status),
            'by_agent': list(by_agent)
        })
    
    @action(detail=True, methods=['get'])
    def returns(self, request, pk=None):
        """Get returns for this agent delivery"""
        delivery = self.get_object()
        
        returns = AgentReturn.objects.filter(
            original_delivery=delivery
        ).select_related('product', 'batch', 'approved_by')
        
        serializer = AgentReturnSerializer(returns, many=True)
        return Response(serializer.data)