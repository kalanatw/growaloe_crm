from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from sales.models import Invoice, InvoiceSettlement
from core.models import FinancialTransaction


class Command(BaseCommand):
    help = 'Populate financial transactions from existing invoices and settlements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing financial transactions before populating',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_existing = options['clear']

        if clear_existing and not dry_run:
            self.stdout.write('Clearing existing financial transactions...')
            FinancialTransaction.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing financial transactions'))

        # Get all invoices and settlements
        invoices = Invoice.objects.all().order_by('created_at')
        settlements = InvoiceSettlement.objects.all().order_by('created_at')

        self.stdout.write(f'Found {invoices.count()} invoices and {settlements.count()} settlements')

        transactions_to_create = []
        
        # Create debit transactions for invoices (money owed to us)
        for invoice in invoices:
            transaction_data = {
                'transaction_type': 'debit',
                'date': invoice.created_at.date(),
                'description': f'Invoice {invoice.invoice_number} - {invoice.shop.name}',
                'amount': invoice.net_total,
                'category': 'invoice_created',
                'reference_number': invoice.invoice_number,
                'invoice_id': invoice.invoice_number,
                'notes': f'Created from invoice to {invoice.shop.name}',
                'created_by': invoice.created_by,
            }
            transactions_to_create.append(transaction_data)

        # Create credit transactions for settlements (money received)
        for settlement in settlements:
            transaction_data = {
                'transaction_type': 'credit',
                'date': settlement.settlement_date.date(),
                'description': f'Payment for Invoice {settlement.invoice.invoice_number} - {settlement.invoice.shop.name}',
                'amount': settlement.total_amount,
                'category': 'invoice_settlement',
                'reference_number': settlement.invoice.invoice_number,
                'invoice_id': settlement.invoice.invoice_number,
                'notes': f'Payment received from {settlement.invoice.shop.name}',
                'created_by': settlement.created_by,
            }
            transactions_to_create.append(transaction_data)

        # Display summary
        total_debits = sum(t['amount'] for t in transactions_to_create if t['transaction_type'] == 'debit')
        total_credits = sum(t['amount'] for t in transactions_to_create if t['transaction_type'] == 'credit')
        net_balance = total_credits - total_debits

        self.stdout.write('\n' + '='*50)
        self.stdout.write('TRANSACTION SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Invoices (Debits): {len([t for t in transactions_to_create if t["transaction_type"] == "debit"])} transactions')
        self.stdout.write(f'Settlements (Credits): {len([t for t in transactions_to_create if t["transaction_type"] == "credit"])} transactions')
        self.stdout.write(f'Total Debits: ${total_debits:,.2f}')
        self.stdout.write(f'Total Credits: ${total_credits:,.2f}')
        self.stdout.write(f'Net Balance (Profit): ${net_balance:,.2f}')
        self.stdout.write('='*50)

        if dry_run:
            self.stdout.write('\nDRY RUN - No transactions were created')
            self.stdout.write('Sample transactions:')
            for i, trans in enumerate(transactions_to_create[:5]):
                self.stdout.write(f'{i+1}. {trans["date"]} - {trans["transaction_type"].upper()} - {trans["description"]} - ${trans["amount"]}')
            if len(transactions_to_create) > 5:
                self.stdout.write(f'... and {len(transactions_to_create) - 5} more transactions')
        else:
            # Create the transactions
            self.stdout.write(f'\nCreating {len(transactions_to_create)} financial transactions...')
            
            with transaction.atomic():
                for trans_data in transactions_to_create:
                    FinancialTransaction.objects.create(**trans_data)

            self.stdout.write(self.style.SUCCESS(f'Successfully created {len(transactions_to_create)} financial transactions'))

        # Show final counts
        if not dry_run:
            total_count = FinancialTransaction.objects.count()
            debit_count = FinancialTransaction.objects.filter(transaction_type='debit').count()
            credit_count = FinancialTransaction.objects.filter(transaction_type='credit').count()
            
            self.stdout.write(f'\nFinal database state:')
            self.stdout.write(f'Total financial transactions: {total_count}')
            self.stdout.write(f'Debit transactions: {debit_count}')
            self.stdout.write(f'Credit transactions: {credit_count}')
