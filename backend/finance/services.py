from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
from typing import Dict, Tuple, Optional

from .models import FinancialTransaction, ProfitSummary, CommissionRecord, DescriptionSuggestion
from sales.models import Invoice, InvoiceSettlement, InvoiceItem, Commission, Return
from products.models import Batch


class ProfitCalculationService:
    """Service class for calculating various profit metrics"""
    
    @staticmethod
    def calculate_realized_profit(start_date: datetime.date, end_date: datetime.date) -> Decimal:
        """
        Calculate realized profit based on actual cash received and expenses
        
        Formula: Realized_Profit = 
            SUM(cash_from_settled_invoices) 
            - SUM(commissions_on_settled) 
            - SUM(expenses) 
            + SUM(additional_income)
        """
        # Get all settlements in date range
        settlements = InvoiceSettlement.objects.filter(
            settlement_date__date__gte=start_date,
            settlement_date__date__lte=end_date
        ).select_related('invoice')
        
        # Calculate cash received from settlements
        cash_from_settlements = settlements.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        # Get commissions paid on settled invoices
        settled_invoice_ids = settlements.values_list('invoice_id', flat=True)
        commissions_on_settled = Commission.objects.filter(
            invoice_id__in=settled_invoice_ids,
            status='paid',
            paid_date__date__gte=start_date,
            paid_date__date__lte=end_date
        ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
        
        # Get additional income (manual income transactions)
        additional_income = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            category__transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Get expenses (manual expense transactions)
        expenses = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            category__transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate realized profit
        realized_profit = (
            cash_from_settlements - 
            commissions_on_settled - 
            expenses + 
            additional_income
        )
        
        return realized_profit
    
    @staticmethod
    def calculate_unrealized_profit(start_date: datetime.date, end_date: datetime.date) -> Decimal:
        """
        Calculate unrealized profit from outstanding invoices
        
        Formula: Unrealized_Profit = 
            SUM(unsettled_invoice_amounts) 
            - SUM(estimated_commissions_on_unsettled)
        """
        # Get unsettled or partially settled invoices in the date range
        unsettled_invoices = Invoice.objects.filter(
            invoice_date__date__gte=start_date,
            invoice_date__date__lte=end_date,
            status__in=['pending', 'partial']
        )
        
        # Calculate total unsettled amounts
        unsettled_amount = unsettled_invoices.aggregate(
            total=Sum('balance_due')
        )['total'] or Decimal('0')
        
        # Calculate estimated commissions on unsettled invoices
        estimated_commissions = Commission.objects.filter(
            invoice__in=unsettled_invoices,
            status__in=['pending', 'calculated']
        ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
        
        # For invoices without commission records, estimate based on default rate (5%)
        invoices_without_commission = unsettled_invoices.exclude(
            id__in=Commission.objects.filter(
                invoice__in=unsettled_invoices
            ).values_list('invoice_id', flat=True)
        )
        
        additional_estimated_commissions = Decimal('0')
        for invoice in invoices_without_commission:
            if invoice.balance_due > 0:
                # Estimate 5% commission on outstanding balance
                additional_estimated_commissions += invoice.balance_due * Decimal('0.05')
        
        total_estimated_commissions = estimated_commissions + additional_estimated_commissions
        
        # Calculate unrealized profit
        unrealized_profit = unsettled_amount - total_estimated_commissions
        
        return unrealized_profit
    
    @staticmethod
    def calculate_spendable_profit(start_date: datetime.date, end_date: datetime.date) -> Decimal:
        """
        Calculate spendable (liquid) profit - safe amount available for spending
        
        Formula: Spendable_Profit = 
            Realized_Profit - SUM(unsettled_invoice_amounts)
        
        This conservative approach accounts for the risk that unsettled invoices may not be collected
        """
        realized_profit = ProfitCalculationService.calculate_realized_profit(start_date, end_date)
        
        # Get total unsettled invoice amounts (collection risk)
        unsettled_amount = Invoice.objects.filter(
            status__in=['pending', 'partial']
        ).aggregate(total=Sum('balance_due'))['total'] or Decimal('0')
        
        # Calculate spendable profit (conservative approach)
        spendable_profit = realized_profit - unsettled_amount
        
        return spendable_profit
    
    @staticmethod
    def calculate_collection_efficiency(start_date: datetime.date, end_date: datetime.date) -> Decimal:
        """
        Calculate collection efficiency as percentage of settled invoices
        
        Formula: Collection_Efficiency = (settled_invoices / total_invoices) * 100
        """
        invoices_in_period = Invoice.objects.filter(
            invoice_date__date__gte=start_date,
            invoice_date__date__lte=end_date
        )
        
        total_invoices = invoices_in_period.count()
        settled_invoices = invoices_in_period.filter(status='paid').count()
        
        if total_invoices > 0:
            return Decimal(str((settled_invoices / total_invoices) * 100))
        
        return Decimal('0')
    
    @staticmethod
    def generate_financial_summary(
        start_date: datetime.date, 
        end_date: datetime.date,
        period_type: str = 'monthly'
    ) -> Dict:
        """
        Generate comprehensive financial summary for the given period
        """
        # Calculate profit metrics
        realized_profit = ProfitCalculationService.calculate_realized_profit(start_date, end_date)
        unrealized_profit = ProfitCalculationService.calculate_unrealized_profit(start_date, end_date)
        spendable_profit = ProfitCalculationService.calculate_spendable_profit(start_date, end_date)
        collection_efficiency = ProfitCalculationService.calculate_collection_efficiency(start_date, end_date)
        
        # Get invoice metrics
        invoices = Invoice.objects.filter(
            invoice_date__date__gte=start_date,
            invoice_date__date__lte=end_date
        )
        
        total_invoices = invoices.count()
        settled_invoices = invoices.filter(status='paid').count()
        unsettled_invoices = invoices.filter(status__in=['pending', 'partial']).count()
        
        # Get amount metrics
        invoice_totals = invoices.aggregate(
            total_amount=Sum('net_total'),
            settled_amount=Sum('paid_amount'),
        )
        
        invoice_total_amount = invoice_totals['total_amount'] or Decimal('0')
        settled_amount = invoice_totals['settled_amount'] or Decimal('0')
        unsettled_amount = invoice_total_amount - settled_amount
        
        # Get income and expense metrics
        income_total = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            category__transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expense_total = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            category__transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Get commission metrics
        commission_records = CommissionRecord.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        commission_total = commission_records.aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
        commission_paid = commission_records.filter(status='paid').aggregate(total=Sum('commission_amount'))['total'] or Decimal('0')
        commission_pending = commission_total - commission_paid
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'type': period_type
            },
            'invoice_metrics': {
                'total_invoices': total_invoices,
                'settled_invoices': settled_invoices,
                'unsettled_invoices': unsettled_invoices,
                'invoice_total_amount': float(invoice_total_amount),
                'settled_amount': float(settled_amount),
                'unsettled_amount': float(unsettled_amount),
            },
            'profit_metrics': {
                'realized_profit': float(realized_profit),
                'unrealized_profit': float(unrealized_profit),
                'spendable_profit': float(spendable_profit),
                'total_potential_profit': float(realized_profit + unrealized_profit),
            },
            'financial_transactions': {
                'additional_income': float(income_total),
                'expenses': float(expense_total),
                'net_adjustments': float(income_total - expense_total),
            },
            'commission_metrics': {
                'commission_total': float(commission_total),
                'commission_paid': float(commission_paid),
                'commission_pending': float(commission_pending),
            },
            'efficiency_metrics': {
                'collection_efficiency': float(collection_efficiency),
            }
        }
    
    @staticmethod
    def get_realized_profit_breakdown(start_date: datetime.date, end_date: datetime.date) -> Dict:
        """
        Get detailed breakdown of realized profit components
        """
        # Get settlements in date range
        settlements = InvoiceSettlement.objects.filter(
            settlement_date__date__gte=start_date,
            settlement_date__date__lte=end_date
        ).select_related('invoice', 'invoice__shop', 'invoice__salesman__user')
        
        # Settlement details
        settlement_details = []
        total_cash_from_settlements = Decimal('0')
        
        for settlement in settlements:
            total_cash_from_settlements += settlement.total_amount
            settlement_details.append({
                'settlement_id': settlement.id,
                'invoice_number': settlement.invoice.invoice_number,
                'shop_name': settlement.invoice.shop.name,
                'settlement_date': settlement.settlement_date.date(),
                'amount': settlement.total_amount,
                'profit_portion': settlement.total_amount  # Assuming full amount is profit for now
            })
        
        # Commission details
        settled_invoice_ids = settlements.values_list('invoice_id', flat=True)
        commissions = Commission.objects.filter(
            invoice_id__in=settled_invoice_ids,
            status='paid',
            paid_date__date__gte=start_date,
            paid_date__date__lte=end_date
        ).select_related('salesman__user')
        
        commission_details = []
        total_commissions_paid = Decimal('0')
        
        for commission in commissions:
            total_commissions_paid += commission.commission_amount
            commission_details.append({
                'commission_id': commission.id,
                'salesman_name': f"{commission.salesman.user.first_name} {commission.salesman.user.last_name}",
                'invoice_number': commission.invoice.invoice_number,
                'amount': commission.commission_amount,
                'payment_date': commission.paid_date.date() if commission.paid_date else None
            })
        
        # Additional income
        additional_income_transactions = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            category__transaction_type='income'
        ).select_related('category')
        
        additional_income_details = []
        total_additional_income = Decimal('0')
        
        for transaction in additional_income_transactions:
            total_additional_income += transaction.amount
            additional_income_details.append({
                'transaction_id': transaction.id,
                'description': transaction.description,
                'category': transaction.category.name,
                'amount': transaction.amount,
                'date': transaction.transaction_date
            })
        
        # Expenses
        expense_transactions = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            category__transaction_type='expense'
        ).select_related('category')
        
        expense_details = []
        total_expenses = Decimal('0')
        
        for transaction in expense_transactions:
            total_expenses += transaction.amount
            expense_details.append({
                'transaction_id': transaction.id,
                'description': transaction.description,
                'category': transaction.category.name,
                'amount': transaction.amount,
                'date': transaction.transaction_date
            })
        
        # Calculate realized profit
        realized_profit = (
            total_cash_from_settlements - 
            total_commissions_paid - 
            total_expenses + 
            total_additional_income
        )
        
        return {
            'cash_from_settlements': {
                'total': total_cash_from_settlements,
                'details': settlement_details
            },
            'commissions_paid': {
                'total': total_commissions_paid,
                'details': commission_details
            },
            'additional_income': {
                'total': total_additional_income,
                'details': additional_income_details
            },
            'expenses': {
                'total': total_expenses,
                'details': expense_details
            },
            'realized_profit': realized_profit,
            'calculation_date': timezone.now().date(),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
    
    @staticmethod
    def get_unrealized_profit_breakdown(start_date: datetime.date, end_date: datetime.date) -> Dict:
        """
        Get detailed breakdown of unrealized profit components
        """
        # Get unsettled invoices
        unsettled_invoices = Invoice.objects.filter(
            invoice_date__date__gte=start_date,
            invoice_date__date__lte=end_date,
            status__in=['pending', 'partial']
        ).select_related('shop', 'salesman__user')
        
        # Outstanding invoice details
        outstanding_details = []
        total_outstanding = Decimal('0')
        
        for invoice in unsettled_invoices:
            if invoice.balance_due > 0:
                days_outstanding = (timezone.now().date() - invoice.invoice_date.date()).days
                total_outstanding += invoice.balance_due
                outstanding_details.append({
                    'invoice_id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'shop_name': invoice.shop.name,
                    'invoice_date': invoice.invoice_date.date(),
                    'amount_due': invoice.balance_due,
                    'days_outstanding': days_outstanding,
                    'estimated_profit': invoice.balance_due  # Simplified - assuming full amount is profit
                })
        
        # Estimated commissions
        estimated_commissions = Commission.objects.filter(
            invoice__in=unsettled_invoices,
            status__in=['pending', 'calculated']
        ).select_related('salesman__user', 'invoice')
        
        commission_details = []
        total_estimated_commissions = Decimal('0')
        
        for commission in estimated_commissions:
            total_estimated_commissions += commission.commission_amount
            commission_details.append({
                'commission_id': commission.id,
                'salesman_name': f"{commission.salesman.user.first_name} {commission.salesman.user.last_name}",
                'invoice_number': commission.invoice.invoice_number,
                'estimated_amount': commission.commission_amount,
                'status': commission.status
            })
        
        # For invoices without commission records, estimate
        invoices_with_commissions = set(estimated_commissions.values_list('invoice_id', flat=True))
        invoices_without_commissions = [inv for inv in unsettled_invoices if inv.id not in invoices_with_commissions]
        
        additional_estimated_commissions = Decimal('0')
        for invoice in invoices_without_commissions:
            if invoice.balance_due > 0:
                estimated_comm = invoice.balance_due * Decimal('0.05')  # 5% default
                additional_estimated_commissions += estimated_comm
                commission_details.append({
                    'commission_id': None,
                    'salesman_name': f"{invoice.salesman.user.first_name} {invoice.salesman.user.last_name}",
                    'invoice_number': invoice.invoice_number,
                    'estimated_amount': estimated_comm,
                    'status': 'estimated'
                })
        
        total_estimated_commissions += additional_estimated_commissions
        
        # Calculate unrealized profit
        unrealized_profit = total_outstanding - total_estimated_commissions
        
        # Collection efficiency calculation
        collection_efficiency = ProfitCalculationService.calculate_collection_efficiency(start_date, end_date)
        
        return {
            'outstanding_invoices': {
                'total': total_outstanding,
                'count': len(outstanding_details),
                'details': outstanding_details
            },
            'estimated_commissions': {
                'total': total_estimated_commissions,
                'details': commission_details
            },
            'unrealized_profit': unrealized_profit,
            'collection_efficiency': collection_efficiency,
            'expected_collections': total_outstanding * (collection_efficiency / 100),
            'potential_bad_debt': total_outstanding * (1 - collection_efficiency / 100),
            'calculation_date': timezone.now().date(),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
    
    @staticmethod
    def get_spendable_profit_analysis() -> Dict:
        """
        Get detailed analysis of spendable profit with risk assessment
        """
        today = timezone.now().date()
        start_date = today.replace(day=1)  # Start of current month
        
        realized_profit = ProfitCalculationService.calculate_realized_profit(start_date, today)
        
        # Get all outstanding invoices (regardless of date)
        outstanding_invoices = Invoice.objects.filter(
            status__in=['pending', 'partial']
        )
        
        total_outstanding = outstanding_invoices.aggregate(
            total=Sum('balance_due')
        )['total'] or Decimal('0')
        
        # Risk assessment based on age of invoices
        high_risk_amount = Decimal('0')
        medium_risk_amount = Decimal('0')
        low_risk_amount = Decimal('0')
        
        for invoice in outstanding_invoices:
            if invoice.balance_due > 0:
                days_outstanding = (today - invoice.invoice_date.date()).days
                
                if days_outstanding > 90:
                    high_risk_amount += invoice.balance_due
                elif days_outstanding > 30:
                    medium_risk_amount += invoice.balance_due
                else:
                    low_risk_amount += invoice.balance_due
        
        # Calculate conservative spendable amount
        spendable_profit = realized_profit - total_outstanding
        
        # Risk-adjusted spendable profit (conservative approach)
        risk_adjusted_spendable = realized_profit - (high_risk_amount * Decimal('0.5')) - (medium_risk_amount * Decimal('0.2'))
        
        # Determine risk level
        if spendable_profit < 0:
            risk_level = 'high'
        elif total_outstanding > realized_profit * 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Recommended cash reserve (20% of monthly expenses)
        monthly_expenses = FinancialTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=today,
            category__transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        recommended_reserve = monthly_expenses * Decimal('0.2')
        
        return {
            'realized_profit': realized_profit,
            'outstanding_invoice_risk': total_outstanding,
            'spendable_profit': spendable_profit,
            'risk_adjusted_spendable': risk_adjusted_spendable,
            'risk_assessment': {
                'level': risk_level,
                'high_risk_invoices': high_risk_amount,
                'medium_risk_invoices': medium_risk_amount,
                'low_risk_invoices': low_risk_amount
            },
            'recommended_cash_reserve': recommended_reserve,
            'safe_to_spend_amount': max(Decimal('0'), risk_adjusted_spendable - recommended_reserve),
            'calculation_date': today
        }


class DescriptionSuggestionService:
    """Service for managing transaction description suggestions"""
    
    @staticmethod
    def get_suggestions(query: str, category_id: Optional[int] = None, limit: int = 10) -> list:
        """Get description suggestions based on partial query"""
        if len(query) < 2:
            return []
        
        suggestions = DescriptionSuggestion.objects.filter(
            description__icontains=query
        )
        
        if category_id:
            suggestions = suggestions.filter(category_id=category_id)
        
        suggestions = suggestions.order_by('-frequency', '-last_used')[:limit]
        
        return [s.description for s in suggestions]
    
    @staticmethod
    def update_suggestion(description: str, category_id: int):
        """Update or create description suggestion"""
        suggestion, created = DescriptionSuggestion.objects.get_or_create(
            description=description,
            defaults={
                'category_id': category_id,
                'frequency': 1
            }
        )
        
        if not created:
            suggestion.frequency += 1
            suggestion.category_id = category_id  # Update category in case it changed
            suggestion.save()


class CommissionCalculationService:
    """Service for calculating and managing commissions"""
    
    @staticmethod
    def calculate_commission_for_settlement(
        settlement: InvoiceSettlement,
        commission_rate: Decimal = Decimal('5.0'),
        calculation_basis: str = 'cash_collected'
    ) -> Decimal:
        """
        Calculate commission for a specific settlement
        """
        if calculation_basis == 'cash_collected':
            # Commission based on actual cash collected
            commission_amount = settlement.total_amount * (commission_rate / 100)
        elif calculation_basis == 'total_sales':
            # Commission based on total invoice amount
            commission_amount = settlement.invoice.net_total * (commission_rate / 100)
        elif calculation_basis == 'profit_margin':
            # Commission based on profit margin (simplified calculation)
            # Assuming 20% profit margin for now
            profit_margin = settlement.total_amount * Decimal('0.2')
            commission_amount = profit_margin * (commission_rate / 100)
        else:
            commission_amount = Decimal('0')
        
        return commission_amount
    
    @staticmethod
    def create_commission_record(
        settlement: InvoiceSettlement,
        commission_rate: Decimal = Decimal('5.0'),
        calculation_basis: str = 'cash_collected',
        created_by = None
    ) -> CommissionRecord:
        """
        Create a commission record for a settlement
        """
        commission_amount = CommissionCalculationService.calculate_commission_for_settlement(
            settlement, commission_rate, calculation_basis
        )
        
        commission_record = CommissionRecord.objects.create(
            invoice=settlement.invoice,
            settlement=settlement,
            salesman=settlement.invoice.salesman,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            calculation_basis=calculation_basis,
            status='calculated',
            created_by=created_by
        )
        
        return commission_record
