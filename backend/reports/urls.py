from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dashboard-metrics', views.DashboardMetricsViewSet)
router.register(r'sales-reports', views.SalesReportViewSet)
router.register(r'inventory-reports', views.InventoryReportViewSet)
router.register(r'financial-reports', views.FinancialReportViewSet)
router.register(r'analytics', views.ReportsAnalyticsViewSet, basename='reports-analytics')

urlpatterns = [
    # Router URLs - all report endpoints are handled by ViewSets
    path('', include(router.urls)),
]
