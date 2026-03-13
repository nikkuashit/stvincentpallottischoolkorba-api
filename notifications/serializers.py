"""
Notifications Serializers

Serializers for notification templates, preferences, and notifications.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    NotificationTemplate,
    NotificationPreference,
    Notification,
    NotificationBatch,
)


# ==============================================================================
# NOTIFICATION TEMPLATE SERIALIZERS
# ==============================================================================

class NotificationTemplateSerializer(serializers.ModelSerializer):
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    event_type_display = serializers.SerializerMethodField()

    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'slug', 'event_type', 'event_type_display',
            'channel', 'channel_display', 'subject', 'body', 'sms_body',
            'description', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_event_type_display(self, obj):
        return dict(NotificationTemplate.EVENT_CHOICES).get(obj.event_type, obj.event_type)


# ==============================================================================
# NOTIFICATION PREFERENCE SERIALIZERS
# ==============================================================================

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email_frequency_display = serializers.CharField(source='get_email_frequency_display', read_only=True)

    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'username',
            'in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled',
            'notification_email', 'notification_phone',
            'email_frequency', 'email_frequency_display',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'event_preferences',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class NotificationPreferenceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification preferences"""
    class Meta:
        model = NotificationPreference
        fields = [
            'in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled',
            'notification_email', 'notification_phone',
            'email_frequency',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'event_preferences'
        ]


# ==============================================================================
# NOTIFICATION SERIALIZERS
# ==============================================================================

class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notifications"""
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body', 'channel', 'channel_display',
            'event_type', 'related_model', 'related_object_id',
            'status', 'status_display', 'priority', 'priority_display',
            'is_read', 'read_at', 'created_at'
        ]

    def get_is_read(self, obj):
        return obj.read_at is not None


class NotificationDetailSerializer(serializers.ModelSerializer):
    """Detailed notification serializer"""
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_read = serializers.SerializerMethodField()
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'body', 'channel', 'channel_display',
            'event_type', 'template', 'template_name',
            'related_model', 'related_object_id',
            'status', 'status_display', 'priority', 'priority_display',
            'sent_at', 'delivered_at', 'read_at', 'is_read',
            'scheduled_for', 'metadata',
            'created_at', 'updated_at'
        ]

    def get_is_read(self, obj):
        return obj.read_at is not None


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )


# ==============================================================================
# NOTIFICATION BATCH SERIALIZERS
# ==============================================================================

class NotificationBatchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing batches"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = NotificationBatch
        fields = [
            'id', 'name', 'title', 'channel', 'channel_display',
            'status', 'status_display',
            'total_recipients', 'sent_count', 'delivered_count', 'failed_count',
            'scheduled_for', 'created_by', 'created_by_name',
            'created_at'
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class NotificationBatchDetailSerializer(serializers.ModelSerializer):
    """Detailed batch serializer"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = NotificationBatch
        fields = [
            'id', 'name', 'description', 'title', 'body',
            'channel', 'channel_display',
            'target_criteria', 'status', 'status_display',
            'total_recipients', 'sent_count', 'delivered_count', 'failed_count',
            'scheduled_for', 'started_at', 'completed_at',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class NotificationBatchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notification batches"""
    class Meta:
        model = NotificationBatch
        fields = [
            'name', 'description', 'title', 'body', 'channel',
            'target_criteria', 'scheduled_for'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
