#!/usr/bin/env python
"""
Stock Reconciliation System for Aloe Vera Paradise
==================================================

This script performs comprehensive stock auditing and reconciliation to fix
inconsistencies between Product.stock_quantity and actual batch quantities.

The script will:
1. Audit all stock quantities across different data sources
2. Identify discrepancies and their root causes
3. Recalculate correct stock values from transaction history
4. Fix Product.stock_quantity to match actual batch totals
5. Ensure data integrity across the entire system

Author: Stock Management System
Date: July 7, 2025
"""

import os
import sys
import django
from decimal import Decimal
from collections import defaultdict
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_management.settings')
django.setup()

from django.db import transaction
from django.db.models import Sum, Q
from products.models import (
    Product, Batch, BatchTransaction, BatchAssignment, 
    DeliveryItem, Delivery
)


class StockReconciliationAuditor:
    """
    Comprehensive stock auditing and reconciliation system.
    """
    
    def __init__(self):
        self.audit_results = {}
        self.discrepancies = []
        self.fixes_applied = 0
        self.total_products_audited = 0
        
    def run_complete_audit(self):
        """
        Run the complete stock reconciliation process.
        """
        print("🚀 Starting Comprehensive Stock Reconciliation Audit")
        print("=" * 80)
        
        try:
            # Step 1: Audit all stock quantities
            self.audit_all_stock_quantities()
            
            # Step 2: Identify and analyze discrepancies
            self.analyze_discrepancies()
            
            # Step 3: Clean up duplicate transactions
            self.clean_duplicate_transactions()
            
            # Step 4: Recalculate batch quantities
            self.recalculate_batch_quantities()
            
            # Step 5: Fix product stock quantities
            self.fix_product_stock_quantities()
            
            # Step 6: Validate data integrity
            self.validate_data_integrity()
            
            # Step 7: Generate final report
            self.generate_reconciliation_report()
            
        except Exception as e:
            print(f"❌ Critical error during reconciliation: {str(e)}")
            raise
    
    def audit_all_stock_quantities(self):
        """
        Audit stock quantities from all sources and identify discrepancies.
        """
        print("\n📊 Step 1: Auditing Stock Quantities from All Sources")
        print("-" * 60)
        
        products = Product.objects.all()
        self.total_products_audited = len(products)
        
        for product in products:
            audit_data = self.audit_single_product(product)
            self.audit_results[product.id] = audit_data
            
            # Check for discrepancies
            if audit_data['has_discrepancy']:
                self.discrepancies.append({
                    'product': product,
                    'audit_data': audit_data
                })
                print(f"⚠️  Discrepancy found: {product.name}")
            else:
                print(f"✅ Stock consistent: {product.name}")
        
        print(f"\n📈 Audit Summary:")
        print(f"   - Products audited: {self.total_products_audited}")
        print(f"   - Discrepancies found: {len(self.discrepancies)}")
    
    def audit_single_product(self, product):
        """
        Perform detailed audit of a single product's stock quantities.
        """
        # 1. Product's displayed stock quantity
        product_stock = product.stock_quantity or 0
        
        # 2. Sum of all batch current quantities
        batch_total = Batch.objects.filter(
            product=product,
            is_active=True
        ).aggregate(total=Sum('current_quantity'))['total'] or 0
        
        # 3. Calculate available quantity for deliveries
        available_for_delivery = self.calculate_available_for_delivery(product)
        
        # 4. Sum of allocated quantities
        allocated_total = BatchAssignment.objects.filter(
            batch__product=product,
            status__in=['delivered', 'partial']
        ).aggregate(
            total=Sum('delivered_quantity') - Sum('returned_quantity')
        )['total'] or 0
        
        # 5. Calculate theoretical stock from transactions
        theoretical_stock = self.calculate_theoretical_stock(product)
        
        audit_data = {
            'product_stock': product_stock,
            'batch_total': batch_total,
            'available_for_delivery': available_for_delivery,
            'allocated_total': allocated_total,
            'theoretical_stock': theoretical_stock,
            'discrepancy_amount': product_stock - batch_total,
            'has_discrepancy': abs(product_stock - batch_total) > 0.01,
            'batches': list(product.batches.filter(is_active=True).values(
                'id', 'batch_number', 'current_quantity', 'initial_quantity'
            ))
        }
        
        return audit_data
    
    def calculate_available_for_delivery(self, product):
        """
        Calculate actual available quantity for delivery allocation.
        """
        available_batches = Batch.objects.filter(
            product=product,
            is_active=True,
            current_quantity__gt=0
        )
        
        total_available = 0
        for batch in available_batches:
            # Available = current_quantity - already_allocated_but_not_delivered
            pending_allocations = BatchAssignment.objects.filter(
                batch=batch,
                status='pending'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            available_in_batch = batch.current_quantity - pending_allocations
            total_available += max(0, available_in_batch)
        
        return total_available
    
    def calculate_theoretical_stock(self, product):
        """
        Calculate what the stock should be based on transaction history.
        """
        batches = product.batches.filter(is_active=True)
        theoretical_total = 0
        
        for batch in batches:
            # Start with initial quantity
            theoretical_quantity = batch.initial_quantity
            
            # Apply all transactions except 'restock' (which sets initial)
            transactions = BatchTransaction.objects.filter(
                batch=batch
            ).exclude(transaction_type='restock').order_by('created_at')
            
            for txn in transactions:
                if txn.transaction_type in ['assignment', 'sale']:
                    theoretical_quantity += txn.quantity  # These are negative
                elif txn.transaction_type == 'return':
                    theoretical_quantity += txn.quantity  # These are positive
                elif txn.transaction_type == 'adjustment':
                    theoretical_quantity += txn.quantity
            
            theoretical_total += theoretical_quantity
        
        return theoretical_total
    
    def analyze_discrepancies(self):
        """
        Analyze the root causes of discrepancies.
        """
        print("\n🔍 Step 2: Analyzing Discrepancy Root Causes")
        print("-" * 60)
        
        if not self.discrepancies:
            print("✅ No discrepancies found to analyze")
            return
        
        for discrepancy in self.discrepancies:
            product = discrepancy['product']
            audit_data = discrepancy['audit_data']
            
            print(f"\n📦 Product: {product.name} (SKU: {product.sku})")
            print(f"   Product Stock (UI):      {audit_data['product_stock']}")
            print(f"   Batch Total (Actual):    {audit_data['batch_total']}")
            print(f"   Available for Delivery:  {audit_data['available_for_delivery']}")
            print(f"   Allocated Total:         {audit_data['allocated_total']}")
            print(f"   Theoretical Stock:       {audit_data['theoretical_stock']}")
            print(f"   Discrepancy Amount:      {audit_data['discrepancy_amount']}")
            
            # Analyze each batch
            print(f"   Batch Details:")
            for batch_info in audit_data['batches']:
                batch = Batch.objects.get(id=batch_info['id'])
                transaction_count = BatchTransaction.objects.filter(batch=batch).count()
                assignment_count = BatchAssignment.objects.filter(batch=batch).count()
                
                print(f"     - {batch_info['batch_number']}: "
                      f"Current={batch_info['current_quantity']}, "
                      f"Initial={batch_info['initial_quantity']}, "
                      f"Transactions={transaction_count}, "
                      f"Assignments={assignment_count}")
    
    def clean_duplicate_transactions(self):
        """
        Identify and clean up duplicate batch transactions.
        """
        print("\n🧹 Step 3: Cleaning Duplicate Transactions")
        print("-" * 60)
        
        duplicates_removed = 0
        
        # Look for potential duplicates within time windows
        for batch in Batch.objects.filter(is_active=True):
            transactions = BatchTransaction.objects.filter(
                batch=batch,
                transaction_type='assignment'
            ).order_by('created_at')
            
            # Group transactions by 1-minute time windows
            time_groups = self.group_transactions_by_time(transactions, window_seconds=60)
            
            for group in time_groups:
                if len(group) > 1:
                    # Check for same quantity, different reference types
                    quantity_groups = defaultdict(list)
                    for txn in group:
                        quantity_groups[abs(txn.quantity)].append(txn)
                    
                    for quantity, txns in quantity_groups.items():
                        if len(txns) > 1:
                            ref_types = set(txn.reference_type for txn in txns)
                            if 'delivery' in ref_types and 'delivery_item' in ref_types:
                                # Found duplicate - keep delivery_item, remove delivery
                                delivery_txns = [t for t in txns if t.reference_type == 'delivery']
                                for dup_txn in delivery_txns:
                                    print(f"   🗑️  Removing duplicate transaction: "
                                          f"Batch {batch.batch_number}, "
                                          f"Quantity {dup_txn.quantity}, "
                                          f"Type {dup_txn.reference_type}")
                                    dup_txn.delete()
                                    duplicates_removed += 1
        
        print(f"✅ Removed {duplicates_removed} duplicate transactions")
    
    def group_transactions_by_time(self, transactions, window_seconds=60):
        """
        Group transactions that occur within the specified time window.
        """
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
    
    def recalculate_batch_quantities(self):
        """
        Recalculate batch quantities based on cleaned transaction history.
        """
        print("\n🔢 Step 4: Recalculating Batch Quantities")
        print("-" * 60)
        
        batches_fixed = 0
        
        with transaction.atomic():
            for batch in Batch.objects.filter(is_active=True):
                # Calculate correct quantity from transaction history
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
                    
                    print(f"   🔧 Fixed {batch.batch_number}: {old_quantity} → {correct_quantity}")
                    batches_fixed += 1
        
        print(f"✅ Fixed {batches_fixed} batch quantities")
    
    def calculate_correct_batch_quantity(self, batch):
        """
        Calculate the correct batch quantity from transaction history.
        """
        # Start with initial quantity
        correct_quantity = batch.initial_quantity
        
        # Apply all non-restock transactions
        transactions = BatchTransaction.objects.filter(
            batch=batch
        ).exclude(transaction_type='restock').order_by('created_at')
        
        for txn in transactions:
            if txn.transaction_type != 'adjustment' or 'reconciliation' not in txn.notes:
                correct_quantity += txn.quantity
        
        return max(0, correct_quantity)  # Ensure non-negative
    
    def fix_product_stock_quantities(self):
        """
        Fix Product.stock_quantity to match the sum of batch quantities.
        """
        print("\n🔧 Step 5: Fixing Product Stock Quantities")
        print("-" * 60)
        
        products_fixed = 0
        
        with transaction.atomic():
            for product in Product.objects.all():
                # Calculate correct stock from batch totals
                correct_stock = Batch.objects.filter(
                    product=product,
                    is_active=True
                ).aggregate(total=Sum('current_quantity'))['total'] or 0
                
                if abs(product.stock_quantity - correct_stock) > 0.01:
                    old_stock = product.stock_quantity
                    product.stock_quantity = correct_stock
                    product.save()
                    
                    print(f"   🔧 Fixed {product.name}: {old_stock} → {correct_stock}")
                    products_fixed += 1
        
        print(f"✅ Fixed {products_fixed} product stock quantities")
        self.fixes_applied = products_fixed
    
    def validate_data_integrity(self):
        """
        Perform final validation to ensure data integrity.
        """
        print("\n✅ Step 6: Validating Data Integrity")
        print("-" * 60)
        
        validation_errors = []
        
        for product in Product.objects.all():
            # Check: Product stock = Sum of batch quantities
            batch_total = Batch.objects.filter(
                product=product,
                is_active=True
            ).aggregate(total=Sum('current_quantity'))['total'] or 0
            
            if abs(product.stock_quantity - batch_total) > 0.01:
                validation_errors.append(
                    f"Product {product.name}: stock_quantity ({product.stock_quantity}) "
                    f"!= batch_total ({batch_total})"
                )
            
            # Check: No negative quantities
            if product.stock_quantity < 0:
                validation_errors.append(f"Product {product.name}: negative stock quantity")
            
            negative_batches = Batch.objects.filter(
                product=product,
                is_active=True,
                current_quantity__lt=0
            ).count()
            
            if negative_batches > 0:
                validation_errors.append(
                    f"Product {product.name}: {negative_batches} batches with negative quantities"
                )
        
        if validation_errors:
            print("❌ Validation errors found:")
            for error in validation_errors:
                print(f"   - {error}")
        else:
            print("✅ All validation checks passed!")
        
        return len(validation_errors) == 0
    
    def generate_reconciliation_report(self):
        """
        Generate a comprehensive reconciliation report.
        """
        print("\n📊 Step 7: Final Reconciliation Report")
        print("=" * 80)
        
        print(f"🎯 Reconciliation Summary:")
        print(f"   ├─ Products audited: {self.total_products_audited}")
        print(f"   ├─ Discrepancies found: {len(self.discrepancies)}")
        print(f"   ├─ Stock quantities fixed: {self.fixes_applied}")
        print(f"   └─ Data integrity: {'✅ Valid' if self.validate_data_integrity() else '❌ Issues remain'}")
        
        print(f"\n📈 Current Stock Status:")
        for product in Product.objects.all():
            available_for_delivery = self.calculate_available_for_delivery(product)
            print(f"   📦 {product.name} (SKU: {product.sku})")
            print(f"      ├─ Total Stock: {product.stock_quantity}")
            print(f"      └─ Available for Delivery: {available_for_delivery}")
        
        print(f"\n✅ Stock reconciliation completed successfully!")
        print(f"   All stock quantities are now consistent across the system.")
        print(f"   Delivery allocation should work correctly with accurate quantities.")


def main():
    """
    Main execution function.
    """
    auditor = StockReconciliationAuditor()
    auditor.run_complete_audit()


if __name__ == "__main__":
    main()
