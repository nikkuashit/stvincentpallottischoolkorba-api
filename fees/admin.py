"""
Fee Management Admin Configuration
"""

from django.contrib import admin
from .models import (
    FeeCategory,
    FeeStructure,
    FeeDiscount,
    StudentFee,
    FeePayment,
    FeeReminder,
)


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    """Admin interface for FeeCategory model."""

    list_display = ['name', 'code', 'is_mandatory', 'display_order', 'is_active']
    list_filter = ['is_mandatory', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['display_order', 'name']
    list_editable = ['display_order', 'is_active']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    """Admin interface for FeeStructure model."""

    list_display = [
        'name', 'academic_year', 'grade', 'category',
        'amount', 'frequency', 'is_active'
    ]
    list_filter = ['academic_year', 'grade', 'category', 'frequency', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-academic_year__start_date', 'category__display_order']
    raw_id_fields = ['academic_year', 'grade', 'category']
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'academic_year', 'grade', 'category')
        }),
        ('Fee Details', {
            'fields': ('amount', 'frequency', 'due_day_of_month')
        }),
        ('Late Fee Configuration', {
            'fields': ('late_fee_type', 'late_fee_value', 'grace_period_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    """Admin interface for FeeDiscount model."""

    list_display = [
        'name', 'discount_type', 'value', 'criteria',
        'valid_from', 'valid_until', 'is_active'
    ]
    list_filter = ['discount_type', 'criteria', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['applicable_categories']
    ordering = ['name']
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'criteria')
        }),
        ('Discount Configuration', {
            'fields': ('discount_type', 'value', 'max_discount_amount')
        }),
        ('Applicability', {
            'fields': ('applicable_categories', 'academic_year')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_combinable', 'is_active')
        }),
    )


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    """Admin interface for StudentFee model."""

    list_display = [
        'student', 'fee_structure', 'base_amount', 'discount_amount',
        'late_fee_amount', 'final_amount', 'paid_amount', 'status', 'due_date'
    ]
    list_filter = ['status', 'fee_structure__academic_year', 'fee_structure__category']
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']
    raw_id_fields = ['student', 'fee_structure']
    filter_horizontal = ['discounts_applied']
    ordering = ['-due_date']
    date_hierarchy = 'due_date'
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Student & Fee Information', {
            'fields': ('student', 'fee_structure', 'period_start', 'period_end', 'due_date')
        }),
        ('Amount Details', {
            'fields': (
                'base_amount', 'discounts_applied', 'discount_amount',
                'late_fee_amount', 'final_amount', 'paid_amount'
            )
        }),
        ('Status', {
            'fields': ('status', 'remarks', 'waiver_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    """Admin interface for FeePayment model."""

    list_display = [
        'receipt_number', 'student_fee', 'amount', 'payment_method',
        'payment_date', 'status', 'created_by'
    ]
    list_filter = ['payment_method', 'status', 'payment_date']
    search_fields = [
        'receipt_number', 'transaction_id',
        'student_fee__student__first_name', 'student_fee__student__last_name'
    ]
    raw_id_fields = ['student_fee', 'created_by', 'verified_by']
    ordering = ['-payment_date', '-created_at']
    date_hierarchy = 'payment_date'
    readonly_fields = ['receipt_number', 'created_at', 'updated_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('student_fee', 'amount', 'payment_method', 'payment_date')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'cheque_number', 'cheque_date', 'bank_name')
        }),
        ('Receipt & Status', {
            'fields': ('receipt_number', 'status', 'created_by')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'refund_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FeeReminder)
class FeeReminderAdmin(admin.ModelAdmin):
    """Admin interface for FeeReminder model."""

    list_display = [
        'student_fee', 'reminder_type', 'channel', 'sent_at', 'sent_to',
        'is_delivered'
    ]
    list_filter = ['reminder_type', 'channel', 'is_delivered', 'sent_at']
    search_fields = [
        'student_fee__student__first_name', 'student_fee__student__last_name',
        'sent_to'
    ]
    raw_id_fields = ['student_fee']
    ordering = ['-sent_at']
    date_hierarchy = 'sent_at'
    readonly_fields = ['sent_at']
    fieldsets = (
        ('Reminder Information', {
            'fields': ('student_fee', 'reminder_type', 'channel')
        }),
        ('Delivery', {
            'fields': ('sent_to', 'sent_at', 'is_delivered', 'delivered_at')
        }),
        ('Content', {
            'fields': ('message_content', 'error_message')
        }),
    )
