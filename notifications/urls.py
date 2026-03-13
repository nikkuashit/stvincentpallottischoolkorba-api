"""
Notifications URL Configuration

API endpoints for notifications, preferences, templates, and batches.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationTemplateViewSet,
    NotificationPreferenceViewSet,
    NotificationViewSet,
    NotificationBatchViewSet,
)

router = DefaultRouter()
router.register(r'templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'batches', NotificationBatchViewSet, basename='notification-batch')

urlpatterns = [
    path('', include(router.urls)),
]
