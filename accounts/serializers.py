"""
Serializers for Accounts App - User Management
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Role, UserProfile


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""

    class Meta:
        model = Role
        fields = [
            'id', 'organization', 'name', 'slug', 'description',
            'permissions', 'is_system_role', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django User model"""

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    user = UserSerializer(read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'organization', 'organization_name',
            'school', 'school_name', 'role', 'role_name',
            'employee_id', 'date_of_birth', 'gender',
            'phone', 'alternate_phone',
            'address_line1', 'address_line2', 'city', 'state',
            'country', 'postal_code',
            'avatar', 'bio', 'is_active', 'last_login_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login_at']


class UserCreateSerializer(serializers.Serializer):
    """Serializer for creating new users"""
    # User fields
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_staff = serializers.BooleanField(default=False)
    is_superuser = serializers.BooleanField(default=False)

    # Profile fields
    organization = serializers.UUIDField()
    school = serializers.UUIDField(required=False, allow_null=True)
    role = serializers.UUIDField()
    employee_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other'],
        required=False,
        allow_blank=True
    )

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
        # Extract user fields
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'first_name': validated_data.get('first_name', ''),
            'last_name': validated_data.get('last_name', ''),
            'is_staff': validated_data.get('is_staff', False),
            'is_superuser': validated_data.get('is_superuser', False),
        }

        # Create user
        user = User.objects.create_user(
            **user_data,
            password=validated_data['password']
        )

        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            organization_id=validated_data['organization'],
            school_id=validated_data.get('school'),
            role_id=validated_data['role'],
            employee_id=validated_data.get('employee_id', ''),
            phone=validated_data.get('phone', ''),
            gender=validated_data.get('gender', ''),
        )

        return profile


class UserUpdateSerializer(serializers.Serializer):
    """Serializer for updating existing users"""
    # User fields
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)

    # Profile fields
    role = serializers.UUIDField(required=False)
    school = serializers.UUIDField(required=False, allow_null=True)
    employee_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other'],
        required=False,
        allow_blank=True
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

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
        if 'is_staff' in validated_data:
            user.is_staff = validated_data['is_staff']
        if 'is_superuser' in validated_data:
            user.is_superuser = validated_data['is_superuser']

        user.save()

        # Update profile fields
        profile_fields = [
            'role_id', 'school_id', 'employee_id', 'phone', 'gender',
            'date_of_birth', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'postal_code', 'bio'
        ]

        for field in profile_fields:
            key = field.replace('_id', '')
            if key in validated_data:
                setattr(instance, field, validated_data[key])

        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing user password"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def save(self):
        """Change password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
