# backend/sales/tests/base_test.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db import models

from accounts.models import Owner, Salesman, Shop
from products.models import Product, Category, Batch, BatchAssignment
from sales.models import Invoice, InvoiceItem, Transaction, Return, InvoiceSettlement, SettlementPayment, Commission
import json

User = get_user_model()

class AloeVeraParadiseBaseTestCase(APITestCase):
    """
    🏪 ALOE VERA PARADISE - BASE TEST CASE
    
    Common setup and utilities for all business module tests.
    This provides the foundation for testing the complete business workflow.
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
            business_name='Aloe Vera Paradise',
            business_license='ALV-2024-001',
            tax_id='TAX-ALV-123456'
        )
        
        # 👨‍💼 Create Salesmen Team
        # Mike Johnson - Northern Territory
        self.salesman1_user = User.objects.create_user(
            username='mike_johnson',
            email='mike@aloeveraparadise.com',
            password='sales2024',
            first_name='Mike',
            last_name='Johnson',
            role='salesman'
        )
        self.salesman1 = Salesman.objects.create(
            user=self.salesman1_user,
            name='Mike Johnson',
            description='Northern Territory Representative - 15% commission',
            profit_margin=Decimal('15.00'),  # 15% commission as profit margin
            owner=self.owner
        )
        
        # Jennifer Davis - Eastern Territory
        self.salesman2_user = User.objects.create_user(
            username='jennifer_davis',
            email='jennifer@aloeveraparadise.com',
            password='sales2024',
            first_name='Jennifer',
            last_name='Davis',
            role='salesman'
        )
        self.salesman2 = Salesman.objects.create(
            user=self.salesman2_user,
            name='Jennifer Davis',
            description='Eastern Territory Representative - 12% commission',
            profit_margin=Decimal('12.00'),  # 12% commission as profit margin
            owner=self.owner
        )
        
        # Carlos Rodriguez - Western Territory
        self.salesman3_user = User.objects.create_user(
            username='carlos_rodriguez',
            email='carlos@aloeveraparadise.com',
            password='sales2024',
            first_name='Carlos',
            last_name='Rodriguez',
            role='salesman'
        )
        self.salesman3 = Salesman.objects.create(
            user=self.salesman3_user,
            name='Carlos Rodriguez',
            description='Western Territory Representative - 18% commission',
            profit_margin=Decimal('18.00'),  # 18% commission as profit margin
            owner=self.owner
        )
        
        # 🏪 Create Shops for each territory
        self.shop1 = Shop.objects.create(
            name='Wellness Hub North',
            address='456 Health Street, North City, NC 67890',
            contact_person='Mike Johnson',
            phone='+1234567894',
            salesman=self.salesman1
        )
        
        self.shop2 = Shop.objects.create(
            name='Natural Beauty East',
            address='789 Organic Avenue, East Town, ET 13579',
            contact_person='Jennifer Davis',
            phone='+1234567895',
            salesman=self.salesman2
        )
        
        self.shop3 = Shop.objects.create(
            name='Paradise Wellness West',
            address='321 Aloe Boulevard, West Valley, WV 24680',
            contact_person='Carlos Rodriguez',
            phone='+1234567896',
            salesman=self.salesman3
        )
        
        # 📦 Create Product Categories
        self.category_skincare = Category.objects.create(
            name='Skincare',
            description='Aloe Vera based skincare products'
        )
        
        self.category_health = Category.objects.create(
            name='Health & Wellness',
            description='Health supplements and wellness products'
        )
        
        self.category_cosmetics = Category.objects.create(
            name='Cosmetics',
            description='Natural beauty and cosmetic products'
        )
        
        # 🌿 Create Premium Product Line
        self.product1 = Product.objects.create(
            name='Premium Aloe Vera Gel',
            description='100% pure aloe vera gel for skin care',
            category=self.category_skincare,
            sku='ALV-GEL-001',
            base_price=Decimal('29.99'),
            cost_price=Decimal('12.00'),
            min_stock_level=50,
            unit='bottle'
        )
        
        self.product2 = Product.objects.create(
            name='Aloe Wellness Drink',
            description='Refreshing aloe vera health drink',
            category=self.category_health,
            sku='ALV-DRINK-001',
            base_price=Decimal('19.99'),
            cost_price=Decimal('8.50'),
            min_stock_level=100,
            unit='bottle'
        )
        
        self.product3 = Product.objects.create(
            name='Aloe Beauty Serum',
            description='Anti-aging serum with aloe extract',
            category=self.category_cosmetics,
            sku='ALV-SERUM-001',
            base_price=Decimal('49.99'),
            cost_price=Decimal('18.00'),
            min_stock_level=30,
            unit='bottle'
        )
        
        self.product4 = Product.objects.create(
            name='Aloe Hand Cream',
            description='Moisturizing hand cream with aloe vera',
            category=self.category_skincare,
            sku='ALV-CREAM-001',
            base_price=Decimal('14.99'),
            cost_price=Decimal('6.00'),
            min_stock_level=80,
            unit='tube'
        )
        
        # Setup API clients for different users
        self.owner_client = APIClient()
        self.owner_client.force_authenticate(user=self.owner_user)
        
        self.salesman1_client = APIClient()
        self.salesman1_client.force_authenticate(user=self.salesman1_user)
        
        self.salesman2_client = APIClient()
        self.salesman2_client.force_authenticate(user=self.salesman2_user)
        
        self.salesman3_client = APIClient()
        self.salesman3_client.force_authenticate(user=self.salesman3_user)
        
        print("✅ Business setup completed successfully!")
        print(f"👥 Owner: {self.owner.business_name}")
        print(f"🧑‍💼 Salesmen: {self.salesman1.name}, {self.salesman2.name}, {self.salesman3.name}")
        print(f"🏪 Shops: {self.shop1.name}, {self.shop2.name}, {self.shop3.name}")
        print(f"🌿 Products: {self.product1.name}, {self.product2.name}, {self.product3.name}, {self.product4.name}")
        
    def create_test_batches(self):
        """Helper method to create test batches for various scenarios"""
        # Create morning production batch
        batch1 = Batch.objects.create(
            product=self.product1,
            batch_number='ALVR001',
            manufacturing_date=date.today(),
            expiry_date=date.today() + timedelta(days=730),
            initial_quantity=200,
            current_quantity=200,
            unit_cost=Decimal('12.00'),
            notes='Premium batch with excellent quality'
        )
        
        batch2 = Batch.objects.create(
            product=self.product2,
            batch_number='ALVR002',
            manufacturing_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            initial_quantity=300,
            current_quantity=300,
            unit_cost=Decimal('8.50'),
            notes='Standard wellness drink batch'
        )
        
        batch3 = Batch.objects.create(
            product=self.product3,
            batch_number='ALVR003',
            manufacturing_date=date.today(),
            expiry_date=date.today() + timedelta(days=540),
            initial_quantity=150,
            current_quantity=150,
            unit_cost=Decimal('18.00'),
            notes='Premium anti-aging serum batch'
        )
        
        batch4 = Batch.objects.create(
            product=self.product4,
            batch_number='ALVR004',
            manufacturing_date=date.today(),
            expiry_date=date.today() + timedelta(days=730),
            initial_quantity=200,
            current_quantity=200,
            unit_cost=Decimal('6.00'),
            notes='Hand cream batch for all territories'
        )
        
        return batch1, batch2, batch3, batch4
        
    def create_batch_assignments(self, batches):
        """Helper method to create batch assignments for salesmen"""
        batch1, batch2, batch3, batch4 = batches
        
        # Give each salesman access to multiple products they need for testing
        # Salesman 1 (Northern) - Premium Gel, Wellness Drink, Beauty Serum, Hand Cream
        assignment1a = BatchAssignment.objects.create(
            batch=batch1,  # Premium Aloe Gel
            salesman=self.salesman1,
            quantity=70,
            delivered_quantity=70,
            status='delivered',
            notes='Northern territory - Premium gel assignment'
        )
        
        assignment1b = BatchAssignment.objects.create(
            batch=batch2,  # Wellness Drink
            salesman=self.salesman1,
            quantity=50,
            delivered_quantity=50,
            status='delivered',
            notes='Northern territory - Wellness drink assignment'
        )
        
        assignment1c = BatchAssignment.objects.create(
            batch=batch3,  # Beauty Serum
            salesman=self.salesman1,
            quantity=30,
            delivered_quantity=30,
            status='delivered',
            notes='Northern territory - Beauty serum assignment'
        )
        
        assignment1d = BatchAssignment.objects.create(
            batch=batch4,  # Hand Cream
            salesman=self.salesman1,
            quantity=50,
            delivered_quantity=50,
            status='delivered',
            notes='Northern territory - Hand cream assignment'
        )
        
        # Salesman 2 (Eastern) - Wellness Drink, Beauty Serum, Hand Cream
        assignment2a = BatchAssignment.objects.create(
            batch=batch2,  # Wellness Drink  
            salesman=self.salesman2,
            quantity=100,
            delivered_quantity=100,
            status='delivered',
            notes='Eastern territory - Wellness drink assignment'
        )
        
        assignment2b = BatchAssignment.objects.create(
            batch=batch3,  # Beauty Serum
            salesman=self.salesman2,
            quantity=60,
            delivered_quantity=60,
            status='delivered',
            notes='Eastern territory - Beauty serum assignment'
        )
        
        assignment2c = BatchAssignment.objects.create(
            batch=batch4,  # Hand Cream
            salesman=self.salesman2,
            quantity=60,
            delivered_quantity=60,
            status='delivered',
            notes='Eastern territory - Hand cream assignment'
        )
        
        # Salesman 3 (Western) - Premium Gel, Beauty Serum, Hand Cream
        assignment3a = BatchAssignment.objects.create(
            batch=batch1,  # Premium Aloe Gel
            salesman=self.salesman3,
            quantity=30,
            delivered_quantity=30,
            status='delivered',
            notes='Western territory - Premium gel assignment'
        )
        
        assignment3b = BatchAssignment.objects.create(
            batch=batch3,  # Beauty Serum
            salesman=self.salesman3,
            quantity=50,
            delivered_quantity=50,
            status='delivered',
            notes='Western territory - Beauty serum assignment'
        )
        
        assignment3c = BatchAssignment.objects.create(
            batch=batch4,  # Hand Cream
            salesman=self.salesman3,
            quantity=40,
            delivered_quantity=40,
            status='delivered',
            notes='Western territory - Hand cream assignment'
        )
        
        return (assignment1a, assignment1b, assignment1c, assignment1d, 
                assignment2a, assignment2b, assignment2c, 
                assignment3a, assignment3b, assignment3c)
        
    def assertBusinessRuleCompliance(self, response_data, business_rules):
        """Helper method to assert business rule compliance"""
        for rule, expected_value in business_rules.items():
            self.assertIn(rule, response_data)
            if expected_value is not None:
                self.assertEqual(response_data[rule], expected_value)
