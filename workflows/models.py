"""
Workflows App - Request & Approval System

This module handles:
- Request types (TC, Leave, Fee Payment, Certificate, etc.)
- Multi-level approval workflows
- Department clearance system (for TC requests)
- Bypass logic for Principal/Super Admin
"""

import uuid
from django.db import models
from django.contrib.auth.models import User


# ==============================================================================
# REQUEST TYPE CONFIGURATION
# ==============================================================================

class RequestType(models.Model):
    """
    Defines types of requests that can be made (TC, Leave, Certificate, etc.)
    """
    REQUEST_CATEGORIES = [
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('financial', 'Financial'),
        ('transport', 'Transport'),
        ('communication', 'Communication'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=REQUEST_CATEGORIES, default='administrative')

    # Configuration
    requires_clearance = models.BooleanField(
        default=False,
        help_text="If True, request requires multi-department clearance (e.g., TC)"
    )
    requires_payment = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Form schema (JSON for dynamic form generation)
    form_schema = models.JSONField(
        default=dict,
        help_text="JSON schema for the request form fields"
    )

    # Who can submit this request
    allowed_roles = models.JSONField(
        default=list,
        help_text="List of roles that can submit this request type"
    )

    # Associated workflow
    approval_workflow = models.ForeignKey(
        'ApprovalWorkflow',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='request_types'
    )

    # Settings
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


# ==============================================================================
# APPROVAL WORKFLOW
# ==============================================================================

class ApprovalWorkflow(models.Model):
    """
    Defines approval workflows with multiple steps
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Configuration
    is_sequential = models.BooleanField(
        default=True,
        help_text="If True, steps must be completed in order"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


class ApprovalStep(models.Model):
    """
    Individual steps in an approval workflow
    """
    APPROVER_TYPE_CHOICES = [
        ('role', 'Role-based'),       # Any user with specified role can approve
        ('specific_user', 'Specific User'),  # Only specific user can approve
        ('department', 'Department Head'),   # Head of specific department
        ('class_teacher', 'Class Teacher'),  # Student's class teacher
        ('parent', 'Parent/Guardian'),       # For student requests requiring parent approval
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name='steps'
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    step_order = models.IntegerField(default=1)

    # Who should approve this step
    approver_type = models.CharField(max_length=50, choices=APPROVER_TYPE_CHOICES, default='role')
    approver_role = models.CharField(
        max_length=50,
        blank=True,
        help_text="Role required for approval (if approver_type is 'role')"
    )
    approver_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_approval_steps',
        help_text="Specific user (if approver_type is 'specific_user')"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department name (if approver_type is 'department')"
    )

    # Step behavior
    is_optional = models.BooleanField(
        default=False,
        help_text="If True, this step can be skipped"
    )
    can_reject = models.BooleanField(
        default=True,
        help_text="If True, approver can reject the request"
    )
    requires_comment = models.BooleanField(
        default=False,
        help_text="If True, approver must provide a comment"
    )

    # Auto-approval rules
    auto_approve_after_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Auto-approve after this many days if not actioned"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workflow', 'step_order']
        unique_together = [['workflow', 'step_order']]
        indexes = [
            models.Index(fields=['workflow', 'step_order']),
        ]

    def __str__(self):
        return f"{self.workflow.name} - Step {self.step_order}: {self.name}"


# ==============================================================================
# CLEARANCE SYSTEM (FOR TC REQUESTS)
# ==============================================================================

class ClearanceType(models.Model):
    """
    Types of departmental clearances required for TC
    e.g., Library, Transport, Accounts, Class Teacher, Admin, Principal
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Department information
    department = models.CharField(max_length=100)

    # Who can provide clearance
    clearance_role = models.CharField(
        max_length=50,
        help_text="Role that can provide this clearance"
    )

    # Order in clearance flow
    clearance_order = models.IntegerField(default=1)

    # What this clearance checks
    check_description = models.TextField(
        blank=True,
        help_text="What this clearance verifies (e.g., 'No pending library books')"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['clearance_order']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.department})"


# ==============================================================================
# REQUESTS
# ==============================================================================

class Request(models.Model):
    """
    Main request model for all types of requests
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending_approval', 'Pending Approval'),
        ('pending_clearance', 'Pending Clearance'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Request identification
    request_number = models.CharField(max_length=50, unique=True)
    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    # Requester information
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='submitted_requests'
    )
    # For parent submitting on behalf of student
    on_behalf_of_student = models.ForeignKey(
        'academics.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests'
    )

    # Request details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    form_data = models.JSONField(
        default=dict,
        help_text="Dynamic form data based on request type schema"
    )

    # Status tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')

    # Current approval step (for workflow tracking)
    current_step = models.ForeignKey(
        ApprovalStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_requests'
    )

    # Bypass information (for Principal/Super Admin)
    is_bypassed = models.BooleanField(
        default=False,
        help_text="True if approval was bypassed by authorized user"
    )
    bypassed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bypassed_requests'
    )
    bypassed_at = models.DateTimeField(null=True, blank=True)
    bypass_reason = models.TextField(blank=True)

    # Payment tracking (if applicable)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('not_required', 'Not Required'),
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='not_required'
    )
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_transaction_id = models.CharField(max_length=100, blank=True)

    # Attachments count (actual files in separate model)
    attachments_count = models.IntegerField(default=0)

    # Dates
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Admin notes (internal)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_number']),
            models.Index(fields=['submitted_by', 'status']),
            models.Index(fields=['request_type', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['on_behalf_of_student']),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.title}"

    def save(self, *args, **kwargs):
        # Generate request number if not set
        if not self.request_number:
            from django.utils import timezone
            import random
            prefix = self.request_type.slug[:3].upper() if self.request_type else 'REQ'
            timestamp = timezone.now().strftime('%Y%m%d')
            random_suffix = str(random.randint(1000, 9999))
            self.request_number = f"{prefix}-{timestamp}-{random_suffix}"
        super().save(*args, **kwargs)


class RequestApproval(models.Model):
    """
    Individual approval records for each step
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
        ('bypassed', 'Bypassed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    approval_step = models.ForeignKey(
        ApprovalStep,
        on_delete=models.PROTECT,
        related_name='approval_records'
    )

    # Approval details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='given_approvals'
    )

    comments = models.TextField(blank=True)

    # Timestamps
    actioned_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['approval_step__step_order']
        unique_together = [['request', 'approval_step']]
        indexes = [
            models.Index(fields=['request', 'status']),
            models.Index(fields=['approved_by', 'status']),
        ]

    def __str__(self):
        return f"{self.request.request_number} - {self.approval_step.name} ({self.status})"


class RequestClearance(models.Model):
    """
    Department clearance records for TC requests
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('not_cleared', 'Not Cleared'),
        ('bypassed', 'Bypassed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='clearances'
    )
    clearance_type = models.ForeignKey(
        ClearanceType,
        on_delete=models.PROTECT,
        related_name='clearance_records'
    )

    # Clearance details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cleared_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='given_clearances'
    )

    # What was verified
    verification_notes = models.TextField(blank=True)

    # Any dues or issues
    pending_dues = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount of pending dues (if any)"
    )
    pending_items = models.TextField(
        blank=True,
        help_text="Description of pending items (e.g., library books)"
    )

    # Timestamps
    actioned_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['clearance_type__clearance_order']
        unique_together = [['request', 'clearance_type']]
        indexes = [
            models.Index(fields=['request', 'status']),
            models.Index(fields=['cleared_by']),
        ]

    def __str__(self):
        return f"{self.request.request_number} - {self.clearance_type.name} ({self.status})"


# ==============================================================================
# REQUEST ATTACHMENTS
# ==============================================================================

class RequestAttachment(models.Model):
    """
    File attachments for requests
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file = models.FileField(upload_to='requests/attachments/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.IntegerField()  # In bytes

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments'
    )

    description = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request']),
        ]

    def __str__(self):
        return f"{self.file_name} - {self.request.request_number}"


# ==============================================================================
# REQUEST HISTORY/AUDIT LOG
# ==============================================================================

class RequestHistory(models.Model):
    """
    Audit trail for all request changes
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('submitted', 'Submitted'),
        ('status_changed', 'Status Changed'),
        ('approval_given', 'Approval Given'),
        ('approval_rejected', 'Approval Rejected'),
        ('clearance_given', 'Clearance Given'),
        ('clearance_denied', 'Clearance Denied'),
        ('bypassed', 'Bypassed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('comment_added', 'Comment Added'),
        ('attachment_added', 'Attachment Added'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='history'
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    action_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='request_actions'
    )

    # State before and after
    previous_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, blank=True)

    # Details
    details = models.JSONField(default=dict)
    comments = models.TextField(blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Request histories"
        indexes = [
            models.Index(fields=['request', '-created_at']),
            models.Index(fields=['action_by']),
        ]

    def __str__(self):
        return f"{self.request.request_number} - {self.action} by {self.action_by}"


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def can_bypass_approval(user):
    """
    Check if user can bypass all approval steps.
    Returns True for Super Admin and Principal (school_admin).
    """
    if not hasattr(user, 'profile'):
        return False

    bypass_roles = ['super_admin', 'school_admin']  # Principal = school_admin
    return user.profile.role in bypass_roles


def process_bypass(request_obj, user, reason=''):
    """
    Process bypass for a request.
    Marks all pending approvals and clearances as bypassed.
    """
    from django.utils import timezone

    if not can_bypass_approval(user):
        raise PermissionError("User does not have bypass privileges")

    now = timezone.now()

    # Mark request as bypassed
    request_obj.is_bypassed = True
    request_obj.bypassed_by = user
    request_obj.bypassed_at = now
    request_obj.bypass_reason = reason
    request_obj.status = 'approved'
    request_obj.save()

    # Mark all pending approvals as bypassed
    request_obj.approvals.filter(status='pending').update(
        status='bypassed',
        approved_by=user,
        actioned_at=now,
        comments=f"Bypassed by {user.get_full_name() or user.username}: {reason}"
    )

    # Mark all pending clearances as bypassed
    request_obj.clearances.filter(status='pending').update(
        status='bypassed',
        cleared_by=user,
        actioned_at=now,
        verification_notes=f"Bypassed by {user.get_full_name() or user.username}: {reason}"
    )

    # Create history entry
    RequestHistory.objects.create(
        request=request_obj,
        action='bypassed',
        action_by=user,
        previous_status='pending_approval',
        new_status='approved',
        details={
            'bypass_reason': reason,
            'approvals_bypassed': request_obj.approvals.filter(status='bypassed').count(),
            'clearances_bypassed': request_obj.clearances.filter(status='bypassed').count(),
        },
        comments=reason
    )

    return request_obj
