# backend/sales/tests.py
"""
🏪 ALOE VERA PARADISE - MAIN TEST SUITE ENTRY POINT
====================================================

This file serves as the main entry point for the Aloe Vera Paradise test suite.
For better maintainability and organization, the actual tests have been 
modularized into the `tests/` directory.

The modular test suite includes:
- Production and batch management tests
- Distribution and territory management tests  
- Sales operations and transaction tests
- Settlements and financial management tests
- Returns and quality management tests
- Business analytics and reporting tests
- End-to-end integration and workflow tests

To run tests:
-----------
# Run all modular tests
python manage.py test sales.tests

# Run specific modules
python manage.py test sales.tests.test_production
python manage.py test sales.tests.test_sales
python manage.py test sales.tests.test_integration

# Run legacy comprehensive test (if needed)
python manage.py test sales.tests_backup_large

For detailed documentation, see sales/tests/__init__.py
"""

# Import all test classes from the modular suite for backward compatibility
from .tests import *

# Create __all__ list if not imported
if '__all__' not in globals():
    __all__ = []

# Legacy import for the original comprehensive test case
try:
    from .tests_backup_large import AloeVeraParadiseComprehensiveTestCase
    __all__.append('AloeVeraParadiseComprehensiveTestCase')
except ImportError:
    # Backup file not available
    pass

# Main test discovery will automatically find all TestCase classes
# in the imported modules