"""
Views for Academics App - Students, Classes, Academic Years
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.db.models import Q

from .models import AcademicYear, Class, Student, Parent, Subject, Course
from .serializers import (
    AcademicYearSerializer,
    ClassSerializer,
    StudentListSerializer,
    StudentDetailSerializer,
    StudentCreateSerializer,
    StudentUpdateSerializer,
    StudentCreateResponseSerializer,
    ParentSerializer,
    SubjectSerializer,
    CourseSerializer,
    get_current_academic_year,
)


class IsAdminOrStaff(BasePermission):
    """Permission class to check if user is admin or staff"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )


class AcademicYearViewSet(viewsets.ModelViewSet):
    """ViewSet for AcademicYear management"""
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = AcademicYear.objects.all()
        is_current = self.request.query_params.get('is_current', None)
        is_active = self.request.query_params.get('is_active', None)

        if is_current is not None:
            queryset = queryset.filter(is_current=is_current.lower() == 'true')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('-start_date')

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get or create the current academic year"""
        academic_year = get_current_academic_year()
        serializer = self.get_serializer(academic_year)
        return Response(serializer.data)


class ClassViewSet(viewsets.ModelViewSet):
    """ViewSet for Class management"""
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = Class.objects.select_related('class_teacher').all()

        grade = self.request.query_params.get('grade', None)
        section = self.request.query_params.get('section', None)
        is_active = self.request.query_params.get('is_active', None)
        search = self.request.query_params.get('search', None)

        if grade:
            queryset = queryset.filter(grade=grade)
        if section:
            queryset = queryset.filter(section__icontains=section)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(section__icontains=search)
            )

        return queryset.order_by('grade', 'section')


class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet for Student management"""
    permission_classes = [IsAdminOrStaff]

    def get_serializer_class(self):
        if self.action == 'create':
            return StudentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        elif self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentListSerializer

    def get_queryset(self):
        queryset = Student.objects.select_related(
            'current_class', 'academic_year', 'user_profile', 'user_profile__user'
        ).all()

        # Filters
        current_class = self.request.query_params.get('current_class', None)
        academic_year = self.request.query_params.get('academic_year', None)
        status_filter = self.request.query_params.get('status', None)
        gender = self.request.query_params.get('gender', None)
        search = self.request.query_params.get('search', None)

        if current_class:
            queryset = queryset.filter(current_class_id=current_class)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if gender:
            queryset = queryset.filter(gender=gender)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(admission_number__icontains=search) |
                Q(roll_number__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset.order_by('first_name', 'last_name')

    def create(self, request, *args, **kwargs):
        """Create a new student with auto-generated credentials"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        # Return response with generated credentials
        response_serializer = StudentCreateResponseSerializer(student)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update student information"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        return Response(StudentDetailSerializer(student).data)

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """Reset student password to default (username123)"""
        student = self.get_object()

        if not student.user_profile or not student.user_profile.user:
            return Response(
                {'error': 'Student does not have a user account'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = student.user_profile.user
        new_password = f"{user.username}123"
        user.set_password(new_password)
        user.save()

        # Set must_change_password flag
        student.user_profile.must_change_password = True
        student.user_profile.save()

        return Response({
            'message': 'Password reset successfully',
            'username': user.username,
            'password': new_password,
            'must_change_password': True
        })

    @action(detail=False, methods=['get'])
    def by_class(self, request):
        """Get students grouped by class"""
        class_id = request.query_params.get('class_id')
        if not class_id:
            return Response(
                {'error': 'class_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        students = self.get_queryset().filter(current_class_id=class_id)
        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)


class ParentViewSet(viewsets.ModelViewSet):
    """ViewSet for Parent management"""
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = Parent.objects.prefetch_related('students').all()

        is_active = self.request.query_params.get('is_active', None)
        search = self.request.query_params.get('search', None)
        student_id = self.request.query_params.get('student', None)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        if student_id:
            queryset = queryset.filter(students__id=student_id)

        return queryset.order_by('first_name', 'last_name')

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_children(self, request):
        """
        Get children (students) associated with the logged-in parent.
        Returns list of students linked to the parent's user profile.
        """
        user = request.user

        # Check if user has a profile with parent role
        if not hasattr(user, 'profile'):
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        profile = user.profile
        if profile.role != 'parent':
            return Response(
                {'error': 'This endpoint is only for parent users'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Find the Parent record associated with this user profile
        try:
            parent = Parent.objects.get(user_profile=profile)
        except Parent.DoesNotExist:
            # Try to find by email match as fallback
            try:
                parent = Parent.objects.get(email=user.email, is_active=True)
            except Parent.DoesNotExist:
                return Response(
                    {'children': [], 'message': 'No children found for this parent'},
                    status=status.HTTP_200_OK
                )

        # Get all active students linked to this parent
        students = parent.students.filter(status='active').select_related('current_class')
        serializer = StudentListSerializer(students, many=True)

        return Response({
            'children': serializer.data,
            'parent_name': f"{parent.first_name} {parent.last_name}",
            'count': students.count()
        })


class SubjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Subject management"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = Subject.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        search = self.request.query_params.get('search', None)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        return queryset.order_by('name')


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for Course management"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = Course.objects.select_related(
            'class_assigned', 'subject', 'teacher', 'academic_year'
        ).all()

        class_id = self.request.query_params.get('class', None)
        subject_id = self.request.query_params.get('subject', None)
        teacher_id = self.request.query_params.get('teacher', None)
        academic_year = self.request.query_params.get('academic_year', None)
        is_active = self.request.query_params.get('is_active', None)

        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('class_assigned__grade', 'subject__name')
