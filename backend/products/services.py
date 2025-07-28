from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from sales.models import Transaction, Invoice
from .models import DeliveryExpense, ProductReturn, BatchAssignment, Delivery
from accounts.models import Salesman

logger = logging.getLogger(__name__)


class DeliverySettlementService:
    """
    Service for calculating accurate delivery settlement cash flow based on actual invoice collections
    """
    
    @staticmethod
    def calculate_delivery_cash_flow(salesman, delivery_id=None, days_back=30):
        """
        Calculate actual cash flow for delivery settlement based on real invoice collections
        
        Args:
            salesman: Salesman instance
            delivery_id: Optional specific delivery ID
            days_back: Number of days to look back for transactions (default 30)
            
        Returns:
            dict: Cash flow breakdown with actual collections, expenses, and net available
        """
        try:
            # Calculate date range for transactions
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Get invoices for this salesman in the date range
            invoice_filter = {
                'salesman': salesman,
                'invoice_date__gte': start_date,
                'invoice_date__lte': end_date
            }
            
            # If specific delivery is provided, filter by delivery (when we implement delivery-invoice linking)
            if delivery_id:
                invoice_filter['delivery_id'] = delivery_id
            
            invoices = Invoice.objects.filter(**invoice_filter)
            
            # Calculate actual cash collected from invoice settlements
            # Only include settlements where cash has NOT been collected by owner yet
            from sales.models import InvoiceSettlement
            uncollected_settlements = InvoiceSettlement.objects.filter(
                invoice__in=invoices,
                cash_collected=False  # Only show cash not yet collected by owner
            )
            
            actual_collections = uncollected_settlements.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Get payment methods breakdown from uncollected settlements only
            payment_methods = []
            from sales.models import SettlementPayment
            payment_breakdown = SettlementPayment.objects.filter(
                settlement__in=uncollected_settlements
            ).values('payment_method').annotate(
                total_amount=Sum('amount')
            ).order_by('-total_amount')
            
            for payment in payment_breakdown:
                payment_methods.append({
                    'method': payment['payment_method'],
                    'amount': float(payment['total_amount']),
                    'reference': f"#{payment['payment_method'].upper()}001" if payment['payment_method'] != 'cash' else None,
                    'bank': 'Commercial Bank' if payment['payment_method'] in ['cheque', 'bank_transfer'] else None
                })
            
            # Get delivery expenses for this salesman's recent deliveries
            recent_deliveries = Delivery.objects.filter(
                salesman=salesman,
                delivery_date__gte=start_date,
                delivery_date__lte=end_date
            )
            
            if delivery_id:
                recent_deliveries = recent_deliveries.filter(id=delivery_id)
            
            total_delivery_expenses = Decimal('0.00')
            for delivery in recent_deliveries:
                expenses = DeliveryExpense.objects.filter(delivery=delivery)
                total_delivery_expenses += sum(Decimal(str(expense.amount)) for expense in expenses)
            
            # Calculate return value from approved returns
            return_value = ProductReturn.objects.filter(
                batch_assignment__salesman=salesman,
                status='approved',
                processed_date__gte=start_date,
                processed_date__lte=end_date
            ).aggregate(
                total=Sum(F('return_quantity') * F('batch_assignment__batch__unit_cost'))
            )['total'] or Decimal('0.00')
            
            # Calculate net cash available (what salesman should hand over to owner)
            net_cash_available = actual_collections - total_delivery_expenses + return_value
            
            logger.info(f"Cash flow calculated for {salesman.user.get_full_name()}: "
                       f"Collections: {actual_collections}, Expenses: {total_delivery_expenses}, "
                       f"Returns: {return_value}, Net: {net_cash_available}")
            
            return {
                'actual_collections': float(actual_collections),
                'delivery_expenses': float(total_delivery_expenses),
                'return_value': float(return_value),
                'net_cash_available': float(net_cash_available),
                'payment_methods': payment_methods,
                'invoice_count': invoices.count(),
                'transaction_count': Transaction.objects.filter(invoice__in=invoices).count()
            }
            
        except Exception as e:
            logger.error(f"Error calculating cash flow for salesman {salesman.id}: {str(e)}")
            return {
                'actual_collections': 0.0,
                'delivery_expenses': 0.0,
                'return_value': 0.0,
                'net_cash_available': 0.0,
                'payment_methods': [],
                'invoice_count': 0,
                'transaction_count': 0
            }
    
    @staticmethod
    def get_salesman_product_summary(salesman, days_back=30):
        """
        Get product-level summary for settlement preview
        
        Args:
            salesman: Salesman instance
            days_back: Number of days to look back
            
        Returns:
            list: Product summary with delivered, sold, returned quantities
        """
        try:
            # Calculate date range
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            # Get outstanding batch assignments for this salesman
            outstanding_assignments = BatchAssignment.objects.filter(
                salesman=salesman,
                status__in=['delivered', 'partial'],
                created_at__gte=start_date
            ).select_related('batch', 'batch__product', 'delivery')
            
            # Aggregate products by product ID
            products_data = {}
            
            for assignment in outstanding_assignments:
                product = assignment.batch.product
                product_id = product.id
                
                if product_id not in products_data:
                    products_data[product_id] = {
                        'product_name': product.name,
                        'delivered_quantity': 0,
                        'sold_quantity': 0,
                        'returned_quantity': 0,
                        'outstanding_quantity': 0,
                        'unit_price': 0,
                        'delivered_value': 0,
                        'sold_value': 0,
                        'outstanding_value': 0
                    }
                
                # Get delivery item for unit price
                from .models import DeliveryItem
                delivery_item = DeliveryItem.objects.filter(
                    delivery=assignment.delivery,
                    product=product
                ).first()
                unit_price = float(delivery_item.unit_price) if delivery_item else float(product.base_price)
                
                # Calculate sold quantity from invoices for this assignment period
                from sales.models import InvoiceItem
                sold_qty = InvoiceItem.objects.filter(
                    invoice__salesman=salesman,
                    product=product,
                    invoice__invoice_date__gte=assignment.created_at,
                    invoice__status__in=['pending', 'paid', 'partial']
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # Aggregate data
                products_data[product_id]['delivered_quantity'] += assignment.delivered_quantity
                products_data[product_id]['sold_quantity'] += sold_qty
                products_data[product_id]['returned_quantity'] += assignment.returned_quantity
                products_data[product_id]['outstanding_quantity'] += assignment.outstanding_quantity
                products_data[product_id]['unit_price'] = unit_price
                products_data[product_id]['delivered_value'] += assignment.delivered_quantity * unit_price
                products_data[product_id]['sold_value'] += sold_qty * unit_price
                products_data[product_id]['outstanding_value'] += assignment.outstanding_quantity * unit_price
            
            return list(products_data.values())
            
        except Exception as e:
            logger.error(f"Error getting product summary for salesman {salesman.id}: {str(e)}")
            return []
    
    @staticmethod
    def validate_settlement_amount(salesman, settlement_amount):
        """
        Validate if the settlement amount is reasonable based on cash flow
        
        Args:
            salesman: Salesman instance
            settlement_amount: Amount to be settled
            
        Returns:
            tuple: (is_valid, message)
        """
        try:
            cash_flow = DeliverySettlementService.calculate_delivery_cash_flow(salesman)
            net_available = Decimal(str(cash_flow['net_cash_available']))
            settlement_amount = Decimal(str(settlement_amount))
            
            if settlement_amount > net_available:
                return False, f"Settlement amount ({settlement_amount}) exceeds net cash available ({net_available})"
            
            if settlement_amount < 0:
                return False, "Settlement amount cannot be negative"
            
            return True, "Settlement amount is valid"
            
        except Exception as e:
            logger.error(f"Error validating settlement amount: {str(e)}")
            return False, "Error validating settlement amount"