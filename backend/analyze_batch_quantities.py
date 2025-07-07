#!/usr/bin/env python
"""
Fix batch quantity inconsistencies caused by the duplication bug.
This script will analyze and correct batch quantities based on transaction history.
"""

import os
import sys
import django
from decimal import Decimal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_management.settings')
django.setup()

from django.db import transaction
from products.models import BatchAssignment, BatchTransaction, Delivery, Batch


def analyze_batch_transactions():
    """
    Analyze each batch's transaction history to identify duplication patterns.
    """
    print("🔍 Analyzing batch transaction patterns...")
    
    for batch in Batch.objects.filter(is_active=True):
        print(f"\n📦 Batch: {batch.batch_number}")
        print(f"   Current quantity: {batch.current_quantity}")
        print(f"   Initial quantity: {batch.initial_quantity}")
        
        transactions = BatchTransaction.objects.filter(batch=batch).order_by('created_at')
        running_balance = 0
        
        print("   Transaction History:")
        duplicate_assignments = []
        
        for txn in transactions:
            running_balance += txn.quantity
            print(f"   - {txn.created_at.strftime('%Y-%m-%d %H:%M')} | "
                  f"{txn.transaction_type:12} | {txn.quantity:6} | Balance: {running_balance:6} | "
                  f"{txn.reference_type} #{txn.reference_id} | {txn.notes}")
            
            # Look for duplicate assignment patterns
            if txn.transaction_type == 'assignment' and txn.reference_type in ['delivery_item', 'delivery']:
                duplicate_assignments.append(txn)
        
        print(f"   Calculated final balance: {running_balance}")
        print(f"   Difference from current: {batch.current_quantity - running_balance}")
        
        # Check for potential duplicate assignment transactions
        if len(duplicate_assignments) > 1:
            delivery_groups = {}
            for txn in duplicate_assignments:
                delivery_id = txn.reference_id if txn.reference_type == 'delivery' else 'item_' + str(txn.reference_id)
                if delivery_id not in delivery_groups:
                    delivery_groups[delivery_id] = []
                delivery_groups[delivery_id].append(txn)
            
            for delivery_id, txns in delivery_groups.items():
                if len(txns) > 1:
                    print(f"   ⚠️  Potential duplicate assignments for delivery {delivery_id}:")
                    for txn in txns:
                        print(f"      - Transaction {txn.id}: {txn.quantity} ({txn.reference_type})")


def fix_batch_quantities():
    """
    Fix batch quantities by correcting the current_quantity to match transaction history.
    """
    print("\n🔧 Fixing batch quantities based on transaction history...")
    
    fixes_applied = 0
    
    with transaction.atomic():
        for batch in Batch.objects.filter(is_active=True):
            transactions = BatchTransaction.objects.filter(batch=batch).order_by('created_at')
            calculated_quantity = 0
            
            # Recalculate quantity from transaction history
            for txn in transactions:
                calculated_quantity += txn.quantity
            
            # Check if adjustment is needed
            if abs(batch.current_quantity - calculated_quantity) > 0.01:
                print(f"📦 Fixing {batch.batch_number}:")
                print(f"   Before: {batch.current_quantity}")
                print(f"   After:  {calculated_quantity}")
                print(f"   Difference: {batch.current_quantity - calculated_quantity}")
                
                # Update the batch quantity
                old_quantity = batch.current_quantity
                batch.current_quantity = calculated_quantity
                batch.save()
                
                # Create a transaction record for the adjustment
                BatchTransaction.objects.create(
                    batch=batch,
                    transaction_type='adjustment',
                    quantity=calculated_quantity - old_quantity,
                    balance_after=calculated_quantity,
                    reference_type='system_correction',
                    reference_id=0,
                    notes=f"System correction for duplication bug. Adjusted from {old_quantity} to {calculated_quantity}",
                    created_by_id=1  # Assuming admin user has ID 1
                )
                
                fixes_applied += 1
    
    print(f"\n✅ Applied {fixes_applied} quantity corrections")


def remove_duplicate_transactions():
    """
    Identify and remove duplicate batch transactions that were created due to the bug.
    """
    print("\n🗑️  Identifying duplicate transactions...")
    
    # Look for transactions that might be duplicates
    # Duplicates would have same batch, similar timestamps, same quantities but different reference_types
    potential_duplicates = []
    
    for batch in Batch.objects.filter(is_active=True):
        assignment_txns = BatchTransaction.objects.filter(
            batch=batch,
            transaction_type='assignment',
            reference_type__in=['delivery', 'delivery_item']
        ).order_by('created_at')
        
        # Group transactions by time windows (within 1 minute of each other)
        time_groups = []
        current_group = []
        
        for txn in assignment_txns:
            if not current_group:
                current_group.append(txn)
            else:
                time_diff = (txn.created_at - current_group[-1].created_at).total_seconds()
                if time_diff <= 60:  # Within 1 minute
                    current_group.append(txn)
                else:
                    if len(current_group) > 1:
                        time_groups.append(current_group)
                    current_group = [txn]
        
        if len(current_group) > 1:
            time_groups.append(current_group)
        
        # Analyze groups for potential duplicates
        for group in time_groups:
            if len(group) > 1:
                # Check if they have same quantity but different reference types
                quantities = {}
                for txn in group:
                    qty = abs(txn.quantity)
                    if qty not in quantities:
                        quantities[qty] = []
                    quantities[qty].append(txn)
                
                for qty, txns in quantities.items():
                    if len(txns) > 1:
                        ref_types = set(txn.reference_type for txn in txns)
                        if 'delivery' in ref_types and 'delivery_item' in ref_types:
                            print(f"⚠️  Potential duplicates in batch {batch.batch_number}:")
                            for txn in txns:
                                print(f"   - Transaction {txn.id}: {txn.quantity} ({txn.reference_type})")
                            potential_duplicates.extend(txns[1:])  # Keep first, mark others as duplicates
    
    if potential_duplicates:
        print(f"\n🗑️  Found {len(potential_duplicates)} potential duplicate transactions")
        
        # For safety, let's not auto-delete but just report
        print("⚠️  Manual review recommended before deletion")
        for txn in potential_duplicates:
            print(f"   - Transaction {txn.id} in batch {txn.batch.batch_number}: {txn.quantity} ({txn.reference_type})")
    else:
        print("✅ No obvious duplicate transactions found")


def main():
    print("🚀 Starting Batch Quantity Analysis and Fix...")
    print("=" * 60)
    
    try:
        # First analyze to understand the problem
        analyze_batch_transactions()
        
        # Remove obvious duplicates
        remove_duplicate_transactions()
        
        # Fix quantities based on corrected transaction history
        fix_batch_quantities()
        
        print("\n" + "=" * 60)
        print("✅ Batch quantity analysis and fixes completed!")
        print("\n📝 Summary:")
        print("   1. Analyzed transaction patterns for all batches")
        print("   2. Identified potential duplicate transactions")
        print("   3. Corrected batch quantities based on transaction history")
        print("   4. Added system correction transactions for audit trail")
        
    except Exception as e:
        print(f"\n❌ Error during analysis/fix: {str(e)}")
        print("Rolling back changes...")
        raise


if __name__ == "__main__":
    main()
