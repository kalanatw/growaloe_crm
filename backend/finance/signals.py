from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import FinancialTransaction, DescriptionSuggestion, ProfitSummary


@receiver(post_save, sender=FinancialTransaction)
def update_description_suggestions(sender, instance, created, **kwargs):
    """
    Update description suggestions when a new transaction is created.
    """
    if created and instance.description:
        suggestion, created = DescriptionSuggestion.objects.get_or_create(
            description=instance.description,
            category=instance.category,
            defaults={'frequency': 1, 'last_used': timezone.now()}
        )
        if not created:
            suggestion.frequency += 1
            suggestion.last_used = timezone.now()
            suggestion.save(update_fields=['frequency', 'last_used'])


@receiver([post_save, post_delete], sender=FinancialTransaction)
def invalidate_profit_cache(sender, instance, **kwargs):
    """
    Invalidate profit summary cache when transactions are modified.
    This ensures profit calculations remain accurate.
    """
    # You can implement cache invalidation logic here
    # For now, we'll just mark that recalculation is needed
    today = timezone.now().date()
    
    # Update or create today's profit summary to trigger recalculation
    try:
        profit_summary = ProfitSummary.objects.get(
            start_date=today,
            end_date=today,
            period_type='daily'
        )
        profit_summary.save()  # This will trigger recalculation in the service
    except ProfitSummary.DoesNotExist:
        # Will be created when next requested
        pass
