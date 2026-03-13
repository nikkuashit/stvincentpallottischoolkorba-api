"""
Serializers for Academics App - Students, Classes, Academic Years
"""

import re
from datetime import datetime
from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from accounts.models import UserProfile
from .models import AcademicYear, Class, Student, Parent, StudentParent, Subject, Course


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


def generate_username(first_name, last_name):
    """
    Generate a unique username based on first_name and last_name.
    Format: firstname.lastname (all lowercase, no special chars)
    If exists, append number: firstname.lastname1, firstname.lastname2, etc.
    """
    # Clean and normalize names
    first = re.sub(r'[^a-zA-Z]', '', first_name.lower().strip())
    last = re.sub(r'[^a-zA-Z]', '', last_name.lower().strip())

    if not first:
        first = 'student'
    if not last:
        last = 'user'

    base_username = f"{first}.{last}"
    username = base_username
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    return username


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

    - Username: auto-generated from first_name.last_name (with number if exists)
    - Password: username + '123'
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

        # Generate username and password
        username = generate_username(first_name, last_name)
        password = f"{username}123"

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
