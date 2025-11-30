"""Django Admin for Tenants App"""

from django.contrib import admin
from .models import SubscriptionPlan, Organization, Subscription, School, Invoice, AuditLog


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'billing_period', 'max_students', 'max_staff', 'is_active', 'display_order']
    list_filter = ['billing_period', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'price']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'email', 'city', 'country', 'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_verified', 'country', 'state']
    search_fields = ['name', 'slug', 'email', 'domain']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'auto_renew', 'plan']
    search_fields = ['organization__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'city', 'state', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'state', 'country', 'organization']
    search_fields = ['name', 'short_name', 'email', 'city']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'subscription', 'total_amount', 'status', 'invoice_date', 'due_date', 'paid_date']
    list_filter = ['status', 'payment_method']
    search_fields = ['invoice_number', 'subscription__organization__name', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'invoice_date'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'user', 'organization', 'ip_address', 'created_at']
    list_filter = ['action', 'model_name', 'organization']
    search_fields = ['action', 'model_name', 'user__user__username', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
