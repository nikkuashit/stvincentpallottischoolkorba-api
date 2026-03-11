"""Serializers for Communications App"""

from rest_framework import serializers
from .models import News, Event, Announcement


class NewsSerializer(serializers.ModelSerializer):
    """Serializer for News model"""
    author_name = serializers.CharField(source='author.user.get_full_name', read_only=True)

    class Meta:
        model = News
        fields = [
            'id', 'organization', 'school', 'title', 'slug', 'summary', 'content',
            'featured_image', 'author', 'author_name', 'published_date', 'is_published',
            'is_featured', 'views_count', 'meta_title', 'meta_description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at', 'views_count']

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    organizer_name = serializers.CharField(source='organizer.user.get_full_name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'organization', 'school', 'title', 'slug', 'description',
            'event_type', 'start_date', 'end_date', 'location', 'featured_image',
            'organizer', 'organizer_name', 'is_published', 'is_featured',
            'max_participants', 'registration_required', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for Announcement model"""
    created_by_name = serializers.CharField(source='created_by.user.get_full_name', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id', 'organization', 'school', 'title', 'content', 'priority',
            'target_audience', 'created_by', 'created_by_name', 'is_published',
            'published_date', 'expiry_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)
