from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'invoice-items', views.InvoiceItemViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'returns', views.ReturnViewSet)
router.register(r'analytics', views.SalesAnalyticsViewSet, basename='sales-analytics')

urlpatterns = [
    # Router URLs - all sales endpoints are handled by ViewSets
    path('', include(router.urls)),
]
