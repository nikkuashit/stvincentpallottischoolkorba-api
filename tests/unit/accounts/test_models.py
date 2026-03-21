"""
Unit tests for accounts models.
"""

import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from tests.factories import UserFactory, UserProfileFactory


User = get_user_model()


@pytest.mark.django_db
class TestUserProfile:
    """Test cases for UserProfile model."""

    def test_create_user_profile(self):
        """Test creating a basic user profile."""
        profile = UserProfileFactory()

        assert profile.id is not None
        assert profile.user is not None
        assert profile.role in ['super_admin', 'school_admin', 'school_staff', 'parent', 'student']

    def test_user_profile_str_representation(self):
        """Test __str__ method returns expected format."""
        user = UserFactory(first_name='John', last_name='Doe')
        profile = UserProfileFactory(user=user, role='school_staff')

        expected = "John Doe - School Staff / Teacher"
        assert str(profile) == expected

    def test_user_profile_str_without_full_name(self):
        """Test __str__ method uses username when no full name."""
        user = UserFactory(username='johndoe', first_name='', last_name='')
        profile = UserProfileFactory(user=user, role='student')

        assert 'johndoe' in str(profile)

    def test_full_name_property(self):
        """Test full_name property returns correct value."""
        user = UserFactory(first_name='Jane', last_name='Smith')
        profile = UserProfileFactory(user=user)

        assert profile.full_name == 'Jane Smith'

    def test_full_name_property_fallback(self):
        """Test full_name property falls back to username."""
        user = UserFactory(username='testuser', first_name='', last_name='')
        profile = UserProfileFactory(user=user)

        assert profile.full_name == 'testuser'

    def test_admin_trait(self):
        """Test admin trait creates super_admin with correct permissions."""
        profile = UserProfileFactory(admin=True)

        assert profile.role == 'super_admin'
        assert profile.user.is_staff is True
        assert profile.user.is_superuser is True

    def test_school_admin_trait(self):
        """Test school_admin trait creates school_admin user."""
        profile = UserProfileFactory(school_admin=True)

        assert profile.role == 'school_admin'
        assert profile.user.is_staff is True

    def test_teacher_trait(self):
        """Test teacher trait creates school_staff with employee_id."""
        profile = UserProfileFactory(teacher=True)

        assert profile.role == 'school_staff'
        assert profile.employee_id.startswith('EMP')
        assert profile.department is not None
        assert profile.designation == 'Teacher'

    def test_student_trait(self):
        """Test student trait creates student with admission_no."""
        profile = UserProfileFactory(student=True)

        assert profile.role == 'student'
        assert profile.admission_no.startswith('SVP')
        assert profile.roll_no is not None

    def test_parent_trait(self):
        """Test parent trait creates parent user."""
        profile = UserProfileFactory(parent=True)

        assert profile.role == 'parent'

    def test_role_choices(self):
        """Test all valid role choices can be assigned."""
        valid_roles = ['super_admin', 'school_admin', 'school_staff', 'parent', 'student']

        for role in valid_roles:
            profile = UserProfileFactory(role=role)
            assert profile.role == role

    def test_user_profile_one_to_one_relationship(self):
        """Test that each user can only have one profile."""
        user = UserFactory()
        profile1 = UserProfileFactory(user=user)

        # Factory uses django_get_or_create, so it returns existing profile
        profile2 = UserProfileFactory(user=user)

        # Should be the same profile instance
        assert profile1.id == profile2.id
        assert UserProfile.objects.filter(user=user).count() == 1

    def test_timestamps(self):
        """Test that created_at and updated_at are set."""
        profile = UserProfileFactory()

        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert profile.created_at <= profile.updated_at
