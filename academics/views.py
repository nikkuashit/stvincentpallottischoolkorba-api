"""
Views for Academics App - Students, Classes, Academic Years, Attendance, Grades
"""

from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import csv
from io import StringIO

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.db.models import Q, Count, Avg, Max, Min
from django.db import transaction
from django.http import HttpResponse

from .models import (
    AcademicYear, Class, Student, Parent, Subject, Course,
    AttendanceSession, Attendance, AttendanceSettings,
    ExamType, Exam, GradingScale, GradeRange, StudentMark, MarkAuditLog,
    # Phase A models
    SchoolSettings, Grade, Section,
    # Phase B models
    StudentEnrollment, StudentPhoto,
    # Phase C models
    ClassTeacher, SubjectTeacher
)
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
    # Attendance serializers
    AttendanceSessionSerializer,
    AttendanceSerializer,
    AttendanceCreateSerializer,
    BulkAttendanceSerializer,
    AttendanceSettingsSerializer,
    # Grades serializers
    ExamTypeSerializer,
    ExamListSerializer,
    ExamDetailSerializer,
    ExamCreateSerializer,
    GradingScaleSerializer,
    GradeRangeSerializer,
    StudentMarkSerializer,
    StudentMarkCreateUpdateSerializer,
    BulkMarksSerializer,
    MarkAuditLogSerializer,
    # Student Admission serializers
    StudentAdmissionSerializer,
    StudentAdmissionResponseSerializer,
    # Phase A serializers - commented out for now, uncomment when using these viewsets
    # SchoolSettingsSerializer,
    # GradeListSerializer,
    # SectionSerializer,
    # Phase B serializers
    StudentEnrollmentSerializer,
    StudentEnrollmentCreateSerializer,
    StudentPhotoSerializer,
    StudentPhotoUploadSerializer,
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


# =============================================================================
# ATTENDANCE VIEWSETS
# =============================================================================

class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for AttendanceSession management"""
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = AttendanceSession.objects.all()
        is_active = self.request.query_params.get('is_active', None)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('display_order', 'name')


class AttendanceSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for AttendanceSettings management"""
    queryset = AttendanceSettings.objects.all()
    serializer_class = AttendanceSettingsSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        # Return single settings object or create default
        settings = AttendanceSettings.objects.first()
        if not settings:
            settings = AttendanceSettings.objects.create()
        return AttendanceSettings.objects.all()


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for Attendance management with analytics"""
    permission_classes = [IsAdminOrStaff]

    def get_serializer_class(self):
        if self.action == 'create':
            return AttendanceCreateSerializer
        return AttendanceSerializer

    def get_queryset(self):
        queryset = Attendance.objects.select_related(
            'student', 'class_assigned', 'session', 'academic_year', 'marked_by'
        ).all()

        # Apply filters
        class_id = self.request.query_params.get('class', None)
        date = self.request.query_params.get('date', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        status_filter = self.request.query_params.get('status', None)
        student_id = self.request.query_params.get('student', None)
        session_id = self.request.query_params.get('session', None)
        academic_year = self.request.query_params.get('academic_year', None)

        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
        if date:
            queryset = queryset.filter(date=date)
        if date_from and date_to:
            queryset = queryset.filter(date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(date__lte=date_to)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        return queryset.order_by('-date', 'student__roll_number')

    def get_staff_classes(self, user_profile):
        """Get classes accessible to a staff member"""
        teacher_classes = Class.objects.filter(class_teacher=user_profile, is_active=True)
        course_classes = Class.objects.filter(
            courses__teacher=user_profile,
            courses__is_active=True
        )
        return (teacher_classes | course_classes).distinct()

    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """Mark attendance for multiple students at once"""
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        class_id = data['class_id']
        date = data['date']
        session_id = data.get('session_id')
        records = data['attendance_records']

        try:
            class_obj = Class.objects.get(id=class_id)
            academic_year = get_current_academic_year()
            session = AttendanceSession.objects.get(id=session_id) if session_id else None
            marked_by = request.user.profile if hasattr(request.user, 'profile') else None
        except (Class.DoesNotExist, AttendanceSession.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for record in records:
                student_id = record['student_id']
                attendance_status = record['status']
                remarks = record.get('remarks', '')

                attendance, created = Attendance.objects.update_or_create(
                    student_id=student_id,
                    date=date,
                    session=session,
                    defaults={
                        'class_assigned': class_obj,
                        'academic_year': academic_year,
                        'status': attendance_status,
                        'remarks': remarks,
                        'marked_by': marked_by
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        return Response({
            'message': 'Attendance marked successfully',
            'created': created_count,
            'updated': updated_count
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='mark-all-present')
    def mark_all_present(self, request):
        """Mark all students in a class as present"""
        class_id = request.data.get('class_id')
        date = request.data.get('date')
        session_id = request.data.get('session_id')

        if not class_id or not date:
            return Response(
                {'error': 'class_id and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            class_obj = Class.objects.get(id=class_id)
            academic_year = get_current_academic_year()
            session = AttendanceSession.objects.get(id=session_id) if session_id else None
            marked_by = request.user.profile if hasattr(request.user, 'profile') else None
        except (Class.DoesNotExist, AttendanceSession.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        students = Student.objects.filter(current_class=class_obj, status='active')
        count = 0

        with transaction.atomic():
            for student in students:
                Attendance.objects.update_or_create(
                    student=student,
                    date=date,
                    session=session,
                    defaults={
                        'class_assigned': class_obj,
                        'academic_year': academic_year,
                        'status': 'present',
                        'marked_by': marked_by
                    }
                )
                count += 1

        return Response({
            'message': f'All {count} students marked as present',
            'count': count
        })

    @action(detail=False, methods=['get'], url_path='by-class')
    def by_class(self, request):
        """Get attendance for a class on a specific date"""
        class_id = request.query_params.get('class_id')
        date = request.query_params.get('date')
        session_id = request.query_params.get('session_id')

        if not class_id or not date:
            return Response(
                {'error': 'class_id and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(
            class_assigned_id=class_id,
            date=date
        )
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        # Get all students in the class to show unmarked ones
        class_obj = Class.objects.get(id=class_id)
        all_students = Student.objects.filter(
            current_class=class_obj, status='active'
        ).order_by('roll_number', 'first_name')

        # Create a map of existing attendance
        attendance_map = {str(a.student_id): a for a in queryset}

        # Build response with all students
        result = []
        for student in all_students:
            attendance = attendance_map.get(str(student.id))
            result.append({
                'student_id': str(student.id),
                'student_name': f"{student.first_name} {student.last_name}",
                'roll_number': student.roll_number,
                'status': attendance.status if attendance else None,
                'remarks': attendance.remarks if attendance else '',
                'attendance_id': str(attendance.id) if attendance else None
            })

        return Response({
            'class_id': class_id,
            'class_name': class_obj.name,
            'date': date,
            'total_students': len(result),
            'marked_count': len([r for r in result if r['status']]),
            'students': result
        })

    @action(detail=False, methods=['get'], url_path='analytics/daily')
    def analytics_daily(self, request):
        """Get daily attendance analytics"""
        date = request.query_params.get('date', datetime.now().date().isoformat())
        class_id = request.query_params.get('class_id')

        queryset = self.get_queryset().filter(date=date)
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)

        total = queryset.count()
        status_counts = queryset.values('status').annotate(count=Count('status'))

        status_distribution = {s['status']: s['count'] for s in status_counts}
        present_count = status_distribution.get('present', 0) + status_distribution.get('late', 0)
        attendance_percentage = (present_count / total * 100) if total > 0 else 0

        return Response({
            'date': date,
            'total_students': total,
            'attendance_percentage': round(attendance_percentage, 2),
            'status_distribution': status_distribution
        })

    @action(detail=False, methods=['get'], url_path='analytics/weekly')
    def analytics_weekly(self, request):
        """Get weekly attendance trends"""
        date_str = request.query_params.get('date', datetime.now().date().isoformat())
        class_id = request.query_params.get('class_id')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        # Get start of week (Monday)
        start_of_week = date - timedelta(days=date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        queryset = self.get_queryset().filter(date__range=[start_of_week, end_of_week])
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)

        # Daily breakdown
        daily_data = []
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            day_attendance = queryset.filter(date=day)
            total = day_attendance.count()
            present = day_attendance.filter(status__in=['present', 'late']).count()
            percentage = (present / total * 100) if total > 0 else 0

            daily_data.append({
                'date': day.isoformat(),
                'day': day.strftime('%A'),
                'total': total,
                'present': present,
                'absent': day_attendance.filter(status='absent').count(),
                'late': day_attendance.filter(status='late').count(),
                'excused': day_attendance.filter(status='excused').count(),
                'percentage': round(percentage, 2)
            })

        # Overall stats
        total = queryset.count()
        present = queryset.filter(status__in=['present', 'late']).count()
        avg_percentage = (present / total * 100) if total > 0 else 0

        return Response({
            'period': {
                'from': start_of_week.isoformat(),
                'to': end_of_week.isoformat()
            },
            'total_records': total,
            'average_attendance_percentage': round(avg_percentage, 2),
            'daily_breakdown': daily_data
        })

    @action(detail=False, methods=['get'], url_path='analytics/monthly')
    def analytics_monthly(self, request):
        """Get monthly attendance report"""
        month = request.query_params.get('month', datetime.now().month)
        year = request.query_params.get('year', datetime.now().year)
        class_id = request.query_params.get('class_id')

        try:
            month = int(month)
            year = int(year)
        except ValueError:
            return Response({'error': 'Invalid month or year'}, status=status.HTTP_400_BAD_REQUEST)

        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()

        queryset = self.get_queryset().filter(date__range=[start_date, end_date])
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)

        # Calculate working days (exclude weekends - Saturday, Sunday)
        working_days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Monday to Friday
                working_days += 1
            current += timedelta(days=1)

        # Status distribution
        status_counts = queryset.values('status').annotate(count=Count('status'))
        status_distribution = {s['status']: s['count'] for s in status_counts}

        total = queryset.count()
        present = status_distribution.get('present', 0) + status_distribution.get('late', 0)
        avg_percentage = (present / total * 100) if total > 0 else 0

        return Response({
            'period': {
                'month': month,
                'year': year,
                'from': start_date.isoformat(),
                'to': end_date.isoformat()
            },
            'working_days': working_days,
            'total_records': total,
            'average_attendance_percentage': round(avg_percentage, 2),
            'status_distribution': status_distribution
        })

    @action(detail=False, methods=['get'], url_path='analytics/class-wise')
    def analytics_class_wise(self, request):
        """Get class-wise attendance comparison"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if not date_from or not date_to:
            # Default to current month
            today = datetime.now().date()
            date_from = today.replace(day=1).isoformat()
            from calendar import monthrange
            _, last_day = monthrange(today.year, today.month)
            date_to = today.replace(day=last_day).isoformat()

        queryset = self.get_queryset().filter(date__range=[date_from, date_to])

        # Group by class
        class_stats = queryset.values('class_assigned__id', 'class_assigned__name').annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late')),
            excused=Count('id', filter=Q(status='excused'))
        )

        result = []
        for stats in class_stats:
            total = stats['total']
            present_and_late = stats['present'] + stats['late']
            percentage = (present_and_late / total * 100) if total > 0 else 0

            result.append({
                'class_id': str(stats['class_assigned__id']),
                'class_name': stats['class_assigned__name'],
                'total_records': total,
                'present': stats['present'],
                'absent': stats['absent'],
                'late': stats['late'],
                'excused': stats['excused'],
                'attendance_percentage': round(percentage, 2)
            })

        # Sort by attendance percentage
        result.sort(key=lambda x: x['attendance_percentage'], reverse=True)

        return Response({
            'period': {'from': date_from, 'to': date_to},
            'classes': result
        })

    @action(detail=False, methods=['get'], url_path='analytics/student/(?P<student_id>[^/.]+)')
    def analytics_student(self, request, student_id=None):
        """Get individual student attendance report"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        queryset = self.get_queryset().filter(student_id=student_id)
        if date_from and date_to:
            queryset = queryset.filter(date__range=[date_from, date_to])

        # Status counts
        status_counts = queryset.values('status').annotate(count=Count('status'))
        status_map = {s['status']: s['count'] for s in status_counts}

        total = queryset.count()
        present = status_map.get('present', 0)
        absent = status_map.get('absent', 0)
        late = status_map.get('late', 0)
        excused = status_map.get('excused', 0)
        attendance_percentage = ((present + late) / total * 100) if total > 0 else 0

        # Get threshold
        settings = AttendanceSettings.objects.first()
        threshold = float(settings.low_attendance_threshold) if settings else 75.0

        # Monthly breakdown
        monthly_data = queryset.extra(
            select={'month': "strftime('%%Y-%%m', date)"}
        ).values('month').annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            late=Count('id', filter=Q(status='late')),
            absent=Count('id', filter=Q(status='absent')),
            excused=Count('id', filter=Q(status='excused'))
        ).order_by('month')

        monthly_breakdown = []
        for m in monthly_data:
            m_total = m['total']
            m_present = m['present'] + m['late']
            m_percentage = (m_present / m_total * 100) if m_total > 0 else 0
            monthly_breakdown.append({
                'month': m['month'],
                'total': m_total,
                'present': m['present'],
                'late': m['late'],
                'absent': m['absent'],
                'excused': m['excused'],
                'percentage': round(m_percentage, 2)
            })

        return Response({
            'student_id': str(student.id),
            'student_name': f"{student.first_name} {student.last_name}",
            'roll_number': student.roll_number,
            'class_name': student.current_class.name if student.current_class else '',
            'period': {
                'from': date_from or 'all',
                'to': date_to or 'all'
            },
            'total_days': total,
            'present_days': present,
            'absent_days': absent,
            'late_days': late,
            'excused_days': excused,
            'attendance_percentage': round(attendance_percentage, 2),
            'threshold': threshold,
            'is_below_threshold': attendance_percentage < threshold,
            'monthly_breakdown': monthly_breakdown
        })

    @action(detail=False, methods=['get'], url_path='analytics/low-attendance')
    def analytics_low_attendance(self, request):
        """Get students with attendance below threshold"""
        class_id = request.query_params.get('class_id')
        threshold = request.query_params.get('threshold')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Get threshold from settings if not provided
        if not threshold:
            settings = AttendanceSettings.objects.first()
            threshold = float(settings.low_attendance_threshold) if settings else 75.0
        else:
            threshold = float(threshold)

        # Default date range to current academic year or last 30 days
        if not date_from or not date_to:
            today = datetime.now().date()
            date_to = today.isoformat()
            date_from = (today - timedelta(days=30)).isoformat()

        # Get all students
        students_queryset = Student.objects.filter(status='active')
        if class_id:
            students_queryset = students_queryset.filter(current_class_id=class_id)

        low_attendance_students = []
        for student in students_queryset:
            attendance = Attendance.objects.filter(
                student=student,
                date__range=[date_from, date_to]
            )
            total = attendance.count()
            if total == 0:
                continue

            present = attendance.filter(status__in=['present', 'late']).count()
            absent = attendance.filter(status='absent').count()
            percentage = (present / total * 100)

            if percentage < threshold:
                low_attendance_students.append({
                    'student_id': str(student.id),
                    'student_name': f"{student.first_name} {student.last_name}",
                    'roll_number': student.roll_number,
                    'class_name': student.current_class.name if student.current_class else '',
                    'attendance_percentage': round(percentage, 2),
                    'absent_days': absent,
                    'total_days': total,
                    'threshold': threshold
                })

        # Sort by attendance percentage (lowest first)
        low_attendance_students.sort(key=lambda x: x['attendance_percentage'])

        return Response({
            'period': {'from': date_from, 'to': date_to},
            'threshold': threshold,
            'count': len(low_attendance_students),
            'students': low_attendance_students
        })

    @action(detail=False, methods=['get'], url_path='analytics/export')
    def export(self, request):
        """Export attendance data as CSV"""
        format_type = request.query_params.get('format', 'csv')
        class_id = request.query_params.get('class_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        student_id = request.query_params.get('student_id')

        queryset = self.get_queryset()
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
        if date_from and date_to:
            queryset = queryset.filter(date__range=[date_from, date_to])
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="attendance_export_{datetime.now().strftime("%Y%m%d")}.csv"'

            writer = csv.writer(response)
            writer.writerow(['Date', 'Student Name', 'Roll No', 'Class', 'Session', 'Status', 'Remarks', 'Marked By'])

            for attendance in queryset:
                writer.writerow([
                    attendance.date.isoformat(),
                    f"{attendance.student.first_name} {attendance.student.last_name}",
                    attendance.student.roll_number,
                    attendance.class_assigned.name,
                    attendance.session.name if attendance.session else '',
                    attendance.status,
                    attendance.remarks,
                    attendance.marked_by.full_name if attendance.marked_by else ''
                ])

            return response

        return Response({'error': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# GRADES / EXAM VIEWSETS
# =============================================================================

class ExamTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for ExamType management"""
    queryset = ExamType.objects.all()
    serializer_class = ExamTypeSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = ExamType.objects.all()
        is_active = self.request.query_params.get('is_active', None)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('display_order', 'name')


class GradingScaleViewSet(viewsets.ModelViewSet):
    """ViewSet for GradingScale management"""
    queryset = GradingScale.objects.all()
    serializer_class = GradingScaleSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = GradingScale.objects.prefetch_related('ranges').all()
        is_active = self.request.query_params.get('is_active', None)
        is_default = self.request.query_params.get('is_default', None)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == 'true')

        return queryset.order_by('-is_default', 'name')

    @action(detail=True, methods=['post'], url_path='add-range')
    def add_range(self, request, pk=None):
        """Add a grade range to a grading scale"""
        grading_scale = self.get_object()
        serializer = GradeRangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        grade_range = serializer.save(grading_scale=grading_scale)
        return Response(GradeRangeSerializer(grade_range).data, status=status.HTTP_201_CREATED)


class ExamViewSet(viewsets.ModelViewSet):
    """ViewSet for Exam management"""
    permission_classes = [IsAdminOrStaff]

    def get_serializer_class(self):
        if self.action == 'create':
            return ExamCreateSerializer
        elif self.action == 'retrieve':
            return ExamDetailSerializer
        return ExamListSerializer

    def get_queryset(self):
        queryset = Exam.objects.select_related(
            'exam_type', 'academic_year', 'class_assigned', 'subject'
        ).all()

        # Apply filters
        exam_type = self.request.query_params.get('exam_type')
        academic_year = self.request.query_params.get('academic_year')
        class_id = self.request.query_params.get('class')
        subject = self.request.query_params.get('subject')
        is_published = self.request.query_params.get('is_published')
        is_locked = self.request.query_params.get('is_locked')
        is_active = self.request.query_params.get('is_active')
        teacher = self.request.query_params.get('teacher')

        if exam_type:
            queryset = queryset.filter(exam_type_id=exam_type)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
        if subject:
            queryset = queryset.filter(subject_id=subject)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')
        if is_locked is not None:
            queryset = queryset.filter(is_locked=is_locked.lower() == 'true')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if teacher:
            # Filter by teacher's courses
            queryset = queryset.filter(
                class_assigned__courses__teacher_id=teacher,
                subject__courses__teacher_id=teacher
            ).distinct()

        return queryset.order_by('-academic_year__start_date', 'exam_type__display_order')

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish exam results"""
        exam = self.get_object()
        exam.is_published = True
        exam.save()
        return Response({
            'message': 'Exam results published successfully',
            'exam_id': str(exam.id),
            'is_published': True
        })

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """Lock exam to prevent further edits"""
        exam = self.get_object()
        exam.is_locked = True
        exam.save()
        return Response({
            'message': 'Exam locked successfully',
            'exam_id': str(exam.id),
            'is_locked': True
        })

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        """Unlock exam to allow edits"""
        exam = self.get_object()
        exam.is_locked = False
        exam.save()
        return Response({
            'message': 'Exam unlocked successfully',
            'exam_id': str(exam.id),
            'is_locked': False
        })

    @action(detail=False, methods=['get'], url_path='my-exams')
    def my_exams(self, request):
        """Get exams for the logged-in staff member's courses"""
        if not hasattr(request.user, 'profile'):
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

        teacher_id = request.user.profile.id
        courses = Course.objects.filter(teacher_id=teacher_id, is_active=True)

        # Get class-subject pairs from courses
        class_subject_pairs = [(c.class_assigned_id, c.subject_id) for c in courses]

        if not class_subject_pairs:
            return Response([])

        # Build query for matching exams
        query = Q()
        for class_id, subject_id in class_subject_pairs:
            query |= Q(class_assigned_id=class_id, subject_id=subject_id)

        exams = self.get_queryset().filter(query)
        serializer = ExamListSerializer(exams, many=True)
        return Response(serializer.data)


class StudentMarkViewSet(viewsets.ModelViewSet):
    """ViewSet for StudentMark management"""
    permission_classes = [IsAdminOrStaff]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudentMarkCreateUpdateSerializer
        return StudentMarkSerializer

    def get_queryset(self):
        queryset = StudentMark.objects.select_related(
            'exam', 'exam__exam_type', 'exam__class_assigned', 'exam__subject',
            'student', 'entered_by'
        ).all()

        exam = self.request.query_params.get('exam')
        student = self.request.query_params.get('student')
        class_id = self.request.query_params.get('class')

        if exam:
            queryset = queryset.filter(exam_id=exam)
        if student:
            queryset = queryset.filter(student_id=student)
        if class_id:
            queryset = queryset.filter(exam__class_assigned_id=class_id)

        return queryset.order_by('student__roll_number')

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Bulk create/update marks for an exam"""
        serializer = BulkMarksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam_id = serializer.validated_data['exam_id']
        marks_data = serializer.validated_data['marks']

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)

        entered_by = request.user.profile if hasattr(request.user, 'profile') else None
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for mark_entry in marks_data:
                student_id = mark_entry['student_id']
                marks_obtained = mark_entry.get('marks_obtained')
                is_absent = mark_entry.get('is_absent', False)
                remarks = mark_entry.get('remarks', '')

                # Validate marks
                if not is_absent and marks_obtained is not None:
                    if marks_obtained < 0 or marks_obtained > exam.max_marks:
                        continue  # Skip invalid marks

                mark, created = StudentMark.objects.update_or_create(
                    exam=exam,
                    student_id=student_id,
                    defaults={
                        'marks_obtained': marks_obtained if not is_absent else None,
                        'is_absent': is_absent,
                        'remarks': remarks,
                        'entered_by': entered_by
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        return Response({
            'message': 'Marks saved successfully',
            'created': created_count,
            'updated': updated_count
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='by-exam')
    def by_exam(self, request):
        """Get all marks for an exam with student list"""
        exam_id = request.query_params.get('exam_id')
        if not exam_id:
            return Response({'error': 'exam_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get all students in the class
        students = Student.objects.filter(
            current_class=exam.class_assigned, status='active'
        ).order_by('roll_number', 'first_name')

        # Get existing marks
        marks = StudentMark.objects.filter(exam=exam)
        marks_map = {str(m.student_id): m for m in marks}

        result = []
        for student in students:
            mark = marks_map.get(str(student.id))
            result.append({
                'student_id': str(student.id),
                'student_name': f"{student.first_name} {student.last_name}",
                'roll_number': student.roll_number,
                'marks_obtained': float(mark.marks_obtained) if mark and mark.marks_obtained else None,
                'is_absent': mark.is_absent if mark else False,
                'percentage': float(mark.percentage) if mark and mark.percentage else None,
                'grade': mark.grade if mark else '',
                'remarks': mark.remarks if mark else '',
                'mark_id': str(mark.id) if mark else None
            })

        # Calculate stats
        valid_marks = [r['marks_obtained'] for r in result if r['marks_obtained'] is not None]
        stats = {
            'total_students': len(result),
            'marks_entered': len(valid_marks),
            'pending': len(result) - len(valid_marks),
            'average': round(sum(valid_marks) / len(valid_marks), 2) if valid_marks else 0,
            'highest': max(valid_marks) if valid_marks else 0,
            'lowest': min(valid_marks) if valid_marks else 0
        }

        return Response({
            'exam_id': str(exam.id),
            'exam_name': exam.name,
            'class_name': exam.class_assigned.name,
            'subject_name': exam.subject.name,
            'max_marks': float(exam.max_marks),
            'passing_marks': float(exam.passing_marks) if exam.passing_marks else None,
            'stats': stats,
            'students': result
        })

    @action(detail=False, methods=['get'], url_path='analytics/class-performance')
    def class_performance(self, request):
        """Get class performance analytics"""
        class_id = request.query_params.get('class_id')
        academic_year = request.query_params.get('academic_year')
        subject = request.query_params.get('subject')
        exam_type = request.query_params.get('exam_type')

        if not class_id:
            return Response({'error': 'class_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get exams for the class
        exams = Exam.objects.filter(class_assigned_id=class_id, is_active=True)
        if academic_year:
            exams = exams.filter(academic_year_id=academic_year)
        if subject:
            exams = exams.filter(subject_id=subject)
        if exam_type:
            exams = exams.filter(exam_type_id=exam_type)

        # Get all marks for these exams
        marks = StudentMark.objects.filter(
            exam__in=exams,
            marks_obtained__isnull=False
        )

        if not marks.exists():
            return Response({
                'message': 'No marks found',
                'class_id': class_id,
                'total_students': 0,
                'average': 0,
                'highest': 0,
                'lowest': 0,
                'pass_percentage': 0,
                'grade_distribution': []
            })

        # Calculate stats
        stats = marks.aggregate(
            average=Avg('percentage'),
            highest=Max('percentage'),
            lowest=Min('percentage'),
            total=Count('id')
        )

        # Calculate pass percentage
        pass_count = marks.filter(percentage__gte=40).count()  # 40% as default pass mark
        pass_percentage = (pass_count / stats['total'] * 100) if stats['total'] > 0 else 0

        # Grade distribution
        grade_counts = marks.values('grade').annotate(count=Count('grade'))
        grade_distribution = [
            {'grade': g['grade'] or 'Ungraded', 'count': g['count']}
            for g in grade_counts
        ]

        try:
            class_obj = Class.objects.get(id=class_id)
            class_name = class_obj.name
        except Class.DoesNotExist:
            class_name = ''

        return Response({
            'class_id': class_id,
            'class_name': class_name,
            'total_students': marks.values('student').distinct().count(),
            'students_appeared': stats['total'],
            'average': round(stats['average'] or 0, 2),
            'highest': round(stats['highest'] or 0, 2),
            'lowest': round(stats['lowest'] or 0, 2),
            'pass_percentage': round(pass_percentage, 2),
            'grade_distribution': grade_distribution
        })

    @action(detail=False, methods=['get'], url_path='analytics/subject-comparison')
    def subject_comparison(self, request):
        """Get subject-wise comparison"""
        class_id = request.query_params.get('class_id')
        academic_year = request.query_params.get('academic_year')
        exam_type = request.query_params.get('exam_type')

        if not class_id:
            return Response({'error': 'class_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        exams = Exam.objects.filter(class_assigned_id=class_id, is_active=True)
        if academic_year:
            exams = exams.filter(academic_year_id=academic_year)
        if exam_type:
            exams = exams.filter(exam_type_id=exam_type)

        # Group by subject
        result = []
        subjects = Subject.objects.filter(exams__in=exams).distinct()

        for subject in subjects:
            subject_marks = StudentMark.objects.filter(
                exam__in=exams.filter(subject=subject),
                marks_obtained__isnull=False
            )

            if subject_marks.exists():
                stats = subject_marks.aggregate(
                    average=Avg('percentage'),
                    highest=Max('percentage'),
                    lowest=Min('percentage'),
                    count=Count('id')
                )

                result.append({
                    'subject_id': str(subject.id),
                    'subject_name': subject.name,
                    'average': round(stats['average'] or 0, 2),
                    'highest': round(stats['highest'] or 0, 2),
                    'lowest': round(stats['lowest'] or 0, 2),
                    'students_count': stats['count']
                })

        # Sort by average (descending)
        result.sort(key=lambda x: x['average'], reverse=True)

        return Response({
            'class_id': class_id,
            'subjects': result
        })

    @action(detail=False, methods=['get'], url_path='analytics/student-progress/(?P<student_id>[^/.]+)')
    def student_progress(self, request, student_id=None):
        """Get student progress over exams"""
        academic_year = request.query_params.get('academic_year')
        subject = request.query_params.get('subject')

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        marks = StudentMark.objects.filter(student=student).select_related(
            'exam', 'exam__exam_type', 'exam__subject'
        )

        if academic_year:
            marks = marks.filter(exam__academic_year_id=academic_year)
        if subject:
            marks = marks.filter(exam__subject_id=subject)

        marks = marks.order_by('exam__exam_type__display_order', 'exam__exam_date')

        exams_data = []
        for mark in marks:
            exams_data.append({
                'exam_id': str(mark.exam.id),
                'exam_name': mark.exam.name,
                'exam_type': mark.exam.exam_type.name,
                'subject': mark.exam.subject.name,
                'date': mark.exam.exam_date.isoformat() if mark.exam.exam_date else None,
                'marks_obtained': float(mark.marks_obtained) if mark.marks_obtained else None,
                'max_marks': float(mark.exam.max_marks),
                'percentage': float(mark.percentage) if mark.percentage else None,
                'grade': mark.grade,
                'is_absent': mark.is_absent
            })

        return Response({
            'student_id': str(student.id),
            'student_name': f"{student.first_name} {student.last_name}",
            'class_name': student.current_class.name if student.current_class else '',
            'exams': exams_data
        })

    @action(detail=False, methods=['get'], url_path='analytics/grade-distribution')
    def grade_distribution(self, request):
        """Get grade distribution for an exam or class"""
        exam_id = request.query_params.get('exam_id')
        class_id = request.query_params.get('class_id')
        academic_year = request.query_params.get('academic_year')

        marks = StudentMark.objects.filter(marks_obtained__isnull=False)

        if exam_id:
            marks = marks.filter(exam_id=exam_id)
        elif class_id:
            marks = marks.filter(exam__class_assigned_id=class_id)
            if academic_year:
                marks = marks.filter(exam__academic_year_id=academic_year)

        if not marks.exists():
            return Response({'grades': []})

        total = marks.count()
        grade_counts = marks.values('grade').annotate(count=Count('grade')).order_by('-count')

        distribution = []
        for g in grade_counts:
            distribution.append({
                'grade': g['grade'] or 'Ungraded',
                'count': g['count'],
                'percentage': round(g['count'] / total * 100, 2)
            })

        return Response({
            'total_students': total,
            'grades': distribution
        })


class MarkAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing mark audit logs"""
    queryset = MarkAuditLog.objects.all()
    serializer_class = MarkAuditLogSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        queryset = MarkAuditLog.objects.select_related(
            'student_mark', 'student_mark__student', 'student_mark__exam', 'changed_by'
        ).all()

        student_mark = self.request.query_params.get('student_mark')
        student = self.request.query_params.get('student')
        exam = self.request.query_params.get('exam')

        if student_mark:
            queryset = queryset.filter(student_mark_id=student_mark)
        if student:
            queryset = queryset.filter(student_mark__student_id=student)
        if exam:
            queryset = queryset.filter(student_mark__exam_id=exam)

        return queryset.order_by('-created_at')


# =============================================================================
# STUDENT ADMISSION WITH PARENT LINKING
# =============================================================================

class StudentAdmissionViewSet(viewsets.ViewSet):
    """
    ViewSet for student admission workflow.

    Creates student with auto-generated credentials and optionally creates
    parent accounts with auto-generated credentials as well.

    POST /api/academics/admissions/
    - Creates student, user account, and profile
    - Creates parent accounts with auto-generated credentials
    - Links parents to student via StudentParent junction
    - Returns all generated credentials for SMS notification
    """
    permission_classes = [IsAdminOrStaff]

    def create(self, request):
        """
        Process student admission with parent account creation.

        Request body:
        {
            "first_name": "Student First",
            "last_name": "Student Last",
            "date_of_birth": "2010-01-15",
            "gender": "male",
            "admission_number": "2024001",
            "admission_date": "2024-04-01",
            "current_class": "<class-uuid>",
            "academic_year": "<academic-year-uuid>",  // optional
            "roll_number": "01",  // optional
            "address_line1": "123 Main St",
            "city": "Korba",
            "state": "Chhattisgarh",
            "postal_code": "495677",
            "parents": [
                {
                    "first_name": "Parent First",
                    "last_name": "Parent Last",
                    "relation": "father",
                    "phone": "9876543210",
                    "email": "parent@email.com",
                    "occupation": "Engineer",
                    "is_primary_contact": true
                }
            ],
            "create_parent_accounts": true
        }

        Response (201):
        {
            "id": "<student-uuid>",
            "admission_number": "2024001",
            "full_name": "Student First Student Last",
            "student_credentials": {
                "username": "student_2024001",
                "password": "Abc12345",
                "must_change_password": true
            },
            "parent_credentials": [
                {
                    "parent_id": "<parent-uuid>",
                    "name": "Parent First Parent Last",
                    "relation": "father",
                    "phone": "9876543210",
                    "username": "parent_9876543210",
                    "password": "Xyz98765",
                    "existing_account": false
                }
            ]
        }
        """
        serializer = StudentAdmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        response_serializer = StudentAdmissionResponseSerializer(student)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# =============================================================================
# PHASE A: ACADEMIC STRUCTURE VIEWSETS
# =============================================================================

class SchoolSettingsViewSet(viewsets.ViewSet):
    """
    ViewSet for SchoolSettings management (Singleton pattern).

    Only one SchoolSettings instance exists per system.

    Endpoints:
    - GET /settings/ - Retrieve current settings
    - PATCH /settings/ - Update settings (admin only)

    No list, create, or delete operations.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get the current school settings (singleton).

        Returns the single SchoolSettings instance or creates it if it doesn't exist.
        """
        from .models import SchoolSettings
        from .serializers import SchoolSettingsSerializer

        settings, created = SchoolSettings.objects.get_or_create(
            pk=1,  # Singleton pattern with fixed primary key
            defaults={
                'admission_number_prefix': 'SVP',
                'default_section_capacity': 65,
            }
        )

        serializer = SchoolSettingsSerializer(settings)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """
        Update school settings (admin only).

        Requires admin/staff permissions.
        """
        from .models import SchoolSettings
        from .serializers import SchoolSettingsSerializer

        # Check admin permission
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admin users can update school settings'},
                status=status.HTTP_403_FORBIDDEN
            )

        settings, created = SchoolSettings.objects.get_or_create(pk=1)
        serializer = SchoolSettingsSerializer(
            settings,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class AcademicYearViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AcademicYear management with enhanced features.

    Provides full CRUD operations plus custom actions:
    - set_current: Mark this academic year as the current one

    Filters:
    - status: Filter by status (planning/active/completed)
    - is_current: Filter current academic year

    Default ordering: start_date descending (newest first)
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['start_date', 'end_date', 'name']

    def get_queryset(self):
        """
        Get academic years with filtering support.

        Query params:
        - status: planning/active/completed
        - is_current: true/false
        """
        from .models import AcademicYear

        queryset = AcademicYear.objects.all()

        # Apply filters
        status_filter = self.request.query_params.get('status', None)
        is_current = self.request.query_params.get('is_current', None)

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if is_current is not None:
            queryset = queryset.filter(is_current=is_current.lower() == 'true')

        return queryset.order_by('-start_date')

    def get_serializer_class(self):
        from .serializers import AcademicYearSerializer
        return AcademicYearSerializer

    def get_permissions(self):
        """
        Admin only for create/update/delete, authenticated for read.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrStaff()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='set-current')
    def set_current(self, request, pk=None):
        """
        Set this academic year as the current one.

        Unsets is_current on all other academic years.
        Requires admin permissions.
        """
        from .models import AcademicYear

        # Check admin permission
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admin users can set current academic year'},
                status=status.HTTP_403_FORBIDDEN
            )

        academic_year = self.get_object()

        with transaction.atomic():
            # Unset all other academic years
            AcademicYear.objects.filter(is_current=True).update(is_current=False)

            # Set this one as current
            academic_year.is_current = True
            academic_year.save()

        from .serializers import AcademicYearSerializer
        serializer = AcademicYearSerializer(academic_year)
        return Response({
            'message': f'Academic year {academic_year.name} set as current',
            'academic_year': serializer.data
        })


class GradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Grade management.

    Provides full CRUD operations plus custom actions:
    - clone: Clone grade structure to a new academic year

    Filters:
    - academic_year: Filter by academic year ID
    - number: Filter by grade number (1-12)

    List response includes section_count.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'number']
    ordering_fields = ['number', 'name']

    def get_queryset(self):
        """
        Get grades with filtering and section count annotation.

        Query params:
        - academic_year: Filter by academic year ID
        - number: Filter by grade number
        """
        from .models import Grade

        queryset = Grade.objects.annotate(
            section_count=Count('sections', distinct=True)
        ).all()

        # Apply filters
        academic_year = self.request.query_params.get('academic_year', None)
        number = self.request.query_params.get('number', None)

        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        if number:
            queryset = queryset.filter(number=number)

        return queryset.order_by('number')

    def get_serializer_class(self):
        from .serializers import GradeSerializer
        return GradeSerializer

    def get_permissions(self):
        """
        Admin only for create/update/delete, authenticated for read.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrStaff()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='clone')
    def clone(self, request, pk=None):
        """
        Clone this grade to a new academic year.

        Creates a copy of the grade with all its sections and settings
        for a new academic year.

        Request body:
        {
            "target_academic_year_id": "<uuid>",
            "include_sections": true,
            "include_subjects": true
        }

        Requires admin permissions.
        """
        from .models import Grade, Section, AcademicYear

        # Check admin permission
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admin users can clone grades'},
                status=status.HTTP_403_FORBIDDEN
            )

        grade = self.get_object()
        target_academic_year_id = request.data.get('target_academic_year_id')
        include_sections = request.data.get('include_sections', True)
        include_subjects = request.data.get('include_subjects', True)

        if not target_academic_year_id:
            return Response(
                {'error': 'target_academic_year_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_academic_year = AcademicYear.objects.get(id=target_academic_year_id)
        except AcademicYear.DoesNotExist:
            return Response(
                {'error': 'Target academic year not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            # Clone the grade
            new_grade = Grade.objects.create(
                number=grade.number,
                name=grade.name,
                academic_year=target_academic_year
            )

            # Clone subjects if requested
            if include_subjects:
                new_grade.subjects.set(grade.subjects.all())

            # Clone sections if requested
            sections_created = 0
            if include_sections:
                for section in grade.sections.all():
                    Section.objects.create(
                        grade=new_grade,
                        name=section.name,
                        capacity=section.capacity,
                        academic_year=target_academic_year
                        # Note: class_teacher is not cloned, must be assigned manually
                    )
                    sections_created += 1

        from .serializers import GradeSerializer
        serializer = GradeSerializer(new_grade)
        return Response({
            'message': f'Grade {grade.name} cloned successfully to {target_academic_year.name}',
            'grade': serializer.data,
            'sections_created': sections_created
        }, status=status.HTTP_201_CREATED)


class SectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Section management.

    Provides full CRUD operations plus custom actions:
    - assign_class_teacher: Assign or update class teacher for section

    Filters:
    - grade: Filter by grade ID
    - academic_year: Filter by academic year ID
    - class_teacher: Filter by class teacher ID

    List response includes:
    - student_count: Number of students enrolled
    - capacity_utilization: Percentage of capacity used
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'grade__name']
    ordering_fields = ['name', 'capacity', 'grade__number']

    def get_queryset(self):
        """
        Get sections with filtering and statistics.

        Query params:
        - grade: Filter by grade ID
        - academic_year: Filter by academic year ID
        - class_teacher: Filter by class teacher ID
        """
        from .models import Section

        queryset = Section.objects.select_related(
            'grade', 'academic_year', 'class_teacher'
        ).annotate(
            student_count=Count('students', distinct=True, filter=Q(students__status='active'))
        ).all()

        # Apply filters
        grade_id = self.request.query_params.get('grade', None)
        academic_year = self.request.query_params.get('academic_year', None)
        class_teacher = self.request.query_params.get('class_teacher', None)

        if grade_id:
            queryset = queryset.filter(grade_id=grade_id)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        if class_teacher:
            queryset = queryset.filter(class_teacher_id=class_teacher)

        return queryset.order_by('grade__number', 'name')

    def get_serializer_class(self):
        from .serializers import SectionSerializer
        return SectionSerializer

    def get_permissions(self):
        """
        Admin only for create/update/delete, authenticated for read.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrStaff()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='assign-class-teacher')
    def assign_class_teacher(self, request, pk=None):
        """
        Assign or update the class teacher for this section.

        Request body:
        {
            "class_teacher_id": "<uuid>"  // UserProfile ID with teacher role
        }

        To remove class teacher, send null or omit class_teacher_id.
        Requires admin permissions.
        """
        from .models import Section
        from accounts.models import UserProfile

        # Check admin permission
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admin users can assign class teachers'},
                status=status.HTTP_403_FORBIDDEN
            )

        section = self.get_object()
        class_teacher_id = request.data.get('class_teacher_id')

        if class_teacher_id:
            try:
                class_teacher = UserProfile.objects.get(id=class_teacher_id)

                # Validate teacher role
                if class_teacher.role not in ['school_staff', 'school_admin', 'teacher']:
                    return Response(
                        {'error': 'Selected user does not have a teacher role'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                section.class_teacher = class_teacher
                section.save()

                message = f'Class teacher {class_teacher.full_name} assigned to {section.grade.name}-{section.name}'
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'Class teacher not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Remove class teacher
            section.class_teacher = None
            section.save()
            message = f'Class teacher removed from {section.grade.name}-{section.name}'

        from .serializers import SectionSerializer
        serializer = SectionSerializer(section)
        return Response({
            'message': message,
            'section': serializer.data
        })
# This file contains Phase B ViewSets to be merged into views.py
# Append this content to the end of academics/views.py

# =============================================================================
# PHASE B: STUDENT CORE VIEWSETS (Enrollment & Photo Management)
# =============================================================================

class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentEnrollment management.

    Provides full CRUD operations plus custom actions:
    - promote: Move student to next grade
    - transfer_section: Move student within same grade
    - withdraw: Mark student as withdrawn

    Filters:
    - student: Filter by student ID
    - section: Filter by section ID
    - academic_year: Filter by academic year ID
    - is_current: Filter current enrollments
    - status: Filter by enrollment status

    Permissions:
    - Read: Authenticated users
    - Write: Admin only
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']
    ordering_fields = ['enrolled_date', 'roll_number', 'created_at']

    def get_serializer_class(self):
        from .serializers import StudentEnrollmentSerializer, StudentEnrollmentCreateSerializer
        if self.action == 'create':
            return StudentEnrollmentCreateSerializer
        return StudentEnrollmentSerializer

    def get_queryset(self):
        from .models import StudentEnrollment

        queryset = StudentEnrollment.objects.select_related(
            'student', 'section', 'section__grade', 'academic_year', 'enrolled_by'
        ).all()

        # Apply filters
        student_id = self.request.query_params.get('student', None)
        section_id = self.request.query_params.get('section', None)
        academic_year_id = self.request.query_params.get('academic_year', None)
        is_current = self.request.query_params.get('is_current', None)
        status_filter = self.request.query_params.get('status', None)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if is_current is not None:
            queryset = queryset.filter(is_current=is_current.lower() == 'true')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-academic_year__start_date', 'section', 'roll_number')

    def get_permissions(self):
        """Admin only for create/update/delete, authenticated for read"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'promote', 'transfer_section', 'withdraw']:
            return [IsAdminOrStaff()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        """Prevent direct deletion - use withdraw action instead"""
        return Response(
            {'error': 'Cannot delete enrollments. Use the withdraw action instead.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'], url_path='promote')
    def promote(self, request, pk=None):
        """
        Promote student to next grade.

        Request body:
        {
            "target_section_id": "<uuid>",  // Section in next grade
            "target_academic_year_id": "<uuid>",  // Next academic year
            "roll_number": 5,  // Optional: roll number in new section
            "enrolled_date": "2026-06-01"  // Optional: enrollment date
        }

        Requires admin permissions.
        """
        from .models import StudentEnrollment, Section, AcademicYear
        from datetime import date

        enrollment = self.get_object()
        target_section_id = request.data.get('target_section_id')
        target_academic_year_id = request.data.get('target_academic_year_id')
        roll_number = request.data.get('roll_number')
        enrolled_date = request.data.get('enrolled_date', date.today().isoformat())

        if not target_section_id or not target_academic_year_id:
            return Response(
                {'error': 'target_section_id and target_academic_year_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_section = Section.objects.get(id=target_section_id)
            target_academic_year = AcademicYear.objects.get(id=target_academic_year_id)
        except (Section.DoesNotExist, AcademicYear.DoesNotExist) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            # Mark current enrollment as promoted
            enrollment.status = 'promoted'
            enrollment.is_current = False
            enrollment.exit_date = date.today()
            enrollment.save()

            # Create new enrollment
            new_enrollment = StudentEnrollment.objects.create(
                student=enrollment.student,
                section=target_section,
                academic_year=target_academic_year,
                roll_number=roll_number,
                enrolled_date=enrolled_date,
                status='active',
                is_current=True,
                enrolled_by=request.user.profile if hasattr(request.user, 'profile') else None
            )

            # Update student's current_section
            enrollment.student.current_section = target_section
            enrollment.student.academic_year = target_academic_year
            enrollment.student.save(update_fields=['current_section', 'academic_year'])

        from .serializers import StudentEnrollmentSerializer
        serializer = StudentEnrollmentSerializer(new_enrollment)
        return Response({
            'message': f'Student promoted to {target_section.full_name}',
            'enrollment': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='transfer-section')
    def transfer_section(self, request, pk=None):
        """
        Transfer student to a different section within the same grade.

        Request body:
        {
            "target_section_id": "<uuid>",  // New section (same grade)
            "roll_number": 5,  // Optional: roll number in new section
            "reason": "Section merge"  // Optional: transfer reason
        }

        Requires admin permissions.
        """
        from .models import StudentEnrollment, Section
        from datetime import date

        enrollment = self.get_object()
        target_section_id = request.data.get('target_section_id')
        roll_number = request.data.get('roll_number')
        reason = request.data.get('reason', '')

        if not target_section_id:
            return Response(
                {'error': 'target_section_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_section = Section.objects.get(id=target_section_id)
        except Section.DoesNotExist:
            return Response(
                {'error': 'Target section not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate same grade
        if target_section.grade != enrollment.section.grade:
            return Response(
                {'error': 'Target section must be in the same grade. Use promote action for different grades.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Mark current enrollment as transferred
            enrollment.status = 'transferred'
            enrollment.is_current = False
            enrollment.exit_date = date.today()
            enrollment.notes = f"{enrollment.notes}\nTransferred to {target_section.full_name}. Reason: {reason}".strip()
            enrollment.save()

            # Create new enrollment
            new_enrollment = StudentEnrollment.objects.create(
                student=enrollment.student,
                section=target_section,
                academic_year=enrollment.academic_year,
                roll_number=roll_number,
                enrolled_date=date.today(),
                status='active',
                is_current=True,
                enrolled_by=request.user.profile if hasattr(request.user, 'profile') else None,
                notes=f"Transferred from {enrollment.section.full_name}. Reason: {reason}"
            )

            # Update student's current_section
            enrollment.student.current_section = target_section
            enrollment.student.save(update_fields=['current_section'])

        from .serializers import StudentEnrollmentSerializer
        serializer = StudentEnrollmentSerializer(new_enrollment)
        return Response({
            'message': f'Student transferred to {target_section.full_name}',
            'enrollment': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='withdraw')
    def withdraw(self, request, pk=None):
        """
        Mark student enrollment as withdrawn.

        Request body:
        {
            "reason": "Family relocation",  // Optional: withdrawal reason
            "exit_date": "2026-03-15"  // Optional: withdrawal date (defaults to today)
        }

        Requires admin permissions.
        """
        from datetime import date

        enrollment = self.get_object()
        reason = request.data.get('reason', '')
        exit_date_str = request.data.get('exit_date')

        if exit_date_str:
            try:
                exit_date = date.fromisoformat(exit_date_str)
            except ValueError:
                return Response(
                    {'error': 'Invalid exit_date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            exit_date = date.today()

        with transaction.atomic():
            enrollment.status = 'withdrawn'
            enrollment.is_current = False
            enrollment.exit_date = exit_date
            enrollment.notes = f"{enrollment.notes}\nWithdrawn. Reason: {reason}".strip()
            enrollment.save()

            # Update student status
            enrollment.student.status = 'inactive'
            enrollment.student.current_section = None
            enrollment.student.save(update_fields=['status', 'current_section'])

        from .serializers import StudentEnrollmentSerializer
        serializer = StudentEnrollmentSerializer(enrollment)
        return Response({
            'message': 'Student enrollment marked as withdrawn',
            'enrollment': serializer.data
        })


class StudentPhotoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentPhoto management with approval workflow.

    Provides full CRUD operations plus custom actions:
    - approve: Admin approves photo, sets as current
    - reject: Admin rejects photo with reason
    - expire_old: Batch expire photos from previous years
    - pending_approval: List all pending photos for admin queue

    Filters:
    - student: Filter by student ID
    - status: Filter by approval status
    - academic_year: Filter by academic year ID
    - is_current: Filter current photos

    Permissions:
    - Read: Authenticated users
    - Upload: Admin or Teacher assigned to student's section
    - Approve/Reject: Admin only
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']
    ordering_fields = ['uploaded_at', 'approved_at']

    def get_serializer_class(self):
        from .serializers import StudentPhotoSerializer, StudentPhotoUploadSerializer
        if self.action == 'create':
            return StudentPhotoUploadSerializer
        return StudentPhotoSerializer

    def get_queryset(self):
        from .models import StudentPhoto

        queryset = StudentPhoto.objects.select_related(
            'student', 'academic_year', 'uploaded_by', 'approved_by'
        ).all()

        # Apply filters
        student_id = self.request.query_params.get('student', None)
        status_filter = self.request.query_params.get('status', None)
        academic_year_id = self.request.query_params.get('academic_year', None)
        is_current = self.request.query_params.get('is_current', None)

        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if is_current is not None:
            queryset = queryset.filter(is_current=is_current.lower() == 'true')

        return queryset.order_by('-uploaded_at')

    def get_permissions(self):
        """
        Permissions:
        - Read: Authenticated
        - Create: Admin or Teacher
        - Approve/Reject/Expire: Admin only
        """
        if self.action in ['approve', 'reject', 'expire_old', 'pending_approval']:
            return [IsAdminOrStaff()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrStaff()]  # Can be refined later for teachers
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approve student photo and set as current.

        Requires admin permissions.
        """
        from datetime import datetime

        photo = self.get_object()

        if photo.status == 'approved':
            return Response(
                {'error': 'Photo is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            photo.status = 'approved'
            photo.is_current = True
            photo.approved_by = request.user.profile if hasattr(request.user, 'profile') else None
            photo.approved_at = datetime.now()
            photo.save()

            # Update student's photo field (for backward compatibility)
            photo.student.photo = photo.image
            photo.student.save(update_fields=['photo'])

        from .serializers import StudentPhotoSerializer
        serializer = StudentPhotoSerializer(photo)
        return Response({
            'message': 'Photo approved and set as current',
            'photo': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        Reject student photo with reason.

        Request body:
        {
            "reason": "Photo quality is poor"
        }

        Requires admin permissions.
        """
        from datetime import datetime

        photo = self.get_object()
        reason = request.data.get('reason', '')

        if not reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if photo.status == 'rejected':
            return Response(
                {'error': 'Photo is already rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        photo.status = 'rejected'
        photo.is_current = False
        photo.rejection_reason = reason
        photo.approved_by = request.user.profile if hasattr(request.user, 'profile') else None
        photo.approved_at = datetime.now()
        photo.save()

        from .serializers import StudentPhotoSerializer
        serializer = StudentPhotoSerializer(photo)
        return Response({
            'message': 'Photo rejected',
            'photo': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='expire-old')
    def expire_old(self, request):
        """
        Batch expire photos from previous academic years.

        Request body:
        {
            "academic_year_id": "<uuid>",  // Optional: expire photos before this year
            "exclude_current": true  // Optional: keep is_current photos (default: true)
        }

        Requires admin permissions.
        """
        from .models import StudentPhoto, AcademicYear

        academic_year_id = request.data.get('academic_year_id')
        exclude_current = request.data.get('exclude_current', True)

        queryset = StudentPhoto.objects.filter(status='approved')

        if exclude_current:
            queryset = queryset.filter(is_current=False)

        if academic_year_id:
            try:
                academic_year = AcademicYear.objects.get(id=academic_year_id)
                # Expire all photos from years before the specified year
                queryset = queryset.filter(
                    academic_year__start_date__lt=academic_year.start_date
                )
            except AcademicYear.DoesNotExist:
                return Response(
                    {'error': 'Academic year not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        updated_count = queryset.update(status='expired')

        return Response({
            'message': f'Expired {updated_count} photos',
            'count': updated_count
        })

    @action(detail=False, methods=['get'], url_path='pending-approval')
    def pending_approval(self, request):
        """
        Get all photos pending approval (admin queue).

        Returns photos with status='pending' ordered by upload date.

        Requires admin permissions.
        """
        from .models import StudentPhoto

        pending_photos = StudentPhoto.objects.filter(
            status='pending'
        ).select_related(
            'student', 'academic_year', 'uploaded_by'
        ).order_by('uploaded_at')

        from .serializers import StudentPhotoSerializer
        serializer = StudentPhotoSerializer(pending_photos, many=True)

        return Response({
            'count': pending_photos.count(),
            'photos': serializer.data
        })


# =============================================================================
# EXTENDED STUDENT VIEWSET (Phase B Actions)
# =============================================================================

# Add these custom actions to the existing StudentViewSet by creating a mixin
# that can be applied to StudentViewSet

class StudentPhotoMixin:
    """Mixin to add photo-related actions to StudentViewSet"""

    @action(detail=True, methods=['post'], url_path='upload-photo')
    def upload_photo(self, request, pk=None):
        """
        Shortcut to upload photo for a student.

        Request body (multipart/form-data):
        {
            "image": <file>,
            "academic_year_id": "<uuid>"  // Optional: defaults to current academic year
        }

        Requires admin or teacher permissions.
        """
        from .models import StudentPhoto
        from .serializers import StudentPhotoUploadSerializer, get_current_academic_year

        student = self.get_object()
        academic_year_id = request.data.get('academic_year_id')

        if not academic_year_id:
            academic_year = get_current_academic_year()
            academic_year_id = academic_year.id

        # Prepare data for serializer
        data = {
            'student': str(student.id),
            'academic_year': str(academic_year_id),
            'image': request.data.get('image')
        }

        serializer = StudentPhotoUploadSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()

        from .serializers import StudentPhotoSerializer
        response_serializer = StudentPhotoSerializer(photo)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='enrollment-history')
    def enrollment_history(self, request, pk=None):
        """
        Get student's complete enrollment history across all academic years.

        Returns all StudentEnrollment records for this student.
        """
        from .models import StudentEnrollment
        from .serializers import StudentEnrollmentSerializer

        student = self.get_object()
        enrollments = StudentEnrollment.objects.filter(
            student=student
        ).select_related(
            'section', 'section__grade', 'academic_year'
        ).order_by('-academic_year__start_date')

        serializer = StudentEnrollmentSerializer(enrollments, many=True)
        return Response({
            'student_id': str(student.id),
            'student_name': f"{student.first_name} {student.last_name}",
            'enrollment_history': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='generate-admission-number')
    def generate_admission_number(self, request):
        """
        Generate next admission number based on school settings.

        Request body:
        {
            "year": 2026  // Optional: year for admission number (defaults to current year)
        }

        Returns:
        {
            "admission_number": "SVP26001"
        }

        Requires admin permissions.
        """
        from .models import SchoolSettings, Student
        from datetime import datetime

        # Get year from request or use current year
        year = request.data.get('year')
        if not year:
            year = datetime.now().year

        # Get school settings
        settings = SchoolSettings.objects.first()
        prefix = settings.admission_number_prefix if settings else 'SVP'

        # Get last admission number for this year
        year_prefix = f"{prefix}{str(year)[-2:]}"
        last_student = Student.objects.filter(
            admission_number__startswith=year_prefix
        ).order_by('admission_number').last()

        if last_student:
            # Extract sequence number and increment
            try:
                last_sequence = int(last_student.admission_number[len(year_prefix):])
                next_sequence = last_sequence + 1
            except (ValueError, IndexError):
                next_sequence = 1
        else:
            next_sequence = 1

        admission_number = f"{year_prefix}{next_sequence:03d}"

        return Response({
            'admission_number': admission_number,
            'prefix': prefix,
            'year': year,
            'sequence': next_sequence
        })


# Apply the mixin to existing StudentViewSet
# This can be done by modifying the StudentViewSet class definition to include the mixin:
# class StudentViewSet(StudentPhotoMixin, viewsets.ModelViewSet):
#     ...


# =============================================================================
# PHASE C: TEACHER ASSIGNMENT VIEWSETS
# =============================================================================

class ClassTeacherViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ClassTeacher assignment management.

    Provides full CRUD operations plus custom actions:
    - by_section: List class teachers grouped by section
    - unassigned_sections: Sections without a primary class teacher

    Filters:
    - academic_year: Filter by academic year ID
    - section: Filter by section ID
    - grade: Filter by section's grade ID
    - teacher: Filter by teacher ID
    - is_primary: Filter by is_primary status (true/false)

    Permissions:
    - Authenticated users for all operations
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['teacher__first_name', 'teacher__last_name', 'section__name']
    ordering_fields = ['section__grade__display_order', 'section__name', 'assigned_at']

    def get_serializer_class(self):
        from .serializers import (
            ClassTeacherListSerializer,
            ClassTeacherDetailSerializer,
            ClassTeacherCreateSerializer
        )
        if self.action == 'list':
            return ClassTeacherListSerializer
        elif self.action == 'retrieve':
            return ClassTeacherDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClassTeacherCreateSerializer
        return ClassTeacherListSerializer

    def get_queryset(self):
        from .models import ClassTeacher

        queryset = ClassTeacher.objects.select_related(
            'section', 'section__grade', 'teacher', 'teacher__user',
            'academic_year', 'assigned_by'
        ).all()

        # Apply filters
        academic_year_id = self.request.query_params.get('academic_year', None)
        section_id = self.request.query_params.get('section', None)
        grade_id = self.request.query_params.get('grade', None)
        teacher_id = self.request.query_params.get('teacher', None)
        is_primary = self.request.query_params.get('is_primary', None)

        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if grade_id:
            queryset = queryset.filter(section__grade_id=grade_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if is_primary is not None:
            queryset = queryset.filter(is_primary=is_primary.lower() == 'true')

        return queryset.order_by('section__grade__display_order', 'section__name', '-is_primary')

    @action(detail=False, methods=['get'], url_path='by-section')
    def by_section(self, request):
        """
        List class teachers grouped by section for an academic year.

        Query params:
        - academic_year: Academic year ID (required)

        Returns:
        {
            "academic_year": "<uuid>",
            "sections": [
                {
                    "section_id": "<uuid>",
                    "section_name": "5A",
                    "grade_number": 5,
                    "primary_teacher": {...},
                    "assistant_teachers": [...]
                },
                ...
            ]
        }
        """
        from .models import ClassTeacher, AcademicYear, Section
        from .serializers import get_current_academic_year

        academic_year_id = request.query_params.get('academic_year')

        if not academic_year_id:
            academic_year = get_current_academic_year()
            academic_year_id = academic_year.id
        else:
            try:
                academic_year = AcademicYear.objects.get(id=academic_year_id)
            except AcademicYear.DoesNotExist:
                return Response(
                    {'error': 'Academic year not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Get all sections for this academic year
        sections = Section.objects.filter(
            academic_year=academic_year,
            is_active=True
        ).select_related('grade').order_by('grade__display_order', 'name')

        result_sections = []
        for section in sections:
            # Get primary class teacher
            primary_assignment = ClassTeacher.objects.filter(
                section=section,
                academic_year=academic_year,
                is_primary=True
            ).select_related('teacher', 'teacher__user').first()

            # Get assistant class teachers
            assistant_assignments = ClassTeacher.objects.filter(
                section=section,
                academic_year=academic_year,
                is_primary=False
            ).select_related('teacher', 'teacher__user')

            section_data = {
                'section_id': str(section.id),
                'section_name': section.name,
                'section_full_name': section.full_name,
                'grade_number': section.grade.number,
                'grade_name': section.grade.name,
                'primary_teacher': None,
                'assistant_teachers': []
            }

            if primary_assignment:
                section_data['primary_teacher'] = {
                    'assignment_id': str(primary_assignment.id),
                    'teacher_id': str(primary_assignment.teacher.id),
                    'teacher_name': primary_assignment.teacher.full_name,
                    'teacher_email': primary_assignment.teacher.user.email if primary_assignment.teacher.user else None,
                    'assigned_at': primary_assignment.assigned_at,
                }

            section_data['assistant_teachers'] = [{
                'assignment_id': str(assignment.id),
                'teacher_id': str(assignment.teacher.id),
                'teacher_name': assignment.teacher.full_name,
                'teacher_email': assignment.teacher.user.email if assignment.teacher.user else None,
                'assigned_at': assignment.assigned_at,
            } for assignment in assistant_assignments]

            result_sections.append(section_data)

        return Response({
            'academic_year_id': str(academic_year.id),
            'academic_year_name': academic_year.name,
            'sections': result_sections
        })

    @action(detail=False, methods=['get'], url_path='unassigned-sections')
    def unassigned_sections(self, request):
        """
        Get sections without a primary class teacher.

        Query params:
        - academic_year: Academic year ID (optional, defaults to current)

        Returns:
        {
            "academic_year": "<uuid>",
            "unassigned_sections": [
                {
                    "section_id": "<uuid>",
                    "section_name": "5B",
                    "grade_number": 5,
                    "has_assistant": false
                },
                ...
            ]
        }
        """
        from .models import ClassTeacher, AcademicYear, Section
        from .serializers import get_current_academic_year

        academic_year_id = request.query_params.get('academic_year')

        if not academic_year_id:
            academic_year = get_current_academic_year()
            academic_year_id = academic_year.id
        else:
            try:
                academic_year = AcademicYear.objects.get(id=academic_year_id)
            except AcademicYear.DoesNotExist:
                return Response(
                    {'error': 'Academic year not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Get all sections for this academic year
        all_sections = Section.objects.filter(
            academic_year=academic_year,
            is_active=True
        ).select_related('grade')

        # Get sections with primary class teachers
        sections_with_primary = ClassTeacher.objects.filter(
            academic_year=academic_year,
            is_primary=True
        ).values_list('section_id', flat=True)

        # Filter sections without primary class teacher
        unassigned_sections = all_sections.exclude(id__in=sections_with_primary)

        result = []
        for section in unassigned_sections:
            # Check if section has any assistant class teachers
            has_assistant = ClassTeacher.objects.filter(
                section=section,
                academic_year=academic_year,
                is_primary=False
            ).exists()

            result.append({
                'section_id': str(section.id),
                'section_name': section.name,
                'section_full_name': section.full_name,
                'grade_number': section.grade.number,
                'grade_name': section.grade.name,
                'capacity': section.capacity,
                'current_strength': section.current_strength,
                'has_assistant': has_assistant
            })

        return Response({
            'academic_year_id': str(academic_year.id),
            'academic_year_name': academic_year.name,
            'count': len(result),
            'unassigned_sections': result
        })


class SubjectTeacherViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SubjectTeacher assignment management.

    Provides full CRUD operations plus custom actions:
    - by_teacher: Group assignments by teacher (teacher's schedule)
    - by_subject: Group assignments by subject across sections
    - toggle_active: Toggle is_active status

    Filters:
    - academic_year: Filter by academic year ID
    - section: Filter by section ID
    - grade: Filter by section's grade ID
    - subject: Filter by subject ID
    - teacher: Filter by teacher ID
    - is_active: Filter by is_active status (true/false)

    Permissions:
    - Authenticated users for all operations
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'teacher__first_name', 'teacher__last_name',
        'subject__name', 'subject__code',
        'section__name'
    ]
    ordering_fields = ['section__grade__display_order', 'section__name', 'subject__name', 'assigned_at']

    def get_serializer_class(self):
        from .serializers import (
            SubjectTeacherListSerializer,
            SubjectTeacherDetailSerializer,
            SubjectTeacherCreateSerializer
        )
        if self.action == 'list':
            return SubjectTeacherListSerializer
        elif self.action == 'retrieve':
            return SubjectTeacherDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SubjectTeacherCreateSerializer
        return SubjectTeacherListSerializer

    def get_queryset(self):
        from .models import SubjectTeacher

        queryset = SubjectTeacher.objects.select_related(
            'section', 'section__grade', 'subject', 'teacher', 'teacher__user',
            'academic_year', 'assigned_by'
        ).all()

        # Apply filters
        academic_year_id = self.request.query_params.get('academic_year', None)
        section_id = self.request.query_params.get('section', None)
        grade_id = self.request.query_params.get('grade', None)
        subject_id = self.request.query_params.get('subject', None)
        teacher_id = self.request.query_params.get('teacher', None)
        is_active = self.request.query_params.get('is_active', None)

        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if grade_id:
            queryset = queryset.filter(section__grade_id=grade_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('section__grade__display_order', 'section__name', 'subject__name')

    @action(detail=False, methods=['get'], url_path='by-teacher')
    def by_teacher(self, request):
        """
        Group subject assignments by teacher (teacher's schedule view).

        Query params:
        - academic_year: Academic year ID (optional, defaults to current)
        - teacher: Teacher ID (optional, to filter specific teacher)

        Returns:
        {
            "academic_year": "<uuid>",
            "teachers": [
                {
                    "teacher_id": "<uuid>",
                    "teacher_name": "John Doe",
                    "total_assignments": 5,
                    "total_periods": 25,
                    "subjects": [
                        {
                            "assignment_id": "<uuid>",
                            "subject_name": "Mathematics",
                            "section_name": "5A",
                            "periods_per_week": 5
                        },
                        ...
                    ]
                },
                ...
            ]
        }
        """
        from .models import SubjectTeacher, AcademicYear
        from .serializers import get_current_academic_year
        from collections import defaultdict

        academic_year_id = request.query_params.get('academic_year')
        teacher_id = request.query_params.get('teacher')

        if not academic_year_id:
            academic_year = get_current_academic_year()
            academic_year_id = academic_year.id
        else:
            try:
                academic_year = AcademicYear.objects.get(id=academic_year_id)
            except AcademicYear.DoesNotExist:
                return Response(
                    {'error': 'Academic year not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Get all subject assignments for this academic year
        queryset = SubjectTeacher.objects.filter(
            academic_year=academic_year,
            is_active=True
        ).select_related('teacher', 'teacher__user', 'subject', 'section', 'section__grade')

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)

        # Group by teacher
        teacher_assignments = defaultdict(list)
        for assignment in queryset:
            teacher_assignments[assignment.teacher].append(assignment)

        # Build result
        result = []
        for teacher, assignments in teacher_assignments.items():
            total_periods = sum(
                assignment.periods_per_week or 0
                for assignment in assignments
            )

            teacher_data = {
                'teacher_id': str(teacher.id),
                'teacher_name': teacher.full_name,
                'teacher_email': teacher.user.email if teacher.user else None,
                'total_assignments': len(assignments),
                'total_periods': total_periods,
                'subjects': [{
                    'assignment_id': str(assignment.id),
                    'subject_id': str(assignment.subject.id),
                    'subject_name': assignment.subject.name,
                    'subject_code': assignment.subject.code,
                    'section_id': str(assignment.section.id),
                    'section_name': assignment.section.name,
                    'section_full_name': assignment.section.full_name,
                    'grade_number': assignment.section.grade.number,
                    'periods_per_week': assignment.periods_per_week,
                } for assignment in sorted(assignments, key=lambda a: (a.section.grade.display_order, a.section.name, a.subject.name))]
            }

            result.append(teacher_data)

        # Sort teachers by name
        result.sort(key=lambda t: t['teacher_name'])

        return Response({
            'academic_year_id': str(academic_year.id),
            'academic_year_name': academic_year.name,
            'count': len(result),
            'teachers': result
        })

    @action(detail=False, methods=['get'], url_path='by-subject')
    def by_subject(self, request):
        """
        Group subject assignments by subject across sections.

        Query params:
        - academic_year: Academic year ID (optional, defaults to current)
        - subject: Subject ID (optional, to filter specific subject)

        Returns:
        {
            "academic_year": "<uuid>",
            "subjects": [
                {
                    "subject_id": "<uuid>",
                    "subject_name": "Mathematics",
                    "subject_code": "MATH",
                    "total_sections": 3,
                    "sections": [
                        {
                            "assignment_id": "<uuid>",
                            "section_name": "5A",
                            "teacher_name": "John Doe",
                            "periods_per_week": 5
                        },
                        ...
                    ]
                },
                ...
            ]
        }
        """
        from .models import SubjectTeacher, AcademicYear
        from .serializers import get_current_academic_year
        from collections import defaultdict

        academic_year_id = request.query_params.get('academic_year')
        subject_id = request.query_params.get('subject')

        if not academic_year_id:
            academic_year = get_current_academic_year()
            academic_year_id = academic_year.id
        else:
            try:
                academic_year = AcademicYear.objects.get(id=academic_year_id)
            except AcademicYear.DoesNotExist:
                return Response(
                    {'error': 'Academic year not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Get all subject assignments for this academic year
        queryset = SubjectTeacher.objects.filter(
            academic_year=academic_year,
            is_active=True
        ).select_related('subject', 'section', 'section__grade', 'teacher', 'teacher__user')

        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        # Group by subject
        subject_assignments = defaultdict(list)
        for assignment in queryset:
            subject_assignments[assignment.subject].append(assignment)

        # Build result
        result = []
        for subject, assignments in subject_assignments.items():
            subject_data = {
                'subject_id': str(subject.id),
                'subject_name': subject.name,
                'subject_code': subject.code,
                'total_sections': len(assignments),
                'sections': [{
                    'assignment_id': str(assignment.id),
                    'section_id': str(assignment.section.id),
                    'section_name': assignment.section.name,
                    'section_full_name': assignment.section.full_name,
                    'grade_number': assignment.section.grade.number,
                    'teacher_id': str(assignment.teacher.id),
                    'teacher_name': assignment.teacher.full_name,
                    'teacher_email': assignment.teacher.user.email if assignment.teacher.user else None,
                    'periods_per_week': assignment.periods_per_week,
                } for assignment in sorted(assignments, key=lambda a: (a.section.grade.display_order, a.section.name))]
            }

            result.append(subject_data)

        # Sort subjects by name
        result.sort(key=lambda s: s['subject_name'])

        return Response({
            'academic_year_id': str(academic_year.id),
            'academic_year_name': academic_year.name,
            'count': len(result),
            'subjects': result
        })

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """
        Toggle the is_active status of a subject teacher assignment.

        Returns:
        {
            "assignment_id": "<uuid>",
            "is_active": true,
            "message": "Assignment activated"
        }
        """
        assignment = self.get_object()

        # Toggle is_active
        assignment.is_active = not assignment.is_active
        assignment.save(update_fields=['is_active', 'updated_at'])

        status_message = "activated" if assignment.is_active else "deactivated"

        return Response({
            'assignment_id': str(assignment.id),
            'is_active': assignment.is_active,
            'message': f'Assignment {status_message} successfully'
        })
