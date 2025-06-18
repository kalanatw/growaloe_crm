from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'salesman-stock', views.SalesmanStockViewSet)
router.register(r'stock-movements', views.StockMovementViewSet)
router.register(r'deliveries', views.DeliveryViewSet)
router.register(r'delivery-items', views.DeliveryItemViewSet)

urlpatterns = [
    # Router URLs - all product endpoints are handled by ViewSets
    path('', include(router.urls)),
]
