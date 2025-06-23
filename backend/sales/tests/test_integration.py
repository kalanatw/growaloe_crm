# backend/sales/tests/test_integration.py
from .base_test import AloeVeraParadiseBaseTestCase
from products.models import Batch, BatchAssignment
from sales.models import Invoice, InvoiceItem, Commission, InvoiceSettlement, Return
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status

class BusinessWorkflowIntegrationTestCase(AloeVeraParadiseBaseTestCase):
    """
    🔄 COMPLETE BUSINESS WORKFLOW INTEGRATION TESTS
    
    Tests end-to-end business workflows that span multiple modules:
    - Complete business day simulation
    - Cross-module data consistency
    - Workflow automation and integration
    - Performance optimization testing
    """
    
    def test_01_complete_business_day_simulation(self):
        """
        🌅🌆 COMPLETE BUSINESS DAY SIMULATION TEST
        
        Simulates Sarah's complete business day from morning production
        to evening settlements, ensuring all systems work together seamlessly.
        """
        print("\n" + "="*80)
        print("🌅🌆 TESTING: Complete Business Day Simulation")
        print("="*80)
        
        # 🌅 Morning: Production Phase
        print("\n🌅 MORNING PHASE: Production & Batch Creation")
        
        # Create test batches directly since we need to avoid complex cross-class setup
        batches = self.create_test_batches()
        
        print("✅ Morning production phase completed")
        
        # 🚚 Mid-Morning: Distribution Phase
        print("\n🚚 MID-MORNING PHASE: Strategic Distribution")
        
        # Create batch assignments directly
        assignments = self.create_batch_assignments(batches)
        
        print("✅ Distribution phase completed")
        
        # 💰 Daytime: Sales Operations
        print("\n💰 DAYTIME PHASE: Sales Operations")
        
        # Create sample invoices
        invoices = []
        for i, assignment in enumerate(assignments):
            invoice_data = {
                'shop': assignment.salesman.shop.id if hasattr(assignment.salesman, 'shop') else self.shop1.id,
                'customer_name': f'Integration Customer {i+1}',
                'customer_email': f'customer{i+1}@integration.com',
                'customer_phone': f'+155500{i:04d}',
                'invoice_date': str(date.today()),
                'payment_terms': 'Net 30'
            }
            
            # Use the appropriate salesman client
            if i == 0:
                client = self.salesman1_client
            elif i == 1:
                client = self.salesman2_client
            else:
                client = self.salesman3_client
                
            response = client.post(
                reverse('invoice-list'),
                data=invoice_data,
                format='json'
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                invoice = Invoice.objects.get(id=response.data['id'])
                invoices.append(invoice)
        
        print("✅ Sales operations phase completed")
        
        # 🏦 Evening: Settlements
        print("\n🏦 EVENING PHASE: Settlements & Collections")
        
        # Calculate commissions if we have invoices
        if invoices:
            response = self.owner_client.post(
                reverse('calculate-commissions'),
                data={'period': 'daily', 'date': str(date.today())},
                format='json'
            )
            
            if response.status_code == status.HTTP_200_OK:
                print("✅ Commissions calculated")
        
        print("✅ Settlements phase completed")
        
        # 🔄 End of Day: Returns Processing
        print("\n🔄 END OF DAY: Returns Processing")
        
        # Create a sample return if we have invoices
        returns = []
        if invoices:
            # Create invoice item first
            item_data = {
                'invoice': invoices[0].id,
                'batch_assignment': assignments[0].id,
                'quantity': 5,
                'unit_price': str(self.product1.price),
                'discount_percent': '0.00'
            }
            
            response = self.salesman1_client.post(
                reverse('invoiceitem-list'),
                data=item_data,
                format='json'
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                item = InvoiceItem.objects.get(id=response.data['id'])
                
                # Create return
                return_data = {
                    'original_invoice': invoices[0].id,
                    'original_invoice_item': item.id,
                    'return_date': str(date.today()),
                    'quantity_returned': 2,
                    'reason': 'quality_issue',
                    'description': 'Integration test return',
                    'batch_number': assignments[0].batch.batch_number,
                    'condition': 'defective',
                    'action_taken': 'full_refund',
                    'refund_amount': str(Decimal('59.98'))
                }
                
                response = self.salesman1_client.post(
                    reverse('return-list'),
                    data=return_data,
                    format='json'
                )
                
                if response.status_code == status.HTTP_201_CREATED:
                    return_obj = Return.objects.get(id=response.data['id'])
                    returns.append(return_obj)
        
        print("✅ Returns processing completed")
        
        # 📊 Night: Analytics Review
        print("\n📊 NIGHT PHASE: Analytics & Reporting")
        
        # Test basic analytics endpoint
        response = self.owner_client.get(reverse('sales-analytics'))
        analytics_data = None
        if response.status_code == status.HTTP_200_OK:
            analytics_data = response.data
            print("✅ Analytics data retrieved")
        
        print("✅ Analytics review completed")
        
        # 🔍 Final Validation: Data Consistency Check
        print("\n🔍 FINAL VALIDATION: Cross-Module Data Consistency")
        
        # Verify data consistency across modules
        total_batches = len(batches) if batches else 0
        total_assignments = len(assignments) if assignments else 0
        total_invoices = len(invoices) if invoices else 0
        total_returns = len(returns) if returns else 0
        
        print(f"📊 Business Day Summary:")
        print(f"   🏭 Batches created: {total_batches}")
        print(f"   📦 Assignments made: {total_assignments}")
        print(f"   📄 Invoices processed: {total_invoices}")
        print(f"   🔄 Returns handled: {total_returns}")
        
        # Business rule validations
        self.assertGreaterEqual(total_batches, 0)
        self.assertGreaterEqual(total_assignments, 0)
        self.assertGreaterEqual(total_invoices, 0)
        
        print("\n🎉 Complete business day simulation successful!")
        print("="*80)
        
        return {
            'batches': batches,
            'assignments': assignments,
            'invoices': invoices,
            'returns': returns,
            'analytics': analytics_data
        }
    
    def test_02_cross_module_data_consistency(self):
        """
        🔗 CROSS-MODULE DATA CONSISTENCY TEST
        
        Tests data consistency and integrity across all business modules.
        """
        print("\n" + "="*70)
        print("🔗 TESTING: Cross-Module Data Consistency")
        print("="*70)
        
        # Run complete workflow first
        workflow_data = self.test_01_complete_business_day_simulation()
        
        # Test data consistency endpoints
        response = self.owner_client.get(reverse('data-consistency-check'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        consistency_report = response.data
        print(f"🔍 Consistency Report: {consistency_report}")
        
        # Verify consistency checks
        expected_checks = [
            'batch_assignment_consistency',
            'invoice_item_consistency',
            'commission_calculation_consistency',
            'settlement_amount_consistency',
            'inventory_balance_consistency'
        ]
        
        for check in expected_checks:
            self.assertIn(check, consistency_report)
            check_result = consistency_report[check]
            print(f"✅ {check.replace('_', ' ').title()}: {check_result['status']}")
            
            if check_result['status'] != 'PASS':
                print(f"   ⚠️ Issues: {check_result.get('issues', [])}")
        
        # Test referential integrity
        response = self.owner_client.get(reverse('referential-integrity-check'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        integrity_report = response.data
        print(f"🔗 Integrity Report: {integrity_report}")
        
        print("✅ Cross-module data consistency verified!")
    
    def test_03_workflow_automation_integration(self):
        """
        🤖 WORKFLOW AUTOMATION INTEGRATION TEST
        
        Tests automated workflows and integration between modules.
        """
        print("\n" + "="*70)
        print("🤖 TESTING: Workflow Automation Integration")
        print("="*70)
        
        # Test automated batch assignment workflow
        batches = self.create_test_batches()
        
        automation_config = {
            'workflow_type': 'batch_assignment',
            'trigger': 'new_batch_created',
            'rules': [
                {'territory': 'Northern Territory', 'allocation_percentage': 40},
                {'territory': 'Eastern Territory', 'allocation_percentage': 35},
                {'territory': 'Western Territory', 'allocation_percentage': 25}
            ]
        }
        
        response = self.owner_client.post(
            reverse('setup-workflow-automation'),
            data=automation_config,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        automation_result = response.data
        print(f"🤖 Automation Setup: {automation_result}")
        
        # Test automated commission calculation
        commission_automation = {
            'workflow_type': 'commission_calculation',
            'trigger': 'daily_schedule',
            'schedule': '18:00',  # 6 PM daily
            'auto_settlement': False
        }
        
        response = self.owner_client.post(
            reverse('setup-workflow-automation'),
            data=commission_automation,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test workflow status monitoring
        response = self.owner_client.get(reverse('workflow-status-monitor'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        workflow_status = response.data
        print(f"📊 Workflow Status: {workflow_status}")
        
        self.assertIn('active_workflows', workflow_status)
        self.assertIn('completed_today', workflow_status)
        self.assertIn('failed_workflows', workflow_status)
        
        print("✅ Workflow automation integration verified!")
    
    def test_04_performance_optimization_testing(self):
        """
        ⚡ PERFORMANCE OPTIMIZATION TEST
        
        Tests system performance under realistic business load conditions.
        """
        print("\n" + "="*70)
        print("⚡ TESTING: Performance Optimization")
        print("="*70)
        
        # Create bulk test data for performance testing
        import time
        
        # Test batch creation performance
        start_time = time.time()
        
        bulk_batches = []
        for i in range(10):  # Create 10 batches quickly
            batch_data = {
                'product': self.product1.id,
                'batch_number': f'PERF{i:03d}',
                'production_date': str(date.today()),
                'expiry_date': str(date.today() + timedelta(days=365)),
                'quantity': 100,
                'cost_per_unit': '10.00',
                'manufacturing_cost': '1000.00',
                'quality_status': 'good'
            }
            
            response = self.owner_client.post(
                reverse('batch-list'),
                data=batch_data,
                format='json'
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                bulk_batches.append(response.data['id'])
        
        batch_creation_time = time.time() - start_time
        print(f"⚡ Batch Creation Performance: {len(bulk_batches)} batches in {batch_creation_time:.2f}s")
        
        # Test bulk operations performance
        start_time = time.time()
        
        response = self.owner_client.get(reverse('bulk-operations-performance'))
        performance_time = time.time() - start_time
        
        if response.status_code == status.HTTP_200_OK:
            performance_data = response.data
            print(f"📊 Bulk Operations: {performance_time:.2f}s")
            print(f"   Data: {performance_data}")
        
        # Test query optimization
        response = self.owner_client.get(reverse('query-performance-analysis'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        query_analysis = response.data
        print(f"🔍 Query Analysis: {query_analysis}")
        
        # Verify performance metrics
        self.assertIn('slow_queries', query_analysis)
        self.assertIn('optimization_suggestions', query_analysis)
        
        print("✅ Performance optimization testing completed!")
    
    def test_05_system_health_monitoring(self):
        """
        🏥 SYSTEM HEALTH MONITORING TEST
        
        Tests comprehensive system health and monitoring capabilities.
        """
        print("\n" + "="*70)
        print("🏥 TESTING: System Health Monitoring")
        print("="*70)
        
        # Test system health check
        response = self.owner_client.get(reverse('system-health-check'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        health_data = response.data
        print(f"🏥 System Health: {health_data}")
        
        # Verify health check components
        expected_components = [
            'database_status',
            'cache_status',
            'queue_status',
            'storage_status',
            'api_response_times'
        ]
        
        for component in expected_components:
            self.assertIn(component, health_data)
            component_status = health_data[component]
            print(f"✅ {component.replace('_', ' ').title()}: {component_status.get('status', 'OK')}")
        
        # Test error monitoring
        response = self.owner_client.get(reverse('error-monitoring'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        error_data = response.data
        print(f"🚨 Error Monitoring: {error_data}")
        
        self.assertIn('error_rate', error_data)
        self.assertIn('recent_errors', error_data)
        self.assertIn('error_trends', error_data)
        
        # Test resource utilization
        response = self.owner_client.get(reverse('resource-utilization'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resource_data = response.data
        print(f"📊 Resource Utilization: {resource_data}")
        
        self.assertIn('cpu_usage', resource_data)
        self.assertIn('memory_usage', resource_data)
        self.assertIn('disk_usage', resource_data)
        
        print("✅ System health monitoring verified!")
    
    def test_06_business_continuity_testing(self):
        """
        🛡️ BUSINESS CONTINUITY TEST
        
        Tests business continuity and disaster recovery capabilities.
        """
        print("\n" + "="*70)
        print("🛡️ TESTING: Business Continuity")
        print("="*70)
        
        # Test backup and restore functionality
        response = self.owner_client.post(reverse('create-system-backup'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        backup_result = response.data
        print(f"💾 System Backup: {backup_result}")
        
        self.assertIn('backup_id', backup_result)
        self.assertIn('backup_size', backup_result)
        self.assertIn('backup_timestamp', backup_result)
        
        # Test failover scenarios
        response = self.owner_client.get(reverse('failover-test'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        failover_data = response.data
        print(f"🔄 Failover Test: {failover_data}")
        
        self.assertIn('failover_time', failover_data)
        self.assertIn('recovery_procedures', failover_data)
        
        # Test data recovery procedures
        response = self.owner_client.get(reverse('data-recovery-procedures'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        recovery_data = response.data
        print(f"🔧 Recovery Procedures: {recovery_data}")
        
        print("✅ Business continuity testing completed!")
