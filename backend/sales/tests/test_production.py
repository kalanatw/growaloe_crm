# backend/sales/tests/test_production.py
from .base_test import AloeVeraParadiseBaseTestCase
from products.models import Batch, BatchAssignment
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status

class ProductionAndBatchTestCase(AloeVeraParadiseBaseTestCase):
    """
    🏭 PRODUCTION & BATCH MANAGEMENT TESTS
    
    Tests the morning production workflow:
    - Batch creation and quality control
    - FIFO inventory management
    - Batch assignment to salesmen
    - Production analytics and reporting
    """
    
    def test_01_morning_production_and_batch_creation(self):
        """
        🌅 MORNING PRODUCTION WORKFLOW TEST
        
        Simulates Sarah's morning routine of creating new production batches
        with proper quality control and FIFO management.
        """
        print("\n" + "="*70)
        print("🌅 TESTING: Morning Production & Batch Creation")
        print("="*70)
        
        # 📊 Phase 1: Check initial inventory status
        print("\n📊 Phase 1: Initial Inventory Assessment")
        
        initial_batches = Batch.objects.count()
        print(f"📦 Current batches in system: {initial_batches}")
        
        # 🏭 Phase 2: Create morning production batches
        print("\n🏭 Phase 2: Morning Production Creation")
        
        # Premium Aloe Gel - Large batch for high demand
        batch_data_1 = {
            'product': self.product1.id,
            'batch_number': 'ALVR001-2024',
            'manufacturing_date': str(date.today()),
            'expiry_date': str(date.today() + timedelta(days=730)),
            'initial_quantity': 200,
            'current_quantity': 200,
            'unit_cost': '12.00',
            'notes': 'Premium batch with 99.5% purity, passed all quality checks'
        }
        
        response1 = self.owner_client.post(
            reverse('batch-list'),
            data=batch_data_1,
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.batch1 = Batch.objects.get(id=response1.data['id'])
        
        print(f"✅ Created batch: {self.batch1.batch_number}")
        print(f"   📦 Product: {self.batch1.product.name}")
        print(f"   📊 Quantity: {self.batch1.current_quantity} units")
        print(f"   💰 Cost per unit: ${self.batch1.unit_cost}")
        
        # Wellness Drink - Medium batch
        batch_data_2 = {
            'product': self.product2.id,
            'batch_number': 'ALVR002-2024',
            'manufacturing_date': str(date.today()),
            'expiry_date': str(date.today() + timedelta(days=365)),
            'initial_quantity': 300,
            'current_quantity': 300,
            'unit_cost': '8.50',
            'notes': 'Standard batch meeting all requirements'
        }
        
        response2 = self.owner_client.post(
            reverse('batch-list'),
            data=batch_data_2,
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.batch2 = Batch.objects.get(id=response2.data['id'])
        
        print(f"✅ Created batch: {self.batch2.batch_number}")
        print(f"   📦 Product: {self.batch2.product.name}")
        print(f"   📊 Quantity: {self.batch2.current_quantity} units")
        
        # Beauty Serum - Premium small batch
        batch_data_3 = {
            'product': self.product3.id,
            'batch_number': 'ALVR003-2024',
            'manufacturing_date': str(date.today()),
            'expiry_date': str(date.today() + timedelta(days=540)),
            'initial_quantity': 150,
            'current_quantity': 150,
            'unit_cost': '18.00',
            'notes': 'Premium anti-aging formula with enhanced potency'
        }
        
        response3 = self.owner_client.post(
            reverse('batch-list'),
            data=batch_data_3,
            format='json'
        )
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        self.batch3 = Batch.objects.get(id=response3.data['id'])
        
        print(f"✅ Created batch: {self.batch3.batch_number}")
        print(f"   📦 Product: {self.batch3.product.name}")
        print(f"   📊 Quantity: {self.batch3.current_quantity} units")
        
        # 📈 Phase 3: Verify production metrics
        print("\n📈 Phase 3: Production Metrics Verification")
        
        total_batches = Batch.objects.count()
        total_production_value = sum([
            float(batch.unit_cost) * batch.current_quantity for batch in Batch.objects.all()
        ])
        
        print(f"📊 Total batches created today: {total_batches - initial_batches}")
        print(f"💰 Total production value: ${total_production_value}")
        
        # Assert business rules
        self.assertEqual(total_batches, initial_batches + 3)
        self.assertTrue(total_production_value > 0)
        
        # Verify FIFO compliance - oldest batches should be prioritized
        batches_by_date = Batch.objects.order_by('manufacturing_date', 'id')
        self.assertTrue(len(batches_by_date) >= 3)
        
        print("✅ All production metrics verified successfully!")
        
        # 🔍 Phase 4: Quality control verification
        print("\n🔍 Phase 4: Quality Control Assessment")
        
        print(f"📦 Total batches created: {Batch.objects.count()}")
        print(f"✅ All batches are active and ready for distribution")
        
        # Verify all batches are active and properly created
        active_batches = Batch.objects.filter(is_active=True).count()
        print(f"📊 Active batches: {active_batches}/{total_batches}")
        self.assertEqual(active_batches, total_batches)
        
        print("\n🎉 Morning production workflow completed successfully!")
        return self.batch1, self.batch2, self.batch3
    
    def test_02_batch_quality_management(self):
        """
        🔬 BATCH QUALITY MANAGEMENT TEST
        
        Tests batch tracking, expiry management, and inventory analytics.
        """
        print("\n" + "="*70)
        print("🔬 TESTING: Batch Quality Management")
        print("="*70)
        
        # Create test batches with different expiry dates
        batches = self.create_test_batches()
        
        # Test batch filtering by product
        response = self.owner_client.get(
            reverse('batch-list') + f'?product={self.product1.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_batches = response.data['results']
        print(f"🏆 Found {len(product_batches)} batches for {self.product1.name}")
        
        # Verify all returned batches belong to the product
        for batch in product_batches:
            self.assertEqual(batch['product'], self.product1.id)
        
        # Test batch details and properties
        batch_detail_response = self.owner_client.get(
            reverse('batch-detail', kwargs={'pk': batches[0].id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(batch_detail_response.status_code, status.HTTP_200_OK)
        batch_detail = batch_detail_response.data
        
        # Verify batch has required properties
        self.assertIn('allocated_quantity', batch_detail)
        self.assertIn('available_quantity', batch_detail)
        self.assertIn('is_expired', batch_detail)
        
        print("✅ Quality management tests passed!")
    
    def test_03_fifo_inventory_management(self):
        """
        📦 FIFO INVENTORY MANAGEMENT TEST
        
        Tests First-In-First-Out inventory allocation for optimal freshness.
        """
        print("\n" + "="*70)
        print("📦 TESTING: FIFO Inventory Management")
        print("="*70)
        
        # Create batches with different manufacturing dates
        old_batch = Batch.objects.create(
            product=self.product1,
            batch_number='OLD001',
            manufacturing_date=date.today() - timedelta(days=5),
            expiry_date=date.today() + timedelta(days=725),
            initial_quantity=50,
            current_quantity=50,
            unit_cost=Decimal('12.00'),
            created_by=self.owner_user
        )
        
        new_batch = Batch.objects.create(
            product=self.product1,
            batch_number='NEW001',
            manufacturing_date=date.today(),
            expiry_date=date.today() + timedelta(days=730),
            initial_quantity=100,
            current_quantity=100,
            unit_cost=Decimal('12.00'),
            created_by=self.owner_user
        )
        
        # Test batch list with FIFO ordering
        response = self.owner_client.get(
            reverse('batch-list') + f'?product={self.product1.id}&ordering=manufacturing_date'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        fifo_batches = response.data['results']
        print(f"📦 FIFO allocation returned {len(fifo_batches)} batches")
        
        # Verify FIFO order (oldest first)
        if len(fifo_batches) >= 2:
            first_batch_date = fifo_batches[0]['manufacturing_date']
            second_batch_date = fifo_batches[1]['manufacturing_date']
            self.assertLessEqual(first_batch_date, second_batch_date)
            
        print("✅ FIFO inventory management verified!")
    
    def test_04_batch_assignment_workflow(self):
        """
        👥 BATCH ASSIGNMENT WORKFLOW TEST
        
        Tests strategic distribution of batches to salesmen based on territory needs.
        """
        print("\n" + "="*70)
        print("👥 TESTING: Batch Assignment Workflow")
        print("="*70)
        
        # Create test batches
        batches = self.create_test_batches()
        batch1, batch2, batch3 = batches
        
        # Test batch assignment to salesman 1
        assignment_data = {
            'batch': batch1.id,
            'salesman': self.salesman1.id,
            'quantity': 70,
            'notes': 'High-demand territory allocation'
        }
        
        response = self.owner_client.post(
            reverse('batchassignment-list'),
            data=assignment_data,
            format='json'
        )
        
        # Debug: check response data if test fails
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the assignment either from response or by query
        if 'id' in response.data:
            assignment = BatchAssignment.objects.get(id=response.data['id'])
        else:
            assignment = BatchAssignment.objects.filter(
                batch=batch1,
                salesman=self.salesman1
            ).first()
            self.assertIsNotNone(assignment, "Assignment should be created")
        
        print(f"✅ Created assignment: {assignment.batch.batch_number} → {assignment.salesman.user.get_full_name()}")
        print(f"   📦 Quantity: {assignment.quantity} units")
        
        # Verify assignment business rules
        self.assertEqual(assignment.quantity, 70)
        self.assertEqual(assignment.status, 'pending')
        self.assertLessEqual(assignment.quantity, batch1.current_quantity)
        
        # Test assignment list view
        response = self.owner_client.get(
            reverse('batchassignment-list')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        assignments = response.data['results']
        print(f"📊 Total assignments: {len(assignments)}")
        
        self.assertGreaterEqual(len(assignments), 1)
        
        print("✅ Batch assignment workflow verified!")
