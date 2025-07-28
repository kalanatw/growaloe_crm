from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'owners', views.OwnerViewSet)
router.register(r'salesmen', views.SalesmanViewSet)
router.register(r'shops', views.ShopViewSet)
router.register(r'margin-policies', views.MarginPolicyViewSet)

urlpatterns = [
    # Authentication endpoints
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Cash flow management endpoints
    path('salesmen/<int:salesman_id>/cash-summary/', views.salesman_cash_summary, name='salesman_cash_summary'),
    path('salesmen/<int:salesman_id>/cash-transactions/', views.cash_transaction_history, name='cash_transaction_history'),
    path('salesmen/<int:salesman_id>/settlement-cash-flow/', views.settlement_cash_flow, name='settlement_cash_flow'),
    path('salesmen/<int:salesman_id>/advance-payment/', views.record_advance_payment, name='record_advance_payment'),
    path('cash-collection/', views.record_cash_collection, name='record_cash_collection'),
    
    # Router URLs
    path('', include(router.urls)),
]
