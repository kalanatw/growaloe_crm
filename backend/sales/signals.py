from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
import logging
from .models import Invoice, Commission, InvoiceItem
from products.models import BatchAssignment, Delivery, DeliveryItem

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Invoice)
def create_commission(sender, instance, created, **kwargs):
    """
    Automatically create commission when an invoice is created or updated
    """
    if instance.status != 'draft' and instance.net_total > 0:
        # Calculate commission amount using Decimal arithmetic
        commission_rate = Decimal('10.00')  # Default 10%
        commission_amount = (instance.net_total * commission_rate) / Decimal('100')
        
        # Create or update commission
        commission, commission_created = Commission.objects.get_or_create(
            invoice=instance,
            defaults={
                'salesman': instance.salesman,
                'commission_rate': commission_rate,
                'invoice_amount': instance.net_total,
                'commission_amount': commission_amount,
                'status': 'pending'
            }
        )
        
        # If commission already exists, update the amounts
        if not commission_created:
            commission.invoice_amount = instance.net_total
            commission.commission_amount = (instance.net_total * commission.commission_rate) / Decimal('100')
            commission.save()


@receiver(post_save, sender=InvoiceItem)
def update_delivery_settlement_status(sender, instance, created, **kwargs):
    """
    Update delivery settlement status when invoice items are created/updated.
    This provides real-time integration between invoices and deliveries.
    """
    try:
        # Get the salesman from the invoice
        salesman = instance.invoice.salesman
        product = instance.product
        
        # Find recent deliveries that might contain this product
        from django.utils import timezone
        from datetime import timedelta
        
        # Look for deliveries in the last 30 days
        recent_deliveries = Delivery.objects.filter(
            salesman=salesman,
            status='delivered',
            created_at__gte=timezone.now() - timedelta(days=30)
        ).select_related('salesman')
        
        # Check if any delivery needs settlement status update
        for delivery in recent_deliveries:
            delivery_items = DeliveryItem.objects.filter(
                delivery=delivery,
                product=product
            )
            
            if delivery_items.exists():
                # Calculate total sold for this delivery's products
                total_delivered = sum(item.quantity for item in delivery.items.all())
                
                # Calculate total sold from all invoices since delivery
                from django.db.models import Sum
                total_sold = InvoiceItem.objects.filter(
                    invoice__salesman=salesman,
                    invoice__invoice_date__gte=delivery.created_at,
                    invoice__status__in=['pending', 'paid', 'partial'],
                    product__in=[item.product for item in delivery.items.all()]
                ).aggregate(total=Sum('quantity'))['total'] or 0
                
                # If significant portion is sold, log for owner review
                if total_sold >= total_delivered * 0.8:  # 80% sold
                    logger.info(f"Delivery {delivery.delivery_number} for {salesman.user.get_full_name()} "
                              f"is {((total_sold/total_delivered)*100):.1f}% sold - consider settlement")
                
        logger.debug(f"Processed invoice item update: {instance.product.name} "
                    f"x{instance.quantity} for {salesman.user.get_full_name()}")
        
    except Exception as e:
        logger.error(f"Error processing invoice item update: {str(e)}")


@receiver(post_delete, sender=InvoiceItem)
def handle_invoice_item_deletion(sender, instance, **kwargs):
    """
    Handle invoice item deletion - may affect settlement calculations
    """
    try:
        logger.info(f"Invoice item deleted: {instance.product.name} "
                   f"x{instance.quantity} for {instance.invoice.salesman.user.get_full_name()}")
    except Exception as e:
        logger.error(f"Error handling invoice item deletion: {str(e)}")
