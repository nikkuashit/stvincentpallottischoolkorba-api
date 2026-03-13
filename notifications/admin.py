"""
Notifications Admin Configuration

Provides Django admin interface for managing:
- Notification templates
- User notification preferences
- Notifications and their delivery status
- Notification batches for bulk sends
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    NotificationTemplate,
    NotificationPreference,
    Notification,
    NotificationBatch,
)


# ==============================================================================
# MODEL ADMINS
# ==============================================================================

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'channel', 'is_active']
    list_filter = ['event_type', 'channel', 'is_active']
    search_fields = ['name', 'slug', 'subject', 'body']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['event_type', 'channel']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'event_type', 'channel')
        }),
        ('Content', {
            'fields': ('subject', 'body', 'sms_body')
        }),
        ('Metadata', {
            'fields': ('description', 'is_active')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled', 'email_frequency']
    list_filter = ['in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled', 'email_frequency']
    search_fields = ['user__username', 'user__email', 'notification_email']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channel Preferences', {
            'fields': ('in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled')
        }),
        ('Contact Details', {
            'fields': ('notification_email', 'notification_phone')
        }),
        ('Frequency', {
            'fields': ('email_frequency',)
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'),
            'classes': ('collapse',)
        }),
        ('Event-Specific Preferences', {
            'fields': ('event_preferences',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'channel', 'event_type', 'status_badge', 'priority', 'sent_at', 'read_at']
    list_filter = ['status', 'channel', 'event_type', 'priority']
    search_fields = ['title', 'body', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'delivered_at', 'read_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Recipient', {
            'fields': ('user',)
        }),
        ('Content', {
            'fields': ('title', 'body', 'channel')
        }),
        ('Event Information', {
            'fields': ('event_type', 'template', 'related_model', 'related_object_id')
        }),
        ('Status', {
            'fields': ('status', 'priority')
        }),
        ('Delivery Tracking', {
            'fields': ('sent_at', 'delivered_at', 'read_at', 'delivery_response', 'retry_count', 'last_error'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('scheduled_for',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'sent': '#17a2b8',
            'delivered': '#28a745',
            'read': '#007bff',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['mark_as_read', 'retry_failed']

    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(read_at__isnull=True).update(
            status='read',
            read_at=timezone.now()
        )
        self.message_user(request, f'{count} notifications marked as read.')

    @admin.action(description='Retry failed notifications')
    def retry_failed(self, request, queryset):
        count = queryset.filter(status='failed').update(
            status='pending',
            retry_count=0,
            last_error=''
        )
        self.message_user(request, f'{count} notifications queued for retry.')


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel', 'status', 'total_recipients', 'sent_count', 'delivered_count', 'failed_count', 'scheduled_for', 'created_by']
    list_filter = ['status', 'channel']
    search_fields = ['name', 'title', 'body']
    readonly_fields = ['total_recipients', 'sent_count', 'delivered_count', 'failed_count', 'started_at', 'completed_at', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Content', {
            'fields': ('title', 'body', 'channel')
        }),
        ('Target Audience', {
            'fields': ('target_criteria',)
        }),
        ('Status & Scheduling', {
            'fields': ('status', 'scheduled_for')
        }),
        ('Statistics', {
            'fields': ('total_recipients', 'sent_count', 'delivered_count', 'failed_count'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('started_at', 'completed_at', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['process_batch']

    @admin.action(description='Process selected batches')
    def process_batch(self, request, queryset):
        count = queryset.filter(status__in=['draft', 'scheduled']).update(status='processing')
        self.message_user(request, f'{count} batches queued for processing.')
