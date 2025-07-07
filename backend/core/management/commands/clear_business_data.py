from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    help = 'Clear all business data (products, batches, invoices, sales, etc.) while keeping user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all business data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete ALL business data while keeping user accounts.\n'
                    'This includes:\n'
                    '- Products and Categories\n'
                    '- Batches and Stock\n'
                    '- Invoices and Sales\n'
                    '- Deliveries and Assignments\n'
                    '- Reports and Metrics\n'
                    '- Company Settings\n'
                    '- Returns and Defects\n\n'
                    'User accounts (Owner, Salesman, Shop, User) will be preserved.\n\n'
                    'Run the command with --confirm to proceed.'
                )
            )
            return

        self.stdout.write('Starting business data cleanup...')
        
        with transaction.atomic():
            try:
                # Delete data in proper order to avoid foreign key constraints
                
                # 1. Sales-related data
                self.delete_model_data('sales', 'Return')
                self.delete_model_data('sales', 'Payment')
                self.delete_model_data('sales', 'InvoiceItem')
                self.delete_model_data('sales', 'Invoice')
                
                # 2. Products-related data (batches, deliveries, etc.)
                self.delete_model_data('products', 'BatchDefect')
                self.delete_model_data('products', 'BatchTransaction')
                self.delete_model_data('products', 'BatchAssignment')
                self.delete_model_data('products', 'DeliveryItem')
                self.delete_model_data('products', 'Delivery')
                self.delete_model_data('products', 'Batch')
                self.delete_model_data('products', 'StockMovement')
                self.delete_model_data('products', 'Product')
                self.delete_model_data('products', 'Category')
                
                # 3. Reports and metrics
                self.delete_model_data('reports', 'SalesReport')
                self.delete_model_data('reports', 'DashboardMetrics')
                
                # 4. Core business settings (but keep user accounts)
                self.delete_model_data('core', 'CompanySettings')
                self.delete_model_data('core', 'AuditLog')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        'Successfully cleared all business data!\n'
                        'User accounts have been preserved.\n'
                        'You can now start testing the batch-centric flow with a clean database.'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error occurred during cleanup: {str(e)}')
                )
                raise

    def delete_model_data(self, app_label, model_name):
        """Delete all instances of a specific model"""
        try:
            model = apps.get_model(app_label, model_name)
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                self.stdout.write(f'  ✓ Deleted {count} {model_name} records')
            else:
                self.stdout.write(f'  - No {model_name} records to delete')
        except LookupError:
            # Model doesn't exist, skip
            self.stdout.write(f'  - Model {app_label}.{model_name} not found, skipping')
        except Exception as e:
            self.stdout.write(f'  ✗ Error deleting {model_name}: {str(e)}')
            raise
