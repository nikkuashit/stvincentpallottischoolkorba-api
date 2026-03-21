"""
Fee Management App - Fee Structure, Discounts, and Payments

This module handles:
- Fee structures per academic year and grade
- Discount rules and eligibility
- Student fee assignments
- Payment tracking and receipts
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class FeeCategory(models.Model):
    """
    Categories for different types of fees.
    Examples: Tuition, Transport, Library, Laboratory, Sports, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short code for the category (e.g., TUI, TRA, LIB)"
    )
    description = models.TextField(blank=True)

    # Display settings
    display_order = models.IntegerField(default=0)
    is_mandatory = models.BooleanField(
        default=True,
        help_text="If true, this fee is required for all students"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fee Category"
        verbose_name_plural = "Fee Categories"
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class FeeStructure(models.Model):
    """
    Fee structure defining amount for a specific academic year, grade, and category.
    This is the master fee definition that gets applied to students.
    """
    FREQUENCY_CHOICES = [
        ('one_time', 'One Time'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core relationships
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    grade = models.ForeignKey(
        'academics.Grade',
        on_delete=models.CASCADE,
        related_name='fee_structures',
        null=True,
        blank=True,
        help_text="If null, applies to all grades"
    )
    category = models.ForeignKey(
        FeeCategory,
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )

    # Fee details
    name = models.CharField(
        max_length=200,
        help_text="Descriptive name (e.g., 'Class 10 Tuition Fee 2025-26')"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='yearly'
    )

    # Due date settings
    due_day_of_month = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month when fee is due (1-28)"
    )

    # Late fee settings
    late_fee_type = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Late Fee'),
            ('fixed', 'Fixed Amount'),
            ('percentage', 'Percentage of Fee'),
        ],
        default='none'
    )
    late_fee_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount or percentage for late fee"
    )
    grace_period_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Days after due date before late fee applies"
    )

    # Additional settings
    is_refundable = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fee Structure"
        verbose_name_plural = "Fee Structures"
        ordering = ['academic_year', 'grade', 'category__display_order']
        unique_together = ['academic_year', 'grade', 'category', 'frequency']

    def __str__(self):
        grade_str = f"Grade {self.grade.number}" if self.grade else "All Grades"
        return f"{self.name} - {grade_str} ({self.academic_year.name})"

    def calculate_late_fee(self, days_overdue):
        """Calculate late fee based on configuration."""
        if self.late_fee_type == 'none' or days_overdue <= self.grace_period_days:
            return Decimal('0.00')

        if self.late_fee_type == 'fixed':
            return self.late_fee_value
        elif self.late_fee_type == 'percentage':
            return (self.amount * self.late_fee_value / 100).quantize(Decimal('0.01'))

        return Decimal('0.00')


class FeeDiscount(models.Model):
    """
    Discount rules that can be applied to student fees.
    Supports various criteria like sibling discount, merit scholarship, etc.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    CRITERIA_CHOICES = [
        ('sibling', 'Sibling Discount'),
        ('merit', 'Merit Scholarship'),
        ('staff_child', 'Staff Child'),
        ('financial_aid', 'Financial Aid'),
        ('sports_quota', 'Sports Quota'),
        ('early_bird', 'Early Bird Payment'),
        ('custom', 'Custom/Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique code for this discount"
    )
    description = models.TextField(blank=True)

    # Discount calculation
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Percentage or fixed amount"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount cap (for percentage discounts)"
    )

    # Eligibility criteria
    criteria = models.CharField(
        max_length=20,
        choices=CRITERIA_CHOICES,
        default='custom'
    )

    # Applicable fee categories (if empty, applies to all)
    applicable_categories = models.ManyToManyField(
        FeeCategory,
        blank=True,
        related_name='discounts',
        help_text="Leave empty to apply to all categories"
    )

    # Academic year scope
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.CASCADE,
        related_name='fee_discounts',
        null=True,
        blank=True,
        help_text="If null, applies to all academic years"
    )

    # Validity period
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)

    is_combinable = models.BooleanField(
        default=False,
        help_text="Can this discount be combined with others?"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fee Discount"
        verbose_name_plural = "Fee Discounts"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_criteria_display()})"

    def calculate_discount(self, base_amount):
        """Calculate discount amount based on type and value."""
        if self.discount_type == 'percentage':
            discount = (base_amount * self.value / 100).quantize(Decimal('0.01'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        else:
            return min(self.value, base_amount)

    def is_valid(self, check_date=None):
        """Check if discount is currently valid."""
        if not self.is_active:
            return False

        check_date = check_date or timezone.now().date()

        if self.valid_from and check_date < self.valid_from:
            return False
        if self.valid_until and check_date > self.valid_until:
            return False

        return True


class StudentFee(models.Model):
    """
    Assigned fee for a specific student.
    Links a student to a fee structure with optional discounts.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core relationships
    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='fees'
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name='student_fees'
    )

    # Fee period (for recurring fees)
    period_start = models.DateField(
        help_text="Start date of the fee period"
    )
    period_end = models.DateField(
        help_text="End date of the fee period"
    )
    due_date = models.DateField()

    # Amounts
    base_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Original fee amount from structure"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    late_fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base amount - discount + late fee"
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Applied discounts
    discounts_applied = models.ManyToManyField(
        FeeDiscount,
        blank=True,
        related_name='student_fees'
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Additional info
    remarks = models.TextField(blank=True)
    waiver_reason = models.TextField(
        blank=True,
        help_text="Reason if fee was waived"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Fee"
        verbose_name_plural = "Student Fees"
        ordering = ['-due_date', 'student']
        unique_together = ['student', 'fee_structure', 'period_start', 'period_end']

    def __str__(self):
        return f"{self.student} - {self.fee_structure.name} ({self.status})"

    @property
    def balance_due(self):
        """Calculate remaining amount to be paid."""
        return max(self.final_amount - self.paid_amount, Decimal('0.00'))

    @property
    def is_overdue(self):
        """Check if fee is past due date."""
        return self.status not in ['paid', 'waived', 'cancelled'] and \
               timezone.now().date() > self.due_date

    def update_status(self):
        """Update status based on payments and due date."""
        if self.status in ['waived', 'cancelled']:
            return

        if self.paid_amount >= self.final_amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        elif self.is_overdue:
            self.status = 'overdue'
        else:
            self.status = 'pending'

        self.save(update_fields=['status', 'updated_at'])

    def calculate_late_fee(self):
        """Calculate and apply late fee if applicable."""
        if self.status in ['paid', 'waived', 'cancelled']:
            return Decimal('0.00')

        if timezone.now().date() <= self.due_date:
            return Decimal('0.00')

        days_overdue = (timezone.now().date() - self.due_date).days
        late_fee = self.fee_structure.calculate_late_fee(days_overdue)

        if late_fee != self.late_fee_amount:
            self.late_fee_amount = late_fee
            self.final_amount = self.base_amount - self.discount_amount + late_fee
            self.save(update_fields=['late_fee_amount', 'final_amount', 'updated_at'])

        return late_fee

    def save(self, *args, **kwargs):
        """Calculate final amount before saving."""
        if not self.final_amount:
            self.final_amount = self.base_amount - self.discount_amount + self.late_fee_amount
        super().save(*args, **kwargs)


class FeePayment(models.Model):
    """
    Individual payment record against a student fee.
    Supports partial payments and multiple payment methods.
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('online', 'Online Payment'),
        ('dd', 'Demand Draft'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core relationships
    student_fee = models.ForeignKey(
        StudentFee,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateField()
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )

    # Receipt information
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated receipt number"
    )

    # Transaction details (for non-cash payments)
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External transaction reference"
    )
    cheque_number = models.CharField(max_length=50, blank=True)
    cheque_date = models.DateField(null=True, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)

    # Status and verification
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='completed'
    )
    verified_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # Additional info
    remarks = models.TextField(blank=True)
    refund_reason = models.TextField(
        blank=True,
        help_text="Reason if payment was refunded"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payments'
    )

    class Meta:
        verbose_name = "Fee Payment"
        verbose_name_plural = "Fee Payments"
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"Receipt #{self.receipt_number} - ₹{self.amount}"

    def save(self, *args, **kwargs):
        """Generate receipt number if not provided."""
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)

        # Update student fee status after payment
        if self.status == 'completed':
            self.student_fee.paid_amount += self.amount
            self.student_fee.update_status()

    @staticmethod
    def generate_receipt_number():
        """Generate a unique receipt number."""
        from django.db.models import Max

        # Format: RCP-YYYYMMDD-XXXX
        today = timezone.now().date()
        prefix = f"RCP-{today.strftime('%Y%m%d')}"

        # Get the last receipt number for today
        last_receipt = FeePayment.objects.filter(
            receipt_number__startswith=prefix
        ).aggregate(Max('receipt_number'))['receipt_number__max']

        if last_receipt:
            try:
                last_num = int(last_receipt.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:04d}"


class FeeReminder(models.Model):
    """
    Track fee payment reminders sent to students/parents.
    """
    REMINDER_TYPE_CHOICES = [
        ('upcoming', 'Upcoming Due Date'),
        ('due', 'Due Date Reminder'),
        ('overdue', 'Overdue Notice'),
        ('final', 'Final Notice'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('app', 'App Notification'),
        ('whatsapp', 'WhatsApp'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student_fee = models.ForeignKey(
        StudentFee,
        on_delete=models.CASCADE,
        related_name='reminders'
    )

    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPE_CHOICES
    )
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES
    )

    sent_at = models.DateTimeField(auto_now_add=True)
    sent_to = models.CharField(
        max_length=200,
        help_text="Email/Phone number sent to"
    )

    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    message_content = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Fee Reminder"
        verbose_name_plural = "Fee Reminders"
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.get_reminder_type_display()} - {self.student_fee.student}"
