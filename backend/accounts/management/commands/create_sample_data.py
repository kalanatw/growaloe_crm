from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Owner, Salesman, Shop, MarginPolicy
from products.models import Category, Product, Batch
from sales.models import Invoice, InvoiceItem, Transaction
from decimal import Decimal
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create Owner
        owner_user, created = User.objects.get_or_create(
            username='john_owner',
            defaults={
                'email': 'owner@example.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'role': 'OWNER'
            }
        )
        if created:
            owner_user.set_password('password123')
            owner_user.save()
        
        owner, created = Owner.objects.get_or_create(
            user=owner_user,
            defaults={
                'business_name': 'Green Valley Distributors',
                'business_license': 'BL123456789',
                'tax_id': 'TAX987654321'
            }
        )

        # Create Margin Policy
        margin_policy, created = MarginPolicy.objects.get_or_create(
            owner=owner,
            defaults={
                'default_salesman_margin': Decimal('15.00'),
                'default_shop_margin': Decimal('10.00'),
                'allow_salesman_override': True,
                'allow_shop_override': True
            }
        )

        # Create Salesmen
        salesman1_user, created = User.objects.get_or_create(
            username='mike_sales',
            defaults={
                'email': 'mike@example.com',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'role': 'SALESMAN'
            }
        )
        if created:
            salesman1_user.set_password('password123')
            salesman1_user.save()
        
        salesman1, created = Salesman.objects.get_or_create(
            user=salesman1_user,
            owner=owner,
            defaults={
                'name': 'Mike Johnson',
                'profit_margin': Decimal('15.00'),
                'description': 'Experienced salesman covering North region'
            }
        )

        salesman2_user, created = User.objects.get_or_create(
            username='sarah_sales',
            defaults={
                'email': 'sarah@example.com',
                'first_name': 'Sarah',
                'last_name': 'Davis',
                'role': 'SALESMAN'
            }
        )
        if created:
            salesman2_user.set_password('password123')
            salesman2_user.save()
        
        salesman2, created = Salesman.objects.get_or_create(
            user=salesman2_user,
            owner=owner,
            defaults={
                'name': 'Sarah Davis',
                'profit_margin': Decimal('12.00'),
                'description': 'Experienced salesman covering South region'
            }
        )

        # Create Shops
        shop1_user, created = User.objects.get_or_create(
            username='corner_shop',
            defaults={
                'email': 'shop1@example.com',
                'first_name': 'Corner',
                'last_name': 'Shop',
                'role': 'SHOP'
            }
        )
        if created:
            shop1_user.set_password('password123')
            shop1_user.save()
        
        shop1, created = Shop.objects.get_or_create(
            user=shop1_user,
            salesman=salesman1,
            defaults={
                'name': 'Corner Grocery Store',
                'contact_person': 'Bob Wilson',
                'phone': '+1234567891',
                'email': 'corner@example.com',
                'address': '456 Corner Street, City',
                'shop_margin': Decimal('10.00'),
                'credit_limit': Decimal('5000.00')
            }
        )

        shop2_user, created = User.objects.get_or_create(
            username='main_mart',
            defaults={
                'email': 'shop2@example.com',
                'first_name': 'Main',
                'last_name': 'Mart',
                'role': 'SHOP'
            }
        )
        if created:
            shop2_user.set_password('password123')
            shop2_user.save()
        
        shop2, created = Shop.objects.get_or_create(
            user=shop2_user,
            salesman=salesman2,
            defaults={
                'name': 'Main Street Mart',
                'contact_person': 'Alice Brown',
                'phone': '+1234567892',
                'email': 'mainmart@example.com',
                'address': '789 Main Street, City',
                'shop_margin': Decimal('8.00'),
                'credit_limit': Decimal('7000.00')
            }
        )

        # Create Categories
        category1, created = Category.objects.get_or_create(
            name='Fresh Produce',
            defaults={'description': 'Fresh fruits and vegetables'}
        )
        
        category2, created = Category.objects.get_or_create(
            name='Beverages',
            defaults={'description': 'Drinks and beverages'}
        )

        category3, created = Category.objects.get_or_create(
            name='Snacks',
            defaults={'description': 'Snacks and confectionery'}
        )

        # Create Products
        products_data = [
            ('Organic Bananas', 'ORG-BAN-001', category1, '2.50', '4.00'),
            ('Red Apples', 'RED-APP-001', category1, '3.00', '4.50'),
            ('Fresh Carrots', 'FRS-CAR-001', category1, '1.80', '3.00'),
            ('Orange Juice', 'ORG-JUI-001', category2, '4.50', '6.00'),
            ('Mineral Water', 'MIN-WAT-001', category2, '1.20', '2.00'),
            ('Energy Drink', 'ENR-DRK-001', category2, '2.80', '4.50'),
            ('Chocolate Bars', 'CHO-BAR-001', category3, '1.50', '2.50'),
            ('Potato Chips', 'POT-CHP-001', category3, '2.20', '3.50'),
            ('Cookies Pack', 'COO-PCK-001', category3, '3.50', '5.00'),
        ]

        products = []
        for name, sku, category, cost, price in products_data:
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'description': f'High quality {name.lower()}',
                    'category': category,
                    'cost_price': Decimal(cost),
                    'base_price': Decimal(price),
                    'unit': 'piece',
                    'min_stock_level': 50
                }
            )
            products.append(product)

        # Create initial batches for each product using add_stock method
        for product in products:
            # Add initial stock to owner using batches
            initial_stock = random.randint(300, 800)
            product.add_stock(
                quantity=initial_stock,
                user=User.objects.filter(is_superuser=True).first(),
                notes=f"Initial stock for {product.name}",
                batch_number=f"INIT-{product.sku}-001"
            )

        # Create Sample Invoices
        salesmen = [salesman1, salesman2]
        shops = [shop1, shop2]
        
        for i in range(5):
            invoice_number = f'INV-2025-{1000 + i}'
            
            # Check if invoice already exists
            if Invoice.objects.filter(invoice_number=invoice_number).exists():
                continue
                
            # Create invoice with minimal required fields first
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                salesman=random.choice(salesmen),
                shop=random.choice(shops),
                due_date=date.today() + timedelta(days=random.randint(7, 30)),
                status='draft',  # Start with draft to avoid calculations
                notes=f'Sample invoice {i+1}'
            )

            # Add items to invoice
            selected_products = random.sample(products, random.randint(2, 4))
            for product in selected_products:
                quantity = random.randint(1, 10)
                unit_price = Decimal(f'{float(product.base_price) * random.uniform(0.9, 1.1):.2f}')
                
                # Create InvoiceItem without triggering invoice calculation
                item = InvoiceItem(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    calculated_price=unit_price,
                    salesman_margin=Decimal('10.00'),
                    shop_margin=Decimal('5.00')
                )
                item.total_price = Decimal(str(quantity)) * unit_price
                item.save()

            # Now manually calculate and update invoice totals
            invoice.subtotal = sum(item.total_price for item in invoice.items.all())
            invoice.discount_amount = Decimal(f'{random.uniform(0, 50):.2f}')
            invoice.net_total = invoice.subtotal - invoice.discount_amount
            invoice.status = random.choice(['draft', 'pending', 'paid', 'partial'])
            invoice.save()

            # Create transactions for paid invoices
            if invoice.status in ['paid', 'partial']:
                amount = invoice.net_total if invoice.status == 'paid' else invoice.net_total * Decimal('0.60')
                Transaction.objects.create(
                    invoice=invoice,
                    payment_method=random.choice(['cash', 'cheque', 'bank_transfer']),
                    amount=amount,
                    reference_number=f'TXN-{invoice.invoice_number}',
                    created_by=owner_user
                )

        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
        self.stdout.write(f'Created:')
        self.stdout.write(f'- 1 Owner: {owner.business_name}')
        self.stdout.write(f'- 2 Salesmen: {salesman1.name}, {salesman2.name}')
        self.stdout.write(f'- 2 Shops: {shop1.name}, {shop2.name}')
        self.stdout.write(f'- 3 Categories: {len(Category.objects.all())} total')
        self.stdout.write(f'- {len(products)} Products')
        self.stdout.write(f'- {Invoice.objects.count()} Sample Invoices')
        self.stdout.write(f'- Stock allocated to all salesmen')
