"""
HR Signals - Auto-create EmployeeProfile for staff users
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from datetime import date


@receiver(post_save, sender=User)
def create_employee_profile_for_staff(sender, instance, created, **kwargs):
    """
    Auto-create EmployeeProfile when a staff user is created or updated to staff.
    """
    from .models import EmployeeProfile, Department, Designation

    # Only proceed if user is staff
    if not instance.is_staff:
        return

    # Check if EmployeeProfile already exists
    if EmployeeProfile.objects.filter(user=instance).exists():
        return

    # Get or create default department
    dept, _ = Department.objects.get_or_create(
        name='Administration',
        defaults={
            'code': 'ADMIN',
            'description': 'Administrative department',
            'is_active': True
        }
    )

    # Get or create default designation
    desg, _ = Designation.objects.get_or_create(
        name='Staff',
        defaults={
            'code': 'STAFF',
            'description': 'General staff',
            'level': 1,
            'is_active': True
        }
    )

    # Generate employee code
    employee_code = f'EMP{instance.pk:04d}'

    # Ensure unique employee_code
    counter = 1
    base_code = employee_code
    while EmployeeProfile.objects.filter(employee_code=employee_code).exists():
        employee_code = f'{base_code}-{counter}'
        counter += 1

    # Create EmployeeProfile
    EmployeeProfile.objects.create(
        user=instance,
        employee_code=employee_code,
        department=dept,
        designation=desg,
        joining_date=date.today(),
        employment_type='permanent',
        employment_status='active'
    )
