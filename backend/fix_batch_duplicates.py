#!/usr/bin/env python
"""
Utility script to clean up duplicate batch assignments and fix quantity discrepancies.
This script should be run after the code fix to clean up existing data.
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
from collections import defaultdict


def clean_duplicate_batch_assignments():
    """
    Clean up duplicate batch assignments that may have been created before the fix.
    Keep the first assignment and remove duplicates, updating quantities accordingly.
    """
    print("🔍 Scanning for duplicate batch assignments...")
    
    # Group assignments by (batch, delivery, salesman)
    assignment_groups = defaultdict(list)
    
    all_assignments = BatchAssignment.objects.select_related(
        'batch', 'delivery', 'salesman'
    ).order_by('created_at')
    
    for assignment in all_assignments:
        if assignment.delivery:  # Only process delivery-related assignments
            key = (assignment.batch_id, assignment.delivery_id, assignment.salesman_id)
            assignment_groups[key].append(assignment)
    
    duplicates_found = 0
    total_cleaned = 0
    
    with transaction.atomic():
        for key, assignments in assignment_groups.items():
            if len(assignments) > 1:
                duplicates_found += 1
                batch_id, delivery_id, salesman_id = key
                
                print(f"\n📦 Found {len(assignments)} duplicate assignments for:")
                print(f"   Batch: {assignments[0].batch.batch_number}")
                print(f"   Delivery: {assignments[0].delivery.delivery_number}")
                print(f"   Salesman: {assignments[0].salesman.user.get_full_name()}")
                
                # Keep the first assignment, merge quantities, remove others
                primary_assignment = assignments[0]
                total_quantity = 0
                total_delivered = 0
                total_returned = 0
                
                for assignment in assignments:
                    total_quantity += assignment.quantity
                    total_delivered += assignment.delivered_quantity
                    total_returned += assignment.returned_quantity
                    print(f"   - Assignment {assignment.id}: {assignment.quantity} qty, {assignment.delivered_quantity} delivered")
                
                # Update the primary assignment with consolidated quantities
                primary_assignment.quantity = total_quantity
                primary_assignment.delivered_quantity = total_delivered
                primary_assignment.returned_quantity = total_returned
                primary_assignment.save()
                
                print(f"   ✅ Consolidated to: {total_quantity} qty, {total_delivered} delivered")
                
                # Remove duplicate assignments
                for assignment in assignments[1:]:
                    assignment.delete()
                    total_cleaned += 1
                    print(f"   🗑️  Removed duplicate assignment {assignment.id}")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   - Found {duplicates_found} sets of duplicate assignments")
    print(f"   - Removed {total_cleaned} duplicate records")
    print(f"   - Database constraints now prevent future duplications")


def verify_batch_quantities():
    """
    Verify that batch quantities are consistent after cleanup.
    """
    print("\n🔍 Verifying batch quantities...")
    
    inconsistencies = 0
    batches_checked = 0
    
    for batch in Batch.objects.filter(is_active=True):
        batches_checked += 1
        
        # Calculate expected quantity based on transactions
        transactions = BatchTransaction.objects.filter(batch=batch).order_by('created_at')
        calculated_quantity = 0
        
        for txn in transactions:
            if txn.transaction_type == 'restock':
                calculated_quantity += txn.quantity
            elif txn.transaction_type in ['assignment', 'sale']:
                calculated_quantity += txn.quantity  # These are already negative
            elif txn.transaction_type == 'return':
                calculated_quantity += txn.quantity
        
        if abs(batch.current_quantity - calculated_quantity) > 0.01:  # Allow for tiny rounding differences
            inconsistencies += 1
            print(f"⚠️  Batch {batch.batch_number}:")
            print(f"   Current: {batch.current_quantity}, Calculated: {calculated_quantity}")
            print(f"   Difference: {batch.current_quantity - calculated_quantity}")
            
            # Optionally fix the inconsistency
            # batch.current_quantity = calculated_quantity
            # batch.save()
    
    print(f"\n📊 Verification Summary:")
    print(f"   - Checked {batches_checked} batches")
    if inconsistencies == 0:
        print(f"   ✅ All batch quantities are consistent!")
    else:
        print(f"   ⚠️  Found {inconsistencies} batches with quantity inconsistencies")


def main():
    print("🚀 Starting Batch Assignment Cleanup...")
    print("=" * 60)
    
    try:
        clean_duplicate_batch_assignments()
        verify_batch_quantities()
        
        print("\n" + "=" * 60)
        print("✅ Cleanup completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Test creating a new delivery to ensure no duplicates")
        print("   2. Monitor batch transactions for consistency")
        print("   3. The unique constraint will prevent future duplications")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        print("Rolling back changes...")
        raise


if __name__ == "__main__":
    main()
