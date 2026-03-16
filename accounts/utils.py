"""
Credential Generation Utilities for User Onboarding

Provides functions for auto-generating usernames and passwords
for admin-managed user registration.

This module centralizes all credential generation logic to avoid duplication
across accounts and academics apps.
"""

import secrets
import string
from django.contrib.auth.models import User


# Characters for password generation (excluding ambiguous: 0, O, l, 1, I)
PASSWORD_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'


def generate_username(role: str, identifier: str) -> str:
    """
    Generate a unique username based on role and identifier.

    Args:
        role: User role ('parent', 'school_staff', 'student', etc.)
        identifier: Role-specific identifier (phone, employee_id, admission_no)

    Returns:
        Unique username string

    Examples:
        - generate_username('parent', '9876543210') -> 'parent_9876543210'
        - generate_username('school_staff', 'EMP001') -> 'staff_emp001'
        - generate_username('student', '2024001') -> 'student_2024001'
    """
    # Normalize identifier: lowercase, remove spaces
    clean_identifier = identifier.lower().strip().replace(' ', '_')

    # Map role to username prefix
    prefix_map = {
        'parent': 'parent',
        'school_staff': 'staff',
        'student': 'student',
        'school_admin': 'admin',
        'super_admin': 'superadmin',
    }

    prefix = prefix_map.get(role, role)
    base_username = f"{prefix}_{clean_identifier}"

    # Ensure uniqueness
    username = base_username
    suffix = 1

    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{suffix}"
        suffix += 1

    return username


def generate_password(length: int = 8) -> str:
    """
    Generate a secure random password.

    Uses alphanumeric characters excluding ambiguous ones (0, O, l, 1, I)
    to improve readability when shared via SMS.

    Args:
        length: Password length (default: 8, minimum: 6)

    Returns:
        Random password string with mix of uppercase, lowercase, and digits
    """
    if length < 6:
        length = 6

    # Ensure at least one of each type
    password_chars = [
        secrets.choice(string.ascii_uppercase.replace('O', '').replace('I', '')),
        secrets.choice(string.ascii_lowercase.replace('l', '')),
        secrets.choice('23456789'),  # Digits without 0 and 1
    ]

    # Fill remaining with random chars
    remaining_length = length - len(password_chars)
    password_chars.extend(
        secrets.choice(PASSWORD_CHARS) for _ in range(remaining_length)
    )

    # Shuffle to avoid predictable pattern
    password_list = list(password_chars)
    secrets.SystemRandom().shuffle(password_list)

    return ''.join(password_list)


def get_identifier_for_role(role: str, data: dict) -> str:
    """
    Extract the appropriate identifier for username generation based on role.

    Args:
        role: User role
        data: Dictionary containing user data

    Returns:
        Identifier string for username generation

    Raises:
        ValueError: If no suitable identifier found for the role
    """
    if role == 'parent':
        # Parents: use phone number
        identifier = data.get('phone', '').strip()
        if not identifier:
            # Fallback to email prefix
            email = data.get('email', '')
            identifier = email.split('@')[0] if email else ''
        if not identifier:
            raise ValueError("Phone or email required for parent account")
        return identifier

    elif role == 'student':
        # Students: use admission number
        identifier = data.get('admission_no', '').strip()
        if not identifier:
            raise ValueError("Admission number required for student account")
        return identifier

    elif role in ('school_staff', 'school_admin'):
        # Staff: use employee ID or email prefix
        identifier = data.get('employee_id', '').strip()
        if not identifier:
            email = data.get('email', '')
            identifier = email.split('@')[0] if email else ''
        if not identifier:
            raise ValueError("Employee ID or email required for staff account")
        return identifier

    else:
        # Fallback: use email prefix or raise error
        email = data.get('email', '')
        if email:
            return email.split('@')[0]
        raise ValueError(f"Cannot determine identifier for role: {role}")
