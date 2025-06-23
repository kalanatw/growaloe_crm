# backend/sales/tests/test_analytics.py
from .base_test import AloeVeraParadiseBaseTestCase
from products.models import Batch, BatchAssignment
from sales.models import Invoice, InvoiceItem, Commission, InvoiceSettlement, SettlementPayment, Return
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status

class AnalyticsTestCase(AloeVeraParadiseBaseTestCase):
    """
    📊 BUSINESS ANALYTICS & REPORTING TESTS
    
    Tests comprehensive business analytics:
    - Performance dashboards
    - Trend analysis and forecasting
    - Business intelligence reports
    - KPI monitoring and alerts
    """
    
    def test_01_comprehensive_business_analytics(self):
        """
        📊 COMPREHENSIVE BUSINESS ANALYTICS TEST
        
        Tests Sarah's evening analytics review covering all business aspects
        including sales performance, inventory analysis, and growth trends.
        """
        print("\n" + "="*80)
        print("📊 TESTING: Comprehensive Business Analytics")
        print("="*80)
        
        # Create necessary batches and assignments for testing
        batches = self.create_test_batches()
        self.create_batch_assignments(batches)
        
        # Create realistic business data for analytics
        analytics_invoices = []
        
        # Create 5 days of sales data for trend analysis
        for i in range(5):
            sale_date = date.today() - timedelta(days=i)
            
            invoice_data = {
                'shop': self.shop1.id,
                'due_date': str(sale_date + timedelta(days=30)),
                'tax_amount': 0.00,
                'discount_amount': i * 5.00,  # Varying discounts
                'shop_margin': 15.00,
                'notes': f'Analytics test data for day {i+1}',
                'terms_conditions': 'Net 30',
                'items': [
                    {
                        'product': self.product1.id,
                        'quantity': 10 + i,  # Varying quantities for trend analysis
                        'unit_price': self.product1.base_price,
                    }
                ]
            }
            
            response = self.salesman1_client.post(
                reverse('invoice-list'),
                data=invoice_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            invoice_data_response = response.data
            analytics_invoices.append(invoice_data_response)
            
        print(f"📈 Created {len(analytics_invoices)} invoices for analytics testing")
        
        # 📊 Phase 1: Business Overview Dashboard using Invoice Summary
        print("\n📊 Phase 1: Business Overview Dashboard")
        
        response = self.owner_client.get(reverse('invoice-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        overview = response.data
        print(f"🏢 Business Overview: {overview}")
        
        # Verify dashboard components
        expected_sections = [
            'total_invoices',
            'total_amount',
            'paid_amount',
            'outstanding_amount',
            'overdue_invoices',
            'draft_invoices'
        ]
        
        for section in expected_sections:
            self.assertIn(section, overview)
            print(f"✅ {section.replace('_', ' ').title()}: {overview[section]}")
        
        # 📈 Phase 2: Sales Trend Analysis using Invoice Data
        print("\n📈 Phase 2: Sales Trend Analysis")
        
        # Get all invoices for trend analysis
        response = self.owner_client.get(reverse('invoice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        invoices_data = response.data.get('results', response.data)
        
        # Calculate trend metrics from invoice data
        sales_trends = {
            'total_invoices': len(invoices_data),
            'total_revenue': sum(float(inv.get('net_total', 0)) for inv in invoices_data),
            'average_order_value': 0,
            'growth_insights': []
        }
        
        if sales_trends['total_invoices'] > 0:
            sales_trends['average_order_value'] = sales_trends['total_revenue'] / sales_trends['total_invoices']
        
        print(f"📊 Sales Trends: {sales_trends}")
        print(f"📈 Total Revenue: ${sales_trends['total_revenue']:.2f}")
        print(f"📊 Average Order Value: ${sales_trends['average_order_value']:.2f}")
        
        self.assertGreater(sales_trends['total_invoices'], 0)
        self.assertGreater(sales_trends['total_revenue'], 0)
        
        # 👥 Phase 3: Salesman Performance Analytics using Commission Data
        print("\n👥 Phase 3: Salesman Performance Analytics")
        
        response = self.owner_client.get(reverse('commission-dashboard-data'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        performance_data = response.data
        print(f"🏆 Performance Data: {performance_data}")
        
        # Verify commission dashboard structure
        self.assertIn('total_pending_commissions', performance_data)
        self.assertIn('total_paid_commissions', performance_data)
        self.assertIn('salesman_commissions', performance_data)
        
        # Analyze individual salesman performance
        for salesman_data in performance_data.get('salesman_commissions', []):
            self.assertIn('salesman_name', salesman_data)
            self.assertIn('pending_commission', salesman_data)
            self.assertIn('total_invoices', salesman_data)
            print(f"👤 {salesman_data['salesman_name']}: ${salesman_data['pending_commission']} pending")
        
        # 📦 Phase 4: Product Performance Analysis using Invoice Items
        print("\n📦 Phase 4: Product Performance Analysis")
        
        # Get invoice items for product analysis
        response = self.owner_client.get(reverse('invoiceitem-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        invoice_items = response.data.get('results', response.data)
        
        # Calculate product performance metrics
        product_analytics = {
            'total_items_sold': len(invoice_items),
            'products_by_quantity': {},
            'products_by_revenue': {},
            'top_selling_products': []
        }
        
        for item in invoice_items:
            product_name = item.get('product_name', 'Unknown')
            quantity = int(item.get('quantity', 0))
            total_price = float(item.get('total_price', 0))
            
            if product_name not in product_analytics['products_by_quantity']:
                product_analytics['products_by_quantity'][product_name] = 0
                product_analytics['products_by_revenue'][product_name] = 0
            
            product_analytics['products_by_quantity'][product_name] += quantity
            product_analytics['products_by_revenue'][product_name] += total_price
        
        print(f"📊 Product Analytics: {product_analytics}")
        print(f"📦 Total Items Sold: {product_analytics['total_items_sold']}")
        
        # 💰 Phase 5: Financial Analytics using Available Data
        print("\n💰 Phase 5: Financial Analytics")
        
        # Get settlements data for financial analysis
        response = self.owner_client.get(reverse('invoicesettlement-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        settlements_data = response.data.get('results', response.data)
        
        financial_analytics = {
            'total_settlements': len(settlements_data),
            'total_settled_amount': sum(float(s.get('total_amount', 0)) for s in settlements_data),
            'settlement_methods': {},
            'cash_flow_insights': []
        }
        
        print(f"💵 Financial Analytics: {financial_analytics}")
        print(f"💰 Total Settled: ${financial_analytics['total_settled_amount']:.2f}")
        
        print("✅ Comprehensive business analytics completed successfully!")
        
        return analytics_invoices
    
    def test_02_kpi_monitoring_and_alerts(self):
        """
        🚨 KPI MONITORING & ALERTS TEST
        
        Tests key performance indicator monitoring and automated alerting system.
        """
        print("\n" + "="*70)
        print("🚨 TESTING: KPI Monitoring & Alerts")
        print("="*70)
        
        # Create test data first
        self.test_01_comprehensive_business_analytics()
        
        # Test KPI dashboard using available commission dashboard
        response = self.owner_client.get(reverse('commission-dashboard-data'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        kpi_data = response.data
        print(f"📊 KPI Dashboard: {kpi_data}")
        
        # Verify KPI metrics structure
        self.assertIn('total_pending_commissions', kpi_data)
        self.assertIn('total_paid_commissions', kpi_data)
        
        # Calculate KPI metrics
        total_commissions = float(kpi_data.get('total_pending_commissions', 0)) + float(kpi_data.get('total_paid_commissions', 0))
        pending_ratio = float(kpi_data.get('total_pending_commissions', 0)) / total_commissions if total_commissions > 0 else 0
        
        print(f"💰 Total Commissions: ${total_commissions:.2f}")
        print(f"⏳ Pending Ratio: {pending_ratio:.2%}")
        
        # Test KPI alerting logic
        alerts = []
        
        # Alert 1: High pending commission ratio
        if pending_ratio > 0.8:
            alerts.append({
                'type': 'high_pending_commissions',
                'severity': 'warning',
                'message': f'High pending commission ratio: {pending_ratio:.2%}'
            })
        
        # Get invoice summary for more KPIs
        response = self.owner_client.get(reverse('invoice-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        invoice_summary = response.data
        overdue_count = int(invoice_summary.get('overdue_invoices', 0))
        total_invoices = int(invoice_summary.get('total_invoices', 0))
        
        # Alert 2: High overdue invoice ratio
        if total_invoices > 0:
            overdue_ratio = overdue_count / total_invoices
            if overdue_ratio > 0.2:  # More than 20% overdue
                alerts.append({
                    'type': 'high_overdue_ratio',
                    'severity': 'critical',
                    'message': f'High overdue invoice ratio: {overdue_ratio:.2%}'
                })
        
        # Alert 3: Cash flow concerns
        outstanding_amount = float(invoice_summary.get('outstanding_amount', 0))
        total_amount = float(invoice_summary.get('total_amount', 0))
        
        if total_amount > 0:
            outstanding_ratio = outstanding_amount / total_amount
            if outstanding_ratio > 0.5:  # More than 50% outstanding
                alerts.append({
                    'type': 'cash_flow_concern',
                    'severity': 'warning',
                    'message': f'High outstanding amount ratio: {outstanding_ratio:.2%}'
                })
        
        print(f"🚨 Generated {len(alerts)} KPI alerts")
        for alert in alerts:
            print(f"   {alert['severity'].upper()}: {alert['message']}")
        
        # Test performance thresholds
        performance_metrics = {
            'commission_efficiency': (1 - pending_ratio) * 100,
            'collection_efficiency': (1 - (overdue_count / total_invoices if total_invoices > 0 else 0)) * 100,
            'cash_flow_health': (1 - (outstanding_amount / total_amount if total_amount > 0 else 0)) * 100
        }
        
        print("\n📈 Performance Metrics:")
        for metric, value in performance_metrics.items():
            status_icon = "✅" if value > 80 else "⚠️" if value > 60 else "❌"
            print(f"   {status_icon} {metric.replace('_', ' ').title()}: {value:.1f}%")
        
        print("✅ KPI monitoring and alerts verification completed!")
        
        # The kpi_dashboard is the invoice summary data  
        print(f"📊 KPI Dashboard: {invoice_summary}")
        
        # Verify basic KPI structure from available data
        expected_metrics = [
            'total_invoices',
            'total_amount',
            'paid_amount',
            'outstanding_amount',
            'overdue_invoices'
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, invoice_summary)
            print(f"✅ {metric.replace('_', ' ').title()}: {invoice_summary[metric]}")
        
        print("✅ All KPI metrics verified successfully!")
        print("✅ KPI monitoring and alerts verified!")
    
    def test_03_predictive_analytics_and_forecasting(self):
        """
        🔮 PREDICTIVE ANALYTICS & FORECASTING TEST
        
        Tests predictive modeling and business forecasting capabilities.
        """
        print("\n" + "="*70)
        print("🔮 TESTING: Predictive Analytics & Forecasting")
        print("="*70)
        
        # Create historical data for forecasting
        self.test_01_comprehensive_business_analytics()
        
        # Test sales forecasting
        response = self.owner_client.get(
            reverse('sales-forecasting'),
            data={'period': '30_days', 'confidence_level': '95'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        forecast = response.data
        print(f"📈 Sales Forecast: {forecast}")
        
        self.assertIn('forecast_data', forecast)
        self.assertIn('confidence_intervals', forecast)
        self.assertIn('trend_analysis', forecast)
        
        # Test inventory demand forecasting
        response = self.owner_client.get(
            reverse('inventory-demand-forecast'),
            data={'product_id': self.product1.id, 'horizon': '60_days'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        demand_forecast = response.data
        print(f"📦 Demand Forecast: {demand_forecast}")
        
        self.assertIn('demand_prediction', demand_forecast)
        self.assertIn('recommended_stock', demand_forecast)
        self.assertIn('reorder_schedule', demand_forecast)
        
        # Test customer behavior prediction
        response = self.owner_client.get(reverse('customer-behavior-prediction'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        behavior_prediction = response.data
        print(f"👥 Behavior Prediction: {behavior_prediction}")
        
        self.assertIn('churn_risk', behavior_prediction)
        self.assertIn('purchase_likelihood', behavior_prediction)
        self.assertIn('customer_segments', behavior_prediction)
        
        print("✅ Predictive analytics and forecasting verified!")
    
    def test_04_business_intelligence_reports(self):
        """
        📋 BUSINESS INTELLIGENCE REPORTS TEST
        
        Tests comprehensive business intelligence reporting and insights.
        """
        print("\n" + "="*70)
        print("📋 TESTING: Business Intelligence Reports")
        print("="*70)
        
        # Create comprehensive test data
        self.test_01_comprehensive_business_analytics()
        
        # Test executive summary report
        response = self.owner_client.get(
            reverse('executive-summary-report'),
            data={'period': 'monthly'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        executive_summary = response.data
        print(f"📊 Executive Summary: {executive_summary}")
        
        # Verify executive summary components
        expected_sections = [
            'key_metrics',
            'performance_highlights',
            'growth_indicators',
            'risk_factors',
            'recommendations'
        ]
        
        for section in expected_sections:
            self.assertIn(section, executive_summary)
            print(f"✅ {section.replace('_', ' ').title()}: Available")
        
        # Test operational efficiency report
        response = self.owner_client.get(reverse('operational-efficiency-report'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        efficiency_report = response.data
        print(f"⚡ Efficiency Report: {efficiency_report}")
        
        self.assertIn('process_efficiency', efficiency_report)
        self.assertIn('resource_utilization', efficiency_report)
        self.assertIn('bottleneck_analysis', efficiency_report)
        
        # Test market analysis report
        response = self.owner_client.get(reverse('market-analysis-report'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        market_analysis = response.data
        print(f"🏪 Market Analysis: {market_analysis}")
        
        self.assertIn('market_trends', market_analysis)
        self.assertIn('competitive_position', market_analysis)
        self.assertIn('market_opportunities', market_analysis)
        
        # Test custom report generation
        custom_report_config = {
            'report_type': 'custom',
            'metrics': ['sales', 'commission', 'inventory'],
            'dimensions': ['territory', 'product', 'time'],
            'filters': {
                'date_range': {
                    'start': str(date.today() - timedelta(days=30)),
                    'end': str(date.today())
                }
            }
        }
        
        response = self.owner_client.post(
            reverse('generate-custom-report'),
            data=custom_report_config,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        custom_report = response.data
        print(f"📄 Custom Report: {custom_report}")
        
        self.assertIn('report_data', custom_report)
        self.assertIn('visualizations', custom_report)
        self.assertIn('insights', custom_report)
        
        print("✅ Business intelligence reports verified!")
    
    def test_05_real_time_analytics_dashboard(self):
        """
        ⚡ REAL-TIME ANALYTICS DASHBOARD TEST
        
        Tests real-time data streaming and live dashboard updates.
        """
        print("\n" + "="*70)
        print("⚡ TESTING: Real-time Analytics Dashboard")
        print("="*70)
        
        # Test real-time dashboard endpoint
        response = self.owner_client.get(reverse('realtime-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        realtime_data = response.data
        print(f"⚡ Real-time Dashboard: {realtime_data}")
        
        # Verify real-time components
        expected_components = [
            'live_sales',
            'active_sessions',
            'inventory_alerts',
            'performance_metrics',
            'system_health'
        ]
        
        for component in expected_components:
            self.assertIn(component, realtime_data)
            print(f"✅ {component.replace('_', ' ').title()}: Live")
        
        # Test data refresh capability
        response = self.owner_client.post(reverse('refresh-dashboard-data'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        refresh_result = response.data
        print(f"🔄 Dashboard Refresh: {refresh_result}")
        
        self.assertIn('refresh_timestamp', refresh_result)
        self.assertIn('data_sources_updated', refresh_result)
        
        # Test live notifications
        response = self.owner_client.get(reverse('live-notifications'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notifications = response.data
        print(f"📢 Live Notifications: {notifications}")
        
        self.assertIn('notifications', notifications)
        self.assertIn('unread_count', notifications)
        
        print("✅ Real-time analytics dashboard verified!")
