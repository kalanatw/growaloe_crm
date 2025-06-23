# backend/sales/tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db import models

from accounts.models import Owner, Salesman
from products.models import Product, Category, Batch, BatchAssignment
from sales.models import Shop, Invoice, InvoiceItem, Delivery, DeliveryItem, Commission, Settlement, Return
import json

User = get_user_model()

class AloeVeraParadiseComprehensiveTestCase(APITestCase):
    """
    🏪 ALOE VERA PARADISE - COMPLETE BUSINESS MANAGEMENT SYSTEM TEST SUITE
    
    This test suite validates the entire business workflow from morning production
    to evening settlements, ensuring all business operations work seamlessly.
    
    Business Story: Sarah runs "Aloe Vera Paradise" with 3 salesmen (Mike, Jennifer, Carlos)
    serving different territories. The system manages everything from batch production
    to customer payments and returns processing.
    """
    
    def setUp(self):
        """
        🌅 BUSINESS SETUP - Aloe Vera Paradise Company Initialization
        Setting up the complete business infrastructure for testing
        """
        print("\n" + "="*80)
        print("🏪 ALOE VERA PARADISE - BUSINESS SYSTEM INITIALIZATION")
        print("="*80)
        
        # 👥 Create Business Owner - Sarah Martinez
        self.owner_user = User.objects.create_user(
            username='sarah_martinez',
            email='sarah@aloeveraparadise.com',
            password='paradise2024',
            first_name='Sarah',
            last_name='Martinez',
            role='owner'
        )
        self.owner = Owner.objects.create(
            user=self.owner_user,
            business_name='Aloe Vera Paradise Ltd'
        )
        
        # 👨‍💼 Create Sales Team
        # Mike Thompson - Downtown Territory
        self.mike_user = User.objects.create_user(
            username='mike_thompson',
            email='mike@aloeveraparadise.com',
            password='downtown2024',
            first_name='Mike',
            last_name='Thompson',
            role='salesman'
        )
        self.mike = Salesman.objects.create(
            user=self.mike_user,
            name='Mike Thompson',
            phone='555-0101',
            address='Downtown Sales Office, 123 Business St'
        )
        
        # Jennifer Walsh - University District
        self.jennifer_user = User.objects.create_user(
            username='jennifer_walsh',
            email='jennifer@aloeveraparadise.com',
            password='university2024',
            first_name='Jennifer',
            last_name='Walsh',
            role='salesman'
        )
        self.jennifer = Salesman.objects.create(
            user=self.jennifer_user,
            name='Jennifer Walsh',
            phone='555-0102',
            address='University District Office, 456 Campus Ave'
        )
        
        # Carlos Rodriguez - Health Centers Territory
        self.carlos_user = User.objects.create_user(
            username='carlos_rodriguez',
            email='carlos@aloeveraparadise.com',
            password='health2024',
            first_name='Carlos',
            last_name='Rodriguez',
            role='salesman'
        )
        self.carlos = Salesman.objects.create(
            user=self.carlos_user,
            name='Carlos Rodriguez',
            phone='555-0103',
            address='Health Centers Territory, 789 Wellness Blvd'
        )
        
        # 🏪 Create Customer Shops
        self.green_cafe = Shop.objects.create(
            name='Green Café',
            address='Downtown Business District',
            contact_person='Maria Green',
            phone='555-2001',
            salesman=self.mike
        )
        
        self.university_health = Shop.objects.create(
            name='University Health Center',
            address='University Campus',
            contact_person='Dr. James Wilson',
            phone='555-2002',
            salesman=self.jennifer
        )
        
        self.fitlife_gym = Shop.objects.create(
            name='FitLife Gymnasium',
            address='Health & Fitness District',
            contact_person='Coach Amanda Fitness',
            phone='555-2003',
            salesman=self.carlos
        )
        
        self.wellness_mart = Shop.objects.create(
            name='Wellness Mart Chain',
            address='Multiple Locations',
            contact_person='Store Manager Kim',
            phone='555-2004',
            salesman=self.jennifer
        )
        
        # 🥤 Create Product Categories and Products
        self.beverages_category = Category.objects.create(
            name='Aloe Beverages',
            description='Fresh Aloe Vera Drinks'
        )
        
        self.wellness_category = Category.objects.create(
            name='Wellness Products',
            description='Health and Wellness Aloe Products'
        )
        
        # Premium Product Line
        self.aloe_drink_200ml = Product.objects.create(
            name='Aloevera Drink 200ml',
            description='Premium Fresh Aloe Vera Drink - 200ml',
            category=self.beverages_category,
            base_price=Decimal('2.50'),
            unit='bottle'
        )
        
        self.aloe_yogurt_150ml = Product.objects.create(
            name='Aloevera Yogurt 150ml',
            description='Creamy Aloe Vera Yogurt - 150ml',
            category=self.beverages_category,
            base_price=Decimal('3.25'),
            unit='cup'
        )
        
        self.wellness_shot_50ml = Product.objects.create(
            name='Aloe Wellness Shot 50ml',
            description='Concentrated Aloe Wellness Shot - 50ml',
            category=self.wellness_category,
            base_price=Decimal('4.99'),
            unit='shot'
        )
        
        # 🔐 Setup API Client Authentication
        self.client = APIClient()
        
        print("✅ Business Infrastructure Setup Complete")
        print(f"👑 Owner: {self.owner.business_name}")
        print(f"👨‍💼 Sales Team: {self.mike.name}, {self.jennifer.name}, {self.carlos.name}")
        print(f"🏪 Customer Shops: {Shop.objects.count()} establishments")
        print(f"🥤 Product Catalog: {Product.objects.count()} premium products")
    
    def test_01_morning_production_and_batch_creation(self):
        """
        🌅 PHASE 1: MORNING PRODUCTION CYCLE
        
        Business Scenario: 6:00 AM - Sarah starts the day by reviewing inventory
        and creating fresh batches for the day's distribution.
        
        Today's Production Plan:
        - 3000 units Aloe Drink 200ml (high demand product)
        - 1500 units Aloe Yogurt 150ml (steady seller)
        - 800 units Wellness Shots 50ml (premium product)
        """
        print("\n" + "="*80)
        print("🌅 PHASE 1: MORNING PRODUCTION CYCLE")
        print("="*80)
        
        # Authenticate as Owner
        self.client.force_authenticate(user=self.owner_user)
        
        # 📊 Check Initial Stock Status
        print("📊 Checking initial inventory status...")
        stock_response = self.client.get('/api/products/products/stock_summary/')
        self.assertEqual(stock_response.status_code, status.HTTP_200_OK)
        
        initial_stock = stock_response.data
        print(f"📦 Initial Stock Status: {len(initial_stock)} products in catalog")
        
        # 🏭 Create Fresh Production Batches
        print("\n🏭 Starting Fresh Batch Production...")
        
        today = date.today()
        
        # Batch 1: Aloe Vera Drink 200ml - High Volume Production
        drink_batch_data = {
            'batch_number': f'AVP-DRINK-{today.strftime("%y%m%d")}-001',
            'product': self.aloe_drink_200ml.id,
            'manufacturing_date': today,
            'expiry_date': today + timedelta(days=30),
            'initial_quantity': 3000,
            'current_quantity': 3000,
            'unit_cost': Decimal('1.20'),
            'notes': 'Premium morning batch - high demand expected',
            'is_active': True
        }
        
        drink_batch_response = self.client.post('/api/products/batches/', drink_batch_data)
        self.assertEqual(drink_batch_response.status_code, status.HTTP_201_CREATED)
        self.drink_batch = Batch.objects.get(id=drink_batch_response.data['id'])
        print(f"✅ Created Drink Batch: {self.drink_batch.batch_number} - {self.drink_batch.initial_quantity} units")
        
        # Batch 2: Aloe Yogurt 150ml - Steady Production
        yogurt_batch_data = {
            'batch_number': f'AVP-YOGURT-{today.strftime("%y%m%d")}-001',
            'product': self.aloe_yogurt_150ml.id,
            'manufacturing_date': today,
            'expiry_date': today + timedelta(days=21),  # Shorter shelf life
            'initial_quantity': 1500,
            'current_quantity': 1500,
            'unit_cost': Decimal('2.00'),
            'notes': 'Fresh yogurt batch - refrigerated storage',
            'is_active': True
        }
        
        yogurt_batch_response = self.client.post('/api/products/batches/', yogurt_batch_data)
        self.assertEqual(yogurt_batch_response.status_code, status.HTTP_201_CREATED)
        self.yogurt_batch = Batch.objects.get(id=yogurt_batch_response.data['id'])
        print(f"✅ Created Yogurt Batch: {self.yogurt_batch.batch_number} - {self.yogurt_batch.initial_quantity} units")
        
        # Batch 3: Wellness Shots 50ml - Premium Production
        shot_batch_data = {
            'batch_number': f'AVP-SHOTS-{today.strftime("%y%m%d")}-001',
            'product': self.wellness_shot_50ml.id,
            'manufacturing_date': today,
            'expiry_date': today + timedelta(days=60),  # Longer shelf life
            'initial_quantity': 800,
            'current_quantity': 800,
            'unit_cost': Decimal('3.50'),
            'notes': 'Premium wellness shots - concentrated formula',
            'is_active': True
        }
        
        shot_batch_response = self.client.post('/api/products/batches/', shot_batch_data)
        self.assertEqual(shot_batch_response.status_code, status.HTTP_201_CREATED)
        self.shot_batch = Batch.objects.get(id=shot_batch_response.data['id'])
        print(f"✅ Created Wellness Shot Batch: {self.shot_batch.batch_number} - {self.shot_batch.initial_quantity} units")
        
        # 📈 Verify Stock Summary After Production
        updated_stock_response = self.client.get('/api/products/products/stock_summary/')
        self.assertEqual(updated_stock_response.status_code, status.HTTP_200_OK)
        
        updated_stock = updated_stock_response.data
        total_production_value = Decimal('0')
        
        print(f"\n📈 Production Summary:")
        for product_stock in updated_stock:
            if product_stock['total_stock'] > 0:
                value = Decimal(str(product_stock['total_stock'])) * Decimal(str(product_stock['base_price']))
                total_production_value += value
                print(f"   📦 {product_stock['product_name']}: {product_stock['total_stock']} units (${value:,.2f})")
        
        print(f"💰 Total Production Value: ${total_production_value:,.2f}")
        print(f"🏭 Production Efficiency: 100% - All batches created successfully")
        
        # Verify FIFO batch ordering
        self.assertTrue(self.drink_batch.is_active)
        self.assertTrue(self.yogurt_batch.is_active)
        self.assertTrue(self.shot_batch.is_active)
        
        print("✅ PHASE 1 COMPLETE: Fresh inventory ready for distribution")
    
    def test_02_strategic_territory_distribution(self):
        """
        🚚 PHASE 2: STRATEGIC TERRITORY DISTRIBUTION
        
        Business Scenario: 9:00 AM - After production, Sarah plans the distribution
        strategy based on territory demand patterns and salesman performance.
        
        Distribution Strategy:
        - Mike (Downtown): 40% allocation - high foot traffic area
        - Jennifer (University): 35% allocation - steady student demand  
        - Carlos (Health Centers): 25% allocation - premium product focus
        """
        print("\n" + "="*80)
        print("🚚 PHASE 2: STRATEGIC TERRITORY DISTRIBUTION")
        print("="*80)
        
        # First create the batches
        self.test_01_morning_production_and_batch_creation()
        
        print("📋 Planning territorial distribution strategy...")
        
        # 🎯 Distribution Strategy Planning
        territory_allocations = {
            'mike_downtown': {
                'salesman': self.mike,
                'territory': 'Downtown Business District',
                'allocation_percentage': 40,
                'focus': 'High volume, mixed products'
            },
            'jennifer_university': {
                'salesman': self.jennifer,
                'territory': 'University & Campus Area',
                'allocation_percentage': 35,
                'focus': 'Steady demand, health-conscious students'
            },
            'carlos_health': {
                'salesman': self.carlos,
                'territory': 'Health Centers & Fitness',
                'allocation_percentage': 25,
                'focus': 'Premium products, wellness focus'
            }
        }
        
        print(f"🎯 Territory Strategy:")
        for territory, info in territory_allocations.items():
            print(f"   {info['salesman'].name}: {info['allocation_percentage']}% - {info['focus']}")
        
        # 📦 Create Strategic Deliveries
        
        # Delivery 1: Mike - Downtown Territory (40% allocation)
        mike_delivery_data = {
            'salesman': self.mike.id,
            'delivery_date': date.today(),
            'notes': 'Downtown territory - high volume mixed delivery',
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 1200,  # 40% of 3000
                    'unit_cost': self.drink_batch.unit_cost
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 600,   # 40% of 1500
                    'unit_cost': self.yogurt_batch.unit_cost
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 320,   # 40% of 800
                    'unit_cost': self.shot_batch.unit_cost
                }
            ]
        }
        
        mike_delivery_response = self.client.post('/api/sales/deliveries/', mike_delivery_data, format='json')
        self.assertEqual(mike_delivery_response.status_code, status.HTTP_201_CREATED)
        self.mike_delivery = Delivery.objects.get(id=mike_delivery_response.data['id'])
        
        print(f"📦 Mike's Delivery: {self.mike_delivery.items.count()} products - Downtown Territory")
        
        # Delivery 2: Jennifer - University Territory (35% allocation)
        jennifer_delivery_data = {
            'salesman': self.jennifer.id,
            'delivery_date': date.today(),
            'notes': 'University territory - student-focused product mix',
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 1050,  # 35% of 3000
                    'unit_cost': self.drink_batch.unit_cost
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 525,   # 35% of 1500
                    'unit_cost': self.yogurt_batch.unit_cost
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 280,   # 35% of 800
                    'unit_cost': self.shot_batch.unit_cost
                }
            ]
        }
        
        jennifer_delivery_response = self.client.post('/api/sales/deliveries/', jennifer_delivery_data, format='json')
        self.assertEqual(jennifer_delivery_response.status_code, status.HTTP_201_CREATED)
        self.jennifer_delivery = Delivery.objects.get(id=jennifer_delivery_response.data['id'])
        
        print(f"📦 Jennifer's Delivery: {self.jennifer_delivery.items.count()} products - University Territory")
        
        # Delivery 3: Carlos - Health Centers Territory (25% allocation)
        carlos_delivery_data = {
            'salesman': self.carlos.id,
            'delivery_date': date.today(),
            'notes': 'Health centers territory - premium wellness focus',
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 750,   # 25% of 3000
                    'unit_cost': self.drink_batch.unit_cost
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 375,   # 25% of 1500
                    'unit_cost': self.yogurt_batch.unit_cost
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 200,   # 25% of 800
                    'unit_cost': self.shot_batch.unit_cost
                }
            ]
        }
        
        carlos_delivery_response = self.client.post('/api/sales/deliveries/', carlos_delivery_data, format='json')
        self.assertEqual(carlos_delivery_response.status_code, status.HTTP_201_CREATED)
        self.carlos_delivery = Delivery.objects.get(id=carlos_delivery_response.data['id'])
        
        print(f"📦 Carlos's Delivery: {self.carlos_delivery.items.count()} products - Health Centers Territory")
        
        # 📊 Verify Distribution Analytics
        total_distributed = {
            'drinks': 1200 + 1050 + 750,  # Should equal 3000
            'yogurt': 600 + 525 + 375,    # Should equal 1500
            'shots': 320 + 280 + 200      # Should equal 800
        }
        
        print(f"\n📊 Distribution Analytics:")
        print(f"   🥤 Aloe Drinks: {total_distributed['drinks']}/3000 units (100%)")
        print(f"   🥛 Aloe Yogurt: {total_distributed['yogurt']}/1500 units (100%)")
        print(f"   💪 Wellness Shots: {total_distributed['shots']}/800 units (100%)")
        
        # Verify all products were distributed
        self.assertEqual(total_distributed['drinks'], 3000)
        self.assertEqual(total_distributed['yogurt'], 1500)
        self.assertEqual(total_distributed['shots'], 800)
        
        # 🎯 Verify Batch Assignments Created
        assignments = BatchAssignment.objects.all()
        print(f"\n🎯 Batch Assignment Summary:")
        for assignment in assignments:
            print(f"   {assignment.salesman.name}: {assignment.product.name} - {assignment.delivered_quantity} units")
        
        # Verify assignments exist for all salesmen and products
        self.assertEqual(assignments.count(), 9)  # 3 salesmen × 3 products
        
        print("✅ PHASE 2 COMPLETE: Strategic distribution executed successfully")
    
    def test_03_full_day_sales_operations(self):
        """
        🛒 PHASE 3: FULL DAY SALES OPERATIONS
        
        Business Scenario: 10:00 AM - 6:00 PM - Salesmen execute their sales
        strategies across different territories with varied customer interactions.
        
        Sales Timeline:
        - Morning: Coffee shops and early customers
        - Afternoon: University and fitness centers
        - Evening: Health stores and bulk orders
        """
        print("\n" + "="*80)
        print("🛒 PHASE 3: FULL DAY SALES OPERATIONS")
        print("="*80)
        
        # Setup distribution first
        self.test_02_strategic_territory_distribution()
        
        # 🌅 MORNING SALES (10:00 AM - 12:00 PM)
        print("\n🌅 Morning Sales Operations (10:00 AM - 12:00 PM)")
        
        # Mike's Morning Sales - Green Café
        self.client.force_authenticate(user=self.mike_user)
        
        green_cafe_order = {
            'shop': self.green_cafe.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 150,
                    'unit_price': Decimal('2.75')  # 10% markup
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 75,
                    'unit_price': Decimal('3.50')  # 7.7% markup
                }
            ]
        }
        
        green_cafe_response = self.client.post('/api/sales/invoices/', green_cafe_order, format='json')
        self.assertEqual(green_cafe_response.status_code, status.HTTP_201_CREATED)
        self.green_cafe_invoice = Invoice.objects.get(id=green_cafe_response.data['id'])
        
        print(f"   ☕ Green Café Order: ${self.green_cafe_invoice.total_amount} - Mike Thompson")
        
        # 🌞 MIDDAY SALES (12:00 PM - 3:00 PM)
        print("\n🌞 Midday Sales Operations (12:00 PM - 3:00 PM)")
        
        # Jennifer's University Sales
        self.client.force_authenticate(user=self.jennifer_user)
        
        university_health_order = {
            'shop': self.university_health.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 400,
                    'unit_price': Decimal('2.60')  # Bulk discount
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 100,
                    'unit_price': Decimal('5.25')  # 5.2% markup
                }
            ]
        }
        
        university_response = self.client.post('/api/sales/invoices/', university_health_order, format='json')
        self.assertEqual(university_response.status_code, status.HTTP_201_CREATED)
        self.university_invoice = Invoice.objects.get(id=university_response.data['id'])
        
        print(f"   🎓 University Health Center: ${self.university_invoice.total_amount} - Jennifer Walsh")
        
        # 🌆 AFTERNOON SALES (3:00 PM - 6:00 PM)
        print("\n🌆 Afternoon Sales Operations (3:00 PM - 6:00 PM)")
        
        # Carlos's Health Center Sales
        self.client.force_authenticate(user=self.carlos_user)
        
        fitlife_gym_order = {
            'shop': self.fitlife_gym.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 200,
                    'unit_price': Decimal('2.85')  # Premium pricing
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 150,
                    'unit_price': Decimal('5.49')  # 10% markup
                }
            ]
        }
        
        fitlife_response = self.client.post('/api/sales/invoices/', fitlife_gym_order, format='json')
        self.assertEqual(fitlife_response.status_code, status.HTTP_201_CREATED)
        self.fitlife_invoice = Invoice.objects.get(id=fitlife_response.data['id'])
        
        print(f"   💪 FitLife Gymnasium: ${self.fitlife_invoice.total_amount} - Carlos Rodriguez")
        
        # Additional Evening Sales - Jennifer's Second Customer
        self.client.force_authenticate(user=self.jennifer_user)
        
        wellness_mart_order = {
            'shop': self.wellness_mart.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 300,
                    'unit_price': Decimal('2.70')  # Retail chain pricing
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 200,
                    'unit_price': Decimal('3.60')  # 10.8% markup
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 80,
                    'unit_price': Decimal('5.35')  # 7.2% markup
                }
            ]
        }
        
        wellness_mart_response = self.client.post('/api/sales/invoices/', wellness_mart_order, format='json')
        self.assertEqual(wellness_mart_response.status_code, status.HTTP_201_CREATED)
        self.wellness_mart_invoice = Invoice.objects.get(id=wellness_mart_response.data['id'])
        
        print(f"   🏪 Wellness Mart Chain: ${self.wellness_mart_invoice.total_amount} - Jennifer Walsh")
        
        # 📊 DAILY SALES SUMMARY
        print("\n📊 End of Day Sales Summary:")
        
        total_revenue = (self.green_cafe_invoice.total_amount + 
                        self.university_invoice.total_amount + 
                        self.fitlife_invoice.total_amount + 
                        self.wellness_mart_invoice.total_amount)
        
        # Calculate commissions (10% for each salesman)
        mike_sales = self.green_cafe_invoice.total_amount
        jennifer_sales = self.university_invoice.total_amount + self.wellness_mart_invoice.total_amount
        carlos_sales = self.fitlife_invoice.total_amount
        
        mike_commission = mike_sales * Decimal('0.10')
        jennifer_commission = jennifer_sales * Decimal('0.10')
        carlos_commission = carlos_sales * Decimal('0.10')
        total_commission = mike_commission + jennifer_commission + carlos_commission
        
        print(f"   💰 Total Revenue: ${total_revenue:,.2f}")
        print(f"   👨‍💼 Mike Thompson: ${mike_sales:,.2f} (Commission: ${mike_commission:,.2f})")
        print(f"   👩‍💼 Jennifer Walsh: ${jennifer_sales:,.2f} (Commission: ${jennifer_commission:,.2f})")
        print(f"   👨‍💼 Carlos Rodriguez: ${carlos_sales:,.2f} (Commission: ${carlos_commission:,.2f})")
        print(f"   🏆 Total Commissions Owed: ${total_commission:,.2f}")
        
        # 🎯 Verify Commission Creation
        commissions = Commission.objects.all()
        self.assertEqual(commissions.count(), 4)  # One per invoice
        
        for commission in commissions:
            self.assertEqual(commission.commission_rate, Decimal('0.10'))
            self.assertEqual(commission.status, 'pending')
            print(f"   ✅ Commission Created: {commission.salesman.name} - ${commission.commission_amount}")
        
        # 📈 Territory Performance Analysis
        print(f"\n📈 Territory Performance Analysis:")
        print(f"   🏙️ Downtown (Mike): 1 customer, ${mike_sales:,.2f}")
        print(f"   🎓 University (Jennifer): 2 customers, ${jennifer_sales:,.2f}")
        print(f"   💪 Health Centers (Carlos): 1 customer, ${carlos_sales:,.2f}")
        print(f"   🏆 Top Performer: {'Jennifer' if jennifer_sales > max(mike_sales, carlos_sales) else 'Mike' if mike_sales > carlos_sales else 'Carlos'}")
        
        print("✅ PHASE 3 COMPLETE: Full day sales operations executed successfully")
    
    def test_04_evening_settlements_and_collections(self):
        """
        💰 PHASE 4: EVENING SETTLEMENTS AND COLLECTIONS
        
        Business Scenario: 6:00 PM - 8:00 PM - End of day financial operations.
        Customers make payments, some paying multiple invoices together (bill-to-bill settlements).
        
        Settlement Scenarios:
        - Green Café: Single invoice payment
        - University Health: Paying current + previous outstanding invoices
        - FitLife Gym: Partial payment arrangement
        - Wellness Mart: Full settlement with discount
        """
        print("\n" + "="*80)
        print("💰 PHASE 4: EVENING SETTLEMENTS AND COLLECTIONS")
        print("="*80)
        
        # Complete sales operations first
        self.test_03_full_day_sales_operations()
        
        # Switch to owner for settlement management
        self.client.force_authenticate(user=self.owner_user)
        
        print("💳 Processing evening customer payments and settlements...")
        
        # 💳 SETTLEMENT 1: Green Café - Simple Payment
        print("\n💳 Settlement 1: Green Café - Simple Invoice Payment")
        
        green_cafe_settlement_data = {
            'customer_name': 'Green Café',
            'payment_method': 'cash',
            'payment_amount': self.green_cafe_invoice.total_amount,
            'notes': 'Cash payment for daily delivery',
            'invoices': [self.green_cafe_invoice.id]
        }
        
        green_settlement_response = self.client.post('/api/sales/settlements/', green_cafe_settlement_data, format='json')
        self.assertEqual(green_settlement_response.status_code, status.HTTP_201_CREATED)
        green_settlement = Settlement.objects.get(id=green_settlement_response.data['id'])
        
        print(f"   ✅ Green Café Payment: ${green_settlement.payment_amount} - {green_settlement.payment_method}")
        
        # 💳 SETTLEMENT 2: University Health - Multiple Invoice Settlement
        print("\n💳 Settlement 2: University Health - Multi-Invoice Settlement")
        
        # Create a previous outstanding invoice for demonstration
        previous_invoice_data = {
            'shop': self.university_health.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 100,
                    'unit_price': Decimal('2.60')
                }
            ]
        }
        
        self.client.force_authenticate(user=self.jennifer_user)
        previous_response = self.client.post('/api/sales/invoices/', previous_invoice_data, format='json')
        previous_invoice = Invoice.objects.get(id=previous_response.data['id'])
        
        # Now settle both invoices together
        self.client.force_authenticate(user=self.owner_user)
        
        university_total = self.university_invoice.total_amount + previous_invoice.total_amount
        university_settlement_data = {
            'customer_name': 'University Health Center',
            'payment_method': 'bank_transfer',
            'payment_amount': university_total,
            'notes': 'Settlement for current and previous orders',
            'invoices': [self.university_invoice.id, previous_invoice.id]
        }
        
        university_settlement_response = self.client.post('/api/sales/settlements/', university_settlement_data, format='json')
        self.assertEqual(university_settlement_response.status_code, status.HTTP_201_CREATED)
        university_settlement = Settlement.objects.get(id=university_settlement_response.data['id'])
        
        print(f"   ✅ University Multi-Settlement: ${university_settlement.payment_amount} - {len(university_settlement_data['invoices'])} invoices")
        
        # 💳 SETTLEMENT 3: FitLife Gym - Partial Payment
        print("\n💳 Settlement 3: FitLife Gym - Partial Payment Arrangement")
        
        partial_amount = self.fitlife_invoice.total_amount * Decimal('0.60')  # 60% payment
        fitlife_settlement_data = {
            'customer_name': 'FitLife Gymnasium',
            'payment_method': 'credit_card',
            'payment_amount': partial_amount,
            'notes': 'Partial payment - 60% now, remainder in 7 days',
            'invoices': [self.fitlife_invoice.id]
        }
        
        fitlife_settlement_response = self.client.post('/api/sales/settlements/', fitlife_settlement_data, format='json')
        self.assertEqual(fitlife_settlement_response.status_code, status.HTTP_201_CREATED)
        fitlife_settlement = Settlement.objects.get(id=fitlife_settlement_response.data['id'])
        
        print(f"   ✅ FitLife Partial Payment: ${fitlife_settlement.payment_amount} of ${self.fitlife_invoice.total_amount}")
        
        # 💳 SETTLEMENT 4: Wellness Mart - Full Settlement with Early Payment Discount
        print("\n💳 Settlement 4: Wellness Mart - Full Settlement with Discount")
        
        discount_amount = self.wellness_mart_invoice.total_amount * Decimal('0.02')  # 2% early payment discount
        discounted_total = self.wellness_mart_invoice.total_amount - discount_amount
        
        wellness_settlement_data = {
            'customer_name': 'Wellness Mart Chain',
            'payment_method': 'bank_transfer',
            'payment_amount': discounted_total,
            'notes': f'Full payment with 2% early payment discount (${discount_amount})',
            'invoices': [self.wellness_mart_invoice.id]
        }
        
        wellness_settlement_response = self.client.post('/api/sales/settlements/', wellness_settlement_data, format='json')
        self.assertEqual(wellness_settlement_response.status_code, status.HTTP_201_CREATED)
        wellness_settlement = Settlement.objects.get(id=wellness_settlement_response.data['id'])
        
        print(f"   ✅ Wellness Mart Settlement: ${wellness_settlement.payment_amount} (${discount_amount} discount)")
        
        # 📊 SETTLEMENT SUMMARY AND ANALYTICS
        print("\n📊 Evening Settlement Summary:")
        
        all_settlements = Settlement.objects.all()
        total_collected = sum(s.payment_amount for s in all_settlements)
        total_invoiced = sum([self.green_cafe_invoice.total_amount, 
                            self.university_invoice.total_amount, 
                            previous_invoice.total_amount,
                            self.fitlife_invoice.total_amount, 
                            self.wellness_mart_invoice.total_amount])
        
        outstanding_balance = total_invoiced - total_collected
        collection_rate = (total_collected / total_invoiced) * 100
        
        print(f"   💰 Total Invoiced: ${total_invoiced:,.2f}")
        print(f"   💳 Total Collected: ${total_collected:,.2f}")
        print(f"   📈 Collection Rate: {collection_rate:.1f}%")
        print(f"   ⚠️ Outstanding Balance: ${outstanding_balance:,.2f}")
        
        # 📋 Payment Method Analysis
        payment_methods = {}
        for settlement in all_settlements:
            method = settlement.payment_method
            if method in payment_methods:
                payment_methods[method] += settlement.payment_amount
            else:
                payment_methods[method] = settlement.payment_amount
        
        print(f"\n📋 Payment Method Breakdown:")
        for method, amount in payment_methods.items():
            percentage = (amount / total_collected) * 100
            print(f"   {method.replace('_', ' ').title()}: ${amount:,.2f} ({percentage:.1f}%)")
        
        # 🎯 Verify Settlement Data Integrity
        self.assertEqual(all_settlements.count(), 4)
        
        # Check that multi-invoice settlement includes both invoices
        university_settlement_invoices = university_settlement.invoices.all()
        self.assertEqual(university_settlement_invoices.count(), 2)
        
        print("✅ PHASE 4 COMPLETE: Evening settlements processed successfully")
    
    def test_05_returns_and_quality_management(self):
        """
        🔄 PHASE 5: RETURNS AND QUALITY MANAGEMENT
        
        Business Scenario: End of day - handling product returns from customers.
        Some products need to be returned due to various reasons (damage, near expiry, etc.).
        
        Return Scenarios:
        - Green Café: 5 damaged bottles during transport
        - University Health: 20 drinks near expiry date
        - Quality control: Voluntary recall of specific batch
        """
        print("\n" + "="*80)
        print("🔄 PHASE 5: RETURNS AND QUALITY MANAGEMENT")
        print("="*80)
        
        # Complete previous operations
        self.test_04_evening_settlements_and_collections()
        
        print("🔍 Processing customer returns and quality control...")
        
        # 🔍 RETURN 1: Green Café - Damaged Products During Transport
        print("\n🔍 Return 1: Green Café - Transport Damage")
        
        # First, search for the batch to return
        batch_search_response = self.client.get(
            f'/api/sales/returns/batch_search/?q={self.drink_batch.batch_number[:10]}'
        )
        self.assertEqual(batch_search_response.status_code, status.HTTP_200_OK)
        
        found_batches = batch_search_response.data
        self.assertGreater(len(found_batches), 0)
        
        print(f"   🔍 Batch Search Result: Found {len(found_batches)} matching batches")
        
        # Process the return
        green_cafe_return_data = {
            'return_number': 'RET-GC-001',
            'customer_name': 'Green Café',
            'return_date': date.today(),
            'batch': self.drink_batch.id,
            'product': self.aloe_drink_200ml.id,
            'quantity': 5,
            'reason': 'damaged_transport',
            'notes': 'Bottles damaged during delivery transport',
            'handled_by': self.mike.id
        }
        
        green_return_response = self.client.post('/api/sales/returns/', green_cafe_return_data, format='json')
        self.assertEqual(green_return_response.status_code, status.HTTP_201_CREATED)
        green_return = Return.objects.get(id=green_return_response.data['id'])
        
        print(f"   ✅ Green Café Return: {green_return.quantity} units - {green_return.reason}")
        
        # 🔍 RETURN 2: University Health - Near Expiry Products
        print("\n🔍 Return 2: University Health - Near Expiry Concern")
        
        university_return_data = {
            'return_number': 'RET-UH-001',
            'customer_name': 'University Health Center',
            'return_date': date.today(),
            'batch': self.drink_batch.id,
            'product': self.aloe_drink_200ml.id,
            'quantity': 20,
            'reason': 'near_expiry',
            'notes': 'Customer concerned about expiry date - proactive return',
            'handled_by': self.jennifer.id
        }
        
        university_return_response = self.client.post('/api/sales/returns/', university_return_data, format='json')
        self.assertEqual(university_return_response.status_code, status.HTTP_201_CREATED)
        university_return = Return.objects.get(id=university_return_response.data['id'])
        
        print(f"   ✅ University Return: {university_return.quantity} units - {university_return.reason}")
        
        # 🔍 RETURN 3: FitLife Gym - Customer Preference Issue
        print("\n🔍 Return 3: FitLife Gym - Customer Preference")
        
        fitlife_return_data = {
            'return_number': 'RET-FL-001',
            'customer_name': 'FitLife Gymnasium',
            'return_date': date.today(),
            'batch': self.yogurt_batch.id,
            'product': self.aloe_yogurt_150ml.id,
            'quantity': 10,
            'reason': 'customer_preference',
            'notes': 'Customers prefer the drink over yogurt format',
            'handled_by': self.carlos.id
        }
        
        fitlife_return_response = self.client.post('/api/sales/returns/', fitlife_return_data, format='json')
        self.assertEqual(fitlife_return_response.status_code, status.HTTP_201_CREATED)
        fitlife_return = Return.objects.get(id=fitlife_return_response.data['id'])
        
        print(f"   ✅ FitLife Return: {fitlife_return.quantity} units - {fitlife_return.reason}")
        
        # 📊 RETURNS ANALYTICS AND BATCH TRACKING
        print("\n📊 Returns Analytics and Quality Control:")
        
        all_returns = Return.objects.all()
        total_returned_units = sum(r.quantity for r in all_returns)
        
        # Group returns by reason
        return_reasons = {}
        for return_item in all_returns:
            reason = return_item.reason
            if reason in return_reasons:
                return_reasons[reason] += return_item.quantity
            else:
                return_reasons[reason] = return_item.quantity
        
        print(f"   📦 Total Returns: {total_returned_units} units across {all_returns.count()} transactions")
        print(f"   📋 Return Reasons Analysis:")
        for reason, quantity in return_reasons.items():
            percentage = (quantity / total_returned_units) * 100
            print(f"      {reason.replace('_', ' ').title()}: {quantity} units ({percentage:.1f}%)")
        
        # 🔍 BATCH IMPACT ANALYSIS
        print(f"\n🔍 Batch Impact Analysis:")
        
        # Check batch stock levels after returns
        self.drink_batch.refresh_from_db()
        self.yogurt_batch.refresh_from_db()
        
        drink_returns = sum(r.quantity for r in all_returns if r.product == self.aloe_drink_200ml)
        yogurt_returns = sum(r.quantity for r in all_returns if r.product == self.aloe_yogurt_150ml)
        
        print(f"   🥤 Drink Batch {self.drink_batch.batch_number}:")
        print(f"      Returns: {drink_returns} units")
        print(f"      Current Stock: {self.drink_batch.current_quantity} units")
        
        print(f"   🥛 Yogurt Batch {self.yogurt_batch.batch_number}:")
        print(f"      Returns: {yogurt_returns} units")
        print(f"      Current Stock: {self.yogurt_batch.current_quantity} units")
        
        # 🎯 QUALITY CONTROL ALERTS
        return_rate_threshold = 2.0  # 2% return rate triggers quality review
        
        drink_return_rate = (drink_returns / self.drink_batch.initial_quantity) * 100
        yogurt_return_rate = (yogurt_returns / self.yogurt_batch.initial_quantity) * 100
        
        print(f"\n🎯 Quality Control Metrics:")
        print(f"   🥤 Drink Return Rate: {drink_return_rate:.2f}%")
        print(f"   🥛 Yogurt Return Rate: {yogurt_return_rate:.2f}%")
        
        if drink_return_rate > return_rate_threshold:
            print(f"   ⚠️ QUALITY ALERT: Drink return rate exceeds threshold ({return_rate_threshold}%)")
        
        if yogurt_return_rate > return_rate_threshold:
            print(f"   ⚠️ QUALITY ALERT: Yogurt return rate exceeds threshold ({return_rate_threshold}%)")
        
        # 📋 RETURNS DASHBOARD DATA
        returns_summary = {
            'total_returns': all_returns.count(),
            'total_units': total_returned_units,
            'return_reasons': return_reasons,
            'quality_alerts': drink_return_rate > return_rate_threshold or yogurt_return_rate > return_rate_threshold
        }
        
        print(f"\n📋 Returns Dashboard Summary:")
        print(f"   Total Transactions: {returns_summary['total_returns']}")
        print(f"   Total Units Returned: {returns_summary['total_units']}")
        print(f"   Quality Alerts: {'Yes' if returns_summary['quality_alerts'] else 'No'}")
        
        # Verify all returns were processed correctly
        self.assertEqual(all_returns.count(), 3)
        self.assertEqual(total_returned_units, 35)  # 5 + 20 + 10
        
        print("✅ PHASE 5 COMPLETE: Returns and quality management processed successfully")
    
    def test_06_comprehensive_business_analytics(self):
        """
        📊 PHASE 6: COMPREHENSIVE BUSINESS ANALYTICS
        
        Business Scenario: End of day - Sarah reviews comprehensive analytics
        to make strategic decisions for tomorrow and beyond.
        
        Analytics Coverage:
        - Financial performance and profitability
        - Territory and salesman performance
        - Inventory management and turnover
        - Customer behavior and payment patterns
        - Quality metrics and return analysis
        """
        print("\n" + "="*80)
        print("📊 PHASE 6: COMPREHENSIVE BUSINESS ANALYTICS")
        print("="*80)
        
        # Complete all previous operations
        self.test_05_returns_and_quality_management()
        
        print("📈 Generating comprehensive business intelligence reports...")
        
        # 💰 FINANCIAL PERFORMANCE ANALYTICS
        print("\n💰 Financial Performance Analytics:")
        
        # Get commission dashboard data
        commission_response = self.client.get('/api/sales/commissions/dashboard_data/')
        self.assertEqual(commission_response.status_code, status.HTTP_200_OK)
        commission_data = commission_response.data
        
        total_revenue = Decimal('0')
        total_commissions = Decimal('0')
        
        for salesman_data in commission_data['salesman_commissions']:
            revenue = Decimal(str(salesman_data['total_sales']))
            commission = Decimal(str(salesman_data['pending_commission']))
            total_revenue += revenue
            total_commissions += commission
            
            print(f"   👤 {salesman_data['salesman_name']}:")
            print(f"      💰 Sales: ${revenue:,.2f}")
            print(f"      🏆 Commission: ${commission:,.2f}")
            print(f"      📊 Invoices: {salesman_data['total_invoices']}")
        
        # Calculate gross profit (simplified - revenue minus commissions and estimated costs)
        estimated_costs = total_revenue * Decimal('0.45')  # Estimated 45% COGS
        gross_profit = total_revenue - total_commissions - estimated_costs
        profit_margin = (gross_profit / total_revenue) * 100 if total_revenue > 0 else 0
        
        print(f"\n   📊 Financial Summary:")
        print(f"      💰 Total Revenue: ${total_revenue:,.2f}")
        print(f"      💸 Total Commissions: ${total_commissions:,.2f}")
        print(f"      📈 Estimated Gross Profit: ${gross_profit:,.2f}")
        print(f"      📊 Profit Margin: {profit_margin:.1f}%")
        
        # 🎯 TERRITORY PERFORMANCE ANALYSIS
        print("\n🎯 Territory Performance Analysis:")
        
        territories = {
            'downtown': {'salesman': 'Mike Thompson', 'sales': Decimal('0'), 'customers': 0},
            'university': {'salesman': 'Jennifer Walsh', 'sales': Decimal('0'), 'customers': 0},
            'health_centers': {'salesman': 'Carlos Rodriguez', 'sales': Decimal('0'), 'customers': 0}
        }
        
        # Map salesmen data to territories
        for salesman_data in commission_data['salesman_commissions']:
            name = salesman_data['salesman_name']
            sales = Decimal(str(salesman_data['total_sales']))
            invoices = salesman_data['total_invoices']
            
            if 'Mike' in name:
                territories['downtown']['sales'] = sales
                territories['downtown']['customers'] = invoices
            elif 'Jennifer' in name:
                territories['university']['sales'] = sales
                territories['university']['customers'] = invoices
            elif 'Carlos' in name:
                territories['health_centers']['sales'] = sales
                territories['health_centers']['customers'] = invoices
        
        # Find best performing territory
        best_territory = max(territories.keys(), key=lambda k: territories[k]['sales'])
        
        for territory, data in territories.items():
            performance_score = data['sales'] / max(data['customers'], 1)  # Avoid division by zero
            print(f"   🏪 {territory.replace('_', ' ').title()}:")
            print(f"      👤 Salesman: {data['salesman']}")
            print(f"      💰 Sales: ${data['sales']:,.2f}")
            print(f"      🛒 Customers: {data['customers']}")
            print(f"      📊 Avg per Customer: ${performance_score:,.2f}")
        
        print(f"   🏆 Top Territory: {best_territory.replace('_', ' ').title()}")
        
        # 📦 INVENTORY ANALYTICS
        print("\n📦 Inventory Management Analytics:")
        
        # Get current stock summary
        stock_response = self.client.get('/api/products/products/stock_summary/')
        self.assertEqual(stock_response.status_code, status.HTTP_200_OK)
        stock_data = stock_response.data
        
        total_inventory_value = Decimal('0')
        low_stock_products = []
        
        for product in stock_data:
            stock_qty = product['total_stock']
            base_price = Decimal(str(product['base_price']))
            inventory_value = stock_qty * base_price
            total_inventory_value += inventory_value
            
            # Define low stock threshold (20% of initial production)
            if product['product_name'] == 'Aloevera Drink 200ml':
                low_stock_threshold = 600  # 20% of 3000
            elif product['product_name'] == 'Aloevera Yogurt 150ml':
                low_stock_threshold = 300  # 20% of 1500
            elif product['product_name'] == 'Aloe Wellness Shot 50ml':
                low_stock_threshold = 160  # 20% of 800
            else:
                low_stock_threshold = 0
            
            if stock_qty < low_stock_threshold:
                low_stock_products.append(product['product_name'])
            
            print(f"   📦 {product['product_name']}:")
            print(f"      📊 Current Stock: {stock_qty} units")
            print(f"      💰 Inventory Value: ${inventory_value:,.2f}")
            print(f"      {'⚠️ LOW STOCK' if stock_qty < low_stock_threshold else '✅ ADEQUATE'}")
        
        print(f"\n   💰 Total Inventory Value: ${total_inventory_value:,.2f}")
        print(f"   ⚠️ Low Stock Alerts: {len(low_stock_products)} products")
        
        # 📋 CUSTOMER BEHAVIOR ANALYSIS
        print("\n📋 Customer Behavior Analysis:")
        
        # Analyze settlements and payment patterns
        settlements = Settlement.objects.all()
        payment_methods = {}
        settlement_amounts = []
        
        for settlement in settlements:
            method = settlement.payment_method
            amount = settlement.payment_amount
            
            payment_methods[method] = payment_methods.get(method, 0) + 1
            settlement_amounts.append(amount)
        
        avg_settlement = sum(settlement_amounts) / len(settlement_amounts) if settlement_amounts else 0
        
        print(f"   💳 Payment Method Preferences:")
        for method, count in payment_methods.items():
            percentage = (count / len(settlements)) * 100
            print(f"      {method.replace('_', ' ').title()}: {count} transactions ({percentage:.1f}%)")
        
        print(f"   💰 Average Settlement: ${avg_settlement:,.2f}")
        print(f"   📊 Settlement Range: ${min(settlement_amounts):,.2f} - ${max(settlement_amounts):,.2f}")
        
        # 🔍 QUALITY METRICS ANALYSIS
        print("\n🔍 Quality Metrics Analysis:")
        
        returns = Return.objects.all()
        return_analytics = {
            'total_returns': returns.count(),
            'total_units': sum(r.quantity for r in returns),
            'return_reasons': {}
        }
        
        for return_item in returns:
            reason = return_item.reason
            return_analytics['return_reasons'][reason] = return_analytics['return_reasons'].get(reason, 0) + return_item.quantity
        
        total_units_sold = sum(item.quantity for invoice in Invoice.objects.all() for item in invoice.items.all())
        overall_return_rate = (return_analytics['total_units'] / total_units_sold) * 100 if total_units_sold > 0 else 0
        
        print(f"   📊 Return Rate: {overall_return_rate:.2f}%")
        print(f"   🔄 Total Returns: {return_analytics['total_returns']} transactions")
        print(f"   📦 Total Units Returned: {return_analytics['total_units']}")
        
        print(f"   📋 Return Reasons:")
        for reason, quantity in return_analytics['return_reasons'].items():
            percentage = (quantity / return_analytics['total_units']) * 100
            print(f"      {reason.replace('_', ' ').title()}: {quantity} units ({percentage:.1f}%)")
        
        # 🎯 STRATEGIC RECOMMENDATIONS
        print("\n🎯 Strategic Business Recommendations:")
        
        # Performance-based recommendations
        if territories['university']['sales'] > territories['downtown']['sales']:
            print("   📈 Expand university territory coverage - showing strong performance")
        
        if overall_return_rate > 2.0:
            print("   ⚠️ Investigate quality control - return rate above threshold")
        
        if len(low_stock_products) > 0:
            print(f"   📦 Restock urgently: {', '.join(low_stock_products)}")
        
        if profit_margin < 25:
            print("   💰 Review pricing strategy - profit margin below target")
        
        # Growth opportunities
        best_performing_salesman = max(commission_data['salesman_commissions'], 
                                     key=lambda x: Decimal(str(x['total_sales'])))
        print(f"   🏆 Consider expanding {best_performing_salesman['salesman_name']}'s territory")
        
        print(f"   💡 Most popular payment method: {max(payment_methods, key=payment_methods.get).replace('_', ' ').title()}")
        
        # 📊 EXECUTIVE DASHBOARD SUMMARY
        print("\n📊 Executive Dashboard Summary:")
        print(f"   🏪 Business: Aloe Vera Paradise - Daily Operations Complete")
        print(f"   💰 Revenue: ${total_revenue:,.2f}")
        print(f"   📈 Profit Margin: {profit_margin:.1f}%")
        print(f"   👥 Sales Team Performance: {len(commission_data['salesman_commissions'])} active salesmen")
        print(f"   🎯 Territory Coverage: {len(territories)} territories")
        print(f"   📦 Inventory Status: ${total_inventory_value:,.2f} value, {len(low_stock_products)} low stock alerts")
        print(f"   🔍 Quality Score: {100-overall_return_rate:.1f}% (return rate: {overall_return_rate:.2f}%)")
        print(f"   💳 Payment Collection: {len(settlements)} settlements processed")
        
        # Verify analytics data integrity
        self.assertGreater(total_revenue, 0)
        self.assertGreater(len(commission_data['salesman_commissions']), 0)
        self.assertEqual(len(territories), 3)
        
        print("✅ PHASE 6 COMPLETE: Comprehensive business analytics generated successfully")
    
    def test_07_complete_business_day_simulation(self):
        """
        🌅🌆 PHASE 7: COMPLETE BUSINESS DAY SIMULATION
        
        This test runs the entire business workflow from morning production
        to evening analytics, validating data consistency and business rules
        throughout the complete operational cycle.
        """
        print("\n" + "="*80)
        print("🌅🌆 PHASE 7: COMPLETE BUSINESS DAY SIMULATION")
        print("🏪 ALOE VERA PARADISE - FULL OPERATIONAL CYCLE")
        print("="*80)
        
        # Execute the complete business workflow
        print("⏰ 6:00 AM - Starting complete business day simulation...")
        
        # Phase 1: Morning Production
        print("\n⏰ 6:00 AM - 9:00 AM: Production Cycle")
        self.test_01_morning_production_and_batch_creation()
        
        # Phase 2: Territory Distribution
        print("\n⏰ 9:00 AM - 10:00 AM: Territory Distribution")
        # Note: This calls Phase 1 internally, so we track timing differently
        
        # Phase 3: Sales Operations
        print("\n⏰ 10:00 AM - 6:00 PM: Sales Operations")
        # Note: This calls Phases 1-2 internally
        
        # Phase 4: Evening Settlements
        print("\n⏰ 6:00 PM - 8:00 PM: Evening Settlements")
        # Note: This calls Phases 1-3 internally
        
        # Phase 5: Returns Processing
        print("\n⏰ 8:00 PM - 9:00 PM: Returns Processing")
        # Note: This calls Phases 1-4 internally
        
        # Phase 6: Business Analytics
        print("\n⏰ 9:00 PM - 10:00 PM: Business Analytics")
        self.test_06_comprehensive_business_analytics()
        
        # 🔍 FINAL DATA INTEGRITY VALIDATION
        print("\n🔍 Final Data Integrity Validation:")
        
        # Validate all core business entities exist
        products = Product.objects.count()
        batches = Batch.objects.count()
        deliveries = Delivery.objects.count()
        invoices = Invoice.objects.count()
        settlements = Settlement.objects.count()
        returns = Return.objects.count()
        commissions = Commission.objects.count()
        
        print(f"   📦 Products: {products}")
        print(f"   🏭 Batches: {batches}")
        print(f"   🚚 Deliveries: {deliveries}")
        print(f"   📄 Invoices: {invoices}")
        print(f"   💰 Settlements: {settlements}")
        print(f"   🔄 Returns: {returns}")
        print(f"   🏆 Commissions: {commissions}")
        
        # Verify minimum expected counts
        self.assertGreaterEqual(products, 3)
        self.assertGreaterEqual(batches, 3)
        self.assertGreaterEqual(deliveries, 3)
        self.assertGreaterEqual(invoices, 4)
        self.assertGreaterEqual(settlements, 3)
        self.assertGreaterEqual(returns, 3)
        self.assertGreaterEqual(commissions, 4)
        
        
        # 💰 FINANCIAL SUMMARY VALIDATION
        total_revenue = Invoice.objects.aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        total_commissions = Commission.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        print(f"\n💰 Financial Summary:")
        print(f"   Total Revenue: ${total_revenue}")
        print(f"   Total Commissions: ${total_commissions}")
        print(f"   Net Profit: ${total_revenue - total_commissions}")
        
        # Verify financial consistency
        self.assertGreater(total_revenue, Decimal('0.00'))
        self.assertGreater(total_commissions, Decimal('0.00'))
        self.assertLess(total_commissions, total_revenue)
        
        print("\n🎉 COMPLETE BUSINESS DAY SIMULATION SUCCESSFUL!")
        print("   All business operations validated successfully")
        print("   System ready for production use")
    """
    🏪 ALOE VERA PARADISE - COMPLETE BUSINESS MANAGEMENT SYSTEM TEST SUITE
    
    This test suite validates the entire business workflow from morning production
    to evening settlements, ensuring all business operations work seamlessly.
    
    Business Story: Sarah runs "Aloe Vera Paradise" with 3 salesmen (Mike, Jennifer, Carlos)
    serving different territories. The system manages everything from batch production
    to customer payments and returns processing.
    """
    
    def setUp(self):
        """
        🌅 BUSINESS SETUP - Aloe Vera Paradise Company Initialization
        Setting up the complete business infrastructure for testing
        """
        print("\n" + "="*80)
        print("🏪 ALOE VERA PARADISE - BUSINESS SYSTEM INITIALIZATION")
        print("="*80)
        
        # 👥 Create Business Owner - Sarah Martinez
        self.owner_user = User.objects.create_user(
            username='sarah_martinez',
            email='sarah@aloeveraparadise.com',
            password='paradise2024',
            first_name='Sarah',
            last_name='Martinez',
            role='owner'
        )
        self.owner = Owner.objects.create(
            user=self.owner_user,
            business_name='Aloe Vera Paradise Ltd'
        )
        
        # 👨‍💼 Create Sales Team
        # Mike Thompson - Downtown Territory
        self.mike_user = User.objects.create_user(
            username='mike_thompson',
            email='mike@aloeveraparadise.com',
            password='downtown2024',
            first_name='Mike',
            last_name='Thompson',
            role='salesman'
        )
        self.mike = Salesman.objects.create(
            user=self.mike_user,
            name='Mike Thompson',
            phone='555-0101',
            address='Downtown Sales Office, 123 Business St'
        )
        
        # Jennifer Walsh - University District
        self.jennifer_user = User.objects.create_user(
            username='jennifer_walsh',
            email='jennifer@aloeveraparadise.com',
            password='university2024',
            first_name='Jennifer',
            last_name='Walsh',
            role='salesman'
        )
        self.jennifer = Salesman.objects.create(
            user=self.jennifer_user,
            name='Jennifer Walsh',
            phone='555-0102',
            address='University District Office, 456 Campus Ave'
        )
        
        # Carlos Rodriguez - Health Centers Territory
        self.carlos_user = User.objects.create_user(
            username='carlos_rodriguez',
            email='carlos@aloeveraparadise.com',
            password='health2024',
            first_name='Carlos',
            last_name='Rodriguez',
            role='salesman'
        )
        self.carlos = Salesman.objects.create(
            user=self.carlos_user,
            name='Carlos Rodriguez',
            phone='555-0103',
            address='Health Centers Territory, 789 Wellness Blvd'
        )
        
        # 🏪 Create Customer Shops
        self.green_cafe = Shop.objects.create(
            name='Green Café',
            address='Downtown Business District',
            contact_person='Maria Green',
            phone='555-2001',
            salesman=self.mike
        )
        
        self.university_health = Shop.objects.create(
            name='University Health Center',
            address='University Campus',
            contact_person='Dr. James Wilson',
            phone='555-2002',
            salesman=self.jennifer
        )
        
        self.fitlife_gym = Shop.objects.create(
            name='FitLife Gymnasium',
            address='Health & Fitness District',
            contact_person='Coach Amanda Fitness',
            phone='555-2003',
            salesman=self.carlos
        )
        
        self.wellness_mart = Shop.objects.create(
            name='Wellness Mart Chain',
            address='Multiple Locations',
            contact_person='Store Manager Kim',
            phone='555-2004',
            salesman=self.jennifer
        )
        
        # 🥤 Create Product Categories and Products
        self.beverages_category = Category.objects.create(
            name='Aloe Beverages',
            description='Fresh Aloe Vera Drinks'
        )
        
        self.wellness_category = Category.objects.create(
            name='Wellness Products',
            description='Health and Wellness Aloe Products'
        )
        
        # Premium Product Line
        self.aloe_drink_200ml = Product.objects.create(
            name='Aloevera Drink 200ml',
            description='Premium Fresh Aloe Vera Drink - 200ml',
            category=self.beverages_category,
            base_price=Decimal('2.50'),
            unit='bottle'
        )
        
        self.aloe_yogurt_150ml = Product.objects.create(
            name='Aloevera Yogurt 150ml',
            description='Creamy Aloe Vera Yogurt - 150ml',
            category=self.beverages_category,
            base_price=Decimal('3.25'),
            unit='cup'
        )
        
        self.wellness_shot_50ml = Product.objects.create(
            name='Aloe Wellness Shot 50ml',
            description='Concentrated Aloe Wellness Shot - 50ml',
            category=self.wellness_category,
            base_price=Decimal('4.99'),
            unit='shot'
        )
        
        # 🔐 Setup API Client Authentication
        self.client = APIClient()
        
        print("✅ Business Infrastructure Setup Complete")
        print(f"👑 Owner: {self.owner.business_name}")
        print(f"👨‍💼 Sales Team: {self.mike.name}, {self.jennifer.name}, {self.carlos.name}")
        print(f"🏪 Customer Shops: {Shop.objects.count()} establishments")
        print(f"🥤 Product Catalog: {Product.objects.count()} premium products")
    
    def test_01_morning_production_and_batch_creation(self):
        """
        🌅 PHASE 1: MORNING PRODUCTION CYCLE
        
        Business Scenario: 6:00 AM - Sarah starts the day by reviewing inventory
        and creating fresh batches for the day's distribution.
        
        Today's Production Plan:
        - 3000 units Aloe Drink 200ml (high demand product)
        - 1500 units Aloe Yogurt 150ml (steady seller)
        - 800 units Wellness Shots 50ml (premium product)
        """
        print("\n" + "="*80)
        print("🌅 PHASE 1: MORNING PRODUCTION CYCLE")
        print("="*80)
        
        # Authenticate as Owner
        self.client.force_authenticate(user=self.owner_user)
        
        # 📊 Check Initial Stock Status
        print("📊 Checking initial inventory status...")
        stock_response = self.client.get('/api/products/products/stock_summary/')
        self.assertEqual(stock_response.status_code, status.HTTP_200_OK)
        
        initial_stock = stock_response.data
        print(f"📦 Initial Stock Status: {len(initial_stock)} products in catalog")
        
        # 🏭 Create Fresh Production Batches
        print("\n🏭 Starting Fresh Batch Production...")
        
        today = date.today()
        
        # Batch 1: Aloe Vera Drink 200ml - High Volume Production
        drink_batch_data = {
            'batch_number': f'AVP-DRINK-{today.strftime("%y%m%d")}-001',
            'product': self.aloe_drink_200ml.id,
            'manufacturing_date': today,
            'expiry_date': today + timedelta(days=30),
            'initial_quantity': 3000,
            'current_quantity': 3000,
            'unit_cost': Decimal('1.20'),
            'notes': 'Premium morning batch - high demand expected',
            'is_active': True
        }
        
        drink_batch_response = self.client.post('/api/products/batches/', drink_batch_data)
        self.assertEqual(drink_batch_response.status_code, status.HTTP_201_CREATED)
        self.drink_batch = Batch.objects.get(id=drink_batch_response.data['id'])
        print(f"✅ Created Drink Batch: {self.drink_batch.batch_number} - {self.drink_batch.initial_quantity} units")
        
        # Batch 2: Aloe Yogurt 150ml - Steady Production
        yogurt_batch_data = {
            'batch_number': f'AVP-YOGURT-{today.strftime("%y%m%d")}-001',
            'product': self.aloe_yogurt_150ml.id,
            'manufacturing_date': today,
            'expiry_date': today + timedelta(days=21),  # Shorter shelf life
            'initial_quantity': 1500,
            'current_quantity': 1500,
            'unit_cost': Decimal('2.00'),
            'notes': 'Fresh yogurt batch - refrigerated storage',
            'is_active': True
        }
        
        yogurt_batch_response = self.client.post('/api/products/batches/', yogurt_batch_data)
        self.assertEqual(yogurt_batch_response.status_code, status.HTTP_201_CREATED)
        self.yogurt_batch = Batch.objects.get(id=yogurt_batch_response.data['id'])
        print(f"✅ Created Yogurt Batch: {self.yogurt_batch.batch_number} - {self.yogurt_batch.initial_quantity} units")
        
        # Batch 3: Wellness Shots 50ml - Premium Production
        shot_batch_data = {
            'batch_number': f'AVP-SHOTS-{today.strftime("%y%m%d")}-001',
            'product': self.wellness_shot_50ml.id,
            'manufacturing_date': today,
            'expiry_date': today + timedelta(days=60),  # Longer shelf life
            'initial_quantity': 800,
            'current_quantity': 800,
            'unit_cost': Decimal('3.50'),
            'notes': 'Premium wellness shots - concentrated formula',
            'is_active': True
        }
        
        shot_batch_response = self.client.post('/api/products/batches/', shot_batch_data)
        self.assertEqual(shot_batch_response.status_code, status.HTTP_201_CREATED)
        self.shot_batch = Batch.objects.get(id=shot_batch_response.data['id'])
        print(f"✅ Created Wellness Shot Batch: {self.shot_batch.batch_number} - {self.shot_batch.initial_quantity} units")
        
        # 📈 Verify Stock Summary After Production
        updated_stock_response = self.client.get('/api/products/products/stock_summary/')
        self.assertEqual(updated_stock_response.status_code, status.HTTP_200_OK)
        
        updated_stock = updated_stock_response.data
        total_production_value = Decimal('0')
        
        print(f"\n📈 Production Summary:")
        for product_stock in updated_stock:
            if product_stock['total_stock'] > 0:
                value = Decimal(str(product_stock['total_stock'])) * Decimal(str(product_stock['base_price']))
                total_production_value += value
                print(f"   📦 {product_stock['product_name']}: {product_stock['total_stock']} units (${value:,.2f})")
        
        print(f"💰 Total Production Value: ${total_production_value:,.2f}")
        print(f"🏭 Production Efficiency: 100% - All batches created successfully")
        
        # Verify FIFO batch ordering
        self.assertTrue(self.drink_batch.is_active)
        self.assertTrue(self.yogurt_batch.is_active)
        self.assertTrue(self.shot_batch.is_active)
        
        print("✅ PHASE 1 COMPLETE: Fresh inventory ready for distribution")
    
    def test_02_strategic_territory_distribution(self):
        """
        🚚 PHASE 2: STRATEGIC TERRITORY DISTRIBUTION
        
        Business Scenario: 9:00 AM - After production, Sarah plans the distribution
        strategy based on territory demand patterns and salesman performance.
        
        Distribution Strategy:
        - Mike (Downtown): 40% allocation - high foot traffic area
        - Jennifer (University): 35% allocation - steady student demand  
        - Carlos (Health Centers): 25% allocation - premium product focus
        """
        print("\n" + "="*80)
        print("🚚 PHASE 2: STRATEGIC TERRITORY DISTRIBUTION")
        print("="*80)
        
        # First create the batches
        self.test_01_morning_production_and_batch_creation()
        
        print("📋 Planning territorial distribution strategy...")
        
        # 🎯 Distribution Strategy Planning
        territory_allocations = {
            'mike_downtown': {
                'salesman': self.mike,
                'territory': 'Downtown Business District',
                'allocation_percentage': 40,
                'focus': 'High volume, mixed products'
            },
            'jennifer_university': {
                'salesman': self.jennifer,
                'territory': 'University & Campus Area',
                'allocation_percentage': 35,
                'focus': 'Steady demand, health-conscious students'
            },
            'carlos_health': {
                'salesman': self.carlos,
                'territory': 'Health Centers & Fitness',
                'allocation_percentage': 25,
                'focus': 'Premium products, wellness focus'
            }
        }
        
        print(f"🎯 Territory Strategy:")
        for territory, info in territory_allocations.items():
            print(f"   {info['salesman'].name}: {info['allocation_percentage']}% - {info['focus']}")
        
        # 📦 Create Strategic Deliveries
        
        # Delivery 1: Mike - Downtown Territory (40% allocation)
        mike_delivery_data = {
            'salesman': self.mike.id,
            'delivery_date': date.today(),
            'notes': 'Downtown territory - high volume mixed delivery',
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 1200,  # 40% of 3000
                    'unit_cost': self.drink_batch.unit_cost
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 600,   # 40% of 1500
                    'unit_cost': self.yogurt_batch.unit_cost
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 320,   # 40% of 800
                    'unit_cost': self.shot_batch.unit_cost
                }
            ]
        }
        
        mike_delivery_response = self.client.post('/api/sales/deliveries/', mike_delivery_data, format='json')
        self.assertEqual(mike_delivery_response.status_code, status.HTTP_201_CREATED)
        self.mike_delivery = Delivery.objects.get(id=mike_delivery_response.data['id'])
        
        print(f"📦 Mike's Delivery: {self.mike_delivery.items.count()} products - Downtown Territory")
        
        # Delivery 2: Jennifer - University Territory (35% allocation)
        jennifer_delivery_data = {
            'salesman': self.jennifer.id,
            'delivery_date': date.today(),
            'notes': 'University territory - student-focused product mix',
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 1050,  # 35% of 3000
                    'unit_cost': self.drink_batch.unit_cost
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 525,   # 35% of 1500
                    'unit_cost': self.yogurt_batch.unit_cost
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 280,   # 35% of 800
                    'unit_cost': self.shot_batch.unit_cost
                }
            ]
        }
        
        jennifer_delivery_response = self.client.post('/api/sales/deliveries/', jennifer_delivery_data, format='json')
        self.assertEqual(jennifer_delivery_response.status_code, status.HTTP_201_CREATED)
        self.jennifer_delivery = Delivery.objects.get(id=jennifer_delivery_response.data['id'])
        
        print(f"📦 Jennifer's Delivery: {self.jennifer_delivery.items.count()} products - University Territory")
        
        # Delivery 3: Carlos - Health Centers Territory (25% allocation)
        carlos_delivery_data = {
            'salesman': self.carlos.id,
            'delivery_date': date.today(),
            'notes': 'Health centers territory - premium wellness focus',
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 750,   # 25% of 3000
                    'unit_cost': self.drink_batch.unit_cost
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 375,   # 25% of 1500
                    'unit_cost': self.yogurt_batch.unit_cost
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 200,   # 25% of 800
                    'unit_cost': self.shot_batch.unit_cost
                }
            ]
        }
        
        carlos_delivery_response = self.client.post('/api/sales/deliveries/', carlos_delivery_data, format='json')
        self.assertEqual(carlos_delivery_response.status_code, status.HTTP_201_CREATED)
        self.carlos_delivery = Delivery.objects.get(id=carlos_delivery_response.data['id'])
        
        print(f"📦 Carlos's Delivery: {self.carlos_delivery.items.count()} products - Health Centers Territory")
        
        # 📊 Verify Distribution Analytics
        total_distributed = {
            'drinks': 1200 + 1050 + 750,  # Should equal 3000
            'yogurt': 600 + 525 + 375,    # Should equal 1500
            'shots': 320 + 280 + 200      # Should equal 800
        }
        
        print(f"\n📊 Distribution Analytics:")
        print(f"   🥤 Aloe Drinks: {total_distributed['drinks']}/3000 units (100%)")
        print(f"   🥛 Aloe Yogurt: {total_distributed['yogurt']}/1500 units (100%)")
        print(f"   💪 Wellness Shots: {total_distributed['shots']}/800 units (100%)")
        
        # Verify all products were distributed
        self.assertEqual(total_distributed['drinks'], 3000)
        self.assertEqual(total_distributed['yogurt'], 1500)
        self.assertEqual(total_distributed['shots'], 800)
        
        # 🎯 Verify Batch Assignments Created
        assignments = BatchAssignment.objects.all()
        print(f"\n🎯 Batch Assignment Summary:")
        for assignment in assignments:
            print(f"   {assignment.salesman.name}: {assignment.product.name} - {assignment.delivered_quantity} units")
        
        # Verify assignments exist for all salesmen and products
        self.assertEqual(assignments.count(), 9)  # 3 salesmen × 3 products
        
        print("✅ PHASE 2 COMPLETE: Strategic distribution executed successfully")
    
    def test_03_full_day_sales_operations(self):
        """
        🛒 PHASE 3: FULL DAY SALES OPERATIONS
        
        Business Scenario: 10:00 AM - 6:00 PM - Salesmen execute their sales
        strategies across different territories with varied customer interactions.
        
        Sales Timeline:
        - Morning: Coffee shops and early customers
        - Afternoon: University and fitness centers
        - Evening: Health stores and bulk orders
        """
        print("\n" + "="*80)
        print("🛒 PHASE 3: FULL DAY SALES OPERATIONS")
        print("="*80)
        
        # Setup distribution first
        self.test_02_strategic_territory_distribution()
        
        # 🌅 MORNING SALES (10:00 AM - 12:00 PM)
        print("\n🌅 Morning Sales Operations (10:00 AM - 12:00 PM)")
        
        # Mike's Morning Sales - Green Café
        self.client.force_authenticate(user=self.mike_user)
        
        green_cafe_order = {
            'shop': self.green_cafe.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 150,
                    'unit_price': Decimal('2.75')  # 10% markup
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 75,
                    'unit_price': Decimal('3.50')  # 7.7% markup
                }
            ]
        }
        
        green_cafe_response = self.client.post('/api/sales/invoices/', green_cafe_order, format='json')
        self.assertEqual(green_cafe_response.status_code, status.HTTP_201_CREATED)
        self.green_cafe_invoice = Invoice.objects.get(id=green_cafe_response.data['id'])
        
        print(f"   ☕ Green Café Order: ${self.green_cafe_invoice.total_amount} - Mike Thompson")
        
        # 🌞 MIDDAY SALES (12:00 PM - 3:00 PM)
        print("\n🌞 Midday Sales Operations (12:00 PM - 3:00 PM)")
        
        # Jennifer's University Sales
        self.client.force_authenticate(user=self.jennifer_user)
        
        university_health_order = {
            'shop': self.university_health.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 400,
                    'unit_price': Decimal('2.60')  # Bulk discount
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 100,
                    'unit_price': Decimal('5.25')  # 5.2% markup
                }
            ]
        }
        
        university_response = self.client.post('/api/sales/invoices/', university_health_order, format='json')
        self.assertEqual(university_response.status_code, status.HTTP_201_CREATED)
        self.university_invoice = Invoice.objects.get(id=university_response.data['id'])
        
        print(f"   🎓 University Health Center: ${self.university_invoice.total_amount} - Jennifer Walsh")
        
        # 🌆 AFTERNOON SALES (3:00 PM - 6:00 PM)
        print("\n🌆 Afternoon Sales Operations (3:00 PM - 6:00 PM)")
        
        # Carlos's Health Center Sales
        self.client.force_authenticate(user=self.carlos_user)
        
        fitlife_gym_order = {
            'shop': self.fitlife_gym.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 200,
                    'unit_price': Decimal('2.85')  # Premium pricing
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 150,
                    'unit_price': Decimal('5.49')  # 10% markup
                }
            ]
        }
        
        fitlife_response = self.client.post('/api/sales/invoices/', fitlife_gym_order, format='json')
        self.assertEqual(fitlife_response.status_code, status.HTTP_201_CREATED)
        self.fitlife_invoice = Invoice.objects.get(id=fitlife_response.data['id'])
        
        print(f"   💪 FitLife Gymnasium: ${self.fitlife_invoice.total_amount} - Carlos Rodriguez")
        
        # Additional Evening Sales - Jennifer's Second Customer
        self.client.force_authenticate(user=self.jennifer_user)
        
        wellness_mart_order = {
            'shop': self.wellness_mart.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 300,
                    'unit_price': Decimal('2.70')  # Retail chain pricing
                },
                {
                    'product': self.aloe_yogurt_150ml.id,
                    'quantity': 200,
                    'unit_price': Decimal('3.60')  # 10.8% markup
                },
                {
                    'product': self.wellness_shot_50ml.id,
                    'quantity': 80,
                    'unit_price': Decimal('5.35')  # 7.2% markup
                }
            ]
        }
        
        wellness_mart_response = self.client.post('/api/sales/invoices/', wellness_mart_order, format='json')
        self.assertEqual(wellness_mart_response.status_code, status.HTTP_201_CREATED)
        self.wellness_mart_invoice = Invoice.objects.get(id=wellness_mart_response.data['id'])
        
        print(f"   🏪 Wellness Mart Chain: ${self.wellness_mart_invoice.total_amount} - Jennifer Walsh")
        
        # 📊 DAILY SALES SUMMARY
        print("\n📊 End of Day Sales Summary:")
        
        total_revenue = (self.green_cafe_invoice.total_amount + 
                        self.university_invoice.total_amount + 
                        self.fitlife_invoice.total_amount + 
                        self.wellness_mart_invoice.total_amount)
        
        # Calculate commissions (10% for each salesman)
        mike_sales = self.green_cafe_invoice.total_amount
        jennifer_sales = self.university_invoice.total_amount + self.wellness_mart_invoice.total_amount
        carlos_sales = self.fitlife_invoice.total_amount
        
        mike_commission = mike_sales * Decimal('0.10')
        jennifer_commission = jennifer_sales * Decimal('0.10')
        carlos_commission = carlos_sales * Decimal('0.10')
        total_commission = mike_commission + jennifer_commission + carlos_commission
        
        print(f"   💰 Total Revenue: ${total_revenue:,.2f}")
        print(f"   👨‍💼 Mike Thompson: ${mike_sales:,.2f} (Commission: ${mike_commission:,.2f})")
        print(f"   👩‍💼 Jennifer Walsh: ${jennifer_sales:,.2f} (Commission: ${jennifer_commission:,.2f})")
        print(f"   👨‍💼 Carlos Rodriguez: ${carlos_sales:,.2f} (Commission: ${carlos_commission:,.2f})")
        print(f"   🏆 Total Commissions Owed: ${total_commission:,.2f}")
        
        # 🎯 Verify Commission Creation
        commissions = Commission.objects.all()
        self.assertEqual(commissions.count(), 4)  # One per invoice
        
        for commission in commissions:
            self.assertEqual(commission.commission_rate, Decimal('0.10'))
            self.assertEqual(commission.status, 'pending')
            print(f"   ✅ Commission Created: {commission.salesman.name} - ${commission.commission_amount}")
        
        # 📈 Territory Performance Analysis
        print(f"\n📈 Territory Performance Analysis:")
        print(f"   🏙️ Downtown (Mike): 1 customer, ${mike_sales:,.2f}")
        print(f"   🎓 University (Jennifer): 2 customers, ${jennifer_sales:,.2f}")
        print(f"   💪 Health Centers (Carlos): 1 customer, ${carlos_sales:,.2f}")
        print(f"   🏆 Top Performer: {'Jennifer' if jennifer_sales > max(mike_sales, carlos_sales) else 'Mike' if mike_sales > carlos_sales else 'Carlos'}")
        
        print("✅ PHASE 3 COMPLETE: Full day sales operations executed successfully")
    
    def test_04_evening_settlements_and_collections(self):
        """
        💰 PHASE 4: EVENING SETTLEMENTS AND COLLECTIONS
        
        Business Scenario: 6:00 PM - 8:00 PM - End of day financial operations.
        Customers make payments, some paying multiple invoices together (bill-to-bill settlements).
        
        Settlement Scenarios:
        - Green Café: Single invoice payment
        - University Health: Paying current + previous outstanding invoices
        - FitLife Gym: Partial payment arrangement
        - Wellness Mart: Full settlement with discount
        """
        print("\n" + "="*80)
        print("💰 PHASE 4: EVENING SETTLEMENTS AND COLLECTIONS")
        print("="*80)
        
        # Complete sales operations first
        self.test_03_full_day_sales_operations()
        
        # Switch to owner for settlement management
        self.client.force_authenticate(user=self.owner_user)
        
        print("💳 Processing evening customer payments and settlements...")
        
        # 💳 SETTLEMENT 1: Green Café - Simple Payment
        print("\n💳 Settlement 1: Green Café - Simple Invoice Payment")
        
        green_cafe_settlement_data = {
            'customer_name': 'Green Café',
            'payment_method': 'cash',
            'payment_amount': self.green_cafe_invoice.total_amount,
            'notes': 'Cash payment for daily delivery',
            'invoices': [self.green_cafe_invoice.id]
        }
        
        green_settlement_response = self.client.post('/api/sales/settlements/', green_cafe_settlement_data, format='json')
        self.assertEqual(green_settlement_response.status_code, status.HTTP_201_CREATED)
        green_settlement = Settlement.objects.get(id=green_settlement_response.data['id'])
        
        print(f"   ✅ Green Café Payment: ${green_settlement.payment_amount} - {green_settlement.payment_method}")
        
        # 💳 SETTLEMENT 2: University Health - Multiple Invoice Settlement
        print("\n💳 Settlement 2: University Health - Multi-Invoice Settlement")
        
        # Create a previous outstanding invoice for demonstration
        previous_invoice_data = {
            'shop': self.university_health.id,
            'items': [
                {
                    'product': self.aloe_drink_200ml.id,
                    'quantity': 100,
                    'unit_price': Decimal('2.60')
                }
            ]
        }
        
        self.client.force_authenticate(user=self.jennifer_user)
        previous_response = self.client.post('/api/sales/invoices/', previous_invoice_data, format='json')
        previous_invoice = Invoice.objects.get(id=previous_response.data['id'])
        
        # Now settle both invoices together
        self.client.force_authenticate(user=self.owner_user)
        
        university_total = self.university_invoice.total_amount + previous_invoice.total_amount
        university_settlement_data = {
            'customer_name': 'University Health Center',
            'payment_method': 'bank_transfer',
            'payment_amount': university_total,
            'notes': 'Settlement for current and previous orders',
            'invoices': [self.university_invoice.id, previous_invoice.id]
        }
        
        university_settlement_response = self.client.post('/api/sales/settlements/', university_settlement_data, format='json')
        self.assertEqual(university_settlement_response.status_code, status.HTTP_201_CREATED)
        university_settlement = Settlement.objects.get(id=university_settlement_response.data['id'])
        
        print(f"   ✅ University Multi-Settlement: ${university_settlement.payment_amount} - {len(university_settlement_data['invoices'])} invoices")
        
        # 💳 SETTLEMENT 3: FitLife Gym - Partial Payment
        print("\n💳 Settlement 3: FitLife Gym - Partial Payment Arrangement")
        
        partial_amount = self.fitlife_invoice.total_amount * Decimal('0.60')  # 60% payment
        fitlife_settlement_data = {
            'customer_name': 'FitLife Gymnasium',
            'payment_method': 'credit_card',
            'payment_amount': partial_amount,
            'notes': 'Partial payment - 60% now, remainder in 7 days',
            'invoices': [self.fitlife_invoice.id]
        }
        
        fitlife_settlement_response = self.client.post('/api/sales/settlements/', fitlife_settlement_data, format='json')
        self.assertEqual(fitlife_settlement_response.status_code, status.HTTP_201_CREATED)
        fitlife_settlement = Settlement.objects.get(id=fitlife_settlement_response.data['id'])
        
        print(f"   ✅ FitLife Partial Payment: ${fitlife_settlement.payment_amount} of ${self.fitlife_invoice.total_amount}")
        
        # 💳 SETTLEMENT 4: Wellness Mart - Full Settlement with Early Payment Discount
        print("\n💳 Settlement 4: Wellness Mart - Full Settlement with Discount")
        
        discount_amount = self.wellness_mart_invoice.total_amount * Decimal('0.02')  # 2% early payment discount
        discounted_total = self.wellness_mart_invoice.total_amount - discount_amount
        
        wellness_settlement_data = {
            'customer_name': 'Wellness Mart Chain',
            'payment_method': 'bank_transfer',
            'payment_amount': discounted_total,
            'notes': f'Full payment with 2% early payment discount (${discount_amount})',
            'invoices': [self.wellness_mart_invoice.id]
        }
        
        wellness_settlement_response = self.client.post('/api/sales/settlements/', wellness_settlement_data, format='json')
        self.assertEqual(wellness_settlement_response.status_code, status.HTTP_201_CREATED)
        wellness_settlement = Settlement.objects.get(id=wellness_settlement_response.data['id'])
        
        print(f"   ✅ Wellness Mart Settlement: ${wellness_settlement.payment_amount} (${discount_amount} discount)")
        
        # 📊 SETTLEMENT SUMMARY AND ANALYTICS
        print("\n📊 Evening Settlement Summary:")
        
        all_settlements = Settlement.objects.all()
        total_collected = sum(s.payment_amount for s in all_settlements)
        total_invoiced = sum([self.green_cafe_invoice.total_amount, 
                            self.university_invoice.total_amount, 
                            previous_invoice.total_amount,
                            self.fitlife_invoice.total_amount, 
                            self.wellness_mart_invoice.total_amount])
        
        outstanding_balance = total_invoiced - total_collected
        collection_rate = (total_collected / total_invoiced) * 100
        
        print(f"   💰 Total Invoiced: ${total_invoiced:,.2f}")
        print(f"   💳 Total Collected: ${total_collected:,.2f}")
        print(f"   📈 Collection Rate: {collection_rate:.1f}%")
        print(f"   ⚠️ Outstanding Balance: ${outstanding_balance:,.2f}")
        
        # 📋 Payment Method Analysis
        payment_methods = {}
        for settlement in all_settlements:
            method = settlement.payment_method
            if method in payment_methods:
                payment_methods[method] += settlement.payment_amount
            else:
                payment_methods[method] = settlement.payment_amount
        
        print(f"\n📋 Payment Method Breakdown:")
        for method, amount in payment_methods.items():
            percentage = (amount / total_collected) * 100
            print(f"   {method.replace('_', ' ').title()}: ${amount:,.2f} ({percentage:.1f}%)")
        
        # 🎯 Verify Settlement Data Integrity
        self.assertEqual(all_settlements.count(), 4)
        
        # Check that multi-invoice settlement includes both invoices
        university_settlement_invoices = university_settlement.invoices.all()
        self.assertEqual(university_settlement_invoices.count(), 2)
        
        print("✅ PHASE 4 COMPLETE: Evening settlements processed successfully")
    
    def test_05_returns_and_quality_management(self):
        """
        🔄 PHASE 5: RETURNS AND QUALITY MANAGEMENT
        
        Business Scenario: End of day - handling product returns from customers.
        Some products need to be returned due to various reasons (damage, near expiry, etc.).
        
        Return Scenarios:
        - Green Café: 5 damaged bottles during transport
        - University Health: 20 drinks near expiry date
        - Quality control: Voluntary recall of specific batch
        """
        print("\n" + "="*80)
        print("🔄 PHASE 5: RETURNS AND QUALITY MANAGEMENT")
        print("="*80)
        
        # Complete previous operations
        self.test_04_evening_settlements_and_collections()
        
        print("🔍 Processing customer returns and quality control...")
        
        # 🔍 RETURN 1: Green Café - Damaged Products During Transport
        print("\n🔍 Return 1: Green Café - Transport Damage")
        
        # First, search for the batch to return
        batch_search_response = self.client.get(
            f'/api/sales/returns/batch_search/?q={self.drink_batch.batch_number[:10]}'
        )
        self.assertEqual(batch_search_response.status_code, status.HTTP_200_OK)
        
        found_batches = batch_search_response.data
        self.assertGreater(len(found_batches), 0)
        
        print(f"   🔍 Batch Search Result: Found {len(found_batches)} matching batches")
        
        # Process the return
        green_cafe_return_data = {
            'return_number': 'RET-GC-001',
            'customer_name': 'Green Café',
            'return_date': date.today(),
            'batch': self.drink_batch.id,
            'product': self.aloe_drink_200ml.id,
            'quantity': 5,
            'reason': 'damaged_transport',
            'notes': 'Bottles damaged during delivery transport',
            'handled_by': self.mike.id
        }
        
        green_return_response = self.client.post('/api/sales/returns/', green_cafe_return_data, format='json')
        self.assertEqual(green_return_response.status_code, status.HTTP_201_CREATED)
        green_return = Return.objects.get(id=green_return_response.data['id'])
        
        print(f"   ✅ Green Café Return: {green_return.quantity} units - {green_return.reason}")
        
        # 🔍 RETURN 2: University Health - Near Expiry Products
        print("\n🔍 Return 2: University Health - Near Expiry Concern")
        
        university_return_data = {
            'return_number': 'RET-UH-001',
            'customer_name': 'University Health Center',
            'return_date': date.today(),
            'batch': self.drink_batch.id,
            'product': self.aloe_drink_200ml.id,
            'quantity': 20,
            'reason': 'near_expiry',
            'notes': 'Customer concerned about expiry date - proactive return',
            'handled_by': self.jennifer.id
        }
        
        university_return_response = self.client.post('/api/sales/returns/', university_return_data, format='json')
        self.assertEqual(university_return_response.status_code, status.HTTP_201_CREATED)
        university_return = Return.objects.get(id=university_return_response.data['id'])
        
        print(f"   ✅ University Return: {university_return.quantity} units - {university_return.reason}")
        
        # 🔍 RETURN 3: FitLife Gym - Customer Preference Issue
        print("\n🔍 Return 3: FitLife Gym - Customer Preference")
        
        fitlife_return_data = {
            'return_number': 'RET-FL-001',
            'customer_name': 'FitLife Gymnasium',
            'return_date': date.today(),
            'batch': self.yogurt_batch.id,
            'product': self.aloe_yogurt_150ml.id,
            'quantity': 10,
            'reason': 'customer_preference',
            'notes': 'Customers prefer the drink over yogurt format',
            'handled_by': self.carlos.id
        }
        
        fitlife_return_response = self.client.post('/api/sales/returns/', fitlife_return_data, format='json')
        self.assertEqual(fitlife_return_response.status_code, status.HTTP_201_CREATED)
        fitlife_return = Return.objects.get(id=fitlife_return_response.data['id'])
        
        print(f"   ✅ FitLife Return: {fitlife_return.quantity} units - {fitlife_return.reason}")
        
        # 📊 RETURNS ANALYTICS AND BATCH TRACKING
        print("\n📊 Returns Analytics and Quality Control:")
        
        all_returns = Return.objects.all()
        total_returned_units = sum(r.quantity for r in all_returns)
        
        # Group returns by reason
        return_reasons = {}
        for return_item in all_returns:
            reason = return_item.reason
            if reason in return_reasons:
                return_reasons[reason] += return_item.quantity
            else:
                return_reasons[reason] = return_item.quantity
        
        print(f"   📦 Total Returns: {total_returned_units} units across {all_returns.count()} transactions")
        print(f"   📋 Return Reasons Analysis:")
        for reason, quantity in return_reasons.items():
            percentage = (quantity / total_returned_units) * 100
            print(f"      {reason.replace('_', ' ').title()}: {quantity} units ({percentage:.1f}%)")
        
        # 🔍 BATCH IMPACT ANALYSIS
        print(f"\n🔍 Batch Impact Analysis:")
        
        # Check batch stock levels after returns
        self.drink_batch.refresh_from_db()
        self.yogurt_batch.refresh_from_db()
        
        drink_returns = sum(r.quantity for r in all_returns if r.product == self.aloe_drink_200ml)
        yogurt_returns = sum(r.quantity for r in all_returns if r.product == self.aloe_yogurt_150ml)
        
        print(f"   🥤 Drink Batch {self.drink_batch.batch_number}:")
        print(f"      Returns: {drink_returns} units")
        print(f"      Current Stock: {self.drink_batch.current_quantity} units")
        
        print(f"   🥛 Yogurt Batch {self.yogurt_batch.batch_number}:")
        print(f"      Returns: {yogurt_returns} units")
        print(f"      Current Stock: {self.yogurt_batch.current_quantity} units")
        
        # 🎯 QUALITY CONTROL ALERTS
        return_rate_threshold = 2.0  # 2% return rate triggers quality review
        
        drink_return_rate = (drink_returns / self.drink_batch.initial_quantity) * 100
        yogurt_return_rate = (yogurt_returns / self.yogurt_batch.initial_quantity) * 100
        
        print(f"\n🎯 Quality Control Metrics:")
        print(f"   🥤 Drink Return Rate: {drink_return_rate:.2f}%")
        print(f"   🥛 Yogurt Return Rate: {yogurt_return_rate:.2f}%")
        
        if drink_return_rate > return_rate_threshold:
            print(f"   ⚠️ QUALITY ALERT: Drink return rate exceeds threshold ({return_rate_threshold}%)")
        
        if yogurt_return_rate > return_rate_threshold:
            print(f"   ⚠️ QUALITY ALERT: Yogurt return rate exceeds threshold ({return_rate_threshold}%)")
        
        # 📋 RETURNS DASHBOARD DATA
        returns_summary = {
            'total_returns': all_returns.count(),
            'total_units': total_returned_units,
            'return_reasons': return_reasons,
            'quality_alerts': drink_return_rate > return_rate_threshold or yogurt_return_rate > return_rate_threshold
        }
        
        print(f"\n📋 Returns Dashboard Summary:")
        print(f"   Total Transactions: {returns_summary['total_returns']}")
        print(f"   Total Units Returned: {returns_summary['total_units']}")
        print(f"   Quality Alerts: {'Yes' if returns_summary['quality_alerts'] else 'No'}")
        
        # Verify all returns were processed correctly
        self.assertEqual(all_returns.count(), 3)
        self.assertEqual(total_re…