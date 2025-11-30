"""Custom permissions for CMS App"""

from rest_framework import permissions


class IsAdminOrStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Allow GET requests for everyone (unauthenticated users included)
    - Allow POST, PUT, PATCH, DELETE only for admin or staff users
    """

    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations (POST, PUT, PATCH, DELETE), check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is admin or staff
        return request.user.is_staff or request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS requests for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations, check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is admin or staff
        return request.user.is_staff or request.user.is_superuser
