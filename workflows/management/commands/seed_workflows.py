"""
Management command to seed workflow data

Creates:
- TC Clearance Types (Class Teacher -> Library -> Transport -> Accounts -> Admin -> Principal)
- TC Approval Workflow with steps
- Common request types (TC, Leave, Certificate, etc.)
"""

from django.core.management.base import BaseCommand
from workflows.models import (
    RequestType,
    ApprovalWorkflow,
    ApprovalStep,
    ClearanceType,
)


class Command(BaseCommand):
    help = 'Seeds workflow data including clearance types and request types'

    def handle(self, *args, **options):
        self.stdout.write('Seeding workflow data...')

        # Create TC Clearance Types
        self.create_clearance_types()

        # Create Approval Workflows
        self.create_approval_workflows()

        # Create Request Types
        self.create_request_types()

        self.stdout.write(self.style.SUCCESS('Successfully seeded workflow data!'))

    def create_clearance_types(self):
        """Create TC clearance types in order"""
        clearance_types = [
            {
                'name': 'Class Teacher Clearance',
                'slug': 'class-teacher-clearance',
                'description': 'Clearance from the student\'s class teacher',
                'department': 'Academic',
                'clearance_role': 'school_staff',
                'clearance_order': 1,
                'check_description': 'Verify student has no pending assignments, no disciplinary issues, and all academic records are updated.',
            },
            {
                'name': 'Library Clearance',
                'slug': 'library-clearance',
                'description': 'Clearance from the library department',
                'department': 'Library',
                'clearance_role': 'school_staff',
                'clearance_order': 2,
                'check_description': 'Verify all library books are returned and no library dues pending.',
            },
            {
                'name': 'Transport Clearance',
                'slug': 'transport-clearance',
                'description': 'Clearance from the transport department',
                'department': 'Transport',
                'clearance_role': 'school_staff',
                'clearance_order': 3,
                'check_description': 'Verify all transport fees are cleared and bus pass is returned.',
            },
            {
                'name': 'Accounts Clearance',
                'slug': 'accounts-clearance',
                'description': 'Clearance from the accounts/finance department',
                'department': 'Finance',
                'clearance_role': 'school_staff',
                'clearance_order': 4,
                'check_description': 'Verify all school fees, exam fees, and other dues are cleared.',
            },
            {
                'name': 'Admin Clearance',
                'slug': 'admin-clearance',
                'description': 'Clearance from the administrative department',
                'department': 'Administration',
                'clearance_role': 'school_staff',
                'clearance_order': 5,
                'check_description': 'Verify all administrative formalities are completed, ID card returned, and student records are complete.',
            },
            {
                'name': 'Principal Clearance',
                'slug': 'principal-clearance',
                'description': 'Final clearance from the Principal',
                'department': 'Principal Office',
                'clearance_role': 'school_admin',
                'clearance_order': 6,
                'check_description': 'Final review and approval of the Transfer Certificate application.',
            },
        ]

        for data in clearance_types:
            obj, created = ClearanceType.objects.update_or_create(
                slug=data['slug'],
                defaults=data
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action}: {obj.name}')

    def create_approval_workflows(self):
        """Create approval workflows"""
        workflows = [
            {
                'name': 'TC Request Workflow',
                'slug': 'tc-request-workflow',
                'description': 'Multi-level approval workflow for Transfer Certificate requests with clearances',
                'is_sequential': True,
                'steps': [
                    {
                        'name': 'Class Teacher Approval',
                        'step_order': 1,
                        'approver_type': 'class_teacher',
                        'description': 'Class teacher reviews and approves the TC request',
                        'requires_comment': True,
                    },
                    {
                        'name': 'Admin Review',
                        'step_order': 2,
                        'approver_type': 'role',
                        'approver_role': 'school_staff',
                        'department': 'Administration',
                        'description': 'Admin staff reviews clearances and documentation',
                    },
                    {
                        'name': 'Principal Approval',
                        'step_order': 3,
                        'approver_type': 'role',
                        'approver_role': 'school_admin',
                        'description': 'Final approval by Principal',
                        'requires_comment': False,
                    },
                ]
            },
            {
                'name': 'Leave Application Workflow',
                'slug': 'leave-application-workflow',
                'description': 'Approval workflow for student leave applications',
                'is_sequential': True,
                'steps': [
                    {
                        'name': 'Class Teacher Approval',
                        'step_order': 1,
                        'approver_type': 'class_teacher',
                        'description': 'Class teacher reviews and approves the leave request',
                    },
                ]
            },
            {
                'name': 'Certificate Request Workflow',
                'slug': 'certificate-request-workflow',
                'description': 'Approval workflow for certificate requests (Bonafide, Character, etc.)',
                'is_sequential': True,
                'steps': [
                    {
                        'name': 'Admin Approval',
                        'step_order': 1,
                        'approver_type': 'role',
                        'approver_role': 'school_staff',
                        'department': 'Administration',
                        'description': 'Admin staff verifies and processes the certificate request',
                    },
                ]
            },
            {
                'name': 'Fee Concession Workflow',
                'slug': 'fee-concession-workflow',
                'description': 'Approval workflow for fee concession requests',
                'is_sequential': True,
                'steps': [
                    {
                        'name': 'Accounts Review',
                        'step_order': 1,
                        'approver_type': 'role',
                        'approver_role': 'school_staff',
                        'department': 'Finance',
                        'description': 'Accounts department reviews the fee concession request',
                    },
                    {
                        'name': 'Principal Approval',
                        'step_order': 2,
                        'approver_type': 'role',
                        'approver_role': 'school_admin',
                        'description': 'Principal approves fee concession',
                        'requires_comment': True,
                    },
                ]
            },
        ]

        for workflow_data in workflows:
            steps_data = workflow_data.pop('steps')
            workflow, created = ApprovalWorkflow.objects.update_or_create(
                slug=workflow_data['slug'],
                defaults=workflow_data
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action} workflow: {workflow.name}')

            # Create/update steps
            for step_data in steps_data:
                step_data['workflow'] = workflow
                step, step_created = ApprovalStep.objects.update_or_create(
                    workflow=workflow,
                    step_order=step_data['step_order'],
                    defaults=step_data
                )
                step_action = 'Created' if step_created else 'Updated'
                self.stdout.write(f'    {step_action} step: {step.name}')

    def create_request_types(self):
        """Create common request types"""
        tc_workflow = ApprovalWorkflow.objects.filter(slug='tc-request-workflow').first()
        leave_workflow = ApprovalWorkflow.objects.filter(slug='leave-application-workflow').first()
        certificate_workflow = ApprovalWorkflow.objects.filter(slug='certificate-request-workflow').first()
        fee_workflow = ApprovalWorkflow.objects.filter(slug='fee-concession-workflow').first()

        request_types = [
            {
                'name': 'Transfer Certificate (TC)',
                'slug': 'transfer-certificate',
                'description': 'Request for Transfer Certificate when leaving the school',
                'category': 'administrative',
                'requires_clearance': True,
                'requires_payment': True,
                'payment_amount': 500.00,
                'approval_workflow': tc_workflow,
                'allowed_roles': ['parent'],
                'display_order': 1,
                'form_schema': {
                    'fields': [
                        {'name': 'reason', 'type': 'textarea', 'label': 'Reason for Transfer', 'required': True},
                        {'name': 'transfer_to', 'type': 'text', 'label': 'Transferring To (School/City)', 'required': True},
                        {'name': 'last_working_day', 'type': 'date', 'label': 'Last Working Day', 'required': True},
                    ]
                }
            },
            {
                'name': 'Leave Application',
                'slug': 'leave-application',
                'description': 'Apply for student leave',
                'category': 'academic',
                'requires_clearance': False,
                'requires_payment': False,
                'approval_workflow': leave_workflow,
                'allowed_roles': ['parent', 'student'],
                'display_order': 2,
                'form_schema': {
                    'fields': [
                        {'name': 'leave_type', 'type': 'select', 'label': 'Leave Type', 'required': True, 'options': ['Sick Leave', 'Personal Leave', 'Family Emergency', 'Other']},
                        {'name': 'from_date', 'type': 'date', 'label': 'From Date', 'required': True},
                        {'name': 'to_date', 'type': 'date', 'label': 'To Date', 'required': True},
                        {'name': 'reason', 'type': 'textarea', 'label': 'Reason for Leave', 'required': True},
                    ]
                }
            },
            {
                'name': 'Bonafide Certificate',
                'slug': 'bonafide-certificate',
                'description': 'Request for Bonafide Certificate',
                'category': 'administrative',
                'requires_clearance': False,
                'requires_payment': True,
                'payment_amount': 100.00,
                'approval_workflow': certificate_workflow,
                'allowed_roles': ['parent', 'student'],
                'display_order': 3,
                'form_schema': {
                    'fields': [
                        {'name': 'purpose', 'type': 'textarea', 'label': 'Purpose of Certificate', 'required': True},
                        {'name': 'copies_needed', 'type': 'number', 'label': 'Number of Copies', 'required': True, 'default': 1},
                    ]
                }
            },
            {
                'name': 'Character Certificate',
                'slug': 'character-certificate',
                'description': 'Request for Character/Conduct Certificate',
                'category': 'administrative',
                'requires_clearance': False,
                'requires_payment': True,
                'payment_amount': 100.00,
                'approval_workflow': certificate_workflow,
                'allowed_roles': ['parent', 'student'],
                'display_order': 4,
                'form_schema': {
                    'fields': [
                        {'name': 'purpose', 'type': 'textarea', 'label': 'Purpose of Certificate', 'required': True},
                    ]
                }
            },
            {
                'name': 'Fee Concession',
                'slug': 'fee-concession',
                'description': 'Request for fee concession or scholarship',
                'category': 'financial',
                'requires_clearance': False,
                'requires_payment': False,
                'approval_workflow': fee_workflow,
                'allowed_roles': ['parent'],
                'display_order': 5,
                'form_schema': {
                    'fields': [
                        {'name': 'concession_type', 'type': 'select', 'label': 'Concession Type', 'required': True, 'options': ['Sibling Discount', 'Staff Ward', 'Merit Scholarship', 'Financial Hardship', 'Other']},
                        {'name': 'concession_amount', 'type': 'number', 'label': 'Requested Concession Amount', 'required': True},
                        {'name': 'reason', 'type': 'textarea', 'label': 'Reason/Justification', 'required': True},
                    ]
                }
            },
            {
                'name': 'Transport Change',
                'slug': 'transport-change',
                'description': 'Request to change transport route or stop',
                'category': 'transport',
                'requires_clearance': False,
                'requires_payment': False,
                'approval_workflow': None,
                'allowed_roles': ['parent'],
                'display_order': 6,
                'form_schema': {
                    'fields': [
                        {'name': 'current_route', 'type': 'text', 'label': 'Current Route/Stop', 'required': True},
                        {'name': 'new_route', 'type': 'text', 'label': 'Requested New Route/Stop', 'required': True},
                        {'name': 'effective_date', 'type': 'date', 'label': 'Effective From', 'required': True},
                        {'name': 'reason', 'type': 'textarea', 'label': 'Reason for Change', 'required': False},
                    ]
                }
            },
            {
                'name': 'Feedback/Complaint',
                'slug': 'feedback-complaint',
                'description': 'Submit feedback or raise a complaint',
                'category': 'communication',
                'requires_clearance': False,
                'requires_payment': False,
                'approval_workflow': None,
                'allowed_roles': ['parent', 'student'],
                'display_order': 7,
                'form_schema': {
                    'fields': [
                        {'name': 'type', 'type': 'select', 'label': 'Type', 'required': True, 'options': ['Feedback', 'Suggestion', 'Complaint', 'Query']},
                        {'name': 'department', 'type': 'select', 'label': 'Related To', 'required': True, 'options': ['Academic', 'Administration', 'Transport', 'Infrastructure', 'Other']},
                        {'name': 'subject', 'type': 'text', 'label': 'Subject', 'required': True},
                        {'name': 'description', 'type': 'textarea', 'label': 'Description', 'required': True},
                    ]
                }
            },
        ]

        for data in request_types:
            obj, created = RequestType.objects.update_or_create(
                slug=data['slug'],
                defaults=data
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action}: {obj.name}')
