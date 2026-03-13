"""
Workflows Admin Configuration

Provides Django admin interface for managing:
- Request types and their configurations
- Approval workflows and steps
- Clearance types for TC requests
- Requests and their approvals
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    RequestType,
    ApprovalWorkflow,
    ApprovalStep,
    ClearanceType,
    Request,
    RequestApproval,
    RequestClearance,
    RequestAttachment,
    RequestHistory,
)


# ==============================================================================
# INLINE ADMINS
# ==============================================================================

class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 1
    ordering = ['step_order']
    fields = ['step_order', 'name', 'approver_type', 'approver_role', 'is_optional', 'can_reject', 'is_active']


class RequestApprovalInline(admin.TabularInline):
    model = RequestApproval
    extra = 0
    readonly_fields = ['approval_step', 'status', 'approved_by', 'actioned_at', 'comments']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class RequestClearanceInline(admin.TabularInline):
    model = RequestClearance
    extra = 0
    readonly_fields = ['clearance_type', 'status', 'cleared_by', 'actioned_at', 'verification_notes', 'pending_dues']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class RequestAttachmentInline(admin.TabularInline):
    model = RequestAttachment
    extra = 0
    readonly_fields = ['file_name', 'file_type', 'file_size', 'uploaded_by', 'created_at']
    fields = ['file', 'file_name', 'file_type', 'file_size', 'uploaded_by', 'description', 'created_at']


class RequestHistoryInline(admin.TabularInline):
    model = RequestHistory
    extra = 0
    readonly_fields = ['action', 'action_by', 'previous_status', 'new_status', 'comments', 'created_at']
    can_delete = False
    ordering = ['-created_at']

    def has_add_permission(self, request, obj=None):
        return False


# ==============================================================================
# MODEL ADMINS
# ==============================================================================

@admin.register(RequestType)
class RequestTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'requires_clearance', 'requires_payment', 'approval_workflow', 'is_active', 'display_order']
    list_filter = ['category', 'requires_clearance', 'requires_payment', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        ('Configuration', {
            'fields': ('requires_clearance', 'requires_payment', 'payment_amount', 'approval_workflow')
        }),
        ('Form Schema', {
            'fields': ('form_schema', 'allowed_roles'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'display_order')
        }),
    )


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_sequential', 'step_count', 'is_active']
    list_filter = ['is_sequential', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ApprovalStepInline]

    def step_count(self, obj):
        return obj.steps.count()
    step_count.short_description = 'Steps'


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'step_order', 'name', 'approver_type', 'approver_role', 'is_optional', 'is_active']
    list_filter = ['workflow', 'approver_type', 'is_optional', 'is_active']
    search_fields = ['name', 'workflow__name']
    ordering = ['workflow', 'step_order']


@admin.register(ClearanceType)
class ClearanceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'department', 'clearance_role', 'clearance_order', 'is_active']
    list_filter = ['department', 'clearance_role', 'is_active']
    search_fields = ['name', 'slug', 'department']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['clearance_order']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'department')
        }),
        ('Clearance Configuration', {
            'fields': ('clearance_role', 'clearance_order', 'check_description')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'title', 'request_type', 'submitted_by', 'status', 'priority', 'is_bypassed', 'created_at']
    list_filter = ['status', 'priority', 'request_type', 'is_bypassed', 'payment_status']
    search_fields = ['request_number', 'title', 'submitted_by__username', 'description']
    readonly_fields = ['request_number', 'created_at', 'updated_at', 'submitted_at', 'completed_at', 'bypassed_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    inlines = [RequestApprovalInline, RequestClearanceInline, RequestAttachmentInline, RequestHistoryInline]

    fieldsets = (
        ('Request Information', {
            'fields': ('request_number', 'request_type', 'title', 'description')
        }),
        ('Requester', {
            'fields': ('submitted_by', 'on_behalf_of_student')
        }),
        ('Status', {
            'fields': ('status', 'priority', 'current_step')
        }),
        ('Bypass Information', {
            'fields': ('is_bypassed', 'bypassed_by', 'bypassed_at', 'bypass_reason'),
            'classes': ('collapse',)
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_amount', 'payment_transaction_id'),
            'classes': ('collapse',)
        }),
        ('Form Data', {
            'fields': ('form_data',),
            'classes': ('collapse',)
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'submitted': 'blue',
            'pending_approval': 'orange',
            'pending_clearance': 'purple',
            'approved': 'green',
            'rejected': 'red',
            'cancelled': 'gray',
            'completed': 'green',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(RequestApproval)
class RequestApprovalAdmin(admin.ModelAdmin):
    list_display = ['request', 'approval_step', 'status', 'approved_by', 'actioned_at']
    list_filter = ['status', 'approval_step__workflow']
    search_fields = ['request__request_number', 'approved_by__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(RequestClearance)
class RequestClearanceAdmin(admin.ModelAdmin):
    list_display = ['request', 'clearance_type', 'status', 'cleared_by', 'pending_dues', 'actioned_at']
    list_filter = ['status', 'clearance_type']
    search_fields = ['request__request_number', 'cleared_by__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'request', 'file_type', 'file_size_display', 'uploaded_by', 'created_at']
    list_filter = ['file_type']
    search_fields = ['file_name', 'request__request_number']
    readonly_fields = ['created_at']

    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'Size'


@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ['request', 'action', 'action_by', 'previous_status', 'new_status', 'created_at']
    list_filter = ['action']
    search_fields = ['request__request_number', 'action_by__username', 'comments']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
