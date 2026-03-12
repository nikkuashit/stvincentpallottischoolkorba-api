"""Serializers for Communications App - Simplified without multi-tenancy"""

from rest_framework import serializers
from .models import News, Event, Announcement


class NewsSerializer(serializers.ModelSerializer):
    """Serializer for News model"""
    author_name = serializers.CharField(source='author.user.get_full_name', read_only=True)

    class Meta:
        model = News
        fields = [
            'id', 'title', 'slug', 'summary', 'content',
            'featured_image', 'author', 'author_name', 'published_date', 'is_published',
            'is_featured', 'views_count', 'meta_title', 'meta_description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'views_count']


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    organizer_name = serializers.CharField(source='organizer.user.get_full_name', read_only=True)
    is_new = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description',
            'event_type', 'start_date', 'end_date', 'location', 'featured_image',
            'organizer', 'organizer_name', 'is_published', 'is_featured',
            'max_participants', 'registration_required', 'created_at', 'updated_at',
            'is_new', 'is_upcoming'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_new(self, obj):
        """Return True if event was created within the last 10 days"""
        from django.utils import timezone
        from datetime import timedelta
        return obj.created_at >= timezone.now() - timedelta(days=10)

    def get_is_upcoming(self, obj):
        """Return True if event start_date is in the future"""
        from django.utils import timezone
        return obj.start_date > timezone.now()


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for Announcement model"""
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'priority',
            'target_audience', 'created_by', 'created_by_name', 'is_published',
            'published_date', 'expiry_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
