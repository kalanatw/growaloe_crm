from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import FinancialTransaction, FinancialSummary
from .serializers import FinancialTransactionSerializer, InvoiceSettlementSerializer, FinancialSummarySerializer
from sales.models import Invoice, InvoiceSettlement
from sales.models import Invoice, InvoiceSettlement
from accounts.permissions import IsOwnerOrDeveloper


class FinancialTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing business income and expense transactions
    """
    queryset = FinancialTransaction.objects.all()
    serializer_class = FinancialTransactionSerializer
    permission_classes = [IsOwnerOrDeveloper]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Search by description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(reference_number__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get financial summary for transactions using accounting principles"""
        # Get date range (default to current month)
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if not date_from or not date_to:
            today = timezone.now().date()
            date_from = today.replace(day=1)
            date_to = today
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        transactions = FinancialTransaction.objects.filter(
            date__range=[date_from, date_to]
        )
        
        # Calculate totals using debit/credit system
        debit_total = transactions.filter(transaction_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        credit_total = transactions.filter(transaction_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        net_balance = credit_total - debit_total  # This is the profit
        
        # Get category breakdown
        credit_by_category = transactions.filter(transaction_type='credit').values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        debit_by_category = transactions.filter(transaction_type='debit').values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        return Response({
            'date_from': date_from,
            'date_to': date_to,
            'total_debits': debit_total,
            'total_credits': credit_total,
            'net_balance': net_balance,
            'credit_by_category': credit_by_category,
            'debit_by_category': debit_by_category,
            'transaction_count': transactions.count()
        })


class InvoiceSettlementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoice settlements/payments
    """
    queryset = InvoiceSettlement.objects.all()
    serializer_class = InvoiceSettlementSerializer
    permission_classes = [IsOwnerOrDeveloper]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by invoice
        invoice_id = self.request.query_params.get('invoice_id')
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
        
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(settlement_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(settlement_date__lte=date_to)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get settlement summary"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if not date_from or not date_to:
            today = timezone.now().date()
            date_from = today.replace(day=1)
            date_to = today
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        settlements = InvoiceSettlement.objects.filter(
            settlement_date__range=[date_from, date_to]
        )
        
        total_settlements = settlements.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Group by payment method
        by_payment_method = settlements.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return Response({
            'date_from': date_from,
            'date_to': date_to,
            'total_settlements': total_settlements,
            'settlement_count': settlements.count(),
            'by_payment_method': by_payment_method
        })


class FinancialDashboardView(viewsets.ViewSet):
    """
    Combined financial dashboard showing both transactions and invoice data
    """
    permission_classes = [IsOwnerOrDeveloper]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get comprehensive financial dashboard data"""
        # Get date range (default to current month)
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if not date_from or not date_to:
            today = timezone.now().date()
            date_from = today.replace(day=1)
            date_to = today
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Financial Transactions
        transactions = FinancialTransaction.objects.filter(
            date__range=[date_from, date_to]
        )
        
        total_debits = transactions.filter(transaction_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        total_credits = transactions.filter(transaction_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Invoice Data
        invoices = Invoice.objects.filter(
            created_at__date__range=[date_from, date_to]
        )
        
        total_invoiced = invoices.aggregate(
            total=Sum('net_total')
        )['total'] or Decimal('0.00')
        
        # Invoice Settlements
        settlements = InvoiceSettlement.objects.filter(
            settlement_date__range=[date_from, date_to]
        )
        
        total_collected = settlements.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Outstanding balance (all time)
        all_invoices = Invoice.objects.all()
        outstanding_balance = all_invoices.aggregate(
            total_invoiced=Sum('net_total'),
            total_paid=Sum('paid_amount')
        )
        
        total_outstanding = (outstanding_balance['total_invoiced'] or Decimal('0.00')) - \
                           (outstanding_balance['total_paid'] or Decimal('0.00'))
        
        # Net balance calculation (Profit = Credits - Debits)
        net_balance = total_credits - total_debits
        
        return Response({
            'period': {
                'date_from': date_from,
                'date_to': date_to
            },
            'transactions': {
                'total_debits': total_debits,
                'total_credits': total_credits,
                'net_balance': net_balance  # This is the profit
            },
            'invoices': {
                'total_invoiced': total_invoiced,
                'total_collected': total_collected,
                'net_invoice_balance': total_invoiced - total_collected,
                'total_outstanding': total_outstanding
            },
            'cash_flow': {
                'total_credits': total_credits,  # All money received
                'total_debits': total_debits,    # All money spent/owed
                'net_cash_flow': net_balance     # Net position
            },
            'summary': {
                'profit': net_balance,  # Credits - Debits
                'outstanding_receivables': total_outstanding,
                'total_business_value': net_balance + total_outstanding
            }
        })
    
    @action(detail=False, methods=['get'])
    def bank_book(self, request):
        """Get bank book style transaction listing"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if not date_from or not date_to:
            today = timezone.now().date()
            date_from = today - timedelta(days=30)
            date_to = today
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Get all financial transactions
        transactions = FinancialTransaction.objects.filter(
            date__range=[date_from, date_to]
        )
        
        # Get all settlements as income entries
        settlements = InvoiceSettlement.objects.filter(
            settlement_date__range=[date_from, date_to]
        ).select_related('invoice').prefetch_related('payments')
        
        # Format transactions for bank book view
        bank_entries = []
        
        # Add financial transactions
        for trans in transactions:
            bank_entries.append({
                'date': trans.date,
                'type': 'transaction',
                'description': trans.description,
                'reference': trans.reference_number,
                'income': trans.amount if trans.transaction_type == 'income' else 0,
                'expense': trans.amount if trans.transaction_type == 'expense' else 0,
                'category': trans.category,
                'notes': trans.notes
            })
        
        # Add settlements as income
        for settlement in settlements:
            # Get the first payment's reference number if available
            first_payment = settlement.payments.first()
            reference = first_payment.reference_number if first_payment else settlement.invoice.invoice_number
            
            # Convert datetime to date for consistent sorting
            settlement_date = settlement.settlement_date.date() if hasattr(settlement.settlement_date, 'date') else settlement.settlement_date
            
            bank_entries.append({
                'date': settlement_date,
                'type': 'settlement',
                'description': f"Payment received - {settlement.invoice.invoice_number}",
                'reference': reference or '',
                'income': settlement.total_amount,
                'expense': 0,
                'category': 'invoice_collection',
                'notes': settlement.notes or ''
            })
        
        # Sort by date
        bank_entries.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate running balance
        running_balance = Decimal('0.00')
        for entry in reversed(bank_entries):
            running_balance += entry['income'] - entry['expense']
            entry['balance'] = running_balance
        
        bank_entries.reverse()  # Show latest first but with correct running balance
        
        return Response({
            'date_from': date_from,
            'date_to': date_to,
            'entries': bank_entries,
            'final_balance': running_balance
        })
