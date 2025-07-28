from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import Salesman, SalesmanCashTransaction


class SalesmanBalanceService:
    """Service class for managing salesman cash balance operations"""
    
    @staticmethod
    def record_cash_collection(salesman, invoice, amount, payment_method='cash', notes='', created_by=None):
        """Record cash collection from customer invoice settlement"""
        with transaction.atomic():
            # Get current balance
            current_balance = salesman.current_balance
            amount = Decimal(str(amount))
            
            # Update salesman balance (increase cash collected)
            new_balance = current_balance + amount
            
            # Create cash transaction record
            cash_transaction = SalesmanCashTransaction.objects.create(
                salesman=salesman,
                transaction_type='collection',
                amount=amount,
                balance_before=current_balance,
                balance_after=new_balance,
                reference_type='invoice',
                reference_id=invoice.invoice_number,
                invoice=invoice,
                description=f"Cash collection from {invoice.shop.name} - Invoice {invoice.invoice_number}",
                notes=notes,
                created_by=created_by
            )
            
            # Update salesman totals
            salesman.current_balance = new_balance
            salesman.total_cash_collected += amount
            salesman.save()
            
            return cash_transaction
    
    @staticmethod
    def record_expense(salesman, amount, description, reference_type=None, reference_id=None, notes='', created_by=None):
        """Record delivery expense that reduces available cash"""
        with transaction.atomic():
            current_balance = salesman.current_balance
            amount = Decimal(str(amount))
            
            # Expenses reduce the available cash (negative impact on balance)
            new_balance = current_balance - amount
            
            # Create expense transaction record
            cash_transaction = SalesmanCashTransaction.objects.create(
                salesman=salesman,
                transaction_type='expense',
                amount=-amount,  # Negative because it reduces available cash
                balance_before=current_balance,
                balance_after=new_balance,
                reference_type=reference_type,
                reference_id=reference_id,
                description=description,
                notes=notes,
                created_by=created_by
            )
            
            # Update salesman balance
            salesman.current_balance = new_balance
            salesman.save()
            
            return cash_transaction
    
    @staticmethod
    def calculate_settlement_cash_flow(salesman):
        """Calculate cash flow for settlement"""
        # Get the last settlement date or use a very old date if never settled
        from datetime import timezone as dt_timezone
        last_settlement = salesman.last_settlement_date or timezone.datetime.min.replace(tzinfo=dt_timezone.utc)
        
        # Get all unsettled cash collections
        collections = SalesmanCashTransaction.objects.filter(
            salesman=salesman,
            transaction_type='collection',
            created_at__gt=last_settlement
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get delivery expenses since last settlement
        expenses = SalesmanCashTransaction.objects.filter(
            salesman=salesman,
            transaction_type='expense',
            created_at__gt=last_settlement
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Expenses are stored as negative values, so we need to make them positive for display
        expenses = abs(expenses)
        
        # Calculate net cash available for settlement
        net_cash_available = collections - expenses
        
        return {
            'total_collections': collections,
            'total_expenses': expenses,
            'net_cash_available': net_cash_available,
            'current_balance': salesman.current_balance,
            'last_settlement_date': last_settlement
        }
    
    @staticmethod
    def settle_salesman_cash(salesman, settlement_amount, settlement_notes='', created_by=None):
        """Settle cash with salesman during delivery settlement"""
        with transaction.atomic():
            current_balance = salesman.current_balance
            settlement_amount = Decimal(str(settlement_amount))
            
            # Calculate new balance after settlement
            new_balance = current_balance - settlement_amount
            
            # Create settlement transaction
            cash_transaction = SalesmanCashTransaction.objects.create(
                salesman=salesman,
                transaction_type='settlement',
                amount=-settlement_amount,  # Negative because cash is leaving salesman
                balance_before=current_balance,
                balance_after=new_balance,
                reference_type='delivery_settlement',
                description=f"Cash settlement with owner - Amount: {settlement_amount}",
                notes=settlement_notes,
                created_by=created_by
            )
            
            # Update salesman balance
            salesman.current_balance = new_balance
            salesman.total_cash_settled += settlement_amount
            salesman.last_settlement_date = timezone.now()
            salesman.save()
            
            return cash_transaction
    
    @staticmethod
    def get_salesman_cash_summary(salesman, days=30):
        """Get cash flow summary for salesman"""
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = SalesmanCashTransaction.objects.filter(
            salesman=salesman,
            created_at__gte=start_date
        )
        
        collections = transactions.filter(transaction_type='collection').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        settlements = transactions.filter(transaction_type='settlement').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        expenses = transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        summary = {
            'total_collections': collections,
            'total_settlements': abs(settlements),  # Make positive for display
            'total_expenses': abs(expenses),  # Make positive for display
            'current_balance': salesman.current_balance,
            'net_cash_position': salesman.net_cash_position,
            'transaction_count': transactions.count(),
            'period_days': days
        }
        
        return summary
    
    @staticmethod
    def get_cash_transaction_history(salesman, limit=50):
        """Get recent cash transaction history for salesman"""
        transactions = SalesmanCashTransaction.objects.filter(
            salesman=salesman
        ).select_related('invoice', 'created_by')[:limit]
        
        return transactions
    
    @staticmethod
    def validate_settlement_amount(salesman, settlement_amount):
        """Validate if settlement amount is valid"""
        cash_flow = SalesmanBalanceService.calculate_settlement_cash_flow(salesman)
        settlement_amount = Decimal(str(settlement_amount))
        
        if settlement_amount < 0:
            return False, "Settlement amount cannot be negative"
        
        if settlement_amount > cash_flow['net_cash_available']:
            return False, f"Settlement amount ({settlement_amount}) exceeds available cash ({cash_flow['net_cash_available']})"
        
        return True, "Valid settlement amount"
    
    @staticmethod
    def record_advance_payment(salesman, amount, notes='', created_by=None):
        """Record advance payment from owner to salesman"""
        with transaction.atomic():
            current_balance = salesman.current_balance
            amount = Decimal(str(amount))
            
            # Advance reduces the salesman's debt to owner (or increases owner's debt to salesman)
            new_balance = current_balance - amount
            
            # Create advance transaction record
            cash_transaction = SalesmanCashTransaction.objects.create(
                salesman=salesman,
                transaction_type='advance',
                amount=-amount,  # Negative because it reduces salesman's debt
                balance_before=current_balance,
                balance_after=new_balance,
                reference_type='advance_payment',
                description=f"Advance payment from owner - Amount: {amount}",
                notes=notes,
                created_by=created_by
            )
            
            # Update salesman balance
            salesman.current_balance = new_balance
            salesman.save()
            
            return cash_transaction
    
    @staticmethod
    def record_balance_adjustment(salesman, amount, reason, notes='', created_by=None):
        """Record manual balance adjustment"""
        with transaction.atomic():
            current_balance = salesman.current_balance
            amount = Decimal(str(amount))
            
            new_balance = current_balance + amount
            
            # Create adjustment transaction record
            cash_transaction = SalesmanCashTransaction.objects.create(
                salesman=salesman,
                transaction_type='adjustment',
                amount=amount,
                balance_before=current_balance,
                balance_after=new_balance,
                reference_type='manual_adjustment',
                description=f"Balance adjustment: {reason}",
                notes=notes,
                created_by=created_by
            )
            
            # Update salesman balance
            salesman.current_balance = new_balance
            salesman.save()
            
            return cash_transaction