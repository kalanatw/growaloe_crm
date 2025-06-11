from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Owner, Salesman, Shop, MarginPolicy


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address')
        }),
    )


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'tax_id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('business_name', 'user__username', 'tax_id')
    raw_id_fields = ('user',)


@admin.register(Salesman)
class SalesmanAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'user', 'profit_margin', 'is_active', 'created_at')
    list_filter = ('is_active', 'owner', 'created_at')
    search_fields = ('name', 'user__username', 'owner__business_name')
    raw_id_fields = ('user', 'owner')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'salesman', 'contact_person', 'phone', 'shop_margin', 'is_active')
    list_filter = ('is_active', 'salesman__owner', 'created_at')
    search_fields = ('name', 'contact_person', 'phone', 'salesman__name')
    raw_id_fields = ('user', 'salesman')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('salesman', 'salesman__owner')


@admin.register(MarginPolicy)
class MarginPolicyAdmin(admin.ModelAdmin):
    list_display = ('owner', 'default_salesman_margin', 'default_shop_margin', 
                   'allow_salesman_override', 'allow_shop_override')
    list_filter = ('allow_salesman_override', 'allow_shop_override')
    raw_id_fields = ('owner',)
