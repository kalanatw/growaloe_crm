from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Batch, BatchTransaction, BatchAssignment, Delivery, DeliveryItem
from sales.models import InvoiceItem, Invoice


class Command(BaseCommand):
    help = 'Clear all stock-related data to start fresh with batch system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm you want to delete all stock data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete ALL stock data including:\n'            '- All batches and batch transactions\n'
            '- All batch assignments\n'
            '- All central stock records\n'
            '- All invoice items and invoices\n'
            '- All deliveries and delivery items\n\n'
                    'Run with --confirm to proceed.'
                )
            )
            return

        self.stdout.write('Starting to clear all stock data...')

        with transaction.atomic():
            # Count records before deletion
            batch_count = Batch.objects.count()
            batch_transaction_count = BatchTransaction.objects.count()
            batch_assignment_count = BatchAssignment.objects.count()
            invoice_item_count = InvoiceItem.objects.count()
            invoice_count = Invoice.objects.count()
            delivery_item_count = DeliveryItem.objects.count()
            delivery_count = Delivery.objects.count()

            # Delete in correct order to respect foreign key constraints
            self.stdout.write('Deleting invoice items...')
            InvoiceItem.objects.all().delete()

            self.stdout.write('Deleting invoices...')
            Invoice.objects.all().delete()

            self.stdout.write('Deleting delivery items...')
            DeliveryItem.objects.all().delete()

            self.stdout.write('Deleting deliveries...')
            Delivery.objects.all().delete()

            self.stdout.write('Deleting batch assignments...')
            BatchAssignment.objects.all().delete()

            self.stdout.write('Deleting batch transactions...')
            BatchTransaction.objects.all().delete()

            self.stdout.write('Deleting batches...')
            Batch.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleared all stock data:\n'
                    f'- {batch_count} batches deleted\n'
                    f'- {batch_transaction_count} batch transactions deleted\n'
                    f'- {batch_assignment_count} batch assignments deleted\n'
                    f'- {invoice_item_count} invoice items deleted\n'
                    f'- {invoice_count} invoices deleted\n'
                    f'- {delivery_item_count} delivery items deleted\n'
                    f'- {delivery_count} deliveries deleted\n'
                    '\nYou can now start fresh with the batch system!'
                )
            )
