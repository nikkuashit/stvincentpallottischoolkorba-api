"""
HR App - Human Resource Management

Manages organizational structure, employee profiles, and leave management.
Includes:
- Departments (Chemistry, Maths, Admin, etc.)
- Designations (Teacher, Department Head, Principal, etc.)
- Employee profiles with reporting hierarchy
- Leave types, policies, and balances
- Leave requests with approval workflow
"""

import uuid
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Department(models.Model):
    """
    Organizational departments.
    Examples: Chemistry Department, Mathematics Department, Administration, etc.
    """
    DEPARTMENT_TYPES = [
        ('academic', 'Academic'),
        ('non_academic', 'Non-Academic'),
        ('administrative', 'Administrative'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code e.g., CHEM, MATH, ADMIN")
    department_type = models.CharField(max_length=20, choices=DEPARTMENT_TYPES, default='academic')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Designation(models.Model):
    """
    Job designations/titles with hierarchical levels.
    Examples: Teacher, Senior Teacher, Department Head, Vice Principal, Principal
    """
    DESIGNATION_CATEGORIES = [
        ('teaching', 'Teaching Staff'),
        ('non_teaching', 'Non-Teaching Staff'),
        ('administrative', 'Administrative Staff'),
        ('management', 'Management'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=DESIGNATION_CATEGORIES, default='teaching')
    level = models.PositiveIntegerField(
        default=1,
        help_text="Hierarchy level (1=lowest, higher=more senior). Used for reporting structure."
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Permissions
    can_approve_leave = models.BooleanField(default=False, help_text="Can approve leave requests of subordinates")
    can_manage_department = models.BooleanField(default=False, help_text="Can manage department settings")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-level', 'name']

    def __str__(self):
        return f"{self.name} (Level {self.level})"


class EmployeeProfile(models.Model):
    """
    Extended employee profile linking UserProfile with HR data.
    Manages reporting structure, department assignments, and employment details.
    """
    EMPLOYMENT_STATUS = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('resigned', 'Resigned'),
        ('terminated', 'Terminated'),
        ('retired', 'Retired'),
    ]

    EMPLOYMENT_TYPE = [
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('probation', 'Probation'),
        ('temporary', 'Temporary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )

    # Department & Designation
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees',
        null=True,
        blank=True
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.PROTECT,
        related_name='employees',
        null=True,
        blank=True
    )

    # Special Roles
    is_department_head = models.BooleanField(
        default=False,
        help_text="Is this employee the head of their department?"
    )

    # Reporting Structure
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        help_text="Direct reporting manager"
    )

    # Employment Details
    employee_code = models.CharField(max_length=50, unique=True)
    joining_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default='active')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE, default='permanent')

    # Work Schedule
    work_days_per_week = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )

    # Exit Details
    resignation_date = models.DateField(null=True, blank=True)
    last_working_date = models.DateField(null=True, blank=True)
    exit_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['designation']),
            models.Index(fields=['reports_to']),
            models.Index(fields=['employment_status']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation.name if self.designation else 'Unassigned'}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def tenure_months(self):
        """Calculate tenure in months from joining date."""
        if not self.joining_date:
            return 0
        delta = relativedelta(date.today(), self.joining_date)
        return delta.years * 12 + delta.months

    @property
    def tenure_years(self):
        """Calculate tenure in years from joining date."""
        if not self.joining_date:
            return 0
        delta = relativedelta(date.today(), self.joining_date)
        return delta.years

    def get_reporting_chain(self):
        """Get the full reporting chain up to top level."""
        chain = []
        current = self.reports_to
        while current:
            chain.append(current)
            current = current.reports_to
        return chain

    def get_subordinates(self, include_indirect=False):
        """Get direct subordinates, optionally including indirect reports."""
        direct = list(self.subordinates.filter(employment_status='active'))
        if not include_indirect:
            return direct

        all_subordinates = list(direct)
        for subordinate in direct:
            all_subordinates.extend(subordinate.get_subordinates(include_indirect=True))
        return all_subordinates

    def can_approve_leave_for(self, employee):
        """Check if this employee can approve leave for another employee."""
        # Check if designation allows leave approval
        if not self.designation or not self.designation.can_approve_leave:
            return False

        # Check if in reporting chain
        reporting_chain = employee.get_reporting_chain()
        return self in reporting_chain


class LeaveType(models.Model):
    """
    Types of leave available in the organization.
    Examples: Casual Leave, Sick Leave, Earned Leave, Maternity Leave, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code e.g., CL, SL, EL")
    description = models.TextField(blank=True)

    # Leave Characteristics
    is_paid = models.BooleanField(default=True)
    requires_document = models.BooleanField(
        default=False,
        help_text="Requires supporting document (e.g., medical certificate)"
    )
    min_days_notice = models.PositiveIntegerField(
        default=0,
        help_text="Minimum days in advance leave must be applied"
    )
    max_consecutive_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum consecutive days allowed at once"
    )

    # Gender Restrictions (for maternity/paternity leave)
    applicable_gender = models.CharField(
        max_length=10,
        choices=[
            ('all', 'All'),
            ('male', 'Male Only'),
            ('female', 'Female Only'),
        ],
        default='all'
    )

    # Color for UI display
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code for UI")

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeavePolicy(models.Model):
    """
    Leave policy defining annual quota and rules for a leave type.
    Can be applied to specific designations or all employees.
    """
    PRORATION_METHODS = [
        ('none', 'No Proration'),
        ('monthly', 'Monthly Proration'),
        ('quarterly', 'Quarterly Proration'),
    ]

    CARRYFORWARD_TYPES = [
        ('none', 'No Carryforward'),
        ('full', 'Full Carryforward'),
        ('partial', 'Partial Carryforward'),
        ('encashment', 'Encashment Only'),
    ]

    ACCRUAL_TYPES = [
        ('yearly', 'Credited Yearly (Start of Year)'),
        ('monthly', 'Credited Monthly'),
        ('quarterly', 'Credited Quarterly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='policies'
    )

    # Applicability
    applicable_to_all = models.BooleanField(
        default=True,
        help_text="If false, applies only to specific designations"
    )
    applicable_designations = models.ManyToManyField(
        Designation,
        blank=True,
        related_name='leave_policies',
        help_text="Designations this policy applies to (if not applicable to all)"
    )

    # Quota
    annual_quota = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Annual leave quota in days"
    )

    # Proration Rules
    proration_method = models.CharField(
        max_length=20,
        choices=PRORATION_METHODS,
        default='monthly',
        help_text="How to prorate leave for mid-year joiners"
    )

    # Accrual Rules
    accrual_type = models.CharField(
        max_length=20,
        choices=ACCRUAL_TYPES,
        default='yearly',
        help_text="When leave is credited to employee balance"
    )

    # Carryforward Rules
    carryforward_type = models.CharField(
        max_length=20,
        choices=CARRYFORWARD_TYPES,
        default='none'
    )
    max_carryforward_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Maximum days that can be carried forward"
    )
    carryforward_expiry_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Months after which carried forward leave expires"
    )

    # Encashment Rules
    allow_encashment = models.BooleanField(default=False)
    min_balance_for_encashment = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Minimum balance required before encashment"
    )
    max_encashment_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True
    )

    # Validity
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['leave_type__name', '-effective_from']
        verbose_name_plural = 'Leave Policies'

    def __str__(self):
        return f"{self.name} - {self.leave_type.name}"

    def calculate_prorated_quota(self, joining_date, year):
        """
        Calculate prorated leave quota based on joining date.
        Returns the number of days the employee is entitled to.
        """
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # If joined before this year, full quota
        if joining_date < year_start:
            return self.annual_quota

        # If joined after this year, no quota
        if joining_date > year_end:
            return Decimal('0')

        if self.proration_method == 'none':
            return self.annual_quota

        # Calculate remaining months/quarters
        remaining_months = 12 - joining_date.month + 1

        if self.proration_method == 'monthly':
            return (self.annual_quota * Decimal(remaining_months) / Decimal('12')).quantize(Decimal('0.5'))

        elif self.proration_method == 'quarterly':
            quarter = (joining_date.month - 1) // 3 + 1
            remaining_quarters = 4 - quarter + 1
            return (self.annual_quota * Decimal(remaining_quarters) / Decimal('4')).quantize(Decimal('0.5'))

        return self.annual_quota

    def is_applicable_to(self, employee):
        """Check if this policy applies to a given employee."""
        if self.applicable_to_all:
            return True
        if not employee.designation:
            return False
        return employee.designation in self.applicable_designations.all()


class LeaveBalance(models.Model):
    """
    Individual employee leave balance for a specific year and leave type.
    Tracks opening balance, accrued, used, and remaining leaves.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances'
    )
    year = models.PositiveIntegerField()

    # Balance Details
    opening_balance = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0'),
        help_text="Carried forward from previous year"
    )
    annual_quota = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0'),
        help_text="Prorated annual entitlement"
    )
    adjustment = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0'),
        help_text="Manual adjustments (+/-)"
    )
    used = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0'),
        help_text="Leave days used"
    )
    pending = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0'),
        help_text="Leave days in pending requests"
    )
    encashed = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0'),
        help_text="Leave days encashed"
    )
    lapsed = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0'),
        help_text="Leave days lapsed/expired"
    )

    # Audit
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['-year', 'leave_type__name']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.code} ({self.year})"

    @property
    def total_available(self):
        """Total available balance including opening, quota, and adjustments."""
        return self.opening_balance + self.annual_quota + self.adjustment

    @property
    def available_balance(self):
        """Remaining balance after used, pending, encashed, and lapsed."""
        return self.total_available - self.used - self.pending - self.encashed - self.lapsed

    def clean(self):
        """Validate that used + pending doesn't exceed available."""
        if self.used + self.pending > self.total_available:
            raise ValidationError("Used + Pending cannot exceed total available balance.")


class LeaveRequest(models.Model):
    """
    Leave request with approval workflow.
    Follows reporting hierarchy for approvals.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('partially_approved', 'Partially Approved'),
    ]

    LEAVE_DURATION_TYPES = [
        ('full_day', 'Full Day'),
        ('first_half', 'First Half'),
        ('second_half', 'Second Half'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    # Leave Dates
    start_date = models.DateField()
    end_date = models.DateField()
    start_duration_type = models.CharField(
        max_length=20,
        choices=LEAVE_DURATION_TYPES,
        default='full_day'
    )
    end_duration_type = models.CharField(
        max_length=20,
        choices=LEAVE_DURATION_TYPES,
        default='full_day'
    )

    # Calculated days (stored for reporting)
    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        editable=False
    )

    # Request Details
    reason = models.TextField()
    contact_during_leave = models.CharField(max_length=100, blank=True)

    # Documents
    document = models.FileField(
        upload_to='hr/leave_documents/',
        null=True,
        blank=True,
        help_text="Supporting document if required"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Approval Chain
    current_approver = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_leave_approvals'
    )
    final_approver = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )

    # Audit
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['current_approver']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.code} ({self.start_date} to {self.end_date})"

    def clean(self):
        """Validate leave request."""
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

        # Check for overlapping requests
        overlapping = LeaveRequest.objects.filter(
            employee=self.employee,
            status__in=['pending', 'approved'],
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("Leave request overlaps with existing request.")

    def save(self, *args, **kwargs):
        """Calculate total days before saving."""
        self.total_days = self.calculate_total_days()
        super().save(*args, **kwargs)

    def calculate_total_days(self):
        """Calculate total leave days based on dates and duration types."""
        if not self.start_date or not self.end_date:
            return Decimal('0')

        # Single day leave
        if self.start_date == self.end_date:
            if self.start_duration_type in ['first_half', 'second_half']:
                return Decimal('0.5')
            return Decimal('1')

        # Multi-day leave
        total = Decimal(str((self.end_date - self.start_date).days + 1))

        # Adjust for half days
        if self.start_duration_type == 'second_half':
            total -= Decimal('0.5')
        if self.end_duration_type == 'first_half':
            total -= Decimal('0.5')

        return total

    def get_approval_chain(self):
        """
        Get the complete approval chain for this request.
        Returns list of employees who need to approve in order.
        """
        chain = []
        current = self.employee.reports_to

        while current:
            if current.designation and current.designation.can_approve_leave:
                chain.append(current)
            current = current.reports_to

        return chain

    def submit(self, user=None):
        """Submit the leave request for approval."""
        from django.utils import timezone

        self.status = 'pending'
        self.submitted_at = timezone.now()
        self.submitted_by = user

        # Set first approver
        approval_chain = self.get_approval_chain()
        if approval_chain:
            self.current_approver = approval_chain[0]

        self.save()

        # Update leave balance (mark as pending)
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=self.employee,
            leave_type=self.leave_type,
            year=self.start_date.year,
            defaults={'annual_quota': Decimal('0')}
        )
        balance.pending += self.total_days
        balance.save()


class LeaveApproval(models.Model):
    """
    Individual approval record for a leave request.
    Each approver in the chain creates a record.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    approver = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='leave_approvals'
    )
    sequence = models.PositiveIntegerField(help_text="Order in approval chain")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)

    acted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence']
        unique_together = ['leave_request', 'approver']

    def __str__(self):
        return f"{self.leave_request} - {self.approver.full_name} ({self.status})"

    def approve(self, comments=''):
        """Approve this step and move to next approver if any."""
        from django.utils import timezone

        self.status = 'approved'
        self.comments = comments
        self.acted_at = timezone.now()
        self.save()

        # Check if there's a next approver
        next_approval = LeaveApproval.objects.filter(
            leave_request=self.leave_request,
            sequence__gt=self.sequence,
            status='pending'
        ).first()

        if next_approval:
            self.leave_request.current_approver = next_approval.approver
            self.leave_request.save()
        else:
            # All approved - finalize
            self._finalize_approval()

    def reject(self, comments=''):
        """Reject the leave request."""
        from django.utils import timezone

        self.status = 'rejected'
        self.comments = comments
        self.acted_at = timezone.now()
        self.save()

        # Update leave request status
        self.leave_request.status = 'rejected'
        self.leave_request.final_approver = self.approver
        self.leave_request.save()

        # Release pending balance
        try:
            balance = LeaveBalance.objects.get(
                employee=self.leave_request.employee,
                leave_type=self.leave_request.leave_type,
                year=self.leave_request.start_date.year
            )
            balance.pending -= self.leave_request.total_days
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass

    def _finalize_approval(self):
        """Finalize the approval process when all approvers have approved."""
        request = self.leave_request
        request.status = 'approved'
        request.final_approver = self.approver
        request.current_approver = None
        request.save()

        # Update leave balance (move from pending to used)
        try:
            balance = LeaveBalance.objects.get(
                employee=request.employee,
                leave_type=request.leave_type,
                year=request.start_date.year
            )
            balance.pending -= request.total_days
            balance.used += request.total_days
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass


class LeaveBalanceAuditLog(models.Model):
    """
    Audit log for leave balance changes.
    Tracks all modifications to leave balances for compliance.
    """
    ACTION_TYPES = [
        ('initial', 'Initial Balance'),
        ('annual_credit', 'Annual Credit'),
        ('carryforward', 'Carryforward'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
        ('adjusted', 'Manual Adjustment'),
        ('encashed', 'Encashed'),
        ('lapsed', 'Lapsed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    leave_balance = models.ForeignKey(
        LeaveBalance,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    days_change = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        help_text="Positive for credit, negative for debit"
    )
    balance_before = models.DecimalField(max_digits=5, decimal_places=1)
    balance_after = models.DecimalField(max_digits=5, decimal_places=1)

    reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reference to related object (e.g., leave request ID)"
    )
    notes = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.leave_balance} - {self.action} ({self.days_change:+.1f})"


class Holiday(models.Model):
    """
    Organization holidays.
    Used for leave calculation and attendance.
    """
    HOLIDAY_TYPES = [
        ('national', 'National Holiday'),
        ('religious', 'Religious Holiday'),
        ('school', 'School Holiday'),
        ('vacation', 'Vacation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    date = models.DateField()
    holiday_type = models.CharField(max_length=20, choices=HOLIDAY_TYPES, default='national')
    description = models.TextField(blank=True)

    # Applicability
    is_optional = models.BooleanField(
        default=False,
        help_text="Optional/restricted holiday"
    )
    applicable_departments = models.ManyToManyField(
        Department,
        blank=True,
        help_text="If empty, applies to all departments"
    )

    year = models.PositiveIntegerField(editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        unique_together = ['name', 'date']

    def __str__(self):
        return f"{self.name} ({self.date})"

    def save(self, *args, **kwargs):
        self.year = self.date.year
        super().save(*args, **kwargs)
