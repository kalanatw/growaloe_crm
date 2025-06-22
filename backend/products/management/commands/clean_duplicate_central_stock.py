from django.core.management.base import BaseCommand
from django.db.models import Count
from products.models import CentralStock


class Command(BaseCommand):
    help = 'Clean up duplicate CentralStock records'

    def handle(self, *args, **options):
        self.stdout.write("Checking for duplicate CentralStock records...")
        
        # Find duplicates
        duplicates = (
            CentralStock.objects
            .values('product', 'location_type', 'location_id')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        total_duplicates = 0
        
        for duplicate in duplicates:
            self.stdout.write(
                f"Found {duplicate['count']} records for "
                f"product_id={duplicate['product']}, "
                f"location_type={duplicate['location_type']}, "
                f"location_id={duplicate['location_id']}"
            )
            
            # Get all records for this combination
            records = CentralStock.objects.filter(
                product_id=duplicate['product'],
                location_type=duplicate['location_type'],
                location_id=duplicate['location_id']
            ).order_by('created_at')
            
            # Keep the first record, sum up quantities from others, then delete duplicates
            first_record = records.first()
            total_quantity = sum(record.quantity for record in records)
            
            # Update the first record with total quantity
            first_record.quantity = total_quantity
            first_record.save()
            
            # Delete the duplicates
            duplicates_to_delete = records.exclude(id=first_record.id)
            count_deleted = duplicates_to_delete.count()
            duplicates_to_delete.delete()
            
            total_duplicates += count_deleted
            self.stdout.write(
                f"  Consolidated {duplicate['count']} records into 1, "
                f"total quantity: {total_quantity}"
            )
        
        if total_duplicates == 0:
            self.stdout.write(
                self.style.SUCCESS("No duplicate CentralStock records found.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleaned up {total_duplicates} duplicate CentralStock records."
                )
            )
