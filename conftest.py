"""
Root pytest configuration and fixtures.

This file provides base fixtures for all tests including:
- Database setup
- Authentication fixtures
- API client fixtures
- Factory imports
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def db_setup(db):
    """Base fixture ensuring database is available."""
    pass


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def user(db):
    """Create a basic user for testing."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )
    return user


@pytest.fixture
def staff_user(db):
    """Create a staff user for testing."""
    user = User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True
    )
    return user


# =============================================================================
# API Client Fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an API client authenticated with a regular user."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an API client authenticated with an admin user."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    """Return an API client authenticated with a staff user."""
    refresh = RefreshToken.for_user(staff_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


# =============================================================================
# Tenant Fixtures
# =============================================================================

@pytest.fixture
def organization(db):
    """Create a test organization."""
    from tenants.models import Organization
    return Organization.objects.create(
        name='Test Organization',
        slug='test-org',
        email='org@example.com',
        is_active=True
    )


@pytest.fixture
def school(db, organization):
    """Create a test school linked to organization."""
    from tenants.models import School
    return School.objects.create(
        organization=organization,
        name='Test School',
        short_name='TS',
        slug='test-school',
        email='school@example.com',
        is_active=True
    )


# =============================================================================
# Factory Registration
# =============================================================================

# Register factories with pytest-factoryboy if available
try:
    from pytest_factoryboy import register
    from tests.factories.user_factories import UserFactory, UserProfileFactory
    from tests.factories.tenant_factories import OrganizationFactory, SchoolFactory
    from tests.factories.academic_factories import (
        AcademicYearFactory,
        GradeFactory,
        SectionFactory,
        StudentFactory,
        RoomLayoutFactory,
        DeskFactory,
        SeatingAssignmentFactory,
        StudentPhotoFactory,
    )
    from tests.factories.cms_factories import (
        NavigationMenuFactory,
        PageFactory,
        SectionModelFactory
    )

    # Register all factories
    register(UserFactory)
    register(UserProfileFactory)
    register(OrganizationFactory)
    register(SchoolFactory)
    register(AcademicYearFactory)
    register(GradeFactory)
    register(SectionFactory)
    register(StudentFactory)
    register(RoomLayoutFactory)
    register(DeskFactory)
    register(SeatingAssignmentFactory)
    register(StudentPhotoFactory)
    register(NavigationMenuFactory)
    register(PageFactory)
    register(SectionModelFactory)
except ImportError:
    # pytest-factoryboy not installed, factories available via direct import
    pass
