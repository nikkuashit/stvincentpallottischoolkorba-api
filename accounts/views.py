"""
Views for Accounts App - User Management with RBAC
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Role, UserProfile
from .serializers import (
    RoleSerializer, UserSerializer, UserProfileSerializer,
    UserCreateSerializer, UserUpdateSerializer, PasswordChangeSerializer
)


class IsAdminOrStaff(BasePermission):
    """
    Permission class to check if user is admin or staff
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )


class IsSuperAdmin(BasePermission):
    """
    Permission class to check if user is super admin
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Role management
    Only admins and super admins can manage roles
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        """
        Filter roles based on user's organization
        Super admins can see all roles
        """
        user = self.request.user

        if user.is_superuser:
            return Role.objects.all()

        # Get user's profile to filter by organization
        try:
            profile = user.profile
            return Role.objects.filter(organization=profile.organization)
        except UserProfile.DoesNotExist:
            return Role.objects.none()

    def perform_create(self, serializer):
        """
        Create role with proper organization context
        """
        # If not super admin, use user's organization
        if not self.request.user.is_superuser:
            try:
                profile = self.request.user.profile
                serializer.save(organization=profile.organization)
            except UserProfile.DoesNotExist:
                raise ValueError("User must have a profile to create roles")
        else:
            serializer.save()


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile management
    Only admins and super admins can manage users
    """
    permission_classes = [IsAdminOrStaff]

    def get_serializer_class(self):
        """
        Use different serializers for different actions
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserProfileSerializer

    def get_queryset(self):
        """
        Filter users based on user's organization
        Super admins can see all users
        """
        user = self.request.user

        if user.is_superuser:
            queryset = UserProfile.objects.all()
        else:
            # Get user's profile to filter by organization
            try:
                profile = user.profile
                queryset = UserProfile.objects.filter(organization=profile.organization)
            except UserProfile.DoesNotExist:
                return UserProfile.objects.none()

        # Support filtering by query parameters
        organization_id = self.request.query_params.get('organization', None)
        school_id = self.request.query_params.get('school', None)
        role_id = self.request.query_params.get('role', None)
        is_active = self.request.query_params.get('is_active', None)
        search = self.request.query_params.get('search', None)

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )

        return queryset.select_related('user', 'organization', 'school', 'role')

    def create(self, request, *args, **kwargs):
        """
        Create a new user with profile
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # If not super admin, ensure organization matches
        if not request.user.is_superuser:
            try:
                profile = request.user.profile
                if str(serializer.validated_data['organization']) != str(profile.organization.id):
                    return Response(
                        {'error': 'Cannot create user for different organization'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'User must have a profile'},
                    status=status.HTTP_403_FORBIDDEN
                )

        profile = serializer.save()

        # Return the profile data
        return Response(
            UserProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        Update user and profile
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check permission to update this user
        if not request.user.is_superuser:
            try:
                profile = request.user.profile
                if instance.organization != profile.organization:
                    return Response(
                        {'error': 'Cannot update user from different organization'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'User must have a profile'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(UserProfileSerializer(profile).data)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete user by deactivating
        """
        instance = self.get_object()

        # Check permission to delete this user
        if not request.user.is_superuser:
            try:
                profile = request.user.profile
                if instance.organization != profile.organization:
                    return Response(
                        {'error': 'Cannot delete user from different organization'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'User must have a profile'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Soft delete - deactivate instead of deleting
        instance.is_active = False
        instance.user.is_active = False
        instance.save()
        instance.user.save()

        return Response(
            {'message': 'User deactivated successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request, pk=None):
        """
        Change user password
        Users can change their own password
        Admins can change any user's password in their organization
        """
        user_profile = self.get_object()
        user = user_profile.user

        # Check if user can change this password
        if request.user.id != user.id:
            # Only admins can change other users' passwords
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check organization match for non-superusers
            if not request.user.is_superuser:
                try:
                    admin_profile = request.user.profile
                    if user_profile.organization != admin_profile.organization:
                        return Response(
                            {'error': 'Cannot change password for user in different organization'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except UserProfile.DoesNotExist:
                    return Response(
                        {'error': 'Admin must have a profile'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user's profile
        """
        try:
            profile = request.user.profile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
