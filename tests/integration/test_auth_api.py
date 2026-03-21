"""
Integration tests for authentication API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.integration
class TestAuthenticationAPI:
    """Test cases for authentication endpoints."""

    def test_login_success(self, api_client):
        """Test successful login returns JWT tokens."""
        user = UserFactory(password='testpass123')

        response = api_client.post('/auth/login/', {
            'username': user.username,
            'password': 'testpass123'
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data or 'key' in response.data

    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials returns error."""
        user = UserFactory(password='testpass123')

        response = api_client.post('/auth/login/', {
            'username': user.username,
            'password': 'wrongpassword'
        })

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]

    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent user returns error."""
        response = api_client.post('/auth/login/', {
            'username': 'nonexistent',
            'password': 'anypassword'
        })

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]

    def test_logout_authenticated_user(self, authenticated_client):
        """Test logout for authenticated user."""
        response = authenticated_client.post('/auth/logout/')

        assert response.status_code == status.HTTP_200_OK

    def test_token_refresh(self, api_client):
        """Test token refresh endpoint."""
        user = UserFactory(password='testpass123')

        # First login to get tokens
        login_response = api_client.post('/auth/login/', {
            'username': user.username,
            'password': 'testpass123'
        })

        # Check if we have refresh token in response
        if 'refresh' in login_response.data:
            refresh_token = login_response.data['refresh']

            # Try to refresh
            refresh_response = api_client.post('/auth/token/refresh/', {
                'refresh': refresh_token
            })

            assert refresh_response.status_code == status.HTTP_200_OK
            assert 'access' in refresh_response.data


@pytest.mark.django_db
@pytest.mark.integration
class TestUserRegistrationAPI:
    """Test cases for user registration endpoints."""

    def test_registration_success(self, api_client):
        """Test successful user registration."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }

        response = api_client.post('/auth/registration/', data)

        # Registration should return 201 Created or 200 OK
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_registration_password_mismatch(self, api_client):
        """Test registration fails with mismatched passwords."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass!'
        }

        response = api_client.post('/auth/registration/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_duplicate_username(self, api_client):
        """Test registration fails with duplicate username."""
        existing_user = UserFactory(username='existinguser')

        data = {
            'username': 'existinguser',
            'email': 'newemail@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }

        response = api_client.post('/auth/registration/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_weak_password(self, api_client):
        """Test registration fails with weak password."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': '123',
            'password2': '123'
        }

        response = api_client.post('/auth/registration/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.integration
class TestProtectedEndpoints:
    """Test access control on protected endpoints."""

    def test_unauthenticated_access_to_protected_endpoint(self, api_client):
        """Test that unauthenticated users can't access protected endpoints."""
        # Try to access admin-only endpoint without auth
        response = api_client.post('/cms/navigation-menus/', {
            'title': 'Test Menu',
            'slug': 'test-menu'
        })

        # Should be unauthorized or forbidden
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    def test_authenticated_read_access(self, authenticated_client):
        """Test authenticated users can read CMS content."""
        response = authenticated_client.get('/cms/navigation-menus/')

        assert response.status_code == status.HTTP_200_OK

    def test_admin_write_access(self, admin_client):
        """Test admin users can create CMS content."""
        response = admin_client.post('/cms/navigation-menus/', {
            'title': 'Test Menu',
            'slug': 'test-menu-admin',
            'menu_type': 'page',
            'display_order': 1
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_staff_write_access(self, staff_client):
        """Test staff users can create CMS content."""
        response = staff_client.post('/cms/navigation-menus/', {
            'title': 'Staff Test Menu',
            'slug': 'staff-test-menu',
            'menu_type': 'page',
            'display_order': 2
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_regular_user_cannot_write(self, authenticated_client):
        """Test regular users cannot create CMS content."""
        response = authenticated_client.post('/cms/navigation-menus/', {
            'title': 'Regular User Menu',
            'slug': 'regular-user-menu',
            'menu_type': 'page',
            'display_order': 3
        })

        # Should be forbidden for regular users
        assert response.status_code == status.HTTP_403_FORBIDDEN
