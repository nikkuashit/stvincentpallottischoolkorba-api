#!/usr/bin/env python
"""
Script to create test parent with 2 children and TC request workflow
Run with: pipenv run python create_parent_test_data.py
"""

import os
import sys
import django
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_api.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from academics.models import AcademicYear, Class, Student, Parent, StudentParent
from workflows.models import (
    RequestType, ApprovalWorkflow, ApprovalStep, ClearanceType
)

def create_test_data():
    print("Creating test parent data...")

    # 1. Create or get academic year
    academic_year, created = AcademicYear.objects.get_or_create(
        name='2024-2025',
        defaults={
            'start_date': date(2024, 4, 1),
            'end_date': date(2025, 3, 31),
            'is_current': True,
            'is_active': True,
        }
    )
    print(f"Academic Year: {academic_year.name} {'(created)' if created else '(exists)'}")

    # 2. Create classes
    class_7a, created = Class.objects.get_or_create(
        grade=7,
        section='A',
        defaults={
            'name': 'Class 7-A',
            'room_number': '201',
            'capacity': 40,
            'is_active': True,
        }
    )
    print(f"Class: {class_7a.name} {'(created)' if created else '(exists)'}")

    class_5a, created = Class.objects.get_or_create(
        grade=5,
        section='A',
        defaults={
            'name': 'Class 5-A',
            'room_number': '105',
            'capacity': 40,
            'is_active': True,
        }
    )
    print(f"Class: {class_5a.name} {'(created)' if created else '(exists)'}")

    # 3. Create parent user
    parent_user, created = User.objects.get_or_create(
        username='rajesh.sharma',
        defaults={
            'email': 'rajesh.sharma@example.com',
            'first_name': 'Rajesh',
            'last_name': 'Sharma',
            'is_active': True,
        }
    )
    if created:
        parent_user.set_password('Parent@123')
        parent_user.save()
        print(f"Parent User: rajesh.sharma (created)")
    else:
        print(f"Parent User: rajesh.sharma (exists)")

    # 4. Create parent user profile
    parent_profile, created = UserProfile.objects.get_or_create(
        user=parent_user,
        defaults={
            'role': 'parent',
            'phone': '+91 9876543210',
            'gender': 'male',
            'address': '123 Green Park Colony, Korba',
            'city': 'Korba',
            'state': 'Chhattisgarh',
            'postal_code': '495677',
        }
    )
    print(f"Parent Profile: {parent_profile} {'(created)' if created else '(exists)'}")

    # 5. Create parent record
    parent, created = Parent.objects.get_or_create(
        email='rajesh.sharma@example.com',
        defaults={
            'user_profile': parent_profile,
            'first_name': 'Rajesh',
            'last_name': 'Sharma',
            'relation': 'father',
            'phone': '+91 9876543210',
            'occupation': 'Business',
            'organization_name': 'Sharma Enterprises',
            'address_line1': '123 Green Park Colony',
            'city': 'Korba',
            'state': 'Chhattisgarh',
            'country': 'India',
            'postal_code': '495677',
            'is_primary_contact': True,
            'is_active': True,
        }
    )
    print(f"Parent Record: {parent} {'(created)' if created else '(exists)'}")

    # 6. Create first student (Aarav - Class 7)
    student1, created = Student.objects.get_or_create(
        admission_number='2024001',
        defaults={
            'current_class': class_7a,
            'academic_year': academic_year,
            'roll_number': '7A01',
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'date_of_birth': date(2012, 5, 15),
            'gender': 'male',
            'email': 'aarav.sharma@student.svps.edu',
            'phone': '+91 9876543211',
            'address_line1': '123 Green Park Colony',
            'city': 'Korba',
            'state': 'Chhattisgarh',
            'country': 'India',
            'postal_code': '495677',
            'admission_date': date(2019, 4, 1),
            'blood_group': 'B+',
            'status': 'active',
        }
    )
    print(f"Student 1: {student1} {'(created)' if created else '(exists)'}")

    # 7. Create second student (Ananya - Class 5)
    student2, created = Student.objects.get_or_create(
        admission_number='2024002',
        defaults={
            'current_class': class_5a,
            'academic_year': academic_year,
            'roll_number': '5A01',
            'first_name': 'Ananya',
            'last_name': 'Sharma',
            'date_of_birth': date(2014, 8, 20),
            'gender': 'female',
            'email': 'ananya.sharma@student.svps.edu',
            'phone': '+91 9876543212',
            'address_line1': '123 Green Park Colony',
            'city': 'Korba',
            'state': 'Chhattisgarh',
            'country': 'India',
            'postal_code': '495677',
            'admission_date': date(2021, 4, 1),
            'blood_group': 'A+',
            'status': 'active',
        }
    )
    print(f"Student 2: {student2} {'(created)' if created else '(exists)'}")

    # 8. Link students to parent
    sp1, created = StudentParent.objects.get_or_create(
        student=student1,
        parent=parent,
        defaults={'is_primary': True}
    )
    print(f"Link: {student1.first_name} -> {parent.first_name} {'(created)' if created else '(exists)'}")

    sp2, created = StudentParent.objects.get_or_create(
        student=student2,
        parent=parent,
        defaults={'is_primary': True}
    )
    print(f"Link: {student2.first_name} -> {parent.first_name} {'(created)' if created else '(exists)'}")

    # 9. Create TC approval workflow
    tc_workflow, created = ApprovalWorkflow.objects.get_or_create(
        slug='tc-approval',
        defaults={
            'name': 'TC Approval Workflow',
            'description': 'Multi-step approval workflow for Transfer Certificate requests',
            'is_sequential': True,
            'is_active': True,
        }
    )
    print(f"Workflow: {tc_workflow.name} {'(created)' if created else '(exists)'}")

    # 10. Create approval steps
    steps = [
        {
            'name': 'Class Teacher Approval',
            'description': 'Class teacher reviews and approves the TC request',
            'step_order': 1,
            'approver_type': 'class_teacher',
            'can_reject': True,
        },
        {
            'name': 'Principal Approval',
            'description': 'Principal gives final approval for TC',
            'step_order': 2,
            'approver_type': 'role',
            'approver_role': 'school_admin',
            'can_reject': True,
        },
    ]

    for step_data in steps:
        step, created = ApprovalStep.objects.get_or_create(
            workflow=tc_workflow,
            step_order=step_data['step_order'],
            defaults=step_data
        )
        print(f"  Step {step_data['step_order']}: {step.name} {'(created)' if created else '(exists)'}")

    # 11. Create clearance types for TC
    clearances = [
        {
            'name': 'Library Clearance',
            'slug': 'library',
            'department': 'Library',
            'clearance_role': 'school_staff',
            'clearance_order': 1,
            'check_description': 'No pending library books or fines',
        },
        {
            'name': 'Accounts Clearance',
            'slug': 'accounts',
            'department': 'Accounts',
            'clearance_role': 'school_staff',
            'clearance_order': 2,
            'check_description': 'No pending fee dues',
        },
        {
            'name': 'Admin Clearance',
            'slug': 'admin',
            'department': 'Administration',
            'clearance_role': 'school_staff',
            'clearance_order': 3,
            'check_description': 'All records updated, ID card returned',
        },
    ]

    for cl_data in clearances:
        cl, created = ClearanceType.objects.get_or_create(
            slug=cl_data['slug'],
            defaults=cl_data
        )
        print(f"Clearance Type: {cl.name} {'(created)' if created else '(exists)'}")

    # 12. Create TC Request Type
    tc_request_type, created = RequestType.objects.get_or_create(
        slug='transfer-certificate',
        defaults={
            'name': 'Transfer Certificate (TC)',
            'description': 'Request for Transfer Certificate to leave the school',
            'category': 'administrative',
            'requires_clearance': True,
            'requires_payment': True,
            'payment_amount': 500.00,
            'form_schema': {
                'fields': [
                    {
                        'name': 'reason',
                        'type': 'textarea',
                        'label': 'Reason for Transfer',
                        'required': True,
                    },
                    {
                        'name': 'transfer_date',
                        'type': 'date',
                        'label': 'Expected Date of Leaving',
                        'required': True,
                    },
                    {
                        'name': 'new_school',
                        'type': 'text',
                        'label': 'Name of New School (if known)',
                        'required': False,
                    },
                ]
            },
            'allowed_roles': ['parent'],
            'approval_workflow': tc_workflow,
            'is_active': True,
            'display_order': 1,
        }
    )
    print(f"Request Type: {tc_request_type.name} {'(created)' if created else '(exists)'}")

    # Summary
    print("\n" + "="*60)
    print("TEST DATA CREATED SUCCESSFULLY!")
    print("="*60)
    print("\nPARENT CREDENTIALS:")
    print(f"  Username: rajesh.sharma")
    print(f"  Password: Parent@123")
    print(f"  Email: rajesh.sharma@example.com")
    print(f"  Role: Parent")
    print("\nMAPPED CHILDREN:")
    print(f"  1. Aarav Sharma (Admission: 2024001, Class: 7-A)")
    print(f"  2. Ananya Sharma (Admission: 2024002, Class: 5-A)")
    print("\nAVAILABLE REQUESTS:")
    print(f"  - Transfer Certificate (TC) - requires clearance from Library, Accounts, Admin")
    print("="*60)

if __name__ == '__main__':
    create_test_data()
