"""
Notifications Views

API endpoints for notifications, preferences, and templates.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Q, Count

from .models import (
    NotificationTemplate,
    NotificationPreference,
    Notification,
    NotificationBatch,
)
from .serializers import (
    NotificationTemplateSerializer,
    NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer,
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationMarkReadSerializer,
    NotificationBatchListSerializer,
    NotificationBatchDetailSerializer,
    NotificationBatchCreateSerializer,
)


# ==============================================================================
# NOTIFICATION TEMPLATE VIEWS
# ==============================================================================

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification templates.
    Admin only for write operations.
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'subject', 'body']
    ordering_fields = ['event_type', 'channel', 'name']
    ordering = ['event_type', 'channel']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by event_type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by channel
        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset


# ==============================================================================
# NOTIFICATION PREFERENCE VIEWS
# ==============================================================================

class NotificationPreferenceViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing user notification preferences.
    Each user can only access their own preferences.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return NotificationPreferenceUpdateSerializer
        return NotificationPreferenceSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's notification preferences"""
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preference)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_preferences(self, request):
        """Update current user's notification preferences"""
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )

        partial = request.method == 'PATCH'
        serializer = NotificationPreferenceUpdateSerializer(
            preference,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(NotificationPreferenceSerializer(preference).data)


# ==============================================================================
# NOTIFICATION VIEWS
# ==============================================================================

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and managing notifications.
    Users can only see their own notifications.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'read_at', 'priority']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NotificationDetailSerializer
        return NotificationListSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by channel
        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            if is_read.lower() == 'true':
                queryset = queryset.filter(read_at__isnull=False)
            else:
                queryset = queryset.filter(read_at__isnull=True)

        # Filter by event_type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Limit to in_app channel for default polling
        in_app_only = self.request.query_params.get('in_app_only')
        if in_app_only == 'true':
            queryset = queryset.filter(channel='in_app')

        return queryset

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(NotificationDetailSerializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark multiple or all notifications as read"""
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids', [])

        queryset = Notification.objects.filter(
            user=request.user,
            read_at__isnull=True
        )

        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)

        count = queryset.update(
            status='read',
            read_at=timezone.now()
        )

        return Response({'marked_read': count})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            user=request.user,
            read_at__isnull=True,
            channel='in_app'
        ).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get notification summary for dashboard"""
        user = request.user

        # Get counts by status
        queryset = Notification.objects.filter(user=user, channel='in_app')

        summary = {
            'total': queryset.count(),
            'unread': queryset.filter(read_at__isnull=True).count(),
            'today': queryset.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'by_priority': {
                'urgent': queryset.filter(priority='urgent', read_at__isnull=True).count(),
                'high': queryset.filter(priority='high', read_at__isnull=True).count(),
                'normal': queryset.filter(priority='normal', read_at__isnull=True).count(),
                'low': queryset.filter(priority='low', read_at__isnull=True).count(),
            }
        }

        # Get recent unread notifications (for quick preview)
        recent_unread = queryset.filter(
            read_at__isnull=True
        ).order_by('-created_at')[:5]

        summary['recent_unread'] = NotificationListSerializer(
            recent_unread,
            many=True
        ).data

        return Response(summary)

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all read notifications"""
        count = Notification.objects.filter(
            user=request.user,
            read_at__isnull=False
        ).delete()[0]

        return Response({'deleted': count})


# ==============================================================================
# NOTIFICATION BATCH VIEWS
# ==============================================================================

class NotificationBatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification batches.
    Admin only.
    """
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'title', 'body']
    ordering_fields = ['created_at', 'scheduled_for', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationBatchCreateSerializer
        if self.action in ['retrieve', 'update', 'partial_update']:
            return NotificationBatchDetailSerializer
        return NotificationBatchListSerializer

    def get_queryset(self):
        queryset = NotificationBatch.objects.all()

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by channel
        channel = self.request.query_params.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)

        return queryset

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send a batch notification"""
        batch = self.get_object()

        if batch.status not in ['draft', 'scheduled']:
            return Response(
                {'error': f'Cannot send batch with status: {batch.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Start processing
        batch.status = 'processing'
        batch.started_at = timezone.now()
        batch.save()

        # TODO: Implement actual batch sending logic
        # For now, just mark as completed
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()

        return Response(NotificationBatchDetailSerializer(batch).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled batch"""
        batch = self.get_object()

        if batch.status != 'scheduled':
            return Response(
                {'error': 'Only scheduled batches can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        batch.status = 'draft'
        batch.scheduled_for = None
        batch.save()

        return Response(NotificationBatchDetailSerializer(batch).data)
