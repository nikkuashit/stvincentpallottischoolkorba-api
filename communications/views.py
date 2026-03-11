"""ViewSets for Communications App"""

from django.db import models
from rest_framework import viewsets, filters
from .models import News, Event, Announcement
from .serializers import NewsSerializer, EventSerializer, AnnouncementSerializer
from cms.permissions import IsAdminOrStaffOrReadOnly


class NewsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for News
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug', 'summary', 'content']
    ordering_fields = ['published_date', 'created_at', 'title', 'views_count']
    ordering = ['-published_date']
    lookup_field = 'slug'

    def get_queryset(self):
        """Filter news based on query parameters"""
        queryset = super().get_queryset()

        # Filter by school
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        # Filter by is_published
        is_published = self.request.query_params.get('is_published', None)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        # Filter by is_featured
        is_featured = self.request.query_params.get('is_featured', None)
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')

        # Show only published news for non-staff users
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Increment views count on retrieve"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        return super().retrieve(request, *args, **kwargs)


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Event
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug', 'description', 'location']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'title']
    ordering = ['-start_date']
    lookup_field = 'slug'

    def get_queryset(self):
        """Filter events based on query parameters"""
        queryset = super().get_queryset()

        # Filter by school
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        # Filter by event_type
        event_type = self.request.query_params.get('event_type', None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by is_published
        is_published = self.request.query_params.get('is_published', None)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        # Filter by is_featured
        is_featured = self.request.query_params.get('is_featured', None)
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')

        # Show only published events for non-staff users
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)

        return queryset


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Announcement
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['published_date', 'created_at', 'priority']
    ordering = ['-published_date']

    def get_queryset(self):
        """Filter announcements based on query parameters"""
        from django.utils import timezone

        queryset = super().get_queryset()

        # Filter by school
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter by is_published
        is_published = self.request.query_params.get('is_published', None)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        # Show only published and non-expired announcements for non-staff users
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            now = timezone.now()
            queryset = queryset.filter(
                is_published=True
            ).filter(
                models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gte=now)
            )

        return queryset
