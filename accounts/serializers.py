"""
Serializers for Accounts App - User Management
Simplified without multi-tenancy
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile
from .utils import generate_username, generate_password, get_identifier_for_role


class JWTUserDetailsSerializer(serializers.ModelSerializer):
    """Custom serializer for dj-rest-auth JWT login response.
    Includes role from profile for RBAC.
    """
    role = serializers.SerializerMethodField()
    must_change_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['pk', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'role', 'must_change_password']
        read_only_fields = ['pk', 'is_staff', 'is_superuser', 'role', 'must_change_password']

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

    def get_must_change_password(self, obj):
        """Check if user must change password on login"""
        try:
            return obj.profile.must_change_password
        except UserProfile.DoesNotExist:
            return False


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
            'must_change_password',
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
    """
    Serializer for creating new users.

    Supports auto-credential generation when auto_generate_credentials=True.
    In this mode, username and password are auto-generated based on role:
    - Parent: username from phone (parent_9876543210)
    - Staff: username from employee_id or email
    - Student: username from admission_no
    """
    # User fields
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True)
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

    # Auto-generation control
    auto_generate_credentials = serializers.BooleanField(default=False)

    def validate_username(self, value):
        """Check if username already exists (only if provided)"""
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        """Check if email already exists (only if provided)"""
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate(self, data):
        """
        Validate data based on auto_generate_credentials flag.
        If auto-generation is off, username, email, and password are required.
        If auto-generation is on, role-specific identifiers are required.
        """
        auto_generate = data.get('auto_generate_credentials', False)
        role = data.get('role', 'student')

        if not auto_generate:
            # Manual mode: username, email, password required
            if not data.get('username'):
                raise serializers.ValidationError({'username': 'Username is required when not auto-generating'})
            if not data.get('email'):
                raise serializers.ValidationError({'email': 'Email is required when not auto-generating'})
            if not data.get('password'):
                raise serializers.ValidationError({'password': 'Password is required when not auto-generating'})
        else:
            # Auto-generate mode: validate role-specific identifiers
            try:
                get_identifier_for_role(role, data)
            except ValueError as e:
                raise serializers.ValidationError({'auto_generate_credentials': str(e)})

        return data

    def create(self, validated_data):
        """Create user and profile with optional auto-credential generation"""
        auto_generate = validated_data.pop('auto_generate_credentials', False)
        role = validated_data.get('role', 'student')

        # Store generated credentials for response
        generated_credentials = None

        if auto_generate:
            # Auto-generate username if not provided
            if not validated_data.get('username'):
                identifier = get_identifier_for_role(role, validated_data)
                validated_data['username'] = generate_username(role, identifier)

            # Auto-generate password if not provided
            if not validated_data.get('password'):
                validated_data['password'] = generate_password()

            # Store for response
            generated_credentials = {
                'username': validated_data['username'],
                'password': validated_data['password'],
            }

        # Determine is_staff based on role
        is_staff = role in ['super_admin', 'school_admin', 'school_staff']
        is_superuser = role == 'super_admin'

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=validated_data.get('is_active', True),
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

        # Create profile with must_change_password=True for auto-generated credentials
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
            must_change_password=auto_generate,  # Force password change for auto-generated
        )

        # Attach generated credentials to profile for serialization
        if generated_credentials:
            profile._generated_credentials = generated_credentials

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


class SelfPasswordChangeSerializer(serializers.Serializer):
    """Serializer for users to change their own password"""
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_username = serializers.CharField(max_length=150, required=False)

    def validate_new_username(self, value):
        """Check if new username is available"""
        user = self.context.get('user')
        if value and value != user.username:
            if User.objects.filter(username=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError("Username already taken")
        return value

    def validate(self, data):
        """Validate current password if user is not forced to change"""
        user = self.context.get('user')
        profile = getattr(user, 'profile', None)

        # If must_change_password is True, don't require current password
        if profile and profile.must_change_password:
            return data

        # Otherwise, require current password verification
        current_password = data.get('current_password')
        if not current_password:
            raise serializers.ValidationError({
                'current_password': 'Current password is required'
            })

        if not user.check_password(current_password):
            raise serializers.ValidationError({
                'current_password': 'Current password is incorrect'
            })

        return data

    def save(self):
        """Update password and optionally username"""
        user = self.context.get('user')
        validated_data = self.validated_data

        # Update password
        user.set_password(validated_data['new_password'])

        # Update username if provided
        if validated_data.get('new_username'):
            user.username = validated_data['new_username']

        user.save()

        # Clear must_change_password flag
        if hasattr(user, 'profile'):
            user.profile.must_change_password = False
            user.profile.save()

        return user


class RoleSerializer(serializers.Serializer):
    """Serializer for role list"""
    id = serializers.CharField()
    name = serializers.CharField()
    display_name = serializers.CharField()
    description = serializers.CharField(required=False)


class BulkUserImportSerializer(serializers.Serializer):
    """
    Serializer for bulk user import from Excel file.

    Accepts an Excel file with user data and imports all valid rows.
    Returns success/error details for each row.
    """
    file = serializers.FileField(
        help_text="Excel file (.xlsx) containing user data"
    )
    role = serializers.ChoiceField(
        choices=['school_staff', 'parent', 'student'],
        help_text="Role for all imported users"
    )
    send_sms = serializers.BooleanField(
        default=False,
        help_text="Send credentials via SMS after import"
    )

    def validate_file(self, value):
        """Validate that the file is an Excel file"""
        if not value.name.endswith('.xlsx'):
            raise serializers.ValidationError(
                "Only .xlsx files are supported. Please use the template."
            )
        # Check file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "File size exceeds 5MB limit."
            )
        return value


class BulkImportResultSerializer(serializers.Serializer):
    """Serializer for bulk import result"""
    total_rows = serializers.IntegerField()
    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    created_users = serializers.ListField(child=serializers.DictField())
    errors = serializers.ListField(child=serializers.DictField())


class UserCreateResponseSerializer(serializers.ModelSerializer):
    """
    Response serializer for user creation that includes generated credentials.
    Used when auto_generate_credentials=True to return the credentials for SMS.
    """
    pk = serializers.IntegerField(source='user.pk', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    generated_credentials = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'pk', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'role', 'phone', 'employee_id', 'admission_no',
            'must_change_password', 'generated_credentials', 'created_at'
        ]

    def get_generated_credentials(self, obj):
        """Return generated credentials if available (only on creation)"""
        return getattr(obj, '_generated_credentials', None)
