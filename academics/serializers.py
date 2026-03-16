"""
Serializers for Academics App - Students, Classes, Academic Years
"""

from datetime import datetime
from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction, models as django_models
from accounts.models import UserProfile
from accounts.utils import generate_username, generate_password
from .models import (
    AcademicYear, Class, Student, Parent, StudentParent, Subject, Course,
    AttendanceSession, Attendance, AttendanceSettings,
    ExamType, Exam, GradingScale, GradeRange, StudentMark, MarkAuditLog,
    # Phase A models
    SchoolSettings, Grade, Section,
    # Phase B models
    StudentEnrollment, StudentPhoto,
    # Phase C models
    ClassTeacher, SubjectTeacher
)


class AcademicYearSerializer(serializers.ModelSerializer):
    """Serializer for AcademicYear model"""
    class Meta:
        model = AcademicYear
        fields = [
            'id', 'name', 'start_date', 'end_date',
            'is_current', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class model"""
    class_teacher_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = [
            'id', 'name', 'grade', 'section', 'class_teacher',
            'class_teacher_name', 'room_number', 'capacity',
            'student_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_class_teacher_name(self, obj):
        if obj.class_teacher:
            return obj.class_teacher.full_name
        return None

    def get_student_count(self, obj):
        return obj.students.filter(status='active').count()


class StudentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing students"""
    class_name = serializers.CharField(source='current_class.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'first_name', 'last_name',
            'full_name', 'username', 'current_class', 'class_name',
            'academic_year', 'academic_year_name', 'gender', 'status',
            'photo', 'created_at'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_username(self, obj):
        if obj.user_profile and obj.user_profile.user:
            return obj.user_profile.user.username
        return None


class StudentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for student with all fields"""
    class_name = serializers.CharField(source='current_class.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    must_change_password = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'first_name', 'last_name',
            'full_name', 'username', 'email', 'date_of_birth', 'gender',
            'phone', 'current_class', 'class_name', 'academic_year', 'academic_year_name',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code',
            'admission_date', 'blood_group', 'photo', 'status',
            'must_change_password', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_username(self, obj):
        if obj.user_profile and obj.user_profile.user:
            return obj.user_profile.user.username
        return None

    def get_email(self, obj):
        if obj.user_profile and obj.user_profile.user:
            return obj.user_profile.user.email
        return obj.email

    def get_must_change_password(self, obj):
        if obj.user_profile:
            return obj.user_profile.must_change_password
        return False


def get_current_academic_year():
    """
    Get or create the current academic year based on current date.
    Format: YYYY-YYYY+1 (e.g., 2026-2027)
    """
    today = datetime.now().date()
    # Academic year typically starts in April/June in India
    # If current month >= June, use current year, else previous year
    if today.month >= 6:
        start_year = today.year
    else:
        start_year = today.year - 1

    end_year = start_year + 1
    year_name = f"{start_year}-{end_year}"

    # Try to get existing academic year
    academic_year = AcademicYear.objects.filter(name=year_name).first()

    if not academic_year:
        # Create new academic year
        academic_year = AcademicYear.objects.create(
            name=year_name,
            start_date=datetime(start_year, 6, 1).date(),
            end_date=datetime(end_year, 5, 31).date(),
            is_current=True,
            is_active=True
        )
        # Set other academic years as not current
        AcademicYear.objects.exclude(id=academic_year.id).update(is_current=False)

    return academic_year


class StudentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new students with auto-generated username/password.

    - Username: auto-generated from role_identifier (student_<admission_number>)
    - Password: secure random password (8 chars)
    - Session: defaults to current academic year
    - must_change_password: True (force password change on first login)
    """
    # Required fields
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'])
    admission_number = serializers.CharField(max_length=50)
    admission_date = serializers.DateField()

    # Class and Session
    current_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(),
        required=False,
        allow_null=True
    )

    # Optional fields
    roll_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Address
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100, default='India')
    postal_code = serializers.CharField(max_length=20)

    # Other optional
    blood_group = serializers.CharField(max_length=10, required=False, allow_blank=True)

    def validate_admission_number(self, value):
        """Check if admission number already exists"""
        if Student.objects.filter(admission_number=value).exists():
            raise serializers.ValidationError("Admission number already exists")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create student with auto-generated user account"""
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']

        # Generate username and password using centralized utility
        username = generate_username('student', validated_data['admission_number'])
        password = generate_password()

        # Get or use provided academic year
        academic_year = validated_data.get('academic_year')
        if not academic_year:
            academic_year = get_current_academic_year()

        # Get email or generate placeholder
        email = validated_data.get('email', '')
        if not email:
            email = f"{username}@student.svpschool.edu.in"

        # Create Django User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )

        # Create UserProfile
        profile = UserProfile.objects.create(
            user=user,
            role='student',
            phone=validated_data.get('phone', ''),
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            admission_no=validated_data['admission_number'],
            roll_no=validated_data.get('roll_number', ''),
            address=validated_data['address_line1'],
            city=validated_data['city'],
            state=validated_data['state'],
            postal_code=validated_data['postal_code'],
            must_change_password=True,  # Force password change on first login
        )

        # Create Student record
        student = Student.objects.create(
            user_profile=profile,
            current_class=validated_data['current_class'],
            academic_year=academic_year,
            admission_number=validated_data['admission_number'],
            roll_number=validated_data.get('roll_number', ''),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            email=email,
            phone=validated_data.get('phone', ''),
            address_line1=validated_data['address_line1'],
            address_line2=validated_data.get('address_line2', ''),
            city=validated_data['city'],
            state=validated_data['state'],
            country=validated_data.get('country', 'India'),
            postal_code=validated_data['postal_code'],
            admission_date=validated_data['admission_date'],
            blood_group=validated_data.get('blood_group', ''),
            status='active',
        )

        # Store generated credentials for response
        student._generated_username = username
        student._generated_password = password

        return student


class StudentUpdateSerializer(serializers.Serializer):
    """Serializer for updating student information"""
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'], required=False)

    # Class and Session
    current_class = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all(), required=False
    )
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), required=False
    )

    roll_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Address
    address_line1 = serializers.CharField(max_length=255, required=False)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=100, required=False)
    postal_code = serializers.CharField(max_length=20, required=False)

    blood_group = serializers.CharField(max_length=10, required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['active', 'inactive', 'graduated', 'transferred'],
        required=False
    )

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update student and related user/profile"""
        # Update student fields
        for field in ['first_name', 'last_name', 'date_of_birth', 'gender',
                      'current_class', 'academic_year', 'roll_number', 'email',
                      'phone', 'address_line1', 'address_line2', 'city', 'state',
                      'country', 'postal_code', 'blood_group', 'status']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()

        # Update related user and profile
        if instance.user_profile:
            profile = instance.user_profile
            user = profile.user

            if 'first_name' in validated_data:
                user.first_name = validated_data['first_name']
            if 'last_name' in validated_data:
                user.last_name = validated_data['last_name']
            if 'email' in validated_data:
                user.email = validated_data['email']
            user.save()

            if 'phone' in validated_data:
                profile.phone = validated_data['phone']
            if 'date_of_birth' in validated_data:
                profile.date_of_birth = validated_data['date_of_birth']
            if 'gender' in validated_data:
                profile.gender = validated_data['gender']
            if 'roll_number' in validated_data:
                profile.roll_no = validated_data['roll_number']
            if 'address_line1' in validated_data:
                profile.address = validated_data['address_line1']
            if 'city' in validated_data:
                profile.city = validated_data['city']
            if 'state' in validated_data:
                profile.state = validated_data['state']
            if 'postal_code' in validated_data:
                profile.postal_code = validated_data['postal_code']
            profile.save()

        return instance


class StudentCreateResponseSerializer(serializers.ModelSerializer):
    """Response serializer for student creation with generated credentials"""
    class_name = serializers.CharField(source='current_class.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    generated_password = serializers.SerializerMethodField()
    must_change_password = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'first_name', 'last_name',
            'full_name', 'username', 'generated_password', 'email',
            'current_class', 'class_name', 'academic_year', 'academic_year_name',
            'gender', 'status', 'must_change_password', 'created_at'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_username(self, obj):
        return getattr(obj, '_generated_username', None) or (
            obj.user_profile.user.username if obj.user_profile else None
        )

    def get_generated_password(self, obj):
        # Only return password on creation
        return getattr(obj, '_generated_password', None)

    def get_must_change_password(self, obj):
        return True


class ParentSerializer(serializers.ModelSerializer):
    """Serializer for Parent model"""
    full_name = serializers.SerializerMethodField()
    student_names = serializers.SerializerMethodField()

    class Meta:
        model = Parent
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'relation',
            'email', 'phone', 'alternate_phone', 'occupation',
            'organization_name', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'postal_code', 'photo',
            'is_primary_contact', 'is_active', 'student_names',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_student_names(self, obj):
        return [
            f"{s.first_name} {s.last_name}"
            for s in obj.students.all()
        ]


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model"""
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""
    class_name = serializers.CharField(source='class_assigned.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'class_assigned', 'class_name', 'subject', 'subject_name',
            'teacher', 'teacher_name', 'academic_year', 'academic_year_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_teacher_name(self, obj):
        if obj.teacher:
            return obj.teacher.full_name
        return None


# =============================================================================
# ATTENDANCE SERIALIZERS
# =============================================================================

class AttendanceSessionSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceSession model"""
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'name', 'code', 'start_time', 'end_time',
            'display_order', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model"""
    student_name = serializers.SerializerMethodField()
    student_roll_no = serializers.CharField(source='student.roll_number', read_only=True)
    class_name = serializers.CharField(source='class_assigned.name', read_only=True)
    session_name = serializers.CharField(source='session.name', read_only=True)
    marked_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'student_roll_no',
            'class_assigned', 'class_name', 'academic_year',
            'session', 'session_name', 'date', 'status', 'remarks',
            'marked_by', 'marked_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'marked_by', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_marked_by_name(self, obj):
        if obj.marked_by:
            return obj.marked_by.full_name
        return None


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating single attendance record"""
    class Meta:
        model = Attendance
        fields = [
            'student', 'class_assigned', 'academic_year',
            'session', 'date', 'status', 'remarks'
        ]

    def create(self, validated_data):
        # Set marked_by from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                validated_data['marked_by'] = request.user.profile
            except Exception:
                pass
        return super().create(validated_data)


class BulkAttendanceRecordSerializer(serializers.Serializer):
    """Serializer for individual record in bulk attendance"""
    student_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=['present', 'absent', 'late', 'excused'])
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class BulkAttendanceSerializer(serializers.Serializer):
    """Serializer for bulk attendance marking"""
    class_id = serializers.UUIDField()
    date = serializers.DateField()
    session_id = serializers.UUIDField(required=False, allow_null=True)
    attendance_records = BulkAttendanceRecordSerializer(many=True)

    def validate_class_id(self, value):
        if not Class.objects.filter(id=value).exists():
            raise serializers.ValidationError("Class not found")
        return value

    def validate_session_id(self, value):
        if value and not AttendanceSession.objects.filter(id=value).exists():
            raise serializers.ValidationError("Session not found")
        return value

    def validate_attendance_records(self, value):
        if not value:
            raise serializers.ValidationError("At least one attendance record is required")
        return value


class AttendanceSettingsSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceSettings model"""
    class Meta:
        model = AttendanceSettings
        fields = [
            'id', 'low_attendance_threshold', 'allow_backdated_entry',
            'max_backdated_days', 'notify_parents_on_absent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceAnalyticsSerializer(serializers.Serializer):
    """Serializer for attendance analytics response"""
    period = serializers.DictField()
    total_students = serializers.IntegerField()
    total_working_days = serializers.IntegerField()
    average_attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    daily_breakdown = serializers.ListField()
    status_distribution = serializers.DictField()


class StudentAttendanceReportSerializer(serializers.Serializer):
    """Serializer for individual student attendance report"""
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    roll_number = serializers.CharField()
    class_name = serializers.CharField()
    period = serializers.DictField()
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    excused_days = serializers.IntegerField()
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_breakdown = serializers.ListField()
    is_below_threshold = serializers.BooleanField()


class LowAttendanceStudentSerializer(serializers.Serializer):
    """Serializer for low attendance alert"""
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    roll_number = serializers.CharField()
    class_name = serializers.CharField()
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    absent_days = serializers.IntegerField()
    threshold = serializers.DecimalField(max_digits=5, decimal_places=2)


# =============================================================================
# GRADES / ASSESSMENT SERIALIZERS
# =============================================================================

class ExamTypeSerializer(serializers.ModelSerializer):
    """Serializer for ExamType model"""
    class Meta:
        model = ExamType
        fields = [
            'id', 'name', 'code', 'description', 'default_max_marks',
            'weightage', 'display_order', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GradeRangeSerializer(serializers.ModelSerializer):
    """Serializer for GradeRange model"""
    class Meta:
        model = GradeRange
        fields = [
            'id', 'grade', 'min_percentage', 'max_percentage',
            'grade_point', 'description'
        ]
        read_only_fields = ['id']


class GradingScaleSerializer(serializers.ModelSerializer):
    """Serializer for GradingScale model"""
    ranges = GradeRangeSerializer(many=True, read_only=True)

    class Meta:
        model = GradingScale
        fields = [
            'id', 'name', 'description', 'is_default', 'is_active',
            'ranges', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExamListSerializer(serializers.ModelSerializer):
    """Serializer for listing exams"""
    exam_type_name = serializers.CharField(source='exam_type.name', read_only=True)
    class_name = serializers.CharField(source='class_assigned.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    marks_entered_count = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            'id', 'name', 'exam_type', 'exam_type_name',
            'academic_year', 'academic_year_name',
            'class_assigned', 'class_name', 'subject', 'subject_name',
            'max_marks', 'passing_marks', 'exam_date',
            'is_published', 'is_locked', 'is_active',
            'marks_entered_count', 'total_students',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_marks_entered_count(self, obj):
        return obj.marks.exclude(marks_obtained__isnull=True).count()

    def get_total_students(self, obj):
        return obj.class_assigned.students.filter(status='active').count()


class ExamDetailSerializer(ExamListSerializer):
    """Detailed serializer for exam with marks"""
    marks = serializers.SerializerMethodField()

    class Meta(ExamListSerializer.Meta):
        fields = ExamListSerializer.Meta.fields + ['marks']

    def get_marks(self, obj):
        marks = obj.marks.select_related('student').all()
        return StudentMarkSerializer(marks, many=True).data


class ExamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating exams"""
    class Meta:
        model = Exam
        fields = [
            'exam_type', 'academic_year', 'class_assigned', 'subject',
            'name', 'max_marks', 'passing_marks', 'exam_date'
        ]

    def validate(self, data):
        # Check for existing exam with same type/year/class/subject
        if Exam.objects.filter(
            exam_type=data['exam_type'],
            academic_year=data['academic_year'],
            class_assigned=data['class_assigned'],
            subject=data['subject']
        ).exists():
            raise serializers.ValidationError(
                "An exam with this type, year, class, and subject already exists"
            )
        return data


class StudentMarkSerializer(serializers.ModelSerializer):
    """Serializer for StudentMark model"""
    student_name = serializers.SerializerMethodField()
    roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    entered_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentMark
        fields = [
            'id', 'exam', 'student', 'student_name', 'roll_number',
            'marks_obtained', 'is_absent', 'percentage', 'grade',
            'remarks', 'entered_by', 'entered_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'percentage', 'grade', 'entered_by', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_entered_by_name(self, obj):
        if obj.entered_by:
            return obj.entered_by.full_name
        return None


class StudentMarkCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating student marks"""
    class Meta:
        model = StudentMark
        fields = ['exam', 'student', 'marks_obtained', 'is_absent', 'remarks']

    def validate(self, data):
        exam = data.get('exam') or (self.instance.exam if self.instance else None)
        marks = data.get('marks_obtained')
        is_absent = data.get('is_absent', False)

        if not is_absent and marks is not None:
            if marks < 0:
                raise serializers.ValidationError({"marks_obtained": "Marks cannot be negative"})
            if exam and marks > exam.max_marks:
                raise serializers.ValidationError({
                    "marks_obtained": f"Marks cannot exceed maximum marks ({exam.max_marks})"
                })

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                validated_data['entered_by'] = request.user.profile
            except Exception:
                pass
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Create audit log before update
        old_marks = instance.marks_obtained
        old_grade = instance.grade

        instance = super().update(instance, validated_data)

        # Create audit log if marks changed
        if old_marks != instance.marks_obtained:
            changed_by = None
            if request and hasattr(request, 'user'):
                try:
                    changed_by = request.user.profile
                except Exception:
                    pass

            MarkAuditLog.objects.create(
                student_mark=instance,
                old_marks=old_marks,
                new_marks=instance.marks_obtained,
                old_grade=old_grade,
                new_grade=instance.grade,
                changed_by=changed_by
            )

        return instance


class BulkMarkEntrySerializer(serializers.Serializer):
    """Serializer for individual mark in bulk entry"""
    student_id = serializers.UUIDField()
    marks_obtained = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        required=False, allow_null=True
    )
    is_absent = serializers.BooleanField(default=False)
    remarks = serializers.CharField(required=False, allow_blank=True, default='')


class BulkMarksSerializer(serializers.Serializer):
    """Serializer for bulk marks entry"""
    exam_id = serializers.UUIDField()
    marks = BulkMarkEntrySerializer(many=True)

    def validate_exam_id(self, value):
        try:
            exam = Exam.objects.get(id=value)
            if exam.is_locked:
                raise serializers.ValidationError("This exam is locked and cannot be edited")
        except Exam.DoesNotExist:
            raise serializers.ValidationError("Exam not found")
        return value

    def validate_marks(self, value):
        if not value:
            raise serializers.ValidationError("At least one mark entry is required")
        return value


class MarkAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for MarkAuditLog model"""
    changed_by_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    exam_name = serializers.CharField(source='student_mark.exam.name', read_only=True)

    class Meta:
        model = MarkAuditLog
        fields = [
            'id', 'student_mark', 'student_name', 'exam_name',
            'old_marks', 'new_marks', 'old_grade', 'new_grade',
            'reason', 'changed_by', 'changed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.full_name
        return None

    def get_student_name(self, obj):
        student = obj.student_mark.student
        return f"{student.first_name} {student.last_name}"


class ClassPerformanceAnalyticsSerializer(serializers.Serializer):
    """Serializer for class performance analytics"""
    class_id = serializers.UUIDField()
    class_name = serializers.CharField()
    subject_id = serializers.UUIDField(required=False)
    subject_name = serializers.CharField(required=False)
    exam_type_id = serializers.UUIDField(required=False)
    exam_type_name = serializers.CharField(required=False)
    total_students = serializers.IntegerField()
    students_appeared = serializers.IntegerField()
    average = serializers.DecimalField(max_digits=5, decimal_places=2)
    highest = serializers.DecimalField(max_digits=5, decimal_places=2)
    lowest = serializers.DecimalField(max_digits=5, decimal_places=2)
    pass_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    grade_distribution = serializers.ListField()


class SubjectComparisonSerializer(serializers.Serializer):
    """Serializer for subject-wise comparison"""
    subject_id = serializers.UUIDField()
    subject_name = serializers.CharField()
    average = serializers.DecimalField(max_digits=5, decimal_places=2)
    highest = serializers.DecimalField(max_digits=5, decimal_places=2)
    lowest = serializers.DecimalField(max_digits=5, decimal_places=2)
    students_count = serializers.IntegerField()


class StudentProgressSerializer(serializers.Serializer):
    """Serializer for student progress over time"""
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    class_name = serializers.CharField()
    exams = serializers.ListField()


class GradeDistributionSerializer(serializers.Serializer):
    """Serializer for grade distribution"""
    grade = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


# =============================================================================
# STUDENT ADMISSION WITH PARENT LINKING SERIALIZERS
# =============================================================================

class ParentInputSerializer(serializers.Serializer):
    """Serializer for parent input during student admission"""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    relation = serializers.ChoiceField(choices=['father', 'mother', 'guardian'])
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20)
    alternate_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    occupation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    organization_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    is_primary_contact = serializers.BooleanField(default=False)


class StudentAdmissionSerializer(serializers.Serializer):
    """
    Serializer for student admission with parent account creation.

    Creates:
    - Student record with user account
    - Parent records with user accounts (auto-generated credentials)
    - StudentParent junction records for linking

    All operations are atomic - failure rolls back everything.
    """
    # Student fields (required)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'])
    admission_number = serializers.CharField(max_length=50)
    admission_date = serializers.DateField()

    # Class and Session
    current_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())
    academic_year = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(),
        required=False,
        allow_null=True
    )

    # Optional student fields
    roll_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # Address
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100, default='India')
    postal_code = serializers.CharField(max_length=20)

    # Other
    blood_group = serializers.CharField(max_length=10, required=False, allow_blank=True)

    # Parent information
    parents = ParentInputSerializer(many=True, min_length=1)
    create_parent_accounts = serializers.BooleanField(default=True)

    def validate_admission_number(self, value):
        """Check if admission number already exists"""
        if Student.objects.filter(admission_number=value).exists():
            raise serializers.ValidationError("Admission number already exists")
        return value

    def validate_parents(self, value):
        """Validate parent data"""
        if not value:
            raise serializers.ValidationError("At least one parent is required")

        # Check for at least one primary contact
        primary_contacts = [p for p in value if p.get('is_primary_contact')]
        if not primary_contacts:
            # If no primary set, make first parent primary
            value[0]['is_primary_contact'] = True

        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create student with parent accounts"""
        # Note: generate_username, generate_password imported at module level

        parents_data = validated_data.pop('parents', [])
        create_parent_accounts = validated_data.pop('create_parent_accounts', True)

        # Get or create academic year
        academic_year = validated_data.get('academic_year')
        if not academic_year:
            academic_year = get_current_academic_year()

        first_name = validated_data['first_name']
        last_name = validated_data['last_name']

        # Generate student username and password
        student_username = generate_username('student', validated_data['admission_number'])
        student_password = generate_password()

        # Get email or generate placeholder
        student_email = validated_data.get('email', '')
        if not student_email:
            student_email = f"{student_username}@student.svpschool.edu.in"

        # Create Django User for student
        student_user = User.objects.create_user(
            username=student_username,
            email=student_email,
            password=student_password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_staff=False,
        )

        # Create UserProfile for student
        student_profile = UserProfile.objects.create(
            user=student_user,
            role='student',
            phone=validated_data.get('phone', ''),
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            admission_no=validated_data['admission_number'],
            roll_no=validated_data.get('roll_number', ''),
            address=validated_data['address_line1'],
            city=validated_data['city'],
            state=validated_data['state'],
            postal_code=validated_data['postal_code'],
            must_change_password=True,
        )

        # Create Student record
        student = Student.objects.create(
            user_profile=student_profile,
            current_class=validated_data['current_class'],
            academic_year=academic_year,
            admission_number=validated_data['admission_number'],
            roll_number=validated_data.get('roll_number', ''),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            email=student_email,
            phone=validated_data.get('phone', ''),
            address_line1=validated_data['address_line1'],
            address_line2=validated_data.get('address_line2', ''),
            city=validated_data['city'],
            state=validated_data['state'],
            country=validated_data.get('country', 'India'),
            postal_code=validated_data['postal_code'],
            admission_date=validated_data['admission_date'],
            blood_group=validated_data.get('blood_group', ''),
            status='active',
        )

        # Store generated credentials
        student._generated_username = student_username
        student._generated_password = student_password
        student._parent_credentials = []

        # Create parent accounts
        for parent_data in parents_data:
            parent_phone = parent_data['phone']
            parent_email = parent_data.get('email', '')

            # Check if parent with same phone already exists
            existing_parent = Parent.objects.filter(phone=parent_phone).first()

            if existing_parent:
                # Link existing parent to this student
                StudentParent.objects.create(
                    student=student,
                    parent=existing_parent,
                    is_primary=parent_data.get('is_primary_contact', False)
                )
                # Add to credentials list (no new account created)
                student._parent_credentials.append({
                    'parent_id': str(existing_parent.id),
                    'name': f"{existing_parent.first_name} {existing_parent.last_name}",
                    'relation': existing_parent.relation,
                    'phone': existing_parent.phone,
                    'existing_account': True,
                    'username': existing_parent.user_profile.user.username if existing_parent.user_profile else None,
                })
            else:
                # Create new parent with account
                if create_parent_accounts:
                    parent_username = generate_username('parent', parent_phone)
                    parent_password = generate_password()

                    # Create user for parent
                    parent_user = User.objects.create_user(
                        username=parent_username,
                        email=parent_email,
                        password=parent_password,
                        first_name=parent_data['first_name'],
                        last_name=parent_data['last_name'],
                        is_active=True,
                        is_staff=False,
                    )

                    # Create UserProfile for parent
                    parent_profile = UserProfile.objects.create(
                        user=parent_user,
                        role='parent',
                        phone=parent_phone,
                        must_change_password=True,
                    )
                else:
                    parent_profile = None
                    parent_username = None
                    parent_password = None

                # Create Parent record
                parent = Parent.objects.create(
                    user_profile=parent_profile,
                    first_name=parent_data['first_name'],
                    last_name=parent_data['last_name'],
                    relation=parent_data['relation'],
                    email=parent_email,
                    phone=parent_phone,
                    alternate_phone=parent_data.get('alternate_phone', ''),
                    occupation=parent_data.get('occupation', ''),
                    organization_name=parent_data.get('organization_name', ''),
                    # Use student's address for parent
                    address_line1=validated_data['address_line1'],
                    address_line2=validated_data.get('address_line2', ''),
                    city=validated_data['city'],
                    state=validated_data['state'],
                    country=validated_data.get('country', 'India'),
                    postal_code=validated_data['postal_code'],
                    is_primary_contact=parent_data.get('is_primary_contact', False),
                    is_active=True,
                )

                # Link parent to student
                StudentParent.objects.create(
                    student=student,
                    parent=parent,
                    is_primary=parent_data.get('is_primary_contact', False)
                )

                # Add to credentials list
                student._parent_credentials.append({
                    'parent_id': str(parent.id),
                    'name': f"{parent.first_name} {parent.last_name}",
                    'relation': parent.relation,
                    'phone': parent_phone,
                    'existing_account': False,
                    'username': parent_username,
                    'password': parent_password,
                })

        return student


class StudentAdmissionResponseSerializer(serializers.ModelSerializer):
    """Response serializer for student admission with all created credentials"""
    class_name = serializers.CharField(source='current_class.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    student_credentials = serializers.SerializerMethodField()
    parent_credentials = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'first_name', 'last_name',
            'full_name', 'email', 'current_class', 'class_name',
            'academic_year', 'academic_year_name', 'gender', 'status',
            'student_credentials', 'parent_credentials', 'created_at'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_student_credentials(self, obj):
        return {
            'username': getattr(obj, '_generated_username', None),
            'password': getattr(obj, '_generated_password', None),
            'must_change_password': True,
        }

    def get_parent_credentials(self, obj):
        return getattr(obj, '_parent_credentials', [])


# =============================================================================
# PHASE A: ACADEMIC STRUCTURE SERIALIZERS
# =============================================================================

# NOTE: The following serializers are for Phase A models (SchoolSettings, Grade, Section)
# These models need to be created in models.py first, then uncomment the imports above.
# Current model references use string notation as placeholders.

class SchoolSettingsSerializer(serializers.ModelSerializer):
    """
    Base serializer for SchoolSettings model.
    Read-only for most users, writable only by admin.
    """
    current_academic_year_name = serializers.CharField(
        source='current_academic_year.name',
        read_only=True
    )

    class Meta:
        # model = SchoolSettings  # Uncomment when model is created
        model = None  # Placeholder - replace with SchoolSettings model
        fields = [
            'id', 'admission_number_prefix', 'current_academic_year',
            'current_academic_year_name', 'default_section_capacity',
            'roll_number_sort_by', 'normalize_special_characters',
            'allow_mid_session_roll_change', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SchoolSettingsUpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer for SchoolSettings.
    Admin-only writable fields with validation.
    """

    class Meta:
        # model = SchoolSettings  # Uncomment when model is created
        model = None  # Placeholder - replace with SchoolSettings model
        fields = [
            'admission_number_prefix', 'current_academic_year',
            'default_section_capacity', 'roll_number_sort_by',
            'normalize_special_characters', 'allow_mid_session_roll_change'
        ]

    def validate_admission_number_prefix(self, value):
        """Validate admission number prefix format"""
        if not value.isalpha():
            raise serializers.ValidationError(
                "Admission number prefix must contain only letters"
            )
        if len(value) > 10:
            raise serializers.ValidationError(
                "Admission number prefix must be 10 characters or less"
            )
        return value.upper()

    def validate_default_section_capacity(self, value):
        """Validate section capacity"""
        if value < 1:
            raise serializers.ValidationError(
                "Section capacity must be at least 1"
            )
        if value > 200:
            raise serializers.ValidationError(
                "Section capacity cannot exceed 200"
            )
        return value


class AcademicYearListSerializer(serializers.ModelSerializer):
    """Minimal serializer for academic year list views"""
    is_current_label = serializers.SerializerMethodField()

    class Meta:
        model = AcademicYear
        fields = [
            'id', 'name', 'start_date', 'end_date',
            'is_current', 'is_current_label', 'is_active'
        ]

    def get_is_current_label(self, obj):
        return 'Current' if obj.is_current else ''


class AcademicYearDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for academic year with statistics"""
    total_students = serializers.SerializerMethodField()
    total_sections = serializers.SerializerMethodField()
    total_grades = serializers.SerializerMethodField()

    class Meta:
        model = AcademicYear
        fields = [
            'id', 'name', 'start_date', 'end_date',
            'is_current', 'is_active', 'total_students',
            'total_sections', 'total_grades',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_students(self, obj):
        """Count active students in this academic year"""
        return obj.students.filter(status='active').count()

    def get_total_sections(self, obj):
        """Count active sections in this academic year"""
        # Will use Section model when available
        return 0  # Placeholder

    def get_total_grades(self, obj):
        """Count distinct grades in this academic year"""
        # Will use Grade model when available
        return 0  # Placeholder


class AcademicYearCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Create/Update serializer for AcademicYear with validation.
    Ensures only one academic year can be is_current=True at a time.
    """

    class Meta:
        model = AcademicYear
        fields = [
            'name', 'start_date', 'end_date', 'is_current', 'is_active'
        ]

    def validate_name(self, value):
        """Validate academic year name format (YYYY-YY)"""
        import re
        pattern = r'^\d{4}-\d{2}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Academic year name must be in format YYYY-YY (e.g., 2025-26)"
            )
        return value

    def validate(self, data):
        """Validate date ranges and current year logic"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date:
            if start_date >= end_date:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })

            # Check for overlapping academic years
            from django.db.models import Q
            overlapping = AcademicYear.objects.filter(
                Q(start_date__lte=end_date, end_date__gte=start_date)
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise serializers.ValidationError(
                    "Academic year dates overlap with existing academic year"
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create academic year, ensuring only one is_current"""
        is_current = validated_data.get('is_current', False)

        if is_current:
            # Set all other academic years to not current
            AcademicYear.objects.filter(is_current=True).update(is_current=False)

        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update academic year, ensuring only one is_current"""
        is_current = validated_data.get('is_current', instance.is_current)

        if is_current and not instance.is_current:
            # Setting this year as current, unset others
            AcademicYear.objects.filter(is_current=True).exclude(pk=instance.pk).update(is_current=False)

        return super().update(instance, validated_data)


class GradeListSerializer(serializers.ModelSerializer):
    """Minimal serializer for grade list views"""
    section_count = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    class Meta:
        # model = Grade  # Uncomment when model is created
        model = None  # Placeholder - replace with Grade model
        fields = [
            'id', 'number', 'name', 'display_name',
            'section_count', 'student_count', 'is_active'
        ]

    def get_section_count(self, obj):
        """Count active sections for this grade"""
        return obj.sections.filter(is_active=True).count()

    def get_student_count(self, obj):
        """Count active students across all sections of this grade"""
        # Sum students from all sections
        total = 0
        for section in obj.sections.filter(is_active=True):
            total += section.students.filter(status='active').count()
        return total


class GradeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for grade with nested subjects and sections"""
    subjects = SubjectSerializer(many=True, read_only=True)
    sections = serializers.SerializerMethodField()
    section_count = serializers.SerializerMethodField()
    total_capacity = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    capacity_utilization = serializers.SerializerMethodField()

    class Meta:
        # model = Grade  # Uncomment when model is created
        model = None  # Placeholder - replace with Grade model
        fields = [
            'id', 'number', 'name', 'display_name', 'subjects',
            'sections', 'section_count', 'total_capacity',
            'total_students', 'capacity_utilization',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_sections(self, obj):
        """Get all sections for this grade"""
        sections = obj.sections.filter(is_active=True).order_by('name')
        from .serializers import SectionListSerializer  # Avoid circular import
        return SectionListSerializer(sections, many=True).data

    def get_section_count(self, obj):
        return obj.sections.filter(is_active=True).count()

    def get_total_capacity(self, obj):
        """Sum capacity across all sections"""
        sections = obj.sections.filter(is_active=True)
        return sum(s.capacity for s in sections if s.capacity)

    def get_total_students(self, obj):
        """Count students across all sections"""
        total = 0
        for section in obj.sections.filter(is_active=True):
            total += section.students.filter(status='active').count()
        return total

    def get_capacity_utilization(self, obj):
        """Calculate percentage of capacity used"""
        total_capacity = self.get_total_capacity(obj)
        total_students = self.get_total_students(obj)

        if total_capacity == 0:
            return 0.0

        return round((total_students / total_capacity) * 100, 2)


class GradeCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for Grade with validation"""
    subjects = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        # model = Grade  # Uncomment when model is created
        model = None  # Placeholder - replace with Grade model
        fields = ['number', 'name', 'display_name', 'subjects', 'is_active']

    def validate_number(self, value):
        """Validate grade number (1-12)"""
        if value < 1 or value > 12:
            raise serializers.ValidationError(
                "Grade number must be between 1 and 12"
            )
        return value

    def validate(self, data):
        """Check for duplicate grade numbers"""
        number = data.get('number')
        if number:
            # TODO: Uncomment when Grade model is created
            # from .models import Grade
            # existing = Grade.objects.filter(number=number)
            # if self.instance:
            #     existing = existing.exclude(pk=self.instance.pk)
            # if existing.exists():
            #     raise serializers.ValidationError({
            #         'number': f"Grade {number} already exists"
            #     })
            pass
        return data


class SectionListSerializer(serializers.ModelSerializer):
    """Minimal serializer for section list views"""
    grade_name = serializers.CharField(source='grade.display_name', read_only=True)
    grade_number = serializers.IntegerField(source='grade.number', read_only=True)
    full_name = serializers.SerializerMethodField()
    class_teacher_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    capacity_utilization = serializers.SerializerMethodField()

    class Meta:
        # model = Section  # Uncomment when model is created
        model = None  # Placeholder - replace with Section model
        fields = [
            'id', 'grade', 'grade_number', 'grade_name', 'name',
            'full_name', 'capacity', 'class_teacher', 'class_teacher_name',
            'student_count', 'capacity_utilization', 'academic_year', 'is_active'
        ]

    def get_full_name(self, obj):
        """Return full section name (e.g., '5A')"""
        return f"{obj.grade.number}{obj.name}"

    def get_class_teacher_name(self, obj):
        """Return class teacher full name"""
        if obj.class_teacher:
            return obj.class_teacher.full_name
        return None

    def get_student_count(self, obj):
        """Count active students in this section"""
        return obj.students.filter(status='active').count()

    def get_capacity_utilization(self, obj):
        """Calculate capacity utilization percentage"""
        if not obj.capacity or obj.capacity == 0:
            return 0.0

        student_count = self.get_student_count(obj)
        return round((student_count / obj.capacity) * 100, 2)


class SectionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for section with nested grade info and students"""
    grade_info = serializers.SerializerMethodField()
    class_teacher_info = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True
    )
    full_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()
    capacity_utilization = serializers.SerializerMethodField()
    capacity_status = serializers.SerializerMethodField()

    class Meta:
        # model = Section  # Uncomment when model is created
        model = None  # Placeholder - replace with Section model
        fields = [
            'id', 'grade', 'grade_info', 'name', 'full_name',
            'capacity', 'class_teacher', 'class_teacher_info',
            'room_number', 'academic_year', 'academic_year_name',
            'student_count', 'students', 'capacity_utilization',
            'capacity_status', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.grade.number}{obj.name}"

    def get_grade_info(self, obj):
        """Return nested grade information"""
        return {
            'id': str(obj.grade.id),
            'number': obj.grade.number,
            'name': obj.grade.name,
            'display_name': obj.grade.display_name
        }

    def get_class_teacher_info(self, obj):
        """Return nested class teacher information"""
        if not obj.class_teacher:
            return None
        return {
            'id': str(obj.class_teacher.id),
            'full_name': obj.class_teacher.full_name,
            'email': obj.class_teacher.user.email if obj.class_teacher.user else None,
            'phone': obj.class_teacher.phone
        }

    def get_student_count(self, obj):
        return obj.students.filter(status='active').count()

    def get_students(self, obj):
        """Return list of students in this section"""
        students = obj.students.filter(status='active').order_by('roll_number', 'first_name', 'last_name')
        return StudentListSerializer(students, many=True).data

    def get_capacity_utilization(self, obj):
        """Calculate capacity utilization percentage"""
        if not obj.capacity or obj.capacity == 0:
            return 0.0

        student_count = self.get_student_count(obj)
        return round((student_count / obj.capacity) * 100, 2)

    def get_capacity_status(self, obj):
        """Return capacity status (available, full, overcapacity)"""
        if not obj.capacity:
            return 'unknown'

        utilization = self.get_capacity_utilization(obj)

        if utilization >= 100:
            return 'full' if utilization == 100 else 'overcapacity'
        elif utilization >= 90:
            return 'near_full'
        else:
            return 'available'


class SectionCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for Section with validation"""

    class Meta:
        # model = Section  # Uncomment when model is created
        model = None  # Placeholder - replace with Section model
        fields = [
            'grade', 'name', 'capacity', 'class_teacher',
            'room_number', 'academic_year', 'is_active'
        ]

    def validate_name(self, value):
        """Validate section name (A-E)"""
        if not value.isalpha() or len(value) != 1:
            raise serializers.ValidationError(
                "Section name must be a single letter (A-E)"
            )
        value = value.upper()
        if value not in ['A', 'B', 'C', 'D', 'E']:
            raise serializers.ValidationError(
                "Section name must be between A and E"
            )
        return value

    def validate_capacity(self, value):
        """Validate section capacity"""
        if value is not None:
            if value < 1:
                raise serializers.ValidationError(
                    "Section capacity must be at least 1"
                )
            if value > 200:
                raise serializers.ValidationError(
                    "Section capacity cannot exceed 200"
                )
        return value

    def validate(self, data):
        """Validate unique section per grade and academic year"""
        grade = data.get('grade')
        name = data.get('name')
        academic_year = data.get('academic_year')

        if grade and name and academic_year:
            # TODO: Uncomment when Section model is created
            # from .models import Section
            # existing = Section.objects.filter(
            #     grade=grade,
            #     name=name,
            #     academic_year=academic_year
            # )
            # if self.instance:
            #     existing = existing.exclude(pk=self.instance.pk)
            #
            # if existing.exists():
            #     raise serializers.ValidationError(
            #         f"Section {name} already exists for Grade {grade.number} in academic year {academic_year.name}"
            #     )
            pass

        # Check if section is at capacity when updating
        if self.instance and 'capacity' in data:
            new_capacity = data['capacity']
            current_students = self.instance.students.filter(status='active').count()

            if new_capacity and new_capacity < current_students:
                raise serializers.ValidationError({
                    'capacity': f"Cannot set capacity to {new_capacity}. "
                               f"Section currently has {current_students} students."
                })

        return data

    def validate_class_teacher(self, value):
        """Validate that class teacher is not already assigned to another section"""
        if value:
            # TODO: Uncomment when Section model is created
            # from .models import Section
            # Check if teacher is already a class teacher for another section
            # existing_assignment = Section.objects.filter(
            #     class_teacher=value,
            #     is_active=True
            # )
            # if self.instance:
            #     existing_assignment = existing_assignment.exclude(pk=self.instance.pk)
            #
            # if existing_assignment.exists():
            #     section = existing_assignment.first()
            #     raise serializers.ValidationError(
            #         f"This teacher is already the class teacher for Section "
            #         f"{section.grade.number}{section.name}"
            #     )
            pass

        return value


# =============================================================================
# PHASE B: STUDENT CORE SERIALIZERS (Enrollment & Photo Management)
# =============================================================================

class StudentEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for StudentEnrollment model"""
    student_name = serializers.SerializerMethodField()
    section_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    enrolled_by_name = serializers.SerializerMethodField()

    class Meta:
        from .models import StudentEnrollment
        model = StudentEnrollment
        fields = [
            'id', 'student', 'student_name', 'section', 'section_name',
            'academic_year', 'academic_year_name', 'roll_number',
            'enrolled_date', 'exit_date', 'status', 'is_current',
            'enrolled_by', 'enrolled_by_name', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_section_name(self, obj):
        return obj.section.full_name

    def get_enrolled_by_name(self, obj):
        if obj.enrolled_by:
            return obj.enrolled_by.full_name
        return None


class StudentEnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StudentEnrollment records"""
    class Meta:
        from .models import StudentEnrollment
        model = StudentEnrollment
        fields = [
            'student', 'section', 'academic_year', 'roll_number',
            'enrolled_date', 'status', 'notes'
        ]

    def create(self, validated_data):
        from .models import StudentEnrollment
        # Set enrolled_by from request context
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            validated_data['enrolled_by'] = request.user.profile

        # Set is_current to True by default
        validated_data.setdefault('is_current', True)

        enrollment = StudentEnrollment.objects.create(**validated_data)

        # Update student's current_section
        student = enrollment.student
        if enrollment.is_current:
            student.current_section = enrollment.section
            student.save(update_fields=['current_section'])

        return enrollment


class StudentPhotoSerializer(serializers.ModelSerializer):
    """Serializer for StudentPhoto model"""
    student_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        from .models import StudentPhoto
        model = StudentPhoto
        fields = [
            'id', 'student', 'student_name', 'academic_year', 'academic_year_name',
            'image', 'file_size', 'width', 'height',
            'status', 'status_display', 'is_current',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at',
            'approved_by', 'approved_by_name', 'approved_at',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'width', 'height', 'uploaded_at',
            'approved_at', 'created_at', 'updated_at'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.full_name
        return None

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.full_name
        return None


class StudentPhotoUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading student photos"""
    class Meta:
        from .models import StudentPhoto
        model = StudentPhoto
        fields = ['student', 'academic_year', 'image']

    def create(self, validated_data):
        from .models import StudentPhoto
        from PIL import Image
        import os

        # Set uploaded_by from request context
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            validated_data['uploaded_by'] = request.user.profile

        # Set default status to pending
        validated_data['status'] = 'pending'
        validated_data['is_current'] = False

        photo = StudentPhoto.objects.create(**validated_data)

        # Extract image metadata
        try:
            img = Image.open(photo.image.path)
            photo.width = img.width
            photo.height = img.height
            photo.file_size = os.path.getsize(photo.image.path)
            photo.save(update_fields=['width', 'height', 'file_size'])
        except Exception:
            # If metadata extraction fails, continue without it
            pass

        return photo
# =============================================================================
# ADDITIONAL PHASE B SERIALIZERS
# These should be appended to academics/serializers.py
# =============================================================================

# StudentEnrollmentListSerializer - minimal fields for list
class StudentEnrollmentListSerializer(serializers.ModelSerializer):
    """Minimal serializer for listing student enrollments"""
    student_name = serializers.SerializerMethodField()
    student_admission_number = serializers.CharField(
        source='student.admission_number',
        read_only=True
    )
    section_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        from .models import StudentEnrollment
        model = StudentEnrollment
        fields = [
            'id', 'student', 'student_name', 'student_admission_number',
            'section', 'section_name', 'academic_year', 'academic_year_name',
            'roll_number', 'enrolled_date', 'exit_date',
            'status', 'status_display', 'is_current'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_section_name(self, obj):
        return obj.section.full_name


# StudentEnrollmentDetailSerializer - full details with nested student/section info
class StudentEnrollmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for student enrollment with nested information"""
    student_info = serializers.SerializerMethodField()
    section_info = serializers.SerializerMethodField()
    academic_year_info = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    enrolled_by_name = serializers.SerializerMethodField()

    class Meta:
        from .models import StudentEnrollment
        model = StudentEnrollment
        fields = [
            'id', 'student', 'student_info', 'section', 'section_info',
            'academic_year', 'academic_year_info', 'roll_number',
            'enrolled_date', 'exit_date', 'status', 'status_display',
            'is_current', 'enrolled_by', 'enrolled_by_name', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'enrolled_by', 'created_at', 'updated_at']

    def get_student_info(self, obj):
        """Return nested student information"""
        return {
            'id': str(obj.student.id),
            'admission_number': obj.student.admission_number,
            'first_name': obj.student.first_name,
            'last_name': obj.student.last_name,
            'full_name': f"{obj.student.first_name} {obj.student.last_name}",
            'status': obj.student.status,
        }

    def get_section_info(self, obj):
        """Return nested section information"""
        return {
            'id': str(obj.section.id),
            'name': obj.section.name,
            'full_name': obj.section.full_name,
            'grade_number': obj.section.grade.number,
            'grade_name': obj.section.grade.name,
            'capacity': obj.section.capacity,
            'current_strength': obj.section.current_strength,
        }

    def get_academic_year_info(self, obj):
        """Return nested academic year information"""
        return {
            'id': str(obj.academic_year.id),
            'name': obj.academic_year.name,
            'start_date': obj.academic_year.start_date,
            'end_date': obj.academic_year.end_date,
            'status': obj.academic_year.status,
            'is_current': obj.academic_year.is_current,
        }

    def get_enrolled_by_name(self, obj):
        """Return enrolled_by user's full name"""
        if obj.enrolled_by:
            return obj.enrolled_by.full_name
        return None


# Enhanced StudentEnrollmentCreateSerializer - for enrolling students with validation
class StudentEnrollmentCreateSerializerEnhanced(serializers.ModelSerializer):
    """Serializer for creating student enrollments with comprehensive validation"""

    class Meta:
        from .models import StudentEnrollment
        model = StudentEnrollment
        fields = [
            'student', 'section', 'academic_year',
            'roll_number', 'enrolled_date', 'notes'
        ]

    def validate(self, data):
        """Validate student enrollment - check for duplicates and capacity"""
        from .models import StudentEnrollment

        student = data.get('student')
        section = data.get('section')
        academic_year = data.get('academic_year')

        # Check if student is already enrolled in the same academic year
        existing_enrollment = StudentEnrollment.objects.filter(
            student=student,
            academic_year=academic_year,
            is_current=True
        ).exclude(
            pk=self.instance.pk if self.instance else None
        )

        if existing_enrollment.exists():
            enrollment = existing_enrollment.first()
            raise serializers.ValidationError({
                'student': f"Student is already enrolled in {enrollment.section.full_name} "
                          f"for academic year {academic_year.name}"
            })

        # Check if section has available capacity
        if section.current_strength >= section.capacity:
            raise serializers.ValidationError({
                'section': f"Section {section.full_name} is at full capacity "
                          f"({section.current_strength}/{section.capacity})"
            })

        # Validate academic year matches section's academic year
        if section.academic_year != academic_year:
            raise serializers.ValidationError({
                'academic_year': f"Academic year must match section's academic year "
                                f"({section.academic_year.name})"
            })

        return data

    def create(self, validated_data):
        """Create enrollment and update student's current section"""
        from .models import StudentEnrollment

        # Set enrolled_by from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                validated_data['enrolled_by'] = request.user.profile
            except Exception:
                pass

        # Set is_current to True for new enrollments
        validated_data['is_current'] = True

        enrollment = StudentEnrollment.objects.create(**validated_data)

        # Update student's current section and academic year
        student = enrollment.student
        student.current_section = enrollment.section
        student.academic_year = enrollment.academic_year
        if enrollment.roll_number:
            student.roll_number = enrollment.roll_number
        student.save()

        return enrollment


# StudentPhotoListSerializer - for photo gallery view
class StudentPhotoListSerializerEnhanced(serializers.ModelSerializer):
    """Minimal serializer for student photo gallery view"""
    student_name = serializers.SerializerMethodField()
    student_admission_number = serializers.CharField(
        source='student.admission_number',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    uploaded_by_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        from .models import StudentPhoto
        model = StudentPhoto
        fields = [
            'id', 'student', 'student_name', 'student_admission_number',
            'image', 'image_url', 'status', 'status_display',
            'is_current', 'uploaded_by', 'uploaded_by_name',
            'uploaded_at', 'academic_year', 'academic_year_name',
            'width', 'height', 'file_size'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.full_name
        return None

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


# StudentPhotoDetailSerializer - full details
class StudentPhotoDetailSerializerEnhanced(serializers.ModelSerializer):
    """Detailed serializer for student photo with full information"""
    student_info = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    uploaded_by_info = serializers.SerializerMethodField()
    approved_by_info = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        from .models import StudentPhoto
        model = StudentPhoto
        fields = [
            'id', 'student', 'student_info', 'image', 'image_url',
            'status', 'status_display', 'uploaded_by', 'uploaded_by_info',
            'uploaded_at', 'approved_by', 'approved_by_info', 'approved_at',
            'rejection_reason', 'is_current', 'file_size', 'width', 'height',
            'academic_year', 'academic_year_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uploaded_by', 'uploaded_at', 'approved_by',
            'approved_at', 'created_at', 'updated_at'
        ]

    def get_student_info(self, obj):
        """Return nested student information"""
        section_name = None
        if obj.student.current_section:
            section_name = obj.student.current_section.full_name

        return {
            'id': str(obj.student.id),
            'admission_number': obj.student.admission_number,
            'first_name': obj.student.first_name,
            'last_name': obj.student.last_name,
            'full_name': f"{obj.student.first_name} {obj.student.last_name}",
            'current_section': section_name,
        }

    def get_uploaded_by_info(self, obj):
        """Return nested uploader information"""
        if not obj.uploaded_by:
            return None
        return {
            'id': str(obj.uploaded_by.id),
            'full_name': obj.uploaded_by.full_name,
            'role': obj.uploaded_by.role,
        }

    def get_approved_by_info(self, obj):
        """Return nested approver information"""
        if not obj.approved_by:
            return None
        return {
            'id': str(obj.approved_by.id),
            'full_name': obj.approved_by.full_name,
            'role': obj.approved_by.role,
        }

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


# StudentPhotoUploadSerializer - for uploading new photos with validation
class StudentPhotoUploadSerializerEnhanced(serializers.ModelSerializer):
    """Serializer for uploading new student photos with validation"""

    class Meta:
        from .models import StudentPhoto
        model = StudentPhoto
        fields = [
            'student', 'image', 'academic_year'
        ]

    def validate_image(self, value):
        """Validate image file size and format"""
        # Maximum file size: 5MB
        max_size = 5 * 1024 * 1024  # 5MB in bytes

        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image file size ({value.size / (1024*1024):.2f}MB) exceeds "
                f"maximum allowed size (5MB). Please compress the image."
            )

        # Validate image format
        allowed_formats = ['image/jpeg', 'image/jpg', 'image/png']
        content_type = value.content_type

        if content_type not in allowed_formats:
            raise serializers.ValidationError(
                f"Invalid image format '{content_type}'. "
                f"Allowed formats: JPEG, PNG"
            )

        return value

    def create(self, validated_data):
        """Create student photo with metadata"""
        from PIL import Image
        import os
        from .models import StudentPhoto

        request = self.context.get('request')
        uploaded_by = None
        if request and hasattr(request, 'user'):
            try:
                uploaded_by = request.user.profile
            except Exception:
                pass

        # Create photo instance
        photo = StudentPhoto.objects.create(
            student=validated_data['student'],
            image=validated_data['image'],
            academic_year=validated_data.get('academic_year'),
            uploaded_by=uploaded_by,
            status='pending',  # Default to pending approval
            is_current=False,
        )

        # Extract image metadata
        try:
            img = Image.open(photo.image.path)
            photo.width = img.width
            photo.height = img.height
            photo.file_size = os.path.getsize(photo.image.path)
            photo.save(update_fields=['width', 'height', 'file_size'])
        except Exception:
            # If metadata extraction fails, just continue
            pass

        return photo


# StudentPhotoApprovalSerializer - for admin approval/rejection
class StudentPhotoApprovalSerializer(serializers.Serializer):
    """Serializer for admin approval/rejection of student photos"""
    status = serializers.ChoiceField(
        choices=['approved', 'rejected'],
        help_text="Approve or reject the photo"
    )
    rejection_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Required if rejecting the photo"
    )
    set_as_current = serializers.BooleanField(
        default=True,
        help_text="Set as current photo if approved"
    )

    def validate(self, data):
        """Validate rejection reason is provided when rejecting"""
        status = data.get('status')
        rejection_reason = data.get('rejection_reason', '').strip()

        if status == 'rejected' and not rejection_reason:
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a photo'
            })

        if status == 'approved' and rejection_reason:
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason should not be provided when approving'
            })

        return data

    def update(self, instance, validated_data):
        """Update photo approval status"""
        from django.utils import timezone

        status = validated_data.get('status')
        set_as_current = validated_data.get('set_as_current', True)

        # Set approval fields
        instance.status = status
        instance.rejection_reason = validated_data.get('rejection_reason', '')

        # Set approved_by and approved_at
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                instance.approved_by = request.user.profile
            except Exception:
                pass

        instance.approved_at = timezone.now()

        # If approved and set_as_current, make it the current photo
        if status == 'approved' and set_as_current:
            instance.is_current = True

        instance.save()

        return instance


# Enhanced StudentSerializer - update existing with Phase B features
class StudentSerializerEnhanced(serializers.ModelSerializer):
    """
    Enhanced Student serializer with Phase B features:
    - current_section_info (nested)
    - current_photo (nested, only approved & is_current)
    - enrollment_history (list of past enrollments)
    - computed fields (has_current_photo, photo_pending_approval)
    - status with display label
    """
    current_section_info = serializers.SerializerMethodField()
    current_photo = serializers.SerializerMethodField()
    enrollment_history = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    full_name = serializers.SerializerMethodField()
    has_current_photo = serializers.SerializerMethodField()
    photo_pending_approval = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True
    )

    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'first_name', 'last_name',
            'full_name', 'date_of_birth', 'gender', 'email', 'phone',
            'current_section', 'current_section_info', 'academic_year',
            'academic_year_name', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'postal_code', 'admission_date',
            'blood_group', 'status', 'status_display', 'current_photo',
            'has_current_photo', 'photo_pending_approval', 'enrollment_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_has_current_photo(self, obj):
        """Check if student has an approved current photo"""
        return obj.photos.filter(is_current=True, status='approved').exists()

    def get_photo_pending_approval(self, obj):
        """Check if student has a photo pending approval"""
        return obj.photos.filter(status='pending').exists()

    def get_current_section_info(self, obj):
        """Return nested current section information"""
        if not obj.current_section:
            return None

        class_teacher_name = None
        if obj.current_section.class_teacher:
            class_teacher_name = obj.current_section.class_teacher.full_name

        return {
            'id': str(obj.current_section.id),
            'name': obj.current_section.name,
            'full_name': obj.current_section.full_name,
            'grade_number': obj.current_section.grade.number,
            'grade_name': obj.current_section.grade.name,
            'class_teacher': class_teacher_name,
        }

    def get_current_photo(self, obj):
        """Return current approved photo information (nested, only approved & is_current)"""
        from .models import StudentPhoto

        photo = obj.photos.filter(is_current=True, status='approved').first()
        if not photo:
            return None

        request = self.context.get('request')
        image_url = None
        if photo.image:
            if request:
                image_url = request.build_absolute_uri(photo.image.url)
            else:
                image_url = photo.image.url

        return {
            'id': str(photo.id),
            'image_url': image_url,
            'uploaded_at': photo.uploaded_at,
            'academic_year': photo.academic_year.name if photo.academic_year else None,
            'width': photo.width,
            'height': photo.height,
        }

    def get_enrollment_history(self, obj):
        """Return list of past enrollments"""
        from .models import StudentEnrollment

        # Get all non-current enrollments
        enrollments = obj.enrollments.filter(
            is_current=False
        ).order_by('-academic_year__start_date')[:5]  # Last 5 enrollments

        return [{
            'id': str(enrollment.id),
            'section': enrollment.section.full_name,
            'academic_year': enrollment.academic_year.name,
            'roll_number': enrollment.roll_number,
            'enrolled_date': enrollment.enrolled_date,
            'exit_date': enrollment.exit_date,
            'status': enrollment.get_status_display(),
        } for enrollment in enrollments]


# =============================================================================
# PHASE C: TEACHER ASSIGNMENT SERIALIZERS
# =============================================================================

class ClassTeacherListSerializer(serializers.ModelSerializer):
    """Minimal serializer for listing class teacher assignments"""
    section_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True
    )

    class Meta:
        model = ClassTeacher
        fields = [
            'id', 'section', 'section_info', 'teacher', 'teacher_info',
            'academic_year', 'academic_year_name', 'is_primary', 'assigned_at'
        ]

    def get_section_info(self, obj):
        """Return nested section information with grade"""
        return {
            'id': str(obj.section.id),
            'name': obj.section.name,
            'full_name': obj.section.full_name,
            'grade_number': obj.section.grade.number,
            'grade_name': obj.section.grade.name,
        }

    def get_teacher_info(self, obj):
        """Return nested teacher information"""
        return {
            'id': str(obj.teacher.id),
            'full_name': obj.teacher.full_name,
            'email': obj.teacher.user.email if obj.teacher.user else None,
        }


class ClassTeacherDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for class teacher assignment with full information"""
    section_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    academic_year_info = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ClassTeacher
        fields = [
            'id', 'section', 'section_info', 'teacher', 'teacher_info',
            'academic_year', 'academic_year_info', 'is_primary',
            'assigned_by', 'assigned_by_name', 'assigned_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'assigned_by', 'assigned_at', 'created_at', 'updated_at']

    def get_section_info(self, obj):
        """Return nested section information with grade"""
        return {
            'id': str(obj.section.id),
            'name': obj.section.name,
            'full_name': obj.section.full_name,
            'grade_number': obj.section.grade.number,
            'grade_name': obj.section.grade.name,
            'capacity': obj.section.capacity,
            'current_strength': obj.section.current_strength,
        }

    def get_teacher_info(self, obj):
        """Return nested teacher information"""
        return {
            'id': str(obj.teacher.id),
            'full_name': obj.teacher.full_name,
            'email': obj.teacher.user.email if obj.teacher.user else None,
            'phone': obj.teacher.phone,
            'role': obj.teacher.role,
        }

    def get_academic_year_info(self, obj):
        """Return nested academic year information"""
        return {
            'id': str(obj.academic_year.id),
            'name': obj.academic_year.name,
            'start_date': obj.academic_year.start_date,
            'end_date': obj.academic_year.end_date,
            'is_current': obj.academic_year.is_current,
        }

    def get_assigned_by_name(self, obj):
        """Return assigned_by user's full name"""
        if obj.assigned_by:
            return obj.assigned_by.full_name
        return None


class ClassTeacherCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating class teacher assignments with validation"""

    class Meta:
        model = ClassTeacher
        fields = [
            'section', 'teacher', 'academic_year', 'is_primary', 'notes'
        ]

    def validate(self, data):
        """
        Validate class teacher assignment:
        - Check if primary class teacher already exists for section+year
        - Ensure teacher is not already assigned as primary to another section
        """
        section = data.get('section')
        teacher = data.get('teacher')
        academic_year = data.get('academic_year')
        is_primary = data.get('is_primary', False)

        # Check if primary class teacher already exists for this section+year
        if is_primary:
            existing_primary = ClassTeacher.objects.filter(
                section=section,
                academic_year=academic_year,
                is_primary=True
            ).exclude(
                pk=self.instance.pk if self.instance else None
            )

            if existing_primary.exists():
                primary_teacher = existing_primary.first()
                raise serializers.ValidationError({
                    'is_primary': f"Primary class teacher already exists for this section "
                                  f"({primary_teacher.teacher.full_name}). "
                                  f"Please mark the existing assignment as non-primary first."
                })

            # Check if teacher is already a primary class teacher for another section
            teacher_primary_assignments = ClassTeacher.objects.filter(
                teacher=teacher,
                academic_year=academic_year,
                is_primary=True
            ).exclude(
                pk=self.instance.pk if self.instance else None
            )

            if teacher_primary_assignments.exists():
                assignment = teacher_primary_assignments.first()
                raise serializers.ValidationError({
                    'teacher': f"This teacher is already the primary class teacher for "
                              f"{assignment.section.full_name}. A teacher can only be the "
                              f"primary class teacher for one section per academic year."
                })

        # Validate academic year matches section's academic year
        if section.academic_year != academic_year:
            raise serializers.ValidationError({
                'academic_year': f"Academic year must match section's academic year "
                                f"({section.academic_year.name})"
            })

        return data

    def create(self, validated_data):
        """Create class teacher assignment and set assigned_by from request"""
        from django.utils import timezone

        # Set assigned_by from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                validated_data['assigned_by'] = request.user.profile
            except Exception:
                pass

        # Set assigned_at timestamp
        validated_data['assigned_at'] = timezone.now()

        return super().create(validated_data)


class SubjectTeacherListSerializer(serializers.ModelSerializer):
    """Minimal serializer for listing subject teacher assignments"""
    section_info = serializers.SerializerMethodField()
    subject_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(
        source='academic_year.name',
        read_only=True
    )

    class Meta:
        model = SubjectTeacher
        fields = [
            'id', 'section', 'section_info', 'subject', 'subject_info',
            'teacher', 'teacher_info', 'academic_year', 'academic_year_name',
            'periods_per_week', 'is_active'
        ]

    def get_section_info(self, obj):
        """Return nested section information"""
        return {
            'id': str(obj.section.id),
            'name': obj.section.name,
            'full_name': obj.section.full_name,
            'grade_number': obj.section.grade.number,
        }

    def get_subject_info(self, obj):
        """Return nested subject information"""
        return {
            'id': str(obj.subject.id),
            'name': obj.subject.name,
            'code': obj.subject.code,
        }

    def get_teacher_info(self, obj):
        """Return nested teacher information"""
        return {
            'id': str(obj.teacher.id),
            'full_name': obj.teacher.full_name,
            'email': obj.teacher.user.email if obj.teacher.user else None,
        }


class SubjectTeacherDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for subject teacher assignment with full information"""
    section_info = serializers.SerializerMethodField()
    subject_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    academic_year_info = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SubjectTeacher
        fields = [
            'id', 'section', 'section_info', 'subject', 'subject_info',
            'teacher', 'teacher_info', 'academic_year', 'academic_year_info',
            'periods_per_week', 'is_active', 'assigned_by', 'assigned_by_name',
            'assigned_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'assigned_by', 'assigned_at', 'created_at', 'updated_at']

    def get_section_info(self, obj):
        """Return nested section information"""
        return {
            'id': str(obj.section.id),
            'name': obj.section.name,
            'full_name': obj.section.full_name,
            'grade_number': obj.section.grade.number,
            'grade_name': obj.section.grade.name,
        }

    def get_subject_info(self, obj):
        """Return nested subject information"""
        return {
            'id': str(obj.subject.id),
            'name': obj.subject.name,
            'code': obj.subject.code,
            'description': obj.subject.description,
        }

    def get_teacher_info(self, obj):
        """Return nested teacher information"""
        return {
            'id': str(obj.teacher.id),
            'full_name': obj.teacher.full_name,
            'email': obj.teacher.user.email if obj.teacher.user else None,
            'phone': obj.teacher.phone,
            'role': obj.teacher.role,
        }

    def get_academic_year_info(self, obj):
        """Return nested academic year information"""
        return {
            'id': str(obj.academic_year.id),
            'name': obj.academic_year.name,
            'start_date': obj.academic_year.start_date,
            'end_date': obj.academic_year.end_date,
            'is_current': obj.academic_year.is_current,
        }

    def get_assigned_by_name(self, obj):
        """Return assigned_by user's full name"""
        if obj.assigned_by:
            return obj.assigned_by.full_name
        return None


class SubjectTeacherCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subject teacher assignments with validation"""

    class Meta:
        model = SubjectTeacher
        fields = [
            'section', 'subject', 'teacher', 'academic_year',
            'periods_per_week'
        ]

    def validate(self, data):
        """
        Validate subject teacher assignment:
        - Check unique constraint (section+subject+academic_year)
        - Ensure academic year matches section's academic year
        - Validate periods_per_week is reasonable
        """
        section = data.get('section')
        subject = data.get('subject')
        academic_year = data.get('academic_year')
        periods_per_week = data.get('periods_per_week')

        # Check unique constraint
        existing_assignment = SubjectTeacher.objects.filter(
            section=section,
            subject=subject,
            academic_year=academic_year
        ).exclude(
            pk=self.instance.pk if self.instance else None
        )

        if existing_assignment.exists():
            teacher = existing_assignment.first().teacher
            raise serializers.ValidationError({
                'subject': f"Subject {subject.name} is already assigned to "
                          f"{teacher.full_name} for this section in {academic_year.name}. "
                          f"Please update the existing assignment instead."
            })

        # Validate academic year matches section's academic year
        if section.academic_year != academic_year:
            raise serializers.ValidationError({
                'academic_year': f"Academic year must match section's academic year "
                                f"({section.academic_year.name})"
            })

        # Validate periods_per_week is reasonable (1-10)
        if periods_per_week is not None:
            if periods_per_week < 1:
                raise serializers.ValidationError({
                    'periods_per_week': 'Periods per week must be at least 1'
                })
            if periods_per_week > 10:
                raise serializers.ValidationError({
                    'periods_per_week': 'Periods per week cannot exceed 10. '
                                       'Please verify this value is correct.'
                })

        return data

    def create(self, validated_data):
        """Create subject teacher assignment and set assigned_by from request"""
        from django.utils import timezone

        # Set assigned_by from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                validated_data['assigned_by'] = request.user.profile
            except Exception:
                pass

        # Set assigned_at timestamp
        validated_data['assigned_at'] = timezone.now()

        # Default is_active to True
        if 'is_active' not in validated_data:
            validated_data['is_active'] = True

        return super().create(validated_data)


class SectionTeachersSerializer(serializers.Serializer):
    """
    Serializer for viewing all teachers assigned to a section.
    Used in section detail view to show:
    - Primary class teacher
    - Assistant class teachers
    - All subject teachers
    """
    section_id = serializers.UUIDField()
    section_name = serializers.CharField()
    academic_year_name = serializers.CharField()

    class_teacher = serializers.SerializerMethodField()
    assistant_teachers = serializers.SerializerMethodField()
    subject_teachers = serializers.SerializerMethodField()

    def get_class_teacher(self, obj):
        """Get primary class teacher"""
        section = obj.get('section')
        if not section:
            return None

        primary_assignment = ClassTeacher.objects.filter(
            section=section,
            is_primary=True,
            academic_year=section.academic_year
        ).select_related('teacher', 'teacher__user').first()

        if not primary_assignment:
            return None

        return {
            'id': str(primary_assignment.id),
            'teacher_id': str(primary_assignment.teacher.id),
            'teacher_name': primary_assignment.teacher.full_name,
            'teacher_email': primary_assignment.teacher.user.email if primary_assignment.teacher.user else None,
            'assigned_at': primary_assignment.assigned_at,
        }

    def get_assistant_teachers(self, obj):
        """Get assistant class teachers (non-primary)"""
        section = obj.get('section')
        if not section:
            return []

        assistant_assignments = ClassTeacher.objects.filter(
            section=section,
            is_primary=False,
            academic_year=section.academic_year
        ).select_related('teacher', 'teacher__user')

        return [{
            'id': str(assignment.id),
            'teacher_id': str(assignment.teacher.id),
            'teacher_name': assignment.teacher.full_name,
            'teacher_email': assignment.teacher.user.email if assignment.teacher.user else None,
            'assigned_at': assignment.assigned_at,
        } for assignment in assistant_assignments]

    def get_subject_teachers(self, obj):
        """Get all subject teachers for this section"""
        section = obj.get('section')
        if not section:
            return []

        subject_assignments = SubjectTeacher.objects.filter(
            section=section,
            academic_year=section.academic_year,
            is_active=True
        ).select_related('teacher', 'teacher__user', 'subject').order_by('subject__name')

        return [{
            'id': str(assignment.id),
            'subject_id': str(assignment.subject.id),
            'subject_name': assignment.subject.name,
            'subject_code': assignment.subject.code,
            'teacher_id': str(assignment.teacher.id),
            'teacher_name': assignment.teacher.full_name,
            'teacher_email': assignment.teacher.user.email if assignment.teacher.user else None,
            'periods_per_week': assignment.periods_per_week,
        } for assignment in subject_assignments]
