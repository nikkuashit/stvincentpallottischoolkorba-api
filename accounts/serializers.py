"""
Serializers for Accounts App - User Management
Simplified without multi-tenancy
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class JWTUserDetailsSerializer(serializers.ModelSerializer):
    """Custom serializer for dj-rest-auth JWT login response.
    Includes role from profile for RBAC.
    """
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['pk', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'role']
        read_only_fields = ['pk', 'is_staff', 'is_superuser', 'role']

    def get_role(self, obj):
        """Get role from user profile"""
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            if obj.is_superuser:
                return 'super_admin'
            elif obj.is_staff:
                return 'school_admin'
            return 'student'


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django User model"""
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login', 'role'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_role(self, obj):
        """Get role from user profile"""
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            if obj.is_superuser:
                return 'super_admin'
            elif obj.is_staff:
                return 'school_admin'
            return 'student'


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model with nested user data"""
    pk = serializers.IntegerField(source='user.pk', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    is_staff = serializers.BooleanField(source='user.is_staff', read_only=True)
    is_superuser = serializers.BooleanField(source='user.is_superuser', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'pk', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login',
            'role', 'phone', 'date_of_birth', 'gender',
            'address', 'city', 'state', 'postal_code',
            'avatar', 'bio',
            'employee_id', 'department', 'designation',
            'admission_no', 'roll_no',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'pk', 'created_at', 'updated_at']


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing users"""
    pk = serializers.IntegerField(source='user.pk', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    is_staff = serializers.BooleanField(source='user.is_staff', read_only=True)
    is_superuser = serializers.BooleanField(source='user.is_superuser', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'pk', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined',
            'role', 'phone', 'avatar'
        ]


class UserCreateSerializer(serializers.Serializer):
    """Serializer for creating new users"""
    # User fields
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)

    # Profile fields
    role = serializers.ChoiceField(
        choices=[
            'super_admin', 'school_admin', 'school_staff', 'parent', 'student'
        ],
        default='student'
    )
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other', ''],
        required=False,
        allow_blank=True
    )

    # Role-specific fields
    employee_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    admission_no = serializers.CharField(max_length=50, required=False, allow_blank=True)
    roll_no = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        """Create user and profile"""
        # Determine is_staff based on role
        role = validated_data.get('role', 'student')
        is_staff = role in ['super_admin', 'school_admin', 'school_staff']
        is_superuser = role == 'super_admin'

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=validated_data.get('is_active', True),
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            role=role,
            phone=validated_data.get('phone', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            gender=validated_data.get('gender', ''),
            employee_id=validated_data.get('employee_id', ''),
            department=validated_data.get('department', ''),
            designation=validated_data.get('designation', ''),
            admission_no=validated_data.get('admission_no', ''),
            roll_no=validated_data.get('roll_no', ''),
        )

        return profile


class UserUpdateSerializer(serializers.Serializer):
    """Serializer for updating existing users"""
    # User fields
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    # Profile fields
    role = serializers.ChoiceField(
        choices=[
            'super_admin', 'school_admin', 'school_staff', 'parent', 'student'
        ],
        required=False
    )
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other', ''],
        required=False,
        allow_blank=True
    )
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    # Role-specific fields
    employee_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    admission_no = serializers.CharField(max_length=50, required=False, allow_blank=True)
    roll_no = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """Update user and profile"""
        user = instance.user

        # Update user fields
        if 'email' in validated_data:
            user.email = validated_data['email']
        if 'first_name' in validated_data:
            user.first_name = validated_data['first_name']
        if 'last_name' in validated_data:
            user.last_name = validated_data['last_name']
        if 'is_active' in validated_data:
            user.is_active = validated_data['is_active']

        # Update is_staff/is_superuser based on role
        if 'role' in validated_data:
            role = validated_data['role']
            user.is_staff = role in ['super_admin', 'school_admin', 'school_staff']
            user.is_superuser = role == 'super_admin'
            instance.role = role

        user.save()

        # Update profile fields
        profile_fields = [
            'phone', 'date_of_birth', 'gender', 'address', 'city',
            'state', 'postal_code', 'bio', 'employee_id', 'department',
            'designation', 'admission_no', 'roll_no'
        ]

        for field in profile_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing user password (by admin)"""
    password = serializers.CharField(write_only=True, min_length=8)

    def save(self, user):
        """Set new password for user"""
        user.set_password(self.validated_data['password'])
        user.save()
        return user


class RoleSerializer(serializers.Serializer):
    """Serializer for role list"""
    id = serializers.CharField()
    name = serializers.CharField()
    display_name = serializers.CharField()
    description = serializers.CharField(required=False)
