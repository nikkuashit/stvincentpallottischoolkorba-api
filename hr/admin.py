"""
HR Admin Configuration

Provides Django admin interfaces for HR management:
- Departments and Designations
- Employee Profiles with reporting structure
- Leave Types, Policies, and Balances
- Leave Requests with approval workflow
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Department,
    Designation,
    EmployeeProfile,
    LeaveType,
    LeavePolicy,
    LeaveBalance,
    LeaveRequest,
    LeaveApproval,
    LeaveBalanceAuditLog,
    Holiday,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'department_type', 'employee_count', 'is_active']
    list_filter = ['department_type', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['name']

    def employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()
    employee_count.short_description = 'Active Employees'


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'level', 'can_approve_leave', 'can_manage_department', 'is_active']
    list_filter = ['category', 'level', 'can_approve_leave', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['-level', 'name']


class SubordinatesInline(admin.TabularInline):
    model = EmployeeProfile
    fk_name = 'reports_to'
    extra = 0
    fields = ['user', 'employee_code', 'department', 'designation']
    readonly_fields = ['user', 'employee_code', 'department', 'designation']
    can_delete = False
    verbose_name = 'Subordinate'
    verbose_name_plural = 'Direct Subordinates'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = [
        'employee_code', 'full_name', 'department', 'designation',
        'is_department_head', 'reports_to_display', 'employment_status', 'joining_date'
    ]
    list_filter = ['department', 'designation', 'employment_status', 'employment_type', 'is_department_head']
    search_fields = ['employee_code', 'user__first_name', 'user__last_name', 'user__email']
    ordering = ['user__first_name', 'user__last_name']
    raw_id_fields = ['user', 'reports_to']
    inlines = [SubordinatesInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_code')
        }),
        ('Department & Role', {
            'fields': ('department', 'designation', 'is_department_head', 'reports_to')
        }),
        ('Employment Details', {
            'fields': ('joining_date', 'confirmation_date', 'employment_status', 'employment_type', 'work_days_per_week')
        }),
        ('Exit Details', {
            'fields': ('resignation_date', 'last_working_date', 'exit_reason'),
            'classes': ('collapse',)
        }),
    )

    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Name'
    full_name.admin_order_field = 'user__first_name'

    def reports_to_display(self, obj):
        if obj.reports_to:
            return obj.reports_to.full_name
        return '-'
    reports_to_display.short_description = 'Reports To'


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'is_paid', 'requires_document',
        'min_days_notice', 'max_consecutive_days', 'color_display', 'is_active'
    ]
    list_filter = ['is_paid', 'requires_document', 'applicable_gender', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; color: white; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'leave_type', 'annual_quota', 'proration_method',
        'carryforward_type', 'effective_from', 'is_active'
    ]
    list_filter = ['leave_type', 'proration_method', 'carryforward_type', 'accrual_type', 'is_active']
    search_fields = ['name', 'leave_type__name']
    filter_horizontal = ['applicable_designations']
    ordering = ['leave_type__name', '-effective_from']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'leave_type', 'annual_quota')
        }),
        ('Applicability', {
            'fields': ('applicable_to_all', 'applicable_designations')
        }),
        ('Proration & Accrual', {
            'fields': ('proration_method', 'accrual_type')
        }),
        ('Carryforward Rules', {
            'fields': ('carryforward_type', 'max_carryforward_days', 'carryforward_expiry_months')
        }),
        ('Encashment Rules', {
            'fields': ('allow_encashment', 'min_balance_for_encashment', 'max_encashment_days'),
            'classes': ('collapse',)
        }),
        ('Validity', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
    )


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'leave_type', 'year', 'opening_balance',
        'annual_quota', 'used', 'pending', 'available_balance'
    ]
    list_filter = ['year', 'leave_type']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_code']
    ordering = ['-year', 'employee__user__first_name']
    raw_id_fields = ['employee']

    def available_balance(self, obj):
        balance = obj.available_balance
        color = 'green' if balance > 0 else 'red' if balance < 0 else 'gray'
        return format_html('<span style="color: {};">{}</span>', color, balance)
    available_balance.short_description = 'Available'


class LeaveApprovalInline(admin.TabularInline):
    model = LeaveApproval
    extra = 0
    fields = ['sequence', 'approver', 'status', 'comments', 'acted_at']
    readonly_fields = ['sequence', 'approver', 'acted_at']
    can_delete = False


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'employee', 'leave_type', 'start_date', 'end_date',
        'total_days', 'status_display', 'current_approver', 'submitted_at'
    ]
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_code']
    ordering = ['-created_at']
    raw_id_fields = ['employee', 'current_approver', 'final_approver']
    inlines = [LeaveApprovalInline]
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Employee', {
            'fields': ('employee',)
        }),
        ('Leave Details', {
            'fields': ('leave_type', 'start_date', 'end_date', 'start_duration_type', 'end_duration_type', 'reason')
        }),
        ('Additional Info', {
            'fields': ('contact_during_leave', 'document')
        }),
        ('Status', {
            'fields': ('status', 'current_approver', 'final_approver', 'submitted_at')
        }),
    )

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'

    def status_display(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'cancelled': 'gray',
            'partially_approved': 'blue',
        }
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; color: white; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(LeaveApproval)
class LeaveApprovalAdmin(admin.ModelAdmin):
    list_display = ['leave_request', 'approver', 'sequence', 'status', 'acted_at']
    list_filter = ['status']
    search_fields = ['leave_request__employee__user__first_name', 'approver__user__first_name']
    ordering = ['leave_request', 'sequence']


@admin.register(LeaveBalanceAuditLog)
class LeaveBalanceAuditLogAdmin(admin.ModelAdmin):
    list_display = ['leave_balance', 'action', 'days_change', 'balance_before', 'balance_after', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['leave_balance__employee__user__first_name', 'reference']
    ordering = ['-created_at']
    readonly_fields = ['leave_balance', 'action', 'days_change', 'balance_before', 'balance_after', 'reference', 'notes', 'performed_by', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'holiday_type', 'is_optional', 'year']
    list_filter = ['year', 'holiday_type', 'is_optional']
    search_fields = ['name']
    ordering = ['date']
    filter_horizontal = ['applicable_departments']
    date_hierarchy = 'date'
