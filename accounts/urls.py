"""URL Configuration for Accounts App"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, UserProfileViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('', include(router.urls)),
]
