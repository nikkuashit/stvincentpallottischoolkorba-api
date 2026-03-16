# =============================================================================
# PHASE B: STUDENT CORE MODELS (To be merged into models.py)
# =============================================================================

import uuid
from django.db import models
from django.core.validators import MinValueValidator


class StudentEnrollment(models.Model):
    """
    Student enrollment history tracking.
    Maintains a complete history of which sections a student has been enrolled in
    across different academic years. Only one enrollment should be marked as current
    per student at any given time.
    """
    EXIT_REASON_CHOICES = [
        ('promoted', 'Promoted'),
        ('transferred', 'Transferred'),
        ('dropped', 'Dropped'),
        ('graduated', 'Graduated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='Student this enrollment belongs to'
    )
    section = models.ForeignKey(
        'Section',
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='Section the student is enrolled in'
    )
    academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='Academic year for this enrollment'
    )

    roll_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Roll number assigned to student in this section'
    )
    enrolled_date = models.DateField(
        help_text='Date when student was enrolled in this section'
    )
    exit_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when student exited this section (if applicable)'
    )
    exit_reason = models.CharField(
        max_length=20,
        choices=EXIT_REASON_CHOICES,
        blank=True,
        help_text='Reason for exiting this section'
    )

    is_current = models.BooleanField(
        default=False,
        help_text='Is this the current active enrollment for the student?'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-academic_year__start_date', '-enrolled_date']
        unique_together = [['student', 'academic_year']]
        indexes = [
            models.Index(fields=['student', 'is_current']),
            models.Index(fields=['section', 'academic_year']),
            models.Index(fields=['academic_year', 'roll_number']),
            models.Index(fields=['is_current']),
        ]
        verbose_name = 'Student Enrollment'
        verbose_name_plural = 'Student Enrollments'

    def __str__(self):
        return f"{self.student} - {self.section} ({self.academic_year.name}) - Roll #{self.roll_number}"

    def save(self, *args, **kwargs):
        """Ensure only one enrollment per student is marked as current"""
        if self.is_current:
            StudentEnrollment.objects.filter(
                student=self.student,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class StudentPhoto(models.Model):
    """
    Student photo management with approval workflow.
    Supports photo upload, admin approval, rejection with reason, and annual refresh tracking.
    Only one photo should be marked as current per student at any given time.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='photos',
        help_text='Student this photo belongs to'
    )
    image = models.ImageField(
        upload_to='student_photos/',
        help_text='Student photo image file'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current approval status of the photo'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (if applicable)'
    )

    uploaded_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_student_photos',
        help_text='User who uploaded this photo'
    )
    approved_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_student_photos',
        help_text='Admin who approved/rejected this photo'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when photo was uploaded'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when photo was approved/rejected'
    )

    is_current = models.BooleanField(
        default=False,
        help_text='Is this the currently active photo for the student?'
    )

    academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.CASCADE,
        related_name='student_photos',
        help_text='Academic year this photo was uploaded for (annual refresh tracking)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['student', 'is_current']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['academic_year']),
            models.Index(fields=['uploaded_by']),
        ]
        verbose_name = 'Student Photo'
        verbose_name_plural = 'Student Photos'

    def __str__(self):
        return f"{self.student} - Photo ({self.get_status_display()}) - {self.uploaded_at.date()}"

    def save(self, *args, **kwargs):
        """Ensure only one photo per student is marked as current"""
        if self.is_current:
            StudentPhoto.objects.filter(
                student=self.student,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def approve(self, approved_by_user):
        """Approve this photo and set it as current"""
        from django.utils import timezone
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.is_current = True
        self.save()

    def reject(self, rejected_by_user, reason):
        """Reject this photo with a reason"""
        from django.utils import timezone
        self.status = 'rejected'
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.is_current = False
        self.save()


# =============================================================================
# MODIFIED STUDENT MODEL (Phase B Updates)
# =============================================================================

# Replace the existing Student model with this updated version:

class Student(models.Model):
    """
    Student information - Core student profile model.

    PHASE B UPDATES:
    - Added current_section FK for fast access to current section
    - Modified admission_number help text to reference SchoolSettings format
    - Changed roll_number from CharField to IntegerField
    - Enhanced status choices to include 'dropped'
    - Added helper methods: get_current_photo(), get_current_enrollment(), etc.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('transferred', 'Transferred'),
        ('dropped', 'Dropped'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # DEPRECATED: Legacy class reference (will be removed after migration)
    current_class = models.ForeignKey(
        'Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text='DEPRECATED: Use current_section instead'
    )

    # PHASE B: New current section reference
    current_section = models.ForeignKey(
        'Section',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_students',
        help_text='Current section the student is enrolled in (fast access)'
    )

    academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text='Current academic session for the student'
    )
    user_profile = models.OneToOneField(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_record'
    )

    # Basic Information
    admission_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Permanent admission number (format: {prefix}{YY}{sequence}, e.g., SVP25001)'
    )
    roll_number = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Current roll number in current section (shortcut field)'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
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

    # Media (DEPRECATED: Use StudentPhoto model instead)
    photo = models.ImageField(
        upload_to='students/photos/',
        null=True,
        blank=True,
        help_text='DEPRECATED: Use StudentPhoto model for photo management'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['admission_number']),
            models.Index(fields=['current_section']),
            models.Index(fields=['academic_year']),
            models.Index(fields=['first_name', 'last_name']),
        ]
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.admission_number}"

    @property
    def full_name(self):
        """Returns full name of the student"""
        return f"{self.first_name} {self.last_name}"

    def get_current_photo(self):
        """
        Returns the current approved photo for the student.
        Returns None if no current photo exists.
        """
        try:
            return self.photos.get(is_current=True, status='approved')
        except:
            return None

    def get_current_enrollment(self):
        """
        Returns the current active enrollment for the student.
        Returns None if no current enrollment exists.
        """
        try:
            return self.enrollments.get(is_current=True)
        except:
            return None

    def has_photo_for_year(self, academic_year):
        """
        Check if student has an approved photo for the given academic year.
        """
        return self.photos.filter(
            academic_year=academic_year,
            status='approved'
        ).exists()

    def get_enrollment_history(self):
        """
        Returns complete enrollment history ordered by most recent first.
        """
        return self.enrollments.all().order_by('-academic_year__start_date', '-enrolled_date')
