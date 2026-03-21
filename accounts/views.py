"""
Views for Accounts App - User Management with RBAC
Simplified without multi-tenancy
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.contrib.auth.models import User
from django.db.models import Q
from .models import UserProfile
from django.http import HttpResponse
from .serializers import (
    UserSerializer, UserProfileSerializer, UserListSerializer,
    UserCreateSerializer, UserUpdateSerializer, PasswordChangeSerializer,
    SelfPasswordChangeSerializer, RoleSerializer, UserCreateResponseSerializer,
    BulkUserImportSerializer
)
from .bulk_import import generate_import_template, parse_excel_file, create_users_from_data


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


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management
    Handles CRUD operations for users with profiles
    """
    permission_classes = [IsAdminOrStaff]
    pagination_class = None

    def get_serializer_class(self):
        """
        Use different serializers for different actions
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserProfileSerializer

    def get_queryset(self):
        """
        Return all user profiles with filtering support.
        By default, excludes students since they are managed via /academics/students/
        """
        queryset = UserProfile.objects.select_related('user').all()

        # Support filtering by query parameters
        role = self.request.query_params.get('role', None)
        is_active = self.request.query_params.get('is_active', None)
        search = self.request.query_params.get('search', None)
        include_students = self.request.query_params.get('include_students', None)

        if role:
            queryset = queryset.filter(role=role)
        elif include_students is None or include_students.lower() not in ['true', '1', 'yes']:
            # By default, exclude students from the users list
            # Students are managed separately via /academics/students/
            queryset = queryset.exclude(role='student')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(user__is_active=is_active_bool)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(admission_no__icontains=search)
            )

        return queryset.order_by('-user__date_joined')

    def create(self, request, *args, **kwargs):
        """
        Create a new user with profile.

        If auto_generate_credentials=True, username and password are auto-generated
        and returned in the response for SMS notification.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        # Use response serializer that includes generated credentials
        response_serializer = UserCreateResponseSerializer(profile)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Get a single user profile by pk (user's pk, not profile's id)
        """
        pk = kwargs.get('pk')
        try:
            # Try to get by user pk first
            profile = UserProfile.objects.select_related('user').get(user__pk=pk)
        except UserProfile.DoesNotExist:
            # Try by profile id
            try:
                profile = UserProfile.objects.select_related('user').get(pk=pk)
            except (UserProfile.DoesNotExist, ValueError):
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Update user and profile
        """
        partial = kwargs.pop('partial', False)
        pk = kwargs.get('pk')

        try:
            # Try to get by user pk first
            instance = UserProfile.objects.select_related('user').get(user__pk=pk)
        except UserProfile.DoesNotExist:
            try:
                instance = UserProfile.objects.select_related('user').get(pk=pk)
            except (UserProfile.DoesNotExist, ValueError):
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(UserProfileSerializer(profile).data)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete user by deactivating
        """
        pk = kwargs.get('pk')

        try:
            instance = UserProfile.objects.select_related('user').get(user__pk=pk)
        except UserProfile.DoesNotExist:
            try:
                instance = UserProfile.objects.select_related('user').get(pk=pk)
            except (UserProfile.DoesNotExist, ValueError):
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Soft delete - deactivate instead of deleting
        instance.user.is_active = False
        instance.user.save()

        return Response(
            {'message': 'User deactivated successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post'], url_path='set_password')
    def set_password(self, request, pk=None):
        """
        Set password for a user (admin only)
        """
        try:
            profile = UserProfile.objects.select_related('user').get(user__pk=pk)
        except UserProfile.DoesNotExist:
            try:
                profile = UserProfile.objects.select_related('user').get(pk=pk)
            except (UserProfile.DoesNotExist, ValueError):
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=profile.user)

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
            # Return basic user info if no profile
            return Response({
                'pk': request.user.pk,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_active': request.user.is_active,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'role': 'super_admin' if request.user.is_superuser else ('school_admin' if request.user.is_staff else 'student')
            })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        """
        Allow authenticated user to change their own password.
        If must_change_password is True, current_password is not required.
        Optionally allows changing username as well.
        """
        serializer = SelfPasswordChangeSerializer(
            data=request.data,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password changed successfully',
            'username': request.user.username,
            'must_change_password': False
        })

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        """
        Bulk import users from an Excel file.

        Accepts an Excel file with user data and creates all valid users.
        Uses database transaction - if any row fails, all are rolled back.

        Request body (multipart/form-data):
        - file: Excel file (.xlsx)
        - role: User role (school_staff, parent, student)
        - send_sms: Boolean, whether to send SMS notifications (default: false)
        """
        serializer = BulkUserImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        role = serializer.validated_data['role']
        send_sms = serializer.validated_data.get('send_sms', False)

        # Parse Excel file
        valid_rows, parse_errors = parse_excel_file(file, role)

        if parse_errors:
            return Response({
                'success': False,
                'message': 'Validation errors found in Excel file',
                'total_rows': len(valid_rows) + len(parse_errors),
                'valid_rows': len(valid_rows),
                'error_count': len(parse_errors),
                'errors': parse_errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        if not valid_rows:
            return Response({
                'success': False,
                'message': 'No valid data rows found in Excel file',
                'total_rows': 0,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create users
        created_users, create_errors = create_users_from_data(valid_rows, role, send_sms)

        if create_errors:
            return Response({
                'success': False,
                'message': 'Import failed - all changes rolled back',
                'total_rows': len(valid_rows),
                'error_count': len(create_errors),
                'errors': create_errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': f'Successfully imported {len(created_users)} users',
            'total_rows': len(valid_rows),
            'success_count': len(created_users),
            'created_users': created_users,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='import-template')
    def import_template(self, request):
        """
        Download Excel template for bulk user import.

        Query parameters:
        - role: User role (school_staff, parent, student)

        Returns an Excel file with proper headers and sample data.
        """
        role = request.query_params.get('role', 'school_staff')

        if role not in ['school_staff', 'parent', 'student']:
            return Response({
                'error': f"Invalid role: {role}. Must be one of: school_staff, parent, student"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate template
        excel_content = generate_import_template(role)

        # Create response with Excel file
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{role}_import_template.xlsx"'

        return response


class RoleViewSet(viewsets.ViewSet):
    """
    ViewSet for listing available roles
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Return list of available roles
        """
        roles = [
            {
                'id': 'school_admin',
                'name': 'school_admin',
                'display_name': 'School Administrator',
                'description': 'Full access to school management'
            },
            {
                'id': 'school_staff',
                'name': 'school_staff',
                'display_name': 'School Staff / Teacher',
                'description': 'Access to class management, attendance, and grades'
            },
            {
                'id': 'parent',
                'name': 'parent',
                'display_name': 'Parent / Guardian',
                'description': 'View children\'s information'
            },
            {
                'id': 'student',
                'name': 'student',
                'display_name': 'Student',
                'description': 'View own information'
            },
        ]
        return Response(roles)
