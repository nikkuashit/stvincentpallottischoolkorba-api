"""
Communications App - News, Events, Announcements

This module handles:
- News articles
- School events
- Announcements
- User notifications
"""

import uuid
from django.db import models


class News(models.Model):
    """News articles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='news'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='news'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    summary = models.TextField()
    content = models.TextField()

    featured_image = models.ImageField(upload_to='news/images/', null=True, blank=True)

    author = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_articles'
    )

    published_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    views_count = models.IntegerField(default=0)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "News"
        ordering = ['-published_date']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['published_date']),
        ]

    def __str__(self):
        return self.title


class Event(models.Model):
    """School events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='events'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='events'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField()

    event_type = models.CharField(
        max_length=50,
        choices=[
            ('academic', 'Academic'),
            ('sports', 'Sports'),
            ('cultural', 'Cultural'),
            ('holiday', 'Holiday'),
            ('other', 'Other')
        ],
        default='academic'
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)

    featured_image = models.ImageField(upload_to='events/images/', null=True, blank=True)

    organizer = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events'
    )

    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    max_participants = models.IntegerField(null=True, blank=True)
    registration_required = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['start_date']),
        ]

    def __str__(self):
        return self.title


class Announcement(models.Model):
    """School announcements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='announcements'
    )

    title = models.CharField(max_length=255)
    content = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        default='normal'
    )

    target_audience = models.JSONField(default=dict)

    created_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements'
    )

    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['published_date', 'expiry_date']),
        ]

    def __str__(self):
        return self.title


class Notification(models.Model):
    """User notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('info', 'Information'),
            ('warning', 'Warning'),
            ('success', 'Success'),
            ('error', 'Error')
        ],
        default='info'
    )

    link = models.CharField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user}"
