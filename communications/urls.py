"""URL Configuration for Communications App"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsViewSet, EventViewSet, AnnouncementViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'events', EventViewSet, basename='event')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('', include(router.urls)),
]
