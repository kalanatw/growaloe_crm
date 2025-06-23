# Test module for sales app - Modular Test Suite

"""
🏪 ALOE VERA PARADISE - MODULAR TEST SUITE
====================================================

This modular test suite provides comprehensive coverage for all business operations
of Aloe Vera Paradise's batch-based POS system. Each module focuses on specific
business areas while maintaining integration capabilities.

Test Modules:
- base_test.py: Common setup and utilities for all tests
- test_production.py: Production and batch management tests
- test_distribution.py: Distribution and territory management tests  
- test_sales.py: Sales operations and transaction tests
- test_settlements.py: Settlements and financial management tests
- test_returns.py: Returns and quality management tests
- test_analytics.py: Business analytics and reporting tests
- test_integration.py: End-to-end integration and workflow tests

Usage:
------
# Run all tests
python manage.py test sales.tests

# Run specific module
python manage.py test sales.tests.test_production
python manage.py test sales.tests.test_sales
python manage.py test sales.tests.test_integration

# Run specific test class
python manage.py test sales.tests.test_production.ProductionAndBatchTestCase

# Run specific test method
python manage.py test sales.tests.test_sales.SalesOperationsTestCase.test_01_full_day_sales_operations
"""

# Import all test classes for discovery
from .base_test import AloeVeraParadiseBaseTestCase
from .test_production import ProductionAndBatchTestCase
from .test_distribution import DistributionTestCase
from .test_sales import SalesOperationsTestCase
from .test_settlements import SettlementsTestCase
from .test_returns import ReturnsTestCase
from .test_analytics import AnalyticsTestCase
from .test_integration import BusinessWorkflowIntegrationTestCase

__all__ = [
    'AloeVeraParadiseBaseTestCase',
    'ProductionAndBatchTestCase',
    'DistributionTestCase', 
    'SalesOperationsTestCase',
    'SettlementsTestCase',
    'ReturnsTestCase',
    'AnalyticsTestCase',
    'BusinessWorkflowIntegrationTestCase',
]
