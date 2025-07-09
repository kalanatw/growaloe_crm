from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanySettingsViewSet
from .financial_views import FinancialTransactionViewSet, InvoiceSettlementViewSet, FinancialDashboardView, ProfitAnalysisViewSet

router = DefaultRouter()
router.register(r'settings', CompanySettingsViewSet, basename='company-settings')
router.register(r'financial-transactions', FinancialTransactionViewSet, basename='financial-transactions')
router.register(r'invoice-settlements', InvoiceSettlementViewSet, basename='invoice-settlements')
router.register(r'financial-dashboard', FinancialDashboardView, basename='financial-dashboard')
router.register(r'reports', ProfitAnalysisViewSet, basename='reports')

urlpatterns = router.urls
