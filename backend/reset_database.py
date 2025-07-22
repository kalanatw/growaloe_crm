#!/usr/bin/env python
"""
Database Reset Script for Aloe Vera Paradise
This script clears all data and creates a fresh admin user.
"""

import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_management.settings')
django.setup()

from django.db import connection, transaction
from accounts.models import User, Owner, Salesman, Shop
from products.models import Product, Category, Batch, BatchTransaction, BatchAssignment, Delivery, DeliveryItem, StockMovement
from sales.models import Invoice, InvoiceItem, Commission, InvoiceSettlement, Return, Transaction as SalesTransaction, SettlementPayment
from finance.models import FinancialTransaction, CommissionRecord, ProfitSummary, TransactionCategory, DescriptionSuggestion
from reports.models import SalesReport, FinancialReport, InventoryReport, DashboardMetrics
from core.models import CompanySettings, FinancialSummary, FinancialTransaction as CoreFinancialTransaction

def clear_all_data():
    """Clear all data from the database in the correct order to avoid foreign key constraints."""
    
    print("🗑️  Starting database cleanup...")
    
    with transaction.atomic():
        # Delete in reverse dependency order to avoid foreign key constraint errors
        
        # Reports and analytics
        print("   Clearing reports and analytics...")
        DashboardMetrics.objects.all().delete()
        SalesReport.objects.all().delete()
        FinancialReport.objects.all().delete()
        InventoryReport.objects.all().delete()
        
        # Finance records
        print("   Clearing finance records...")
        DescriptionSuggestion.objects.all().delete()
        CommissionRecord.objects.all().delete()
        FinancialTransaction.objects.all().delete()
        ProfitSummary.objects.all().delete()
        
        # Core financial data
        print("   Clearing core financial data...")
        CoreFinancialTransaction.objects.all().delete()
        FinancialSummary.objects.all().delete()
        
        # Sales data
        print("   Clearing sales data...")
        SettlementPayment.objects.all().delete()
        Return.objects.all().delete()
        SalesTransaction.objects.all().delete()
        InvoiceSettlement.objects.all().delete()
        Commission.objects.all().delete()
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        
        # Product and inventory data
        print("   Clearing product and inventory data...")
        BatchAssignment.objects.all().delete()
        BatchTransaction.objects.all().delete()
        StockMovement.objects.all().delete()
        DeliveryItem.objects.all().delete()
        Delivery.objects.all().delete()
        Batch.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        
        # Account hierarchy (shops -> salesmen -> owners -> users)
        print("   Clearing account data...")
        Shop.objects.all().delete()
        Salesman.objects.all().delete()
        Owner.objects.all().delete()
        
        # Clear all users except superusers (we'll recreate admin)
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(is_superuser=True).delete()  # Clear existing admin too
        
        # Clear company settings (optional)
        CompanySettings.objects.all().delete()
        
        # Don't delete TransactionCategory as it might have seed data
        # TransactionCategory.objects.all().delete()
        
    print("✅ Database cleanup completed!")

def create_admin_user():
    """Create the admin user with username 'admin' and password 'admin123'."""
    
    print("👤 Creating admin user...")
    
    try:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@aloeveraparadise.com',
            password='admin123',
            role='developer',
            first_name='Admin',
            last_name='User'
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Email: admin@aloeveraparadise.com")
        print(f"   Role: developer")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return None

def create_sample_categories():
    """Create some basic product categories."""
    
    print("📦 Creating sample categories...")
    
    categories = [
        {'name': 'Aloe Vera Gel', 'description': 'Pure aloe vera gel products'},
        {'name': 'Skincare', 'description': 'Aloe vera based skincare products'},
        {'name': 'Health Supplements', 'description': 'Aloe vera health and wellness products'},
        {'name': 'Cosmetics', 'description': 'Aloe vera cosmetic products'},
    ]
    
    created_categories = []
    for cat_data in categories:
        category = Category.objects.create(**cat_data)
        created_categories.append(category)
        print(f"   ✅ Created category: {category.name}")
    
    return created_categories

def create_transaction_categories():
    """Create basic transaction categories if they don't exist."""
    
    print("💰 Creating transaction categories...")
    
    categories = [
        {'name': 'Sales Revenue', 'transaction_type': 'income', 'description': 'Revenue from product sales'},
        {'name': 'Product Purchase', 'transaction_type': 'expense', 'description': 'Cost of purchasing products'},
        {'name': 'Marketing', 'transaction_type': 'expense', 'description': 'Marketing and advertising expenses'},
        {'name': 'Office Expenses', 'transaction_type': 'expense', 'description': 'General office and administrative expenses'},
        {'name': 'Commission Payments', 'transaction_type': 'expense', 'description': 'Commission payments to salesmen'},
        {'name': 'Other Income', 'transaction_type': 'income', 'description': 'Other sources of income'},
    ]
    
    for cat_data in categories:
        category, created = TransactionCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        if created:
            print(f"   ✅ Created transaction category: {category.name}")
        else:
            print(f"   ℹ️  Transaction category already exists: {category.name}")

def reset_database():
    """Main function to reset the entire database."""
    
    print("🚀 Starting Aloe Vera Paradise Database Reset")
    print("=" * 50)
    
    try:
        # Step 1: Clear all existing data
        clear_all_data()
        
        # Step 2: Create admin user
        admin_user = create_admin_user()
        
        if not admin_user:
            print("❌ Failed to create admin user. Exiting.")
            return False
        
        # Step 3: Create basic categories
        create_sample_categories()
        
        # Step 4: Create transaction categories
        create_transaction_categories()
        
        print("\n" + "=" * 50)
        print("🎉 Database reset completed successfully!")
        print("\n📋 Summary:")
        print("   • All existing data cleared")
        print("   • Admin user created (admin/admin123)")
        print("   • Sample product categories created")
        print("   • Transaction categories created")
        print("\n🌐 You can now:")
        print("   • Login to admin panel: http://localhost:8000/admin/")
        print("   • Login to frontend: http://localhost:3000/")
        print("   • Start creating owners, products, and managing inventory")
        print("\n✨ Your Aloe Vera Paradise system is ready to use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database reset: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL data in your database!")
    print("This action cannot be undone.")
    
    # Ask for confirmation
    confirm = input("\nAre you sure you want to proceed? (type 'yes' to continue): ")
    
    if confirm.lower() == 'yes':
        success = reset_database()
        sys.exit(0 if success else 1)
    else:
        print("❌ Database reset cancelled.")
        sys.exit(0)