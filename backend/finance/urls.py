from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.FinancialTransactionViewSet, basename='transactions')
router.register(r'categories', views.TransactionCategoryViewSet, basename='categories')
router.register(r'commissions', views.CommissionRecordViewSet, basename='commissions')

urlpatterns = [
    path('', include(router.urls)),
    
    # Profit calculation endpoints
    path('profits/realized/', views.RealizedProfitView.as_view(), name='realized-profit'),
    path('profits/unrealized/', views.UnrealizedProfitView.as_view(), name='unrealized-profit'),
    path('profits/spendable/', views.SpendableProfitView.as_view(), name='spendable-profit'),
    path('profits/summary/', views.ProfitSummaryView.as_view(), name='profit-summary'),
    
    # Dashboard and reporting
    path('dashboard/', views.FinancialDashboardView.as_view(), name='dashboard'),
    path('reports/daily/', views.DailyReportView.as_view(), name='daily-report'),
    path('reports/weekly/', views.WeeklyReportView.as_view(), name='weekly-report'),
    path('reports/monthly/', views.MonthlyReportView.as_view(), name='monthly-report'),
    path('reports/collection-efficiency/', views.CollectionEfficiencyView.as_view(), name='collection-efficiency'),
    
    # Transaction management
    path('transactions/summary/', views.TransactionSummaryView.as_view(), name='transaction-summary'),
    path('transactions/suggestions/', views.DescriptionSuggestionsView.as_view(), name='description-suggestions'),
    
    # Commission reporting
    path('commissions/summary/', views.CommissionSummaryView.as_view(), name='commission-summary'),
]
