"""
Accounts Signals - Auto-create related records based on user role

This module handles auto-creation of role-specific records when UserProfile is created:
- role='student' -> creates Student record
- role='parent' -> creates Parent record
- role='school_staff' or 'school_admin' -> EmployeeProfile handled by hr.signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date

from .models import UserProfile


@receiver(post_save, sender=UserProfile)
def create_student_for_student_role(sender, instance, created, **kwargs):
    """
    Auto-create or link Student record when a UserProfile is created/updated with role='student'.
    Links the UserProfile to the Student record via user_profile field.

    Logic:
    1. If UserProfile has admission_no, try to find and link existing Student
    2. If no existing Student found, create a new one
    """
    if instance.role != 'student':
        return

    from academics.models import Student, AcademicYear

    # Check if Student already exists for this profile
    if hasattr(instance, 'student_record') and instance.student_record:
        return

    # Check if a Student with this user_profile already exists
    if Student.objects.filter(user_profile=instance).exists():
        return

    # If UserProfile has admission_no, try to find existing Student
    if instance.admission_no:
        existing_student = Student.objects.filter(
            admission_number=instance.admission_no,
            user_profile__isnull=True  # Not linked to any user yet
        ).first()

        if existing_student:
            # Link existing Student to this UserProfile
            existing_student.user_profile = instance
            existing_student.save(update_fields=['user_profile'])
            return

    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()

    # Generate admission number if not provided
    admission_number = instance.admission_no
    if not admission_number:
        # Generate a unique admission number
        year_prefix = date.today().strftime('%Y')
        last_student = Student.objects.filter(
            admission_number__startswith=year_prefix
        ).order_by('-admission_number').first()

        if last_student:
            try:
                last_seq = int(last_student.admission_number[-4:])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        admission_number = f"{year_prefix}{new_seq:04d}"

    # Create new Student record with data from UserProfile
    Student.objects.create(
        user_profile=instance,
        admission_number=admission_number,
        first_name=instance.user.first_name or 'Unknown',
        last_name=instance.user.last_name or 'Student',
        date_of_birth=instance.date_of_birth or date.today(),
        gender=instance.gender or 'other',
        email=instance.user.email,
        phone=instance.phone,
        address_line1=instance.address or 'Not provided',
        city=instance.city or 'Not provided',
        state=instance.state or 'Not provided',
        postal_code=instance.postal_code or '000000',
        admission_date=date.today(),
        academic_year=current_year,
        status='active'
    )


@receiver(post_save, sender=UserProfile)
def create_parent_for_parent_role(sender, instance, created, **kwargs):
    """
    Auto-create Parent record when a UserProfile is created/updated with role='parent'.
    Links the UserProfile to the Parent record via user_profile field.
    """
    if instance.role != 'parent':
        return

    from academics.models import Parent

    # Check if Parent already exists for this profile
    if hasattr(instance, 'parent_record') and instance.parent_record:
        return

    # Check if a Parent with this user_profile already exists
    if Parent.objects.filter(user_profile=instance).exists():
        return

    # Create Parent record with data from UserProfile
    Parent.objects.create(
        user_profile=instance,
        first_name=instance.user.first_name or 'Unknown',
        last_name=instance.user.last_name or 'Parent',
        relation='guardian',  # Default, can be updated later
        email=instance.user.email or f'{instance.user.username}@example.com',
        phone=instance.phone or '0000000000',
        address_line1=instance.address or 'Not provided',
        city=instance.city or 'Not provided',
        state=instance.state or 'Not provided',
        postal_code=instance.postal_code or '000000',
        is_primary_contact=True,
        is_active=True
    )
