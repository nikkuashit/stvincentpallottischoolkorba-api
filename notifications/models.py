"""
Notifications App - Communication & Notification System

This module handles:
- Notification templates for different events
- User notifications (in-app, email, SMS, push)
- User notification preferences
- Notification delivery tracking
"""

import uuid
from django.db import models
from django.contrib.auth.models import User


# ==============================================================================
# NOTIFICATION TEMPLATES
# ==============================================================================

class NotificationTemplate(models.Model):
    """
    Templates for different notification events
    """
    CHANNEL_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]

    EVENT_CHOICES = [
        # Request events
        ('request_submitted', 'Request Submitted'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
        ('request_pending_approval', 'Request Pending Your Approval'),
        ('request_pending_clearance', 'Request Pending Your Clearance'),
        ('request_completed', 'Request Completed'),
        ('request_cancelled', 'Request Cancelled'),
        ('request_bypassed', 'Request Bypassed'),

        # Clearance events
        ('clearance_granted', 'Clearance Granted'),
        ('clearance_denied', 'Clearance Denied'),
        ('clearance_pending', 'Clearance Pending'),

        # Payment events
        ('payment_pending', 'Payment Pending'),
        ('payment_completed', 'Payment Completed'),
        ('payment_failed', 'Payment Failed'),

        # General events
        ('announcement', 'Announcement'),
        ('reminder', 'Reminder'),
        ('system_alert', 'System Alert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)

    # Template content (supports placeholders like {{user_name}}, {{request_number}})
    subject = models.CharField(
        max_length=255,
        blank=True,
        help_text="Subject line (for email/push)"
    )
    body = models.TextField(
        help_text="Template body with placeholders like {{user_name}}, {{request_number}}"
    )

    # For SMS (shorter version)
    sms_body = models.CharField(
        max_length=160,
        blank=True,
        help_text="Short SMS version (max 160 chars)"
    )

    # Metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['event_type', 'channel']
        unique_together = [['event_type', 'channel']]
        indexes = [
            models.Index(fields=['event_type', 'channel', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"


# ==============================================================================
# NOTIFICATION PREFERENCES
# ==============================================================================

class NotificationPreference(models.Model):
    """
    User preferences for receiving notifications
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Channel preferences
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)

    # Contact details for notifications
    notification_email = models.EmailField(
        blank=True,
        help_text="Email for notifications (uses account email if blank)"
    )
    notification_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number for SMS notifications"
    )

    # Frequency preferences
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily_digest', 'Daily Digest'),
            ('weekly_digest', 'Weekly Digest'),
        ],
        default='immediate'
    )

    # Quiet hours (no notifications during this time)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Event-specific preferences (JSON: { "event_type": { "in_app": true, "email": false, ... } })
    event_preferences = models.JSONField(
        default=dict,
        help_text="Fine-grained control over which events trigger which channels"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Notification preferences for {self.user.username}"

    def is_channel_enabled(self, channel, event_type=None):
        """
        Check if a channel is enabled for the user, optionally for a specific event
        """
        # Check event-specific preference first
        if event_type and event_type in self.event_preferences:
            event_pref = self.event_preferences[event_type]
            if channel in event_pref:
                return event_pref[channel]

        # Fall back to global preference
        channel_map = {
            'in_app': self.in_app_enabled,
            'email': self.email_enabled,
            'sms': self.sms_enabled,
            'push': self.push_enabled,
        }
        return channel_map.get(channel, False)


# ==============================================================================
# NOTIFICATIONS
# ==============================================================================

class Notification(models.Model):
    """
    Individual notifications sent to users
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Recipient
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Notification content
    title = models.CharField(max_length=255)
    body = models.TextField()
    channel = models.CharField(
        max_length=20,
        choices=[
            ('in_app', 'In-App'),
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('push', 'Push Notification'),
        ]
    )

    # Event information
    event_type = models.CharField(max_length=50, blank=True)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Related object (for deep linking)
    related_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="Model name (e.g., 'workflows.Request')"
    )
    related_object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of the related object"
    )

    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')

    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # For email/SMS
    delivery_response = models.TextField(
        blank=True,
        help_text="Response from email/SMS provider"
    )
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)

    # Scheduling
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Schedule notification for later"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional context data"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['user', 'channel', 'status']),
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['related_model', 'related_object_id']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username} ({self.status})"

    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        if not self.read_at:
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at', 'updated_at'])


# ==============================================================================
# NOTIFICATION BATCH (FOR BULK NOTIFICATIONS)
# ==============================================================================

class NotificationBatch(models.Model):
    """
    Batch of notifications for bulk sends (e.g., announcements)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Batch content
    title = models.CharField(max_length=255)
    body = models.TextField()
    channel = models.CharField(
        max_length=20,
        choices=[
            ('in_app', 'In-App'),
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('push', 'Push Notification'),
        ]
    )

    # Target audience (JSON filter criteria)
    target_criteria = models.JSONField(
        default=dict,
        help_text="Filter criteria for recipients (e.g., {'role': 'parent', 'class': '10A'})"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='draft'
    )

    # Stats
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)

    # Tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Creator
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notification_batches'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Notification batches"
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def create_notification(
    user,
    title,
    body,
    channel='in_app',
    event_type='',
    related_model='',
    related_object_id=None,
    priority='normal',
    metadata=None
):
    """
    Helper function to create a notification
    """
    # Check user preferences
    if hasattr(user, 'notification_preferences'):
        prefs = user.notification_preferences
        if not prefs.is_channel_enabled(channel, event_type):
            return None

    notification = Notification.objects.create(
        user=user,
        title=title,
        body=body,
        channel=channel,
        event_type=event_type,
        related_model=related_model,
        related_object_id=related_object_id,
        priority=priority,
        metadata=metadata or {},
        status='pending'
    )

    # For in-app notifications, mark as sent immediately
    if channel == 'in_app':
        from django.utils import timezone
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])

    return notification


def send_request_notification(request_obj, event_type, recipient_users=None):
    """
    Send notifications for request events to relevant users
    """
    from django.utils import timezone

    notifications = []

    # Determine recipients based on event type
    if recipient_users is None:
        recipient_users = []

        if event_type in ['request_submitted', 'request_pending_approval', 'request_pending_clearance']:
            # Always notify super_admin and school_admin for new requests
            from accounts.models import UserProfile
            admin_profiles = UserProfile.objects.filter(
                role__in=['super_admin', 'school_admin']
            )
            recipient_users = list(set([p.user for p in admin_profiles]))

            # Also notify next approver(s) if there's an approval workflow
            if event_type == 'request_pending_approval' and request_obj.current_step:
                step = request_obj.current_step
                if step.approver_type == 'role':
                    # Get all users with this role
                    profiles = UserProfile.objects.filter(role=step.approver_role)
                    role_users = [p.user for p in profiles]
                    recipient_users = list(set(recipient_users + role_users))
                elif step.approver_user and step.approver_user not in recipient_users:
                    recipient_users.append(step.approver_user)

            # Notify clearance staff if pending clearance
            if event_type == 'request_pending_clearance':
                from workflows.models import ClearanceType
                clearance_types = ClearanceType.objects.filter(is_active=True)
                for ct in clearance_types:
                    profiles = UserProfile.objects.filter(role=ct.clearance_role)
                    clearance_users = [p.user for p in profiles]
                    recipient_users = list(set(recipient_users + clearance_users))

        elif event_type in ['request_approved', 'request_rejected', 'request_completed', 'request_bypassed']:
            # Notify the requester
            recipient_users = [request_obj.submitted_by]

    # Create notifications for each recipient
    for user in recipient_users:
        title_map = {
            'request_submitted': f"New Request: {request_obj.request_number}",
            'request_approved': f"Request Approved: {request_obj.request_number}",
            'request_rejected': f"Request Rejected: {request_obj.request_number}",
            'request_pending_approval': f"Pending Approval: {request_obj.request_number}",
            'request_pending_clearance': f"Pending Clearance: {request_obj.request_number}",
            'request_completed': f"Request Completed: {request_obj.request_number}",
            'request_bypassed': f"Request Bypassed: {request_obj.request_number}",
        }

        body_map = {
            'request_submitted': f"A new {request_obj.request_type.name} request has been submitted by {request_obj.submitted_by.get_full_name() or request_obj.submitted_by.username}.",
            'request_approved': f"Your {request_obj.request_type.name} request has been approved.",
            'request_rejected': f"Your {request_obj.request_type.name} request has been rejected.",
            'request_pending_approval': f"A {request_obj.request_type.name} request from {request_obj.submitted_by.get_full_name() or request_obj.submitted_by.username} is pending approval.",
            'request_pending_clearance': f"A {request_obj.request_type.name} request from {request_obj.submitted_by.get_full_name() or request_obj.submitted_by.username} requires clearance.",
            'request_completed': f"Your {request_obj.request_type.name} request has been completed.",
            'request_bypassed': f"Your {request_obj.request_type.name} request has been approved (bypassed by admin).",
        }

        notification = create_notification(
            user=user,
            title=title_map.get(event_type, f"Request Update: {request_obj.request_number}"),
            body=body_map.get(event_type, f"Update on {request_obj.request_type.name} request."),
            channel='in_app',
            event_type=event_type,
            related_model='workflows.Request',
            related_object_id=request_obj.id,
            metadata={
                'request_number': request_obj.request_number,
                'request_type': request_obj.request_type.slug,
                'status': request_obj.status,
            }
        )

        if notification:
            notifications.append(notification)

    return notifications
