from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from products.models import Batch
from sales.models import InvoiceItem


class Command(BaseCommand):
    help = 'Fix batch current quantities based on actual invoice item transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        with transaction.atomic():
            batches = Batch.objects.all()
            
            for batch in batches:
                # Calculate total sold from this batch
                total_sold = InvoiceItem.objects.filter(batch=batch).aggregate(
                    total=Sum('quantity')
                )['total'] or 0
                
                # Calculate what the current quantity should be
                expected_current = batch.initial_quantity - total_sold
                
                # Ensure it doesn't go below 0
                corrected_current = max(0, expected_current)
                
                if batch.current_quantity != corrected_current:
                    self.stdout.write(
                        f'Batch {batch.batch_number}:'
                    )
                    self.stdout.write(
                        f'  Initial: {batch.initial_quantity}, '
                        f'Total sold: {total_sold}, '
                        f'Current: {batch.current_quantity}, '
                        f'Expected: {expected_current}, '
                        f'Corrected: {corrected_current}'
                    )
                    
                    if not dry_run:
                        batch.current_quantity = corrected_current
                        batch.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Updated to {corrected_current}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  → Would update to {corrected_current}')
                        )
                else:
                    if not dry_run:
                        self.stdout.write(f'Batch {batch.batch_number}: OK')
            
            if dry_run:
                # Rollback the transaction in dry run mode
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes made'))
            else:
                self.stdout.write(self.style.SUCCESS('Batch quantities fixed successfully!'))
