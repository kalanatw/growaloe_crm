"""
Tests for Excel Reporting Service
"""

from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import os

from accounts.models import User, Owner, Salesman, Shop
from products.models import Product, Category, Delivery, DeliveryItem
from sales.models import Invoice, InvoiceItem, Transaction
from reports.excel_service import ExcelReportService, generate_all_reports


class ExcelReportServiceTest(TestCase):
    """Test cases for Excel reporting service"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.owner_user = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='testpass123',
            role='owner'
        )
        
        self.salesman_user = User.objects.create_user(
            username='salesman_test',
            email='salesman@test.com',
            password='testpass123',
            role='salesman'
        )
        
        # Create owner
        self.owner = Owner.objects.create(
            user=self.owner_user,
            business_name='Test Business',
            business_license='BL123456'
        )
        
        # Create salesman
        self.salesman = Salesman.objects.create(
            owner=self.owner,
            user=self.salesman_user,
            name='Test Salesman',
            profit_margin=10.00
        )
        
        # Create shop
        self.shop = Shop.objects.create(
            salesman=self.salesman,
            name='Test Shop',
            location='Test Location',
            contact_person='Test Contact'
        )
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            sku='TEST001',
            base_price=Decimal('100.00'),
            cost_price=Decimal('80.00'),
            min_stock_level=10,
            owner=self.owner
        )
        
        # Create test invoices
        self.create_test_invoices()
        
        # Create test deliveries
        self.create_test_deliveries()
    
    def create_test_invoices(self):
        """Create test invoices for reporting"""
        today = timezone.now().date()
        
        for i in range(5):
            invoice = Invoice.objects.create(
                shop=self.shop,
                salesman=self.salesman,
                invoice_date=today - timedelta(days=i),
                status='paid',
                subtotal=Decimal('500.00'),
                net_total=Decimal('500.00'),
                paid_amount=Decimal('400.00'),
                balance_due=Decimal('100.00'),
                created_by=self.owner_user
            )
            
            # Create invoice items
            InvoiceItem.objects.create(
                invoice=invoice,
                product=self.product,
                quantity=5,
                unit_price=Decimal('100.00'),
                salesman_margin=Decimal('10.00')
            )
            
            # Create transaction
            Transaction.objects.create(
                invoice=invoice,
                transaction_type='payment',
                payment_method='cash',
                amount=Decimal('400.00'),
                transaction_date=invoice.invoice_date,
                created_by=self.owner_user
            )
    
    def create_test_deliveries(self):
        """Create test deliveries for reporting"""
        today = timezone.now().date()
        
        for i in range(3):
            delivery = Delivery.objects.create(
                salesman=self.salesman,
                delivery_date=today - timedelta(days=i),
                status='delivered',
                total_margin_earned=Decimal('50.00'),
                created_by=self.owner_user
            )
            
            # Create delivery items
            DeliveryItem.objects.create(
                delivery=delivery,
                product=self.product,
                quantity=10,
                unit_price=Decimal('100.00')
            )
    
    def test_excel_service_initialization(self):
        """Test Excel service initialization"""
        service = ExcelReportService()
        self.assertIsNotNone(service)
        self.assertIsNotNone(service.styles)
        self.assertIn('header', service.styles)
        self.assertIn('currency', service.styles)
    
    def test_master_dashboard_generation(self):
        """Test master dashboard report generation"""
        service = ExcelReportService()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        filepath = service.generate_master_dashboard(week_ago, today)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.xlsx'))
        self.assertIn('master_dashboard', filepath)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def test_delivery_performance_generation(self):
        """Test delivery performance report generation"""
        service = ExcelReportService()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        filepath = service.generate_delivery_performance(week_ago, today)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.xlsx'))
        self.assertIn('delivery_performance', filepath)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def test_salesman_performance_generation(self):
        """Test salesman performance report generation"""
        service = ExcelReportService()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        filepath = service.generate_salesman_performance(week_ago, today)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.xlsx'))
        self.assertIn('salesman_performance', filepath)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def test_cash_flow_analysis_generation(self):
        """Test cash flow analysis report generation"""
        service = ExcelReportService()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        filepath = service.generate_cash_flow_analysis(week_ago, today)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.xlsx'))
        self.assertIn('cash_flow_analysis', filepath)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def test_product_analytics_generation(self):
        """Test product analytics report generation"""
        service = ExcelReportService()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        filepath = service.generate_product_analytics(week_ago, today)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.xlsx'))
        self.assertIn('product_analytics', filepath)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def test_customer_analysis_generation(self):
        """Test customer analysis report generation"""
        service = ExcelReportService()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        filepath = service.generate_customer_analysis(week_ago, today)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.xlsx'))
        self.assertIn('customer_analysis', filepath)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def test_generate_all_reports(self):
        """Test generating all reports at once"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        reports = generate_all_reports(week_ago, today)
        
        self.assertEqual(len(reports), 6)  # Should generate 6 different report types
        
        expected_reports = [
            'master_dashboard',
            'delivery_performance',
            'salesman_performance',
            'cash_flow_analysis',
            'product_analytics',
            'customer_analysis'
        ]
        
        for report_type in expected_reports:
            self.assertIn(report_type, reports)
            filepath = reports[report_type]
            self.assertTrue(os.path.exists(filepath))
            
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def test_kpi_calculation(self):
        """Test KPI calculation logic"""
        service = ExcelReportService()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        kpis = service._calculate_kpis(week_ago, today)
        
        self.assertIn('Total Revenue', kpis)
        self.assertIn('Deliveries', kpis)
        self.assertIn('Collection Rate', kpis)
        self.assertIn('Outstanding', kpis)
        
        # Check KPI structure
        for kpi_name, kpi_data in kpis.items():
            self.assertIn('current', kpi_data)
            self.assertIn('previous', kpi_data)
            self.assertIn('change_pct', kpi_data)
            self.assertIn('trend', kpi_data)
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove any remaining test files
        reports_dir = os.path.join('media', 'reports')
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.startswith(('master_dashboard', 'delivery_performance', 
                                      'salesman_performance', 'cash_flow_analysis',
                                      'product_analytics', 'customer_analysis')):
                    filepath = os.path.join(reports_dir, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)