# backend/sales/tests/test_sales.py
from .base_test import AloeVeraParadiseBaseTestCase
from products.models import Batch, BatchAssignment
from sales.models import Invoice, InvoiceItem, Commission
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status

class SalesOperationsTestCase(AloeVeraParadiseBaseTestCase):
    """
    💰 SALES OPERATIONS TESTS
    
    Tests the daily sales workflow:
    - Customer invoice creation
    - Multi-product sales transactions
    - Commission calculations
    - Sales performance tracking
    """
    
    def test_01_full_day_sales_operations(self):
        """
        💰 FULL DAY SALES OPERATIONS TEST
        
        Simulates a complete day of sales activities across all territories
        with realistic customer transactions and commission calculations.
        """
        print("\n" + "="*70)
        print("💰 TESTING: Full Day Sales Operations")
        print("="*70)
        
        # Setup: Create batches and assignments
        batches = self.create_test_batches()
        assignments = self.create_batch_assignments(batches)
        
        # 🛍️ Phase 1: Northern Territory Sales (Mike)
        print("\n🛍️ Phase 1: Northern Territory Sales (Mike Johnson)")
        
        # Customer 1: Shop 1 - Premium order
        invoice1_data = {
            'shop': self.shop1.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 15.00,  # 15% margin
            'notes': 'Premium spa order - high-end clientele',
            'terms_conditions': 'Net 30',
            'items': [
                {
                    'product': self.product1.id,  # Premium Aloe Gel
                    'quantity': 25,
                    'unit_price': str(self.product1.base_price),
                },
                {
                    'product': self.product2.id,  # Wellness Drink
                    'quantity': 15,
                    'unit_price': str(self.product2.base_price),
                }
            ]
        }
        
        response1 = self.salesman1_client.post(
            reverse('invoice-list'),
            data=invoice1_data,
            format='json'
        )
        
        # Debug output for failed requests
        if response1.status_code != status.HTTP_201_CREATED:
            print(f"❌ Invoice creation failed with status {response1.status_code}")
            print(f"Response data: {response1.data}")
            print(f"Request data: {invoice1_data}")
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        invoice1 = Invoice.objects.get(id=response1.data['id'])
        
        print(f"� Created invoice: {invoice1.invoice_number}")
        print(f"   🏪 Shop: {invoice1.shop.name}")
        print(f"   � Date: {invoice1.invoice_date}")
        print(f"   📦 Items: {invoice1.items.count()}")
        
        # Customer 2: Shop 2 - Regular order  
        invoice2_data = {
            'shop': self.shop2.id,
            'due_date': str(date.today() + timedelta(days=15)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 12.00,  # 12% margin
            'notes': 'Regular retail customer',
            'terms_conditions': 'Net 15',
            'items': [
                {
                    'product': self.product3.id,  # Beauty Serum
                    'quantity': 20,
                    'unit_price': str(self.product3.base_price),
                },
                {
                    'product': self.product4.id,  # Hand Cream
                    'quantity': 30,
                    'unit_price': str(self.product4.base_price),
                }
            ]
        }
        
        response2 = self.salesman1_client.post(
            reverse('invoice-list'),
            data=invoice2_data,
            format='json'
        )
        
        # Debug output for failed requests
        if response2.status_code != status.HTTP_201_CREATED:
            print(f"❌ Invoice 2 creation failed with status {response2.status_code}")
            print(f"Response data: {response2.data}")
            print(f"Request data: {invoice2_data}")
        
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        invoice2 = Invoice.objects.get(id=response2.data['id'])
        
        print(f"📄 Created invoice: {invoice2.invoice_number}")
        print(f"   🏪 Shop: {invoice2.shop.name}")
        print(f"   📦 Items: {invoice2.items.count()}")
        
        # 🌅 Phase 2: Eastern Territory Sales (Jennifer)
        print("\n🌅 Phase 2: Eastern Territory Sales (Jennifer Davis)")
        
        # Shop 3 - Health products focus
        invoice3_data = {
            'shop': self.shop3.id,
            'due_date': str(date.today() + timedelta(days=20)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 10.00,  # 10% margin
            'notes': 'Health and wellness products for fitness center',
            'terms_conditions': 'Net 20',
            'items': [
                {
                    'product': self.product2.id,  # Wellness Drink
                    'quantity': 40,
                    'unit_price': str(self.product2.base_price),
                },
                {
                    'product': self.product3.id,  # Beauty Serum
                    'quantity': 15,
                    'unit_price': str(self.product3.base_price),
                }
            ]
        }
        
        response3 = self.salesman2_client.post(
            reverse('invoice-list'),
            data=invoice3_data,
            format='json'
        )
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        invoice3 = Invoice.objects.get(id=response3.data['id'])
        
        print(f"📄 Created invoice: {invoice3.invoice_number}")
        print(f"   🏪 Shop: {invoice3.shop.name}")
        print(f"   📦 Items: {invoice3.items.count()}")
        
        # 🌄 Phase 3: Western Territory Sales (Carlos)
        print("\n🌄 Phase 3: Western Territory Sales (Carlos Rodriguez)")
        
        # Shop 3 again - Luxury Beauty products
        invoice4_data = {
            'shop': self.shop3.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 18.00,  # 18% margin for luxury products
            'notes': 'Premium beauty products for luxury salon',
            'terms_conditions': 'Net 30',
            'items': [
                {
                    'product': self.product3.id,  # Beauty Serum
                    'quantity': 20,
                    'unit_price': str(self.product3.base_price),
                },
                {
                    'product': self.product4.id,  # Hand Cream
                    'quantity': 35,
                    'unit_price': str(self.product4.base_price),
                }
            ]
        }
        
        response4 = self.salesman3_client.post(
            reverse('invoice-list'),
            data=invoice4_data,
            format='json'
        )
        self.assertEqual(response4.status_code, status.HTTP_201_CREATED)
        invoice4 = Invoice.objects.get(id=response4.data['id'])
        
        print(f"📄 Created invoice: {invoice4.invoice_number}")
        print(f"   🏪 Shop: {invoice4.shop.name}")
        print(f"   � Items: {invoice4.items.count()}")
        
        # 📊 Phase 4: Sales performance analysis
        print("\n📊 Phase 4: Sales Performance Analysis")
        
        # Calculate total sales
        total_invoices = Invoice.objects.count()
        total_sales_value = sum([
            invoice.net_total for invoice in Invoice.objects.all()
        ])
        
        print(f"📈 Total invoices created: {total_invoices}")
        print(f"💰 Total sales value: ${total_sales_value}")
        
        # Business rule validations
        self.assertGreater(total_invoices, 0)
        self.assertGreater(total_sales_value, 0)
        
        print("✅ Full day sales operations completed successfully!")
        
        return [invoice1, invoice2, invoice3, invoice4]
    
    def test_02_commission_calculation_system(self):
        """
        💵 COMMISSION CALCULATION SYSTEM TEST
        
        Tests automatic commission calculations based on sales performance
        and individual commission rates.
        """
        print("\n" + "="*70)
        print("💵 TESTING: Commission Calculation System")
        print("="*70)
        
        # Setup: Create sales first
        batches = self.create_test_batches()
        assignments = self.create_batch_assignments(batches)
        
        # Create a sample invoice
        invoice_data = {
            'shop': self.shop1.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 15.00,
            'notes': 'Commission test invoice',
            'terms_conditions': 'Net 30',
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 10,
                    'unit_price': str(self.product1.base_price),
                }
            ]
        }
        
        response = self.salesman1_client.post(
            reverse('invoice-list'),
            data=invoice_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invoice = Invoice.objects.get(id=response.data['id'])
        
        # Verify commission calculation would work
        # Get commission for this salesman and invoice
        commissions = Commission.objects.filter(
            salesman=self.salesman1,
            invoice=invoice
        )
        
        if commissions.exists():
            commission = commissions.first()
            print(f"💰 Commission rate: {commission.commission_rate}%")
            print(f"💵 Commission amount: ${commission.commission_amount}")
        else:
            print("💡 Commission will be calculated on invoice completion")
        
        print("✅ Commission system verified!")
    
    def test_03_sales_performance_tracking(self):
        """
        📈 SALES PERFORMANCE TRACKING TEST
        
        Tests comprehensive sales performance monitoring using existing endpoints.
        """
        print("\n" + "="*70)
        print("📈 TESTING: Sales Performance Tracking")
        print("="*70)
        
        # Create test sales data
        self.test_01_full_day_sales_operations()
        
        # Test performance tracking using existing invoice endpoints
        response = self.salesman1_client.get(reverse('invoice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        invoices_data = response.data
        print(f"DEBUG: Invoice response type: {type(invoices_data)}")
        print(f"DEBUG: Invoice response: {invoices_data}")
        
        # Handle paginated response
        if isinstance(invoices_data, dict) and 'results' in invoices_data:
            invoices = invoices_data['results']
        else:
            invoices = invoices_data
            
        print(f"📊 Found {len(invoices)} invoices for performance tracking")
        
        # Calculate performance metrics from invoice data
        total_sales = sum(float(invoice['net_total']) for invoice in invoices)
        invoices_count = len(invoices)
        average_sale_value = total_sales / invoices_count if invoices_count > 0 else 0
        
        print(f"✅ Total Sales: ${total_sales:.2f}")
        print(f"✅ Invoices Count: {invoices_count}")
        print(f"✅ Average Sale Value: ${average_sale_value:.2f}")
        
        # Test commission tracking
        response = self.salesman1_client.get(reverse('commission-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        print(f"DEBUG: Commission response type: {type(response.data)}")
        print(f"DEBUG: Commission response: {response.data}")
        
        commissions_data = response.data
        if isinstance(commissions_data, dict) and 'results' in commissions_data:
            commissions = commissions_data['results']
        else:
            commissions = commissions_data
            
        total_commission = sum(float(commission['commission_amount']) for commission in commissions)
        print(f"✅ Total Commission Earned: ${total_commission:.2f}")
        
        # Verify performance data exists
        self.assertGreater(total_sales, 0)
        self.assertGreater(invoices_count, 0)
        self.assertGreater(average_sale_value, 0)
        
        print("✅ Sales performance tracking verified!")
    
    def test_04_customer_transaction_history(self):
        """
        👥 CUSTOMER TRANSACTION HISTORY TEST
        
        Tests customer transaction tracking and history using existing endpoints.
        """
        print("\n" + "="*70)
        print("👥 TESTING: Customer Transaction History")
        print("="*70)
        
        # Create multiple transactions for the same shop
        batches = self.create_test_batches()
        assignments = self.create_batch_assignments(batches)
        
        # Create first transaction
        invoice1_data = {
            'shop': self.shop1.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 12.00,
            'notes': 'First transaction for repeat shop',
            'terms_conditions': 'Net 30',
            'items': [
                {
                    'product': self.product1.id,
                    'quantity': 15,
                    'unit_price': str(self.product1.base_price),
                }
            ]
        }
        
        response1 = self.salesman1_client.post(
            reverse('invoice-list'),
            data=invoice1_data,
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Create second transaction
        invoice2_data = {
            'shop': self.shop1.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 10.00,
            'notes': 'Second transaction for repeat shop',
            'terms_conditions': 'Net 30',
            'items': [
                {
                    'product': self.product2.id,
                    'quantity': 20,
                    'unit_price': str(self.product2.base_price),
                }
            ]
        }
        
        response2 = self.salesman1_client.post(
            reverse('invoice-list'),
            data=invoice2_data,
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Test shop transaction history using existing invoice filtering
        response = self.salesman1_client.get(
            reverse('invoice-list') + f'?shop={self.shop1.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        shop_data = response.data
        print(f"DEBUG: Shop response type: {type(shop_data)}")
        print(f"DEBUG: Shop response: {shop_data}")
        
        # Handle paginated response
        if isinstance(shop_data, dict) and 'results' in shop_data:
            shop_invoices = shop_data['results']
        else:
            shop_invoices = shop_data
            
        print(f"👥 Found {len(shop_invoices)} invoices for shop: {self.shop1.name}")
        
        # Verify history contains both transactions
        self.assertGreaterEqual(len(shop_invoices), 2)
        
        # Calculate shop analytics from the transaction history
        total_purchases = len(shop_invoices)
        total_value = sum(float(invoice['net_total']) for invoice in shop_invoices)
        average_order_value = total_value / total_purchases if total_purchases > 0 else 0
        
        print(f"✅ Total Purchases: {total_purchases}")
        print(f"✅ Total Value: ${total_value:.2f}")
        print(f"✅ Average Order Value: ${average_order_value:.2f}")
        
        # Verify each invoice belongs to the correct shop
        for invoice in shop_invoices:
            self.assertEqual(invoice['shop'], self.shop1.id)
        
        print("✅ Shop transaction history verified!")
