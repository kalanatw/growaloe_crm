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


class ProfitAnalysisViewSet(viewsets.ViewSet):
    """
    ViewSet for detailed profit analysis and breakdowns
    """
    permission_classes = [IsOwnerOrDeveloper]
    
    @action(detail=False, methods=['get'])
    def profit_breakdown(self, request):
        """Get comprehensive profit breakdown matching frontend requirements"""
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Import models here to avoid circular imports
        from sales.models import Invoice, InvoiceSettlement
        
        # Calculate Realized Profit components
        realized_breakdown = self._get_realized_profit_breakdown(start_date, end_date)
        
        # Calculate Unrealized Profit components  
        unrealized_breakdown = self._get_unrealized_profit_breakdown(start_date, end_date)
        
        # Calculate Spendable Profit
        spendable_breakdown = self._get_spendable_profit_breakdown(
            realized_breakdown['amount'], 
            unrealized_breakdown['components']['outstanding_invoices']
        )
        
        # Calculate summary metrics
        total_sales = Invoice.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).aggregate(total=Sum('net_total'))['total'] or Decimal('0.00')
        
        total_collections = InvoiceSettlement.objects.filter(
            settlement_date__date__range=[start_date, end_date]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        all_outstanding = Invoice.objects.filter(
            balance_due__gt=0
        ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0.00')
        
        collection_efficiency = (total_collections / total_sales) if total_sales > 0 else 0
        
        return Response({
            'realized': realized_breakdown,
            'unrealized': unrealized_breakdown,
            'spendable': spendable_breakdown,
            'summary': {
                'total_sales': float(total_sales),
                'total_collections': float(total_collections),
                'total_outstanding': float(all_outstanding),
                'collection_efficiency': float(collection_efficiency)
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
    
    def _get_realized_profit_breakdown(self, start_date, end_date):
        """Calculate realized profit breakdown"""
        from sales.models import Invoice, InvoiceSettlement
        
        # Cash from settled invoices
        settlements = InvoiceSettlement.objects.filter(
            settlement_date__date__range=[start_date, end_date]
        ).select_related('invoice')
        
        cash_from_settlements = settlements.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Commissions on settled invoices (assuming 5% commission rate for now)
        # This should be calculated based on actual commission records when available
        commissions_on_settled = cash_from_settlements * Decimal('0.05')
        
        # Additional income (financial transactions marked as income)
        additional_income = FinancialTransaction.objects.filter(
            date__range=[start_date, end_date],
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Expenses (financial transactions marked as expense)
        expenses = FinancialTransaction.objects.filter(
            date__range=[start_date, end_date],
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate realized profit
        realized_profit = cash_from_settlements - commissions_on_settled - expenses + additional_income
        
        return {
            'type': 'realized',
            'amount': float(realized_profit),
            'components': {
                'sales_revenue': float(cash_from_settlements),
                'collection_amount': float(cash_from_settlements),
                'pending_commissions': float(commissions_on_settled),
                'recent_collections': float(cash_from_settlements),
                'calculation_details': f'Collections: {cash_from_settlements} - Commissions: {commissions_on_settled} - Expenses: {expenses} + Other Income: {additional_income}'
            },
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'last_updated': timezone.now().isoformat()
        }
    
    def _get_unrealized_profit_breakdown(self, start_date, end_date):
        """Calculate unrealized profit breakdown"""
        from sales.models import Invoice
        
        # Outstanding invoices
        outstanding_invoices = Invoice.objects.filter(
            balance_due__gt=0
        ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0.00')
        
        # Estimated commissions on outstanding invoices
        estimated_commissions = outstanding_invoices * Decimal('0.05')
        
        # Calculate unrealized profit
        unrealized_profit = outstanding_invoices - estimated_commissions
        
        return {
            'type': 'unrealized',
            'amount': float(unrealized_profit),
            'components': {
                'outstanding_invoices': float(outstanding_invoices),
                'pending_commissions': float(estimated_commissions),
                'calculation_details': f'Outstanding: {outstanding_invoices} - Estimated Commissions: {estimated_commissions}'
            },
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'last_updated': timezone.now().isoformat()
        }
    
    def _get_spendable_profit_breakdown(self, realized_profit, outstanding_invoices):
        """Calculate spendable profit breakdown"""
        # Ensure we're working with Decimal types
        realized_profit = Decimal(str(realized_profit))
        outstanding_invoices = Decimal(str(outstanding_invoices))
        
        # Conservative approach: reserve 10% of outstanding invoices as risk buffer
        risk_reserve = outstanding_invoices * Decimal('0.1')
        commission_reserve = outstanding_invoices * Decimal('0.05')
        spendable_profit = max(Decimal('0'), realized_profit - risk_reserve)
        
        return {
            'type': 'spendable',
            'amount': float(spendable_profit),
            'components': {
                'recent_collections': float(realized_profit),
                'pending_commissions': float(commission_reserve),
                'calculation_details': f'Realized Profit: {realized_profit} - Risk Reserve (10% of outstanding): {risk_reserve}'
            },
            'date_range': {
                'start_date': timezone.now().date().isoformat(),
                'end_date': timezone.now().date().isoformat()
            },
            'last_updated': timezone.now().isoformat()
        }
