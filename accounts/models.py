"""
Accounts App - User Management & Authentication

Simplified user model without multi-tenancy.
Uses Django's built-in User model with an extended UserProfile for role.
"""

import uuid
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extended user profile with role-based access control.
    Simplified single-tenant model.
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('school_admin', 'School Administrator'),
        ('school_staff', 'School Staff / Teacher'),
        ('parent', 'Parent / Guardian'),
        ('student', 'Student'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='student'
    )

    # Personal Information
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        blank=True
    )

    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Profile
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    # Role-specific fields
    # For staff/teachers
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    # For students
    admission_no = models.CharField(max_length=50, blank=True)
    roll_no = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
