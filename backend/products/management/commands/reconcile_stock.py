from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum, Q
from products.models import (
    Product, Batch, BatchTransaction, BatchAssignment, 
    DeliveryItem, Delivery
)
from collections import defaultdict


class Command(BaseCommand):
    help = 'Reconcile stock quantities and fix inconsistencies between Product.stock_quantity and Batch totals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--fix-duplicates',
            action='store_true',
            help='Remove duplicate batch transactions',
        )
        parser.add_argument(
            '--product-id',
            type=int,
            help='Reconcile specific product by ID',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.fix_duplicates = options['fix_duplicates']
        self.product_id = options.get('product_id')
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Stock Reconciliation Process')
        )
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE: No changes will be made')
            )
        
        try:
            self.run_reconciliation()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during reconciliation: {str(e)}')
            )
            raise

    def run_reconciliation(self):
        """Run the complete reconciliation process"""
        
        # Step 1: Audit current state
        discrepancies = self.audit_stock_quantities()
        
        if not discrepancies:
            self.stdout.write(
                self.style.SUCCESS('✅ No stock discrepancies found!')
            )
            return
        
        # Step 2: Clean duplicates if requested
        if self.fix_duplicates:
            self.clean_duplicate_transactions()
        
        # Step 3: Fix the quantities
        if not self.dry_run:
            self.fix_stock_quantities(discrepancies)
            self.stdout.write(
                self.style.SUCCESS('✅ Stock reconciliation completed!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('DRY RUN: Use without --dry-run to apply fixes')
            )

    def audit_stock_quantities(self):
        """Audit all products and identify discrepancies"""
        self.stdout.write('\n📊 Auditing Stock Quantities...')
        
        if self.product_id:
            products = Product.objects.filter(id=self.product_id)
        else:
            products = Product.objects.all()
        
        discrepancies = []
        
        for product in products:
            # Product's calculated total stock (from properties)
            product_total_stock = product.total_stock
            
            # Sum of batch quantities (direct calculation)
            batch_total = Batch.objects.filter(
                product=product,
                is_active=True
            ).aggregate(total=Sum('current_quantity'))['total'] or 0
            
            # Owner stock (unallocated)
            owner_stock = product.owner_stock
            
            # Available for delivery
            available_for_delivery = self.calculate_available_for_delivery(product)
            
            # Check for discrepancy between calculated total and actual batch sum
            discrepancy = product_total_stock - batch_total
            
            # Also check if there's an issue with available vs owner stock
            availability_issue = abs(available_for_delivery - owner_stock) > 0.01
            
            if abs(discrepancy) > 0.01 or availability_issue:
                discrepancies.append({
                    'product': product,
                    'product_total_stock': product_total_stock,
                    'batch_total': batch_total,
                    'owner_stock': owner_stock,
                    'available_for_delivery': available_for_delivery,
                    'discrepancy': discrepancy,
                    'availability_issue': availability_issue
                })
                
                self.stdout.write(
                    f'⚠️  {product.name} (SKU: {product.sku})'
                )
                self.stdout.write(
                    f'    Product Total Stock: {product_total_stock}'
                )
                self.stdout.write(
                    f'    Batch Total: {batch_total}'
                )
                self.stdout.write(
                    f'    Owner Stock: {owner_stock}'
                )
                self.stdout.write(
                    f'    Available for Delivery: {available_for_delivery}'
                )
                self.stdout.write(
                    f'    Stock Discrepancy: {discrepancy}'
                )
                if availability_issue:
                    self.stdout.write(
                        f'    Availability Issue: Owner({owner_stock}) != Available({available_for_delivery})'
                    )
            else:
                self.stdout.write(
                    f'✅ {product.name}: Stock consistent (Total: {product_total_stock}, Available: {available_for_delivery})'
                )
        
        self.stdout.write(
            f'\n📈 Found {len(discrepancies)} products with stock discrepancies'
        )
        
        return discrepancies

    def calculate_available_for_delivery(self, product):
        """Calculate actual available quantity for delivery"""
        available_batches = Batch.objects.filter(
            product=product,
            is_active=True,
            current_quantity__gt=0
        )
        
        total_available = 0
        for batch in available_batches:
            # Subtract pending allocations
            pending_allocations = BatchAssignment.objects.filter(
                batch=batch,
                status='pending'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            available_in_batch = batch.current_quantity - pending_allocations
            total_available += max(0, available_in_batch)
        
        return total_available

    def clean_duplicate_transactions(self):
        """Remove duplicate batch transactions"""
        self.stdout.write('\n🧹 Cleaning Duplicate Transactions...')
        
        duplicates_removed = 0
        
        if not self.dry_run:
            with transaction.atomic():
                for batch in Batch.objects.filter(is_active=True):
                    duplicates_removed += self.remove_batch_duplicates(batch)
        else:
            for batch in Batch.objects.filter(is_active=True):
                duplicates_removed += self.count_batch_duplicates(batch)
        
        self.stdout.write(
            f'🗑️  {"Would remove" if self.dry_run else "Removed"} {duplicates_removed} duplicate transactions'
        )

    def remove_batch_duplicates(self, batch):
        """Remove duplicate transactions for a specific batch"""
        transactions = BatchTransaction.objects.filter(
            batch=batch,
            transaction_type='assignment'
        ).order_by('created_at')
        
        duplicates_removed = 0
        time_groups = self.group_by_time_window(transactions)
        
        for group in time_groups:
            if len(group) > 1:
                quantity_groups = defaultdict(list)
                for txn in group:
                    quantity_groups[abs(txn.quantity)].append(txn)
                
                for quantity, txns in quantity_groups.items():
                    if len(txns) > 1:
                        ref_types = set(txn.reference_type for txn in txns)
                        if 'delivery' in ref_types and 'delivery_item' in ref_types:
                            # Remove delivery transactions, keep delivery_item
                            delivery_txns = [t for t in txns if t.reference_type == 'delivery']
                            for dup_txn in delivery_txns:
                                dup_txn.delete()
                                duplicates_removed += 1
        
        return duplicates_removed

    def count_batch_duplicates(self, batch):
        """Count duplicate transactions for a specific batch (dry run)"""
        transactions = BatchTransaction.objects.filter(
            batch=batch,
            transaction_type='assignment'
        ).order_by('created_at')
        
        duplicates_count = 0
        time_groups = self.group_by_time_window(transactions)
        
        for group in time_groups:
            if len(group) > 1:
                quantity_groups = defaultdict(list)
                for txn in group:
                    quantity_groups[abs(txn.quantity)].append(txn)
                
                for quantity, txns in quantity_groups.items():
                    if len(txns) > 1:
                        ref_types = set(txn.reference_type for txn in txns)
                        if 'delivery' in ref_types and 'delivery_item' in ref_types:
                            delivery_txns = [t for t in txns if t.reference_type == 'delivery']
                            duplicates_count += len(delivery_txns)
        
        return duplicates_count

    def group_by_time_window(self, transactions, window_seconds=60):
        """Group transactions by time window"""
        groups = []
        current_group = []
        
        for txn in transactions:
            if not current_group:
                current_group.append(txn)
            else:
                time_diff = (txn.created_at - current_group[-1].created_at).total_seconds()
                if time_diff <= window_seconds:
                    current_group.append(txn)
                else:
                    if len(current_group) > 1:
                        groups.append(current_group)
                    current_group = [txn]
        
        if len(current_group) > 1:
            groups.append(current_group)
        
        return groups

    def fix_stock_quantities(self, discrepancies):
        """Fix the batch quantities based on transaction history"""
        self.stdout.write('\n🔧 Fixing Batch Quantities...')
        
        fixes_applied = 0
        
        with transaction.atomic():
            for discrepancy_data in discrepancies:
                product = discrepancy_data['product']
                
                # Fix each batch quantity based on transaction history
                batches = Batch.objects.filter(product=product, is_active=True)
                
                for batch in batches:
                    correct_quantity = self.calculate_correct_batch_quantity(batch)
                    
                    if abs(batch.current_quantity - correct_quantity) > 0.01:
                        old_quantity = batch.current_quantity
                        batch.current_quantity = correct_quantity
                        batch.save()
                        
                        # Create adjustment transaction
                        BatchTransaction.objects.create(
                            batch=batch,
                            transaction_type='adjustment',
                            quantity=correct_quantity - old_quantity,
                            balance_after=correct_quantity,
                            reference_type='stock_reconciliation',
                            reference_id=0,
                            notes=f"Stock reconciliation: Fixed from {old_quantity} to {correct_quantity}",
                            created_by_id=1  # System user
                        )
                        
                        self.stdout.write(
                            f'   ✅ Fixed batch {batch.batch_number}: {old_quantity} → {correct_quantity}'
                        )
                        fixes_applied += 1
        
        self.stdout.write(
            f'🎯 Applied {fixes_applied} batch quantity fixes'
        )

        # Validate the fixes
        self.validate_fixes()

    def calculate_correct_batch_quantity(self, batch):
        """Calculate correct batch quantity from transaction history"""
        # Start with initial quantity
        correct_quantity = batch.initial_quantity
        
        # Apply all transactions except restock and previous reconciliation adjustments
        transactions = BatchTransaction.objects.filter(
            batch=batch
        ).exclude(
            transaction_type='restock'
        ).exclude(
            Q(transaction_type='adjustment') & Q(notes__icontains='reconciliation')
        ).order_by('created_at')
        
        for txn in transactions:
            correct_quantity += txn.quantity
        
        return max(0, correct_quantity)  # Ensure non-negative

    def validate_fixes(self):
        """Validate that all fixes are correct"""
        self.stdout.write('\n✅ Validating Fixes...')
        
        validation_errors = 0
        
        for product in Product.objects.all():
            batch_total = Batch.objects.filter(
                product=product,
                is_active=True
            ).aggregate(total=Sum('current_quantity'))['total'] or 0
            
            product_total_stock = product.total_stock
            available_for_delivery = self.calculate_available_for_delivery(product)
            
            # Validate that calculated total matches batch sum
            if abs(product_total_stock - batch_total) > 0.01:
                self.stdout.write(
                    f'❌ Stock calculation error for {product.name}: '
                    f'calculated={product_total_stock}, batches={batch_total}'
                )
                validation_errors += 1
            
            # Validate no negative quantities
            negative_batches = Batch.objects.filter(
                product=product,
                is_active=True,
                current_quantity__lt=0
            ).count()
            
            if negative_batches > 0:
                self.stdout.write(
                    f'❌ {product.name} has {negative_batches} batches with negative quantities'
                )
                validation_errors += 1
            
            # Report final status
            if validation_errors == 0:
                self.stdout.write(
                    f'✅ {product.name}: Total={product_total_stock}, Available={available_for_delivery}'
                )
        
        if validation_errors == 0:
            self.stdout.write('✅ All validations passed!')
        else:
            self.stdout.write(f'❌ {validation_errors} validation errors remain')
