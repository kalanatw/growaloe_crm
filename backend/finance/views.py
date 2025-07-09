from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from rest_framework.views import APIView

from .models import (
    TransactionCategory, 
    FinancialTransaction, 
    DescriptionSuggestion, 
    ProfitSummary,
    CommissionRecord
)
from .serializers import (
    TransactionCategorySerializer,
    FinancialTransactionSerializer,
    FinancialTransactionCreateSerializer,
    DescriptionSuggestionSerializer,
    ProfitSummarySerializer,
    CommissionRecordSerializer,
    FinancialDashboardSerializer,
    TransactionFilterSerializer,
    ProfitCalculationRequestSerializer,
    CommissionPaymentSerializer,
    TransactionSummarySerializer
)
from .services import (
    ProfitCalculationService,
    DescriptionSuggestionService,
    CommissionCalculationService
)


class TransactionCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing transaction categories"""
    
    queryset = TransactionCategory.objects.all()
    serializer_class = TransactionCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'transaction_type', 'created_at']
    ordering = ['transaction_type', 'name']


class FinancialTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing financial transactions"""
    
    queryset = FinancialTransaction.objects.select_related('category', 'created_by')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_date', 'category', 'category__transaction_type']
    search_fields = ['description', 'reference_number', 'category__name']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    ordering = ['-transaction_date', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FinancialTransactionCreateSerializer
        return FinancialTransactionSerializer
    
    def perform_create(self, serializer):
        """Set created_by and update description suggestions"""
        transaction = serializer.save(created_by=self.request.user)
        
        # Update description suggestions
        DescriptionSuggestionService.update_suggestion(
            transaction.description,
            transaction.category.id
        )
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Get description suggestions based on query"""
        query = request.query_params.get('q', '')
        category_id = request.query_params.get('category_id')
        
        suggestions = DescriptionSuggestionService.get_suggestions(
            query, 
            int(category_id) if category_id else None
        )
        
        return Response(suggestions)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary by category"""
        filter_serializer = TransactionFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        
        filters = Q()
        validated_data = filter_serializer.validated_data
        
        if validated_data.get('start_date'):
            filters &= Q(transaction_date__gte=validated_data['start_date'])
        if validated_data.get('end_date'):
            filters &= Q(transaction_date__lte=validated_data['end_date'])
        if validated_data.get('transaction_type') != 'all':
            filters &= Q(category__transaction_type=validated_data['transaction_type'])
        
        # Get summary by category
        summary = FinancialTransaction.objects.filter(filters).values(
            'category__name',
            'category__transaction_type'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')
        
        # Calculate total for percentage calculation
        total_amount = sum(item['total_amount'] for item in summary if item['total_amount'])
        
        # Add percentage to each item
        for item in summary:
            if total_amount > 0 and item['total_amount']:
                item['percentage'] = (item['total_amount'] / total_amount) * 100
            else:
                item['percentage'] = 0
        
        summary_data = [
            {
                'category_name': item['category__name'],
                'transaction_type': item['category__transaction_type'],
                'count': item['count'],
                'total_amount': item['total_amount'],
                'percentage': item['percentage']
            }
            for item in summary
        ]
        
        serializer = TransactionSummarySerializer(summary_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get financial dashboard data"""
        # Get date range from request, default to current month
        today = timezone.now().date()
        start_date = request.query_params.get(
            'start_date', 
            today.replace(day=1).isoformat()
        )
        end_date = request.query_params.get('end_date', today.isoformat())
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate financial summary
        dashboard_data = ProfitCalculationService.generate_financial_summary(
            start_date, end_date
        )
        
        serializer = FinancialDashboardSerializer(dashboard_data)
        return Response(serializer.data)


class ProfitSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for profit summaries"""
    
    queryset = ProfitSummary.objects.all()
    serializer_class = ProfitSummarySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['period_type', 'start_date', 'end_date']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']
    
    @action(detail=False, methods=['get'])
    def calculate(self, request):
        """Calculate profit metrics for a specific period"""
        serializer = ProfitCalculationRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        period_type = validated_data['period_type']
        
        # Calculate profits
        profit_data = ProfitCalculationService.generate_financial_summary(
            start_date, end_date, period_type
        )
        
        return Response(profit_data)
    
    @action(detail=False, methods=['get'])
    def realized(self, request):
        """Get realized profit details"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        realized_profit = ProfitCalculationService.calculate_realized_profit(start_date, end_date)
        
        return Response({
            'period': {'start_date': start_date, 'end_date': end_date},
            'realized_profit': float(realized_profit)
        })
    
    @action(detail=False, methods=['get'])
    def unrealized(self, request):
        """Get unrealized profit details"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        unrealized_profit = ProfitCalculationService.calculate_unrealized_profit(start_date, end_date)
        
        return Response({
            'period': {'start_date': start_date, 'end_date': end_date},
            'unrealized_profit': float(unrealized_profit)
        })
    
    @action(detail=False, methods=['get'])
    def spendable(self, request):
        """Get spendable profit details"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        spendable_profit = ProfitCalculationService.calculate_spendable_profit(start_date, end_date)
        
        return Response({
            'period': {'start_date': start_date, 'end_date': end_date},
            'spendable_profit': float(spendable_profit)
        })
    
    @action(detail=False, methods=['get'])
    def realized_breakdown(self, request):
        """Get detailed realized profit breakdown"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        breakdown = ProfitCalculationService.get_realized_profit_breakdown(start_date, end_date)
        return Response(breakdown)
    
    @action(detail=False, methods=['get'])
    def unrealized_breakdown(self, request):
        """Get detailed unrealized profit breakdown"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        breakdown = ProfitCalculationService.get_unrealized_profit_breakdown(start_date, end_date)
        return Response(breakdown)
    
    @action(detail=False, methods=['get'])
    def spendable_analysis(self, request):
        """Get detailed spendable profit analysis with risk assessment"""
        analysis = ProfitCalculationService.get_spendable_profit_analysis()
        return Response(analysis)


class CommissionRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing commission records"""
    
    queryset = CommissionRecord.objects.select_related(
        'invoice', 'settlement', 'salesman__user', 'created_by'
    )
    serializer_class = CommissionRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'salesman', 'invoice', 'payment_date']
    search_fields = ['invoice__invoice_number', 'salesman__user__first_name', 'salesman__user__last_name']
    ordering_fields = ['created_at', 'payment_date', 'commission_amount']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set created_by when creating commission record"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def pay_commissions(self, request):
        """Mark multiple commissions as paid"""
        serializer = CommissionPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        commission_ids = validated_data['commission_ids']
        payment_date = validated_data['payment_date']
        payment_reference = validated_data.get('payment_reference', '')
        notes = validated_data.get('notes', '')
        
        # Update commission records
        updated_count = CommissionRecord.objects.filter(
            id__in=commission_ids,
            status__in=['calculated', 'pending']
        ).update(
            status='paid',
            payment_date=payment_date,
            payment_reference=payment_reference,
            notes=notes
        )
        
        return Response({
            'success': True,
            'updated_count': updated_count,
            'message': f'{updated_count} commission records marked as paid'
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending commission records"""
        pending_commissions = self.queryset.filter(status__in=['calculated', 'pending'])
        
        # Apply filters
        salesman_id = request.query_params.get('salesman')
        if salesman_id:
            pending_commissions = pending_commissions.filter(salesman_id=salesman_id)
        
        page = self.paginate_queryset(pending_commissions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pending_commissions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get commission summary"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        filters = Q()
        if start_date:
            filters &= Q(created_at__date__gte=start_date)
        if end_date:
            filters &= Q(created_at__date__lte=end_date)
        
        commissions = CommissionRecord.objects.filter(filters)
        
        summary = {
            'total_commissions': commissions.count(),
            'total_amount': float(commissions.aggregate(total=Sum('commission_amount'))['total'] or 0),
            'paid_amount': float(commissions.filter(status='paid').aggregate(total=Sum('commission_amount'))['total'] or 0),
            'pending_amount': float(commissions.filter(status__in=['calculated', 'pending']).aggregate(total=Sum('commission_amount'))['total'] or 0),
            'by_status': {}
        }
        
        # Get breakdown by status
        status_breakdown = commissions.values('status').annotate(
            count=Count('id'),
            amount=Sum('commission_amount')
        )
        
        for item in status_breakdown:
            summary['by_status'][item['status']] = {
                'count': item['count'],
                'amount': float(item['amount'] or 0)
            }
        
        return Response(summary)


class FinancialReportsViewSet(viewsets.ViewSet):
    """ViewSet for financial reports"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Generate daily financial report"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report_data = ProfitCalculationService.generate_financial_summary(
            report_date, report_date, 'daily'
        )
        
        return Response({
            'report_type': 'daily',
            'data': report_data
        })
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Generate weekly financial report"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Calculate start of week (Monday)
            start_date = date - timedelta(days=date.weekday())
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report_data = ProfitCalculationService.generate_financial_summary(
            start_date, end_date, 'weekly'
        )
        
        return Response({
            'report_type': 'weekly',
            'data': report_data
        })
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Generate monthly financial report"""
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        try:
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        except ValueError:
            return Response(
                {"error": "Invalid year or month"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report_data = ProfitCalculationService.generate_financial_summary(
            start_date, end_date, 'monthly'
        )
        
        return Response({
            'report_type': 'monthly',
            'data': report_data
        })
    
    @action(detail=False, methods=['get'])
    def collection_efficiency(self, request):
        """Generate collection efficiency report"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        collection_efficiency = ProfitCalculationService.calculate_collection_efficiency(
            start_date, end_date
        )
        
        return Response({
            'report_type': 'collection_efficiency',
            'period': {'start_date': start_date, 'end_date': end_date},
            'collection_efficiency': float(collection_efficiency)
        })


# Individual API Views for easier URL routing
class RealizedProfitView(APIView):
    """API view for calculating realized profit"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get realized profit calculation"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        realized_profit = ProfitCalculationService.calculate_realized_profit(date)
        
        return Response({
            'date': date,
            'realized_profit': float(realized_profit),
            'calculation_time': timezone.now()
        })


class UnrealizedProfitView(APIView):
    """API view for calculating unrealized profit"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get unrealized profit calculation"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        unrealized_profit = ProfitCalculationService.calculate_unrealized_profit(date)
        
        return Response({
            'date': date,
            'unrealized_profit': float(unrealized_profit),
            'calculation_time': timezone.now()
        })


class SpendableProfitView(APIView):
    """API view for calculating spendable profit"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get spendable profit calculation"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        spendable_profit = ProfitCalculationService.calculate_spendable_profit(date)
        
        return Response({
            'date': date,
            'spendable_profit': float(spendable_profit),
            'calculation_time': timezone.now()
        })


class ProfitSummaryView(APIView):
    """API view for comprehensive profit summary"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive profit summary"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate all profit types
        realized_profit = ProfitCalculationService.calculate_realized_profit(date)
        unrealized_profit = ProfitCalculationService.calculate_unrealized_profit(date)
        spendable_profit = ProfitCalculationService.calculate_spendable_profit(date)
        collection_efficiency = ProfitCalculationService.calculate_collection_efficiency(date, date)
        
        return Response({
            'date': date,
            'realized_profit': float(realized_profit),
            'unrealized_profit': float(unrealized_profit),
            'spendable_profit': float(spendable_profit),
            'collection_efficiency': float(collection_efficiency),
            'calculation_time': timezone.now()
        })


class FinancialDashboardView(APIView):
    """API view for financial dashboard data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get financial dashboard data"""
        dashboard_data = ProfitCalculationService.generate_financial_summary(
            timezone.now().date(), timezone.now().date(), 'daily'
        )
        
        # Add additional dashboard metrics
        today = timezone.now().date()
        recent_transactions = FinancialTransaction.objects.filter(
            date__gte=today - timedelta(days=7)
        ).order_by('-date')[:10]
        
        pending_commissions = CommissionRecord.objects.filter(
            status='earned'
        ).aggregate(
            total=Sum('commission_amount')
        )['total'] or Decimal('0.00')
        
        dashboard_data.update({
            'recent_transactions': FinancialTransactionSerializer(recent_transactions, many=True).data,
            'pending_commissions': float(pending_commissions),
            'last_updated': timezone.now()
        })
        
        return Response(dashboard_data)


class DailyReportView(APIView):
    """API view for daily financial reports"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get daily financial report"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report_data = ProfitCalculationService.generate_financial_summary(
            date, date, 'daily'
        )
        
        return Response({
            'report_type': 'daily',
            'date': date,
            'data': report_data
        })


class WeeklyReportView(APIView):
    """API view for weekly financial reports"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get weekly financial report"""
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Calculate start of week (Monday)
            start_date = date - timedelta(days=date.weekday())
            end_date = start_date + timedelta(days=6)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report_data = ProfitCalculationService.generate_financial_summary(
            start_date, end_date, 'weekly'
        )
        
        return Response({
            'report_type': 'weekly',
            'start_date': start_date,
            'end_date': end_date,
            'data': report_data
        })


class MonthlyReportView(APIView):
    """API view for monthly financial reports"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get monthly financial report"""
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        try:
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        except ValueError:
            return Response(
                {"error": "Invalid year or month"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report_data = ProfitCalculationService.generate_financial_summary(
            start_date, end_date, 'monthly'
        )
        
        return Response({
            'report_type': 'monthly',
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'data': report_data
        })


class CollectionEfficiencyView(APIView):
    """API view for collection efficiency reports"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get collection efficiency report"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        collection_efficiency = ProfitCalculationService.calculate_collection_efficiency(
            start_date, end_date
        )
        
        return Response({
            'report_type': 'collection_efficiency',
            'start_date': start_date,
            'end_date': end_date,
            'collection_efficiency': float(collection_efficiency)
        })


class TransactionSummaryView(APIView):
    """API view for transaction summary"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get transaction summary"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        transaction_type = request.query_params.get('type')
        
        queryset = FinancialTransaction.objects.all()
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        
        summary = queryset.aggregate(
            total_income=Sum('amount', filter=Q(type='income')),
            total_expense=Sum('amount', filter=Q(type='expense')),
            transaction_count=Count('id')
        )
        
        return Response({
            'summary': {
                'total_income': float(summary['total_income'] or 0),
                'total_expense': float(summary['total_expense'] or 0),
                'net_amount': float((summary['total_income'] or 0) - (summary['total_expense'] or 0)),
                'transaction_count': summary['transaction_count']
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'transaction_type': transaction_type
            }
        })


class DescriptionSuggestionsView(APIView):
    """API view for description suggestions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get description suggestions"""
        query = request.query_params.get('q', '')
        category_id = request.query_params.get('category')
        limit = int(request.query_params.get('limit', 10))
        
        suggestions = DescriptionSuggestionService.get_suggestions(
            query, category_id, limit
        )
        
        return Response({
            'suggestions': DescriptionSuggestionSerializer(suggestions, many=True).data,
            'query': query,
            'category_id': category_id
        })


class CommissionSummaryView(APIView):
    """API view for commission summary"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get commission summary"""
        status_filter = request.query_params.get('status')
        salesperson_id = request.query_params.get('salesperson')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = CommissionRecord.objects.all()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if salesperson_id:
            queryset = queryset.filter(salesperson_id=salesperson_id)
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_earned__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_earned__lte=end_date)
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        summary = queryset.aggregate(
            total_earned=Sum('commission_amount', filter=Q(status='earned')),
            total_paid=Sum('commission_amount', filter=Q(status='paid')),
            total_pending=Sum('commission_amount', filter=Q(status='pending')),
            commission_count=Count('id')
        )
        
        return Response({
            'summary': {
                'total_earned': float(summary['total_earned'] or 0),
                'total_paid': float(summary['total_paid'] or 0),
                'total_pending': float(summary['total_pending'] or 0),
                'commission_count': summary['commission_count']
            },
            'filters': {
                'status': status_filter,
                'salesperson_id': salesperson_id,
                'start_date': start_date,
                'end_date': end_date
            }
        })
