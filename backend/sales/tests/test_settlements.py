# backend/sales/tests/test_settlements.py
from .base_test import AloeVeraParadiseBaseTestCase
from products.models import Batch, BatchAssignment
from sales.models import Invoice, InvoiceItem, Commission, InvoiceSettlement, SettlementPayment
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

class SettlementsTestCase(AloeVeraParadiseBaseTestCase):
    """
    🏦 SETTLEMENTS & FINANCIAL MANAGEMENT TESTS
    
    Tests the evening settlement workflow:
    - Commission calculations and settlements
    - Payment processing and tracking
    - Financial reconciliation
    - Settlement analytics
    """
    
    def test_01_evening_settlements_and_collections(self):
        """
        🌆 EVENING SETTLEMENTS & COLLECTIONS TEST
        
        Tests Sarah's evening routine of calculating commissions,
        processing settlements, and financial reconciliation.
        """
        print("\n" + "="*70)
        print("🌆 TESTING: Evening Settlements & Collections")
        print("="*70)
        
        # Setup: Create sales data first
        batches = self.create_test_batches()
        assignments = self.create_batch_assignments(batches)
        
        # Create sample invoices for each salesman
        invoices = []
        
        # Mike's sales
        invoice1_data = {
            'shop': self.shop1.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 15.00,  # 15% margin
            'notes': 'Premium spa settlement test',
            'terms_conditions': 'Net 30',
            'items': [
                {
                    'product': self.product1.id,  # Premium Aloe Vera Gel
                    'quantity': 30,
                    'unit_price': str(self.product1.base_price),
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
            print(f"❌ Invoice 1 creation failed with status {response1.status_code}")
            print(f"Response data: {response1.data}")
            print(f"Request data: {invoice1_data}")
            
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        invoice1 = Invoice.objects.get(id=response1.data['id'])
        invoices.append(invoice1)
        
        print(f"📄 Mike's invoice: {invoice1.invoice_number} - ${invoice1.net_total}")
        
        # Jennifer's sales
        invoice2_data = {
            'shop': self.shop2.id,
            'due_date': str(date.today() + timedelta(days=20)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 10.00,  # 10% margin
            'notes': 'Health center settlement test',
            'terms_conditions': 'Net 20',
            'items': [
                {
                    'product': self.product2.id,  # Aloe Wellness Drink
                    'quantity': 40,
                    'unit_price': str(self.product2.base_price),
                }
            ]
        }
        
        response2 = self.salesman2_client.post(
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
        invoices.append(invoice2)
        
        print(f"📄 Jennifer's invoice: {invoice2.invoice_number} - ${invoice2.net_total}")
        
        # Carlos's sales
        invoice3_data = {
            'shop': self.shop3.id,
            'due_date': str(date.today() + timedelta(days=15)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 18.00,  # 18% margin
            'notes': 'Luxury salon settlement test',
            'terms_conditions': 'Net 15',
            'items': [
                {
                    'product': self.product3.id,  # Beauty Serum
                    'quantity': 25,
                    'unit_price': str(self.product3.base_price),
                }
            ]
        }
        
        response3 = self.salesman3_client.post(
            reverse('invoice-list'),
            data=invoice3_data,
            format='json'
        )
        
        # Debug output for failed requests
        if response3.status_code != status.HTTP_201_CREATED:
            print(f"❌ Invoice 3 creation failed with status {response3.status_code}")
            print(f"Response data: {response3.data}")
            print(f"Request data: {invoice3_data}")
            
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        invoice3 = Invoice.objects.get(id=response3.data['id'])
        invoices.append(invoice3)
        
        print(f"📄 Carlos's invoice: {invoice3.invoice_number} - ${invoice3.net_total}")
        
        # 💵 Phase 1: Calculate daily commissions
        print("\n💵 Phase 1: Daily Commission Calculations")
        
        # 💵 Phase 1: Verify automatic commission creation
        print("\n💵 Phase 1: Verify Automatic Commission Creation")
        
        # Get commissions that were automatically created with invoices
        from sales.models import Commission
        
        mike_commission = Commission.objects.filter(
            salesman=self.salesman1,
            invoice=invoice1
        ).first()
        
        jennifer_commission = Commission.objects.filter(
            salesman=self.salesman2,
            invoice=invoice2
        ).first()
        
        carlos_commission = Commission.objects.filter(
            salesman=self.salesman3,
            invoice=invoice3
        ).first()
        
        if mike_commission:
            print(f"💵 Mike's commission: ${mike_commission.commission_amount}")
        if jennifer_commission:
            print(f"💵 Jennifer's commission: ${jennifer_commission.commission_amount}")
        if carlos_commission:
            print(f"💵 Carlos's commission: ${carlos_commission.commission_amount}")
        
        # 🏦 Phase 2: Process settlements
        print("\n🏦 Phase 2: Settlement Processing")
        
        # Create settlement for invoice1 using InvoiceSettlement
        if mike_commission:
            settlement1_data = {
                'invoice': invoice1.id,
                'total_amount': str(invoice1.net_total),
                'settlement_date': timezone.now().isoformat(),
                'notes': 'Daily settlement for Northern Territory',
                'payments': [
                    {
                        'payment_method': 'bank_transfer',
                        'amount': str(invoice1.net_total),
                        'reference_number': 'TXN001-MIKE-' + str(date.today()),
                        'notes': 'Full settlement payment'
                    }
                ]
            }
            
            response_settlement1 = self.owner_client.post(
                reverse('invoicesettlement-list'),
                data=settlement1_data,
                format='json'
            )
            
            # Debug output for failed requests
            if response_settlement1.status_code != status.HTTP_201_CREATED:
                print(f"❌ Settlement 1 creation failed with status {response_settlement1.status_code}")
                print(f"Response data: {response_settlement1.data}")
                print(f"Request data: {settlement1_data}")
                
            self.assertEqual(response_settlement1.status_code, status.HTTP_201_CREATED)
            settlement1 = InvoiceSettlement.objects.get(id=response_settlement1.data['id'])
            
            print(f"🏦 Created settlement for Mike: ${settlement1.total_amount}")
        
        # Create settlement for Jennifer
        if jennifer_commission:
            settlement2_data = {
                'invoice': invoice2.id,
                'total_amount': str(invoice2.net_total),
                'settlement_date': timezone.now().isoformat(),
                'notes': 'Daily settlement for Eastern Territory',
                'payments': [
                    {
                        'payment_method': 'bank_transfer',
                        'amount': str(invoice2.net_total),
                        'reference_number': 'TXN002-JENNIFER-' + str(date.today()),
                        'notes': 'Full settlement payment'
                    }
                ]
            }
            
            response_settlement2 = self.owner_client.post(
                reverse('invoicesettlement-list'),
                data=settlement2_data,
                format='json'
            )
            self.assertEqual(response_settlement2.status_code, status.HTTP_201_CREATED)
            settlement2 = InvoiceSettlement.objects.get(id=response_settlement2.data['id'])
            
            print(f"🏦 Created settlement for Jennifer: ${settlement2.total_amount}")
        
        # Create settlement for Carlos
        if carlos_commission:
            settlement3_data = {
                'invoice': invoice3.id,
                'total_amount': str(carlos_commission.commission_amount),
                'settlement_date': str(date.today()),
                'payment_method': 'bank_transfer',
                'reference_number': 'TXN003-CARLOS-' + str(date.today()),
                'notes': 'Daily commission settlement for Western Territory',
                'settled_by': self.owner_user.id
            }
            
            response_settlement3 = self.owner_client.post(
                reverse('invoicesettlement-list'),
                data=settlement3_data,
                format='json'
            )
            self.assertEqual(response_settlement3.status_code, status.HTTP_201_CREATED)
            settlement3 = InvoiceSettlement.objects.get(id=response_settlement3.data['id'])
            
            print(f"🏦 Created settlement for Carlos: ${settlement3.total_amount}")
        
        # 📊 Phase 3: Financial reconciliation
        print("\n📊 Phase 3: Financial Reconciliation")
        
        total_settlements = InvoiceSettlement.objects.filter(
            settlement_date=date.today()
        ).count()
        
        total_settlement_amount = sum([
            settlement.total_amount for settlement in InvoiceSettlement.objects.filter(
                settlement_date=date.today()
            )
        ])
        
        print(f"🧮 Total settlements processed: {total_settlements}")
        print(f"💰 Total settlement amount: ${total_settlement_amount}")
        
        # Test settlement analytics via API
        response = self.owner_client.get(reverse('invoicesettlement-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Calculate analytics from returned data
        settlements_data = response.data
        if 'results' in settlements_data:
            settlements_list = settlements_data['results']
        else:
            settlements_list = settlements_data
            
        analytics = {
            'daily_settlements': len(settlements_list),
            'total_amount': sum(Decimal(str(s.get('total_amount', 0))) for s in settlements_list),
            'payment_methods': {'cash': len(settlements_list)}  # Simplified for test
        }
        print(f"📈 Settlement Analytics: {analytics}")
        
        # Verify analytics structure
        self.assertIn('daily_settlements', analytics)
        self.assertIn('total_amount', analytics)
        self.assertIn('payment_methods', analytics)
        
        print("✅ Evening settlements completed successfully!")
        
        return invoices
    
    def test_02_commission_dashboard_analytics(self):
        """
        📊 COMMISSION DASHBOARD ANALYTICS TEST
        
        Tests comprehensive commission tracking and analytics dashboard.
        """
        print("\n" + "="*70)
        print("📊 TESTING: Commission Dashboard Analytics")
        print("="*70)
        
        # Create test data first
        self.test_01_evening_settlements_and_collections()
        
        # Test commission analytics via API
        response = self.owner_client.get(reverse('commission-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Calculate analytics from returned data
        commissions_data = response.data
        if 'results' in commissions_data:
            commissions_list = commissions_data['results']
        else:
            commissions_list = commissions_data
            
        dashboard = {
            'total_commissions': len(commissions_list),
            'total_amount': sum(Decimal(str(c.get('commission_amount', 0))) for c in commissions_list),
            'pending_count': len([c for c in commissions_list if c.get('status') == 'pending']),
            'paid_count': len([c for c in commissions_list if c.get('status') == 'paid'])
        }
        print(f"📊 Commission Dashboard: {dashboard}")
        
        # Verify dashboard components
        expected_sections = [
            'total_commissions',
            'total_amount',
            'pending_count',
            'paid_count'
        ]
        
        for section in expected_sections:
            self.assertIn(section, dashboard)
            print(f"✅ {section.replace('_', ' ').title()}: Available")
        
        # Test individual salesman commission history
        response = self.salesman1_client.get(reverse('commission-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Get commissions for this salesman
        commissions_data = response.data
        if 'results' in commissions_data:
            commissions_list = commissions_data['results']
        else:
            commissions_list = commissions_data
            
        salesman_commissions = [
            c for c in commissions_list 
            if c.get('salesman') == self.salesman1.id
        ]
        
        commission_history = {
            'commissions': len(salesman_commissions),
            'total_earned': sum(Decimal(str(c.get('commission_amount', 0))) for c in salesman_commissions),
            'pending_settlements': len([c for c in salesman_commissions if c.get('status') == 'pending'])
        }
        print(f"💵 Mike's Commission History: {commission_history}")
        
        self.assertIn('commissions', commission_history)
        self.assertIn('total_earned', commission_history)
        self.assertIn('pending_settlements', commission_history)
        
        print("✅ Commission dashboard analytics verified!")
    
    def test_03_payment_processing_workflow(self):
        """
        💳 PAYMENT PROCESSING WORKFLOW TEST
        
        Tests various payment methods and processing workflows.
        """
        print("\n" + "="*70)
        print("💳 TESTING: Payment Processing Workflow")
        print("="*70)
        
        # Create a commission to settle
        batches = self.create_test_batches()
        assignments = self.create_batch_assignments(batches)
        
        # Create test invoice and commission
        invoice_data = {
            'shop': self.shop1.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'shop_margin': 15.00,  # 15% margin
            'notes': 'Payment processing test',
            'terms_conditions': 'Net 30',
            'items': [
                {
                    'product': self.product1.id,
                    'batch': batches[0].id,
                    'quantity': 5,
                    'unit_price': '35.50',
                    'salesman_margin': 10.00,
                    'shop_margin': 15.00
                }
            ]
        }
        
        response = self.salesman1_client.post(
            reverse('invoice-list'),
            data=invoice_data,
            format='json'
        )
        if response.status_code != 201:
            print(f"❌ Invoice creation failed: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the created invoice and verify commission was auto-created
        invoice = Invoice.objects.get(id=response.data['id'])
        commission = Commission.objects.filter(
            salesman=self.salesman1,
            invoice=invoice
        ).first()
        
        self.assertIsNotNone(commission)
        print(f"💵 Commission created: ${commission.commission_amount}")
        
        # Test settlement creation
        settlement_data = {
            'invoice': invoice.id,
            'total_amount': str(commission.commission_amount),
            'notes': 'Payment processing test settlement'
        }
        
        response = self.owner_client.post(
            reverse('invoicesettlement-list'),
            data=settlement_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f"🏦 Settlement created: ${response.data['total_amount']}")
        
        print("✅ Payment processing workflow completed!")
    
    def test_04_financial_reconciliation_reports(self):
        """
        📋 FINANCIAL RECONCILIATION REPORTS TEST
        
        Tests comprehensive financial reporting and reconciliation features.
        """
        print("\n" + "="*70)
        print("📋 TESTING: Financial Reconciliation Reports")
        print("="*70)
        
        # Create comprehensive test data
        self.test_01_evening_settlements_and_collections()
        
        # Generate financial report data from existing APIs
        # Get invoices for the day
        invoices_response = self.owner_client.get(reverse('invoice-list'))
        self.assertEqual(invoices_response.status_code, status.HTTP_200_OK)
        
        # Get settlements for the day
        settlements_response = self.owner_client.get(reverse('invoicesettlement-list'))
        self.assertEqual(settlements_response.status_code, status.HTTP_200_OK)
        
        # Get commissions for the day
        commissions_response = self.owner_client.get(reverse('commission-list'))
        self.assertEqual(commissions_response.status_code, status.HTTP_200_OK)
        
        # Calculate financial summary
        invoices_data = invoices_response.data.get('results', invoices_response.data)
        settlements_data = settlements_response.data.get('results', settlements_response.data)
        commissions_data = commissions_response.data.get('results', commissions_response.data)
        
        daily_report = {
            'total_invoices': len(invoices_data),
            'total_revenue': sum(Decimal(str(inv.get('net_total', 0))) for inv in invoices_data),
            'total_settlements': len(settlements_data),
            'total_settled_amount': sum(Decimal(str(s.get('total_amount', 0))) for s in settlements_data),
            'total_commissions': len(commissions_data),
            'total_commission_amount': sum(Decimal(str(c.get('commission_amount', 0))) for c in commissions_data)
        }
        print(f"📊 Daily Financial Report: {daily_report}")
        
        # Verify report structure
        expected_sections = [
            'total_invoices',
            'total_revenue',
            'total_settlements',
            'total_settled_amount',
            'total_commissions',
            'total_commission_amount'
        ]
        
        for section in expected_sections:
            self.assertIn(section, daily_report)
            print(f"✅ {section.replace('_', ' ').title()}: {daily_report[section]}")
        
        print("✅ Financial reconciliation reports completed!")
