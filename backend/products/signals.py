from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.utils import timezone
from .models import Product, DeliveryItem, Delivery, BatchAssignment, Batch
from sales.models import InvoiceItem, Invoice


@receiver(pre_save, sender=InvoiceItem)
def validate_invoice_item_stock(sender, instance, **kwargs):
    """
    Validate that there's enough stock before saving an invoice item using batch system
    """
    # Skip validation for draft invoices
    if instance.invoice.status == 'draft':
        return
    
    # Skip validation if this is an update and quantity didn't change
    if instance.pk:
        try:
            old_instance = InvoiceItem.objects.get(pk=instance.pk)
            if old_instance.quantity == instance.quantity:
                return
        except InvoiceItem.DoesNotExist:
            pass
    
    # Check salesman stock availability using batch assignments
    try:
        # Get total available quantity from batch assignments
        assignments = BatchAssignment.objects.filter(
            salesman=instance.invoice.salesman,
            batch__product=instance.product,
            status__in=['delivered', 'partial'],
            batch__is_active=True
        ).exclude(
            batch__expiry_date__lt=timezone.now().date()
        ).annotate(
            available_qty=F('delivered_quantity') - F('returned_quantity')
        ).filter(available_qty__gt=0)
        
        total_available = sum(assignment.available_qty for assignment in assignments)
        
        if total_available == 0:
            raise ValidationError(
                f"No stock allocation found for {instance.product.name} "
                f"for salesman {instance.invoice.salesman.name}"
            )
        
        required_quantity = instance.quantity
        if instance.pk:
            # If updating, only check the difference
            old_instance = InvoiceItem.objects.get(pk=instance.pk)
            required_quantity = instance.quantity - old_instance.quantity
        
        if required_quantity > 0 and total_available < required_quantity:
            raise ValidationError(
                f"Insufficient stock for {instance.product.name}. "
                f"Available: {total_available}, Required: {required_quantity}"
            )
    except Exception as e:
        # Handle any other database errors gracefully
        raise ValidationError(
            f"Error checking stock for {instance.product.name}: {str(e)}"
        )


@receiver(pre_save, sender=DeliveryItem)
def validate_delivery_item_stock(sender, instance, **kwargs):
    """
    Validate that there's enough owner stock before creating/updating a delivery
    """
    # Only validate when delivery is being marked as delivered
    if instance.delivery.status != 'delivered':
        return
    
    required_quantity = instance.quantity
    if instance.pk:
        # If updating, only check the difference
        try:
            old_instance = DeliveryItem.objects.get(pk=instance.pk)
            required_quantity = instance.quantity - old_instance.quantity
        except DeliveryItem.DoesNotExist:
            pass
    
    if required_quantity > 0:
        # Check owner stock using available batches
        available_batches = Batch.objects.filter(
            product=instance.product,
            is_active=True,
            current_quantity__gt=0
        ).order_by('manufacturing_date', 'expiry_date')
        
        total_available = sum(batch.current_quantity for batch in available_batches)
        
        if total_available < required_quantity:
            raise ValidationError(
                f"Insufficient stock for {instance.product.name}. "
                f"Available: {total_available}, Required: {required_quantity}"
            )


@receiver(post_save, sender=Delivery)
def update_delivery_stock_on_status_change(sender, instance, created, **kwargs):
    """
    Update stock allocations when delivery status changes to 'delivered'
    """
    if not created and instance.status == 'delivered':
        # Stock allocation is now handled by batch assignments in the serializer
        # This signal is kept for potential future batch assignment logic
        pass


@receiver(pre_save, sender=Invoice)
def validate_invoice_stock_before_status_change(sender, instance, **kwargs):
    """
    Validate stock availability when invoice status changes from draft to active
    """
    if instance.pk:
        try:
            old_instance = Invoice.objects.get(pk=instance.pk)
            # If changing from draft to non-draft, validate all items
            if old_instance.status == 'draft' and instance.status != 'draft':
                for item in instance.items.all():
                    validate_invoice_item_stock(InvoiceItem, item)
        except Invoice.DoesNotExist:
            pass
