from django.contrib import admin
from .models import Category, Product, StockMovement, Batch, BatchTransaction, BatchAssignment, Delivery, DeliveryItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'base_price', 'total_stock', 
                   'owner_stock', 'salesman_stock', 'min_stock_level', 'is_low_stock', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    raw_id_fields = ('created_by',)
    readonly_fields = ('created_at', 'updated_at', 'total_stock', 'owner_stock', 'salesman_stock')
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'



@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'salesman', 'reference_id', 'created_at')
    list_filter = ('movement_type', 'created_at', 'salesman__owner')
    search_fields = ('product__name', 'reference_id', 'notes')
    raw_id_fields = ('product', 'salesman', 'created_by')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'salesman')
