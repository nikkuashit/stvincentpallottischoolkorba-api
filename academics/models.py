"""
Academics App - Academic Management

This module handles:
- Academic years
- Classes and grades
- Students and parents
- Subjects and courses
"""

import uuid
from django.db import models


class AcademicYear(models.Model):
    """Academic year configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='academic_years'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='academic_years'
    )

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = [['organization', 'school', 'name']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_current']),
        ]

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Class(models.Model):
    """Class/Grade configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='classes'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='classes'
    )

    name = models.CharField(max_length=100)
    grade = models.IntegerField()
    section = models.CharField(max_length=10)
    class_teacher = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_classes'
    )

    room_number = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['grade', 'section']
        unique_together = [['organization', 'school', 'grade', 'section']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Student(models.Model):
    """Student information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='students'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='students'
    )
    current_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    # Basic Information
    admission_number = models.CharField(max_length=50)
    roll_number = models.CharField(max_length=50, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ]
    )

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)

    # Academic
    admission_date = models.DateField()
    blood_group = models.CharField(max_length=10, blank=True)

    # Media
    photo = models.ImageField(upload_to='students/photos/', null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('graduated', 'Graduated'),
            ('transferred', 'Transferred')
        ],
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        unique_together = [['organization', 'school', 'admission_number']]
        indexes = [
            models.Index(fields=['organization', 'school', 'status']),
            models.Index(fields=['admission_number']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.admission_number}"


class Parent(models.Model):
    """Parent/Guardian information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='parents'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='parents'
    )
    students = models.ManyToManyField(
        Student,
        related_name='parents',
        through='StudentParent'
    )

    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    relation = models.CharField(
        max_length=20,
        choices=[
            ('father', 'Father'),
            ('mother', 'Mother'),
            ('guardian', 'Guardian')
        ]
    )

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)

    # Professional
    occupation = models.CharField(max_length=100, blank=True)
    organization_name = models.CharField(max_length=255, blank=True)

    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)

    # Media
    photo = models.ImageField(upload_to='parents/photos/', null=True, blank=True)

    # Status
    is_primary_contact = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relation})"


class StudentParent(models.Model):
    """Junction table for Student-Parent relationship"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='student_parents'
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['organization', 'student', 'parent']]
        indexes = [
            models.Index(fields=['organization', 'student']),
            models.Index(fields=['organization', 'parent']),
        ]

    def __str__(self):
        return f"{self.student} - {self.parent}"


class Subject(models.Model):
    """Subject/Course subjects"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = [['organization', 'school', 'code']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(models.Model):
    """Course assignment to classes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='courses'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='courses'
    )
    class_assigned = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    teacher = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_courses'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='courses'
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_assigned', 'subject']
        unique_together = [['organization', 'school', 'class_assigned', 'subject', 'academic_year']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.class_assigned.name}"
