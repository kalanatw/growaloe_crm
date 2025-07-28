from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
import logging

from .models import InvoiceSettlement
from accounts.models import SalesmanCashTransaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=InvoiceSettlement)
def update_salesman_balance_on_settlement(sender, instance, created, **kwargs):
    """
    Automatically update salesman balance when invoice settlements are created
    """
    if created and instance.invoice and instance.invoice.salesman:
        salesman = instance.invoice.salesman
        amount = instance.total_amount
        
        try:
            with transaction.atomic():
                # Get current balance before update
                balance_before = salesman.current_balance
                
                # Update salesman balance
                salesman.total_cash_collected += amount
                salesman.current_balance += amount
                salesman.save()
                
                # Create cash transaction record for audit trail
                SalesmanCashTransaction.objects.create(
                    salesman=salesman,
                    transaction_type='collection',
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=salesman.current_balance,
                    reference_type='invoice_settlement',
                    reference_id=str(instance.id),
                    invoice=instance.invoice,
                    description=f'Auto-updated from invoice {instance.invoice.invoice_number} settlement',
                    notes=f'Settlement ID: {instance.id}',
                    created_by=instance.created_by
                )
                
                logger.info(f"Signal: Updated salesman {salesman.user.get_full_name()} balance: "
                           f"collected LKR {amount}, new balance: LKR {salesman.current_balance}")
                
        except Exception as e:
            logger.error(f"Signal: Error updating salesman balance for transaction {instance.id}: {str(e)}")
            import traceback
            logger.error(f"Signal: Full traceback: {traceback.format_exc()}")