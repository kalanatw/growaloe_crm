#!/usr/bin/env python
"""
Seed script for finance app data
Run this to populate the financial management system with sample data
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Add the backend directory to the path
sys.path.append('/Users/kalana/Desktop/Personal/ZentraLabs/grow-aloe/backend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_management.settings')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from finance.models import TransactionCategory, FinancialTransaction
from sales.models import Invoice
from accounts.models import Salesman, Shop

User = get_user_model()

def create_sample_transaction_categories():
    """Create sample transaction categories"""
    categories = [
        {'name': 'Office Rent', 'transaction_type': 'expense', 'description': 'Monthly office rent payments'},
        {'name': 'Utilities', 'transaction_type': 'expense', 'description': 'Electricity, water, internet bills'},
        {'name': 'Marketing', 'transaction_type': 'expense', 'description': 'Advertising and marketing expenses'},
        {'name': 'Equipment', 'transaction_type': 'expense', 'description': 'Office equipment and supplies'},
        {'name': 'Consulting', 'transaction_type': 'expense', 'description': 'Professional consulting fees'},
        {'name': 'Interest Income', 'transaction_type': 'income', 'description': 'Bank interest and investment income'},
        {'name': 'Service Income', 'transaction_type': 'income', 'description': 'Additional service fees'},
        {'name': 'Rental Income', 'transaction_type': 'income', 'description': 'Income from property rentals'},
    ]

    created_categories = []
    for cat_data in categories:
        category, created = TransactionCategory.objects.get_or_create(
            name=cat_data['name'],
            transaction_type=cat_data['transaction_type'],
            defaults={'description': cat_data['description']}
        )
        if created:
            print(f"Created category: {category.name}")
        created_categories.append(category)
    return created_categories

def create_sample_transactions():
    """Create sample financial transactions"""
    # Get or create a user for transactions
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('admin123')
        user.save()
        print(f"Created admin user: {user.username}")
    
    # Get categories
    categories = list(TransactionCategory.objects.all())
    if not categories:
        print("No categories found. Creating them first...")
        categories = create_sample_transaction_categories()
    
    # Sample transaction data
    transactions_data = [
        {'description': 'Office Rent - January', 'amount': Decimal('2500.00'), 'category_type': 'expense', 'days_ago': 30},
        {'description': 'Electricity Bill', 'amount': Decimal('450.00'), 'category_type': 'expense', 'days_ago': 25},
        {'description': 'Internet Bill', 'amount': Decimal('150.00'), 'category_type': 'expense', 'days_ago': 20},
        {'description': 'Marketing Campaign', 'amount': Decimal('1200.00'), 'category_type': 'expense', 'days_ago': 15},
        {'description': 'Office Supplies', 'amount': Decimal('300.00'), 'category_type': 'expense', 'days_ago': 10},
        {'description': 'Bank Interest', 'amount': Decimal('125.00'), 'category_type': 'income', 'days_ago': 5},
        {'description': 'Consulting Service', 'amount': Decimal('800.00'), 'category_type': 'income', 'days_ago': 3},
        {'description': 'Equipment Purchase', 'amount': Decimal('2200.00'), 'category_type': 'expense', 'days_ago': 1},
    ]
    
    created_transactions = []
    for trans_data in transactions_data:
        # Find a category of the right type
        category = next(
            (cat for cat in categories if cat.transaction_type == trans_data['category_type']),
            categories[0]  # fallback to first category
        )
        
        transaction_date = datetime.now().date() - timedelta(days=trans_data['days_ago'])
        
        transaction, created = FinancialTransaction.objects.get_or_create(
            description=trans_data['description'],
            defaults={
                'amount': trans_data['amount'],
                'category': category,
                'transaction_date': transaction_date,
                'created_by': user,
                'reference_number': f"REF{transaction_date.strftime('%Y%m%d')}{len(created_transactions)+1:03d}"
            }
        )
        
        if created:
            print(f"Created transaction: {transaction.description} - {transaction.amount}")
        created_transactions.append(transaction)
    
    return created_transactions

def main():
    """Main seeding function"""
    print("Starting finance app data seeding...")
    
    print("\n1. Creating transaction categories...")
    categories = create_sample_transaction_categories()
    print(f"Created {len(categories)} categories")
    
    print("\n2. Creating sample transactions...")
    transactions = create_sample_transactions()
    print(f"Created {len(transactions)} transactions")
    
    print("\n3. Summary:")
    print(f"Total Categories: {TransactionCategory.objects.count()}")
    print(f"Total Transactions: {FinancialTransaction.objects.count()}")
    
    # Calculate some basic stats
    total_income = FinancialTransaction.objects.filter(
        category__transaction_type='income'
    ).aggregate(total=django.db.models.Sum('amount'))['total'] or Decimal('0')
    
    total_expenses = FinancialTransaction.objects.filter(
        category__transaction_type='expense'
    ).aggregate(total=django.db.models.Sum('amount'))['total'] or Decimal('0')
    
    print(f"Total Income: ${total_income}")
    print(f"Total Expenses: ${total_expenses}")
    print(f"Net Income: ${total_income - total_expenses}")
    
    print("\nFinance app seeding completed successfully!")

if __name__ == '__main__':
    main()
