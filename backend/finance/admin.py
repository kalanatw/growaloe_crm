from django.contrib import admin
from .models import (
    TransactionCategory, FinancialTransaction, 
    DescriptionSuggestion, ProfitSummary, CommissionRecord
)


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'transaction_type', 'is_active', 'created_at']
    list_filter = ['transaction_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['transaction_type', 'name']


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'transaction_type', 'category', 'transaction_date', 'created_by']
    list_filter = ['category__transaction_type', 'category', 'transaction_date', 'created_at']
    search_fields = ['description', 'reference_number']
    ordering = ['-transaction_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('description', 'amount', 'category', 'transaction_date')
        }),
        ('Additional Info', {
            'fields': ('reference_number', 'notes', 'attachment'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DescriptionSuggestion)
class DescriptionSuggestionAdmin(admin.ModelAdmin):
    list_display = ['description', 'category', 'frequency', 'last_used']
    list_filter = ['category', 'last_used']
    search_fields = ['description']
    ordering = ['-frequency', '-last_used']


@admin.register(ProfitSummary)
class ProfitSummaryAdmin(admin.ModelAdmin):
    list_display = ['start_date', 'end_date', 'period_type', 'realized_profit', 'unrealized_profit', 'spendable_profit']
    list_filter = ['period_type', 'start_date']
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CommissionRecord)
class CommissionRecordAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'salesman', 'commission_amount', 'status', 'payment_date']
    list_filter = ['status', 'payment_date', 'created_at']
    search_fields = ['invoice__invoice_number', 'salesman__user__username', 'salesman__user__first_name', 'salesman__user__last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('invoice', 'salesman', 'commission_rate', 'commission_amount', 'calculation_basis')
        }),
        ('Status', {
            'fields': ('status', 'payment_date', 'payment_reference')
        }),
        ('Additional Info', {
            'fields': ('settlement', 'notes'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
