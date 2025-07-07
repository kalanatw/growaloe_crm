from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import salesman_views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'salesman-stock', views.SalesmanStockViewSet, basename='salesmanstock')
router.register(r'stock-movements', views.StockMovementViewSet)
router.register(r'deliveries', views.DeliveryViewSet)
router.register(r'delivery-items', views.DeliveryItemViewSet)
router.register(r'batches', views.BatchViewSet)
router.register(r'batch-assignments', views.BatchAssignmentViewSet, basename='batchassignment')

# New salesman-centric endpoints
router.register(r'salesman-deliveries', salesman_views.SalesmanDeliveryViewSet, basename='salesmandeliveries')
router.register(r'delivery-settlements', salesman_views.DeliverySettlementViewSet, basename='deliverysettlements')

urlpatterns = [
    # Router URLs - all product endpoints are handled by ViewSets
    path('', include(router.urls)),
    
    # Main delivery management endpoints (salesman-centric)
    path('deliveries/by-salesman/', salesman_views.DeliveryBySalesmanView.as_view(), name='deliveries-by-salesman'),
    path('deliveries/salesman/<int:salesman_id>/details/', salesman_views.SalesmanDeliveryDetailView.as_view(), name='salesman-delivery-details'),
    path('deliveries/settle/<int:salesman_id>/', salesman_views.SettleSalesmanDeliveryView.as_view(), name='settle-salesman-delivery'),
    path('deliveries/update-sold/', salesman_views.UpdateSoldQuantitiesView.as_view(), name='update-sold-quantities'),
]
