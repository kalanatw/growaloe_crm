from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Invoice, Commission


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
