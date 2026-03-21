"""
Academics App - Academic Management

Simplified without multi-tenancy.
This module handles:
- Academic years
- Classes and grades
- Students and parents
- Subjects and courses
- Attendance tracking
- Grades and assessments
"""

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# =============================================================================
# PHASE A: FOUNDATION MODELS (Academic Structure Redesign)
# =============================================================================

class GradeType(models.Model):
    """
    Configurable grade types that admins can manage.
    Defines the available grades like Nursery, Pre-KG, KG, Class 1-12, etc.

    This allows schools to customize their grade structure without code changes.
    """
    CATEGORY_CHOICES = [
        ('pre_primary', 'Pre-Primary'),
        ('primary', 'Primary'),
        ('middle', 'Middle School'),
        ('secondary', 'Secondary'),
        ('senior_secondary', 'Senior Secondary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Unique identifier for the grade (e.g., -3, -2, -1, 1, 2, ... 12)
    number = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(-10), MaxValueValidator(15)],
        help_text="Unique grade number. Use negative for pre-primary (e.g., -3=Nursery, -2=Pre-KG, -1=KG)"
    )

    # Display name
    name = models.CharField(
        max_length=100,
        help_text="Display name for this grade (e.g., 'Nursery', 'Pre-KG', 'Class 5')"
    )

    # Short name for labels
    short_name = models.CharField(
        max_length=20,
        blank=True,
        help_text="Short name for compact displays (e.g., 'Nur', 'LKG', '5')"
    )

    # Category for grouping in UI
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='primary',
        help_text="Category for grouping in dropdowns"
    )

    # Display order for sorting
    display_order = models.IntegerField(
        default=0,
        help_text="Order for display purposes (lower numbers appear first)"
    )

    # Description
    description = models.TextField(
        blank=True,
        help_text="Optional description for this grade type"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this grade type available for use?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'number']
        verbose_name = "Grade Type"
        verbose_name_plural = "Grade Types"
        indexes = [
            models.Index(fields=['display_order', 'number']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.number})"

    def save(self, *args, **kwargs):
        # Auto-generate short_name if not provided
        if not self.short_name:
            if self.number < 0:
                # For pre-primary, use first 3 letters
                self.short_name = self.name[:3].upper()
            else:
                # For classes, use the number
                self.short_name = str(self.number)

        # Auto-set display_order if not set
        if self.display_order == 0:
            if self.number < 0:
                self.display_order = self.number + 10  # -3→7, -2→8, -1→9
            else:
                self.display_order = self.number + 9  # 1→10, 2→11, ... 12→21

        # Auto-set category based on number if not explicitly set
        if self.category == 'primary':  # Default value, might need updating
            if self.number < 0:
                self.category = 'pre_primary'
            elif self.number <= 5:
                self.category = 'primary'
            elif self.number <= 8:
                self.category = 'middle'
            elif self.number <= 10:
                self.category = 'secondary'
            else:
                self.category = 'senior_secondary'

        super().save(*args, **kwargs)

    @classmethod
    def get_default_grade_types(cls):
        """Returns default grade types for initial setup."""
        return [
            {'number': -3, 'name': 'Nursery', 'short_name': 'NUR', 'category': 'pre_primary', 'display_order': 1},
            {'number': -2, 'name': 'Pre-KG (LKG)', 'short_name': 'LKG', 'category': 'pre_primary', 'display_order': 2},
            {'number': -1, 'name': 'KG (UKG)', 'short_name': 'UKG', 'category': 'pre_primary', 'display_order': 3},
            {'number': 1, 'name': 'Class 1', 'short_name': '1', 'category': 'primary', 'display_order': 4},
            {'number': 2, 'name': 'Class 2', 'short_name': '2', 'category': 'primary', 'display_order': 5},
            {'number': 3, 'name': 'Class 3', 'short_name': '3', 'category': 'primary', 'display_order': 6},
            {'number': 4, 'name': 'Class 4', 'short_name': '4', 'category': 'primary', 'display_order': 7},
            {'number': 5, 'name': 'Class 5', 'short_name': '5', 'category': 'primary', 'display_order': 8},
            {'number': 6, 'name': 'Class 6', 'short_name': '6', 'category': 'middle', 'display_order': 9},
            {'number': 7, 'name': 'Class 7', 'short_name': '7', 'category': 'middle', 'display_order': 10},
            {'number': 8, 'name': 'Class 8', 'short_name': '8', 'category': 'middle', 'display_order': 11},
            {'number': 9, 'name': 'Class 9', 'short_name': '9', 'category': 'secondary', 'display_order': 12},
            {'number': 10, 'name': 'Class 10', 'short_name': '10', 'category': 'secondary', 'display_order': 13},
            {'number': 11, 'name': 'Class 11', 'short_name': '11', 'category': 'senior_secondary', 'display_order': 14},
            {'number': 12, 'name': 'Class 12', 'short_name': '12', 'category': 'senior_secondary', 'display_order': 15},
        ]


class SchoolSettings(models.Model):
    """
    Singleton model for school-wide settings and configuration.
    Only one instance should exist in the database.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # School identity
    school_name = models.CharField(max_length=200, default="St. Vincent Pallotti School")
    school_short_name = models.CharField(max_length=50, default="SVPS", blank=True)
    logo = models.ImageField(upload_to='school/logo/', null=True, blank=True)

    # Contact information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Academic settings
    admission_number_prefix = models.CharField(
        max_length=10,
        default="SVP",
        help_text="Prefix for admission numbers (e.g., SVP25001)"
    )
    current_academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_year_settings',
        help_text="Currently active academic year"
    )
    # Roll number algorithm settings
    roll_number_sort_by = models.CharField(
        max_length=50,
        default="first_name,last_name,admission_number",
        help_text="Comma-separated fields for roll number sorting"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "School Settings"
        verbose_name_plural = "School Settings"

    def __str__(self):
        return f"{self.school_name} - Settings"

    def save(self, *args, **kwargs):
        """Ensure only one SchoolSettings instance exists (singleton pattern)"""
        if not self.pk and SchoolSettings.objects.exists():
            raise ValueError("Only one SchoolSettings instance is allowed")
        return super().save(*args, **kwargs)


class AcademicYear(models.Model):
    """
    Academic year configuration (e.g., 2025-26).
    Represents a single academic session for the entire school.
    """
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Academic year name (e.g., 2025-26)"
    )
    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning',
        help_text="Current status of the academic year"
    )
    is_current = models.BooleanField(
        default=False,
        help_text="Is this the currently active academic year?"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Ensure only one academic year is marked as current"""
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Grade(models.Model):
    """
    Grade/Class level for a specific academic year.
    References GradeType for the grade configuration.

    Example: Grade for "Class 5" in academic year "2025-26"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to GradeType for configuration
    grade_type = models.ForeignKey(
        GradeType,
        on_delete=models.PROTECT,
        related_name='grades',
        null=True,
        blank=True,
        help_text="Reference to the grade type configuration"
    )

    # Keep number for backward compatibility (will be synced from grade_type)
    number = models.IntegerField(
        validators=[MinValueValidator(-10), MaxValueValidator(15)],
        help_text="Grade number (synced from grade_type)"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Display name (auto-generated from grade_type if not provided)"
    )
    description = models.TextField(blank=True)

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='grades',
        help_text="Academic year this grade belongs to"
    )

    subjects = models.ManyToManyField(
        'Subject',
        related_name='grades',
        blank=True,
        help_text="Subjects taught in this grade (same across all sections)"
    )

    display_order = models.IntegerField(
        default=0,
        help_text="Order for display purposes (auto-set from grade_type if 0)"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['academic_year', 'display_order', 'number']
        unique_together = [['academic_year', 'number']]
        indexes = [
            models.Index(fields=['academic_year', 'number']),
            models.Index(fields=['academic_year', 'display_order']),
            models.Index(fields=['is_active']),
            models.Index(fields=['grade_type']),
        ]

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.academic_year.name})"
        return f"{self.get_default_name()} ({self.academic_year.name})"

    def get_default_name(self):
        """Get default name based on grade_type or number."""
        if self.grade_type:
            return self.grade_type.name
        # Fallback for backward compatibility
        if self.number < 0:
            names = {-3: 'Nursery', -2: 'Pre-KG', -1: 'KG'}
            return names.get(self.number, f"Pre-Primary {self.number}")
        return f"Class {self.number}"

    def save(self, *args, **kwargs):
        # Sync number and display_order from grade_type if available
        if self.grade_type:
            self.number = self.grade_type.number
            if self.display_order == 0:
                self.display_order = self.grade_type.display_order

        # Auto-generate name if not provided
        if not self.name:
            self.name = self.get_default_name()

        # Auto-set display_order based on number if still 0
        if self.display_order == 0:
            if self.number < 0:
                self.display_order = self.number + 4  # -3→1, -2→2, -1→3
            else:
                self.display_order = self.number + 3  # 1→4, 2→5, ... 12→15

        super().save(*args, **kwargs)


class Section(models.Model):
    """
    Section within a grade (e.g., 5A, 5B, 5C).
    Previously, section was just a field in the Class model.
    Now it's a separate entity with its own properties.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="Grade this section belongs to"
    )
    name = models.CharField(
        max_length=10,
        help_text="Section name (e.g., A, B, C)"
    )

    class_teacher = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_teacher_sections',
        help_text="Class teacher assigned to this section"
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="Academic year this section belongs to"
    )

    room_number = models.CharField(max_length=50, blank=True)

    room_layout = models.ForeignKey(
        'RoomLayout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections',
        help_text="Room layout template assigned to this section"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Is this section currently active?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['grade', 'name']
        unique_together = [['grade', 'name', 'academic_year']]
        indexes = [
            models.Index(fields=['grade', 'name']),
            models.Index(fields=['academic_year']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.grade.number}{self.name} ({self.academic_year.name})"

    @property
    def full_name(self):
        """Returns full section name (e.g., 'Class 5A')"""
        return f"Class {self.grade.number}{self.name}"

    @property
    def current_strength(self):
        """Returns current number of students in this section"""
        return self.students.filter(status='active').count()

    @property
    def capacity(self):
        """Returns total seat capacity from assigned room layout, or None if no layout"""
        if self.room_layout:
            return self.room_layout.total_seats
        return None

    @property
    def available_capacity(self):
        """Returns available seats in this section"""
        if self.capacity is None:
            return None
        return self.capacity - self.current_strength


# =============================================================================
# PHASE B: STUDENT CORE MODELS (Student Enrollment & Photo Management)
# =============================================================================

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
        Section,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='Section the student is enrolled in'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text='Academic year for this enrollment'
    )

    roll_number = models.CharField(
        max_length=20,
        help_text='Roll number assigned to student in this section (supports alphanumeric like 7A01)'
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
    Student photo management with approval workflow and history tracking.
    Maintains all historical photos with admin approval required.
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
        help_text="Student this photo belongs to"
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='student_photos',
        null=True,
        blank=True,
        help_text="Academic year when this photo was uploaded"
    )

    # Photo file
    image = models.ImageField(
        upload_to='students/photos/%Y/%m/',
        help_text="Student photo (passport size recommended)"
    )

    # Metadata
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    width = models.IntegerField(
        null=True,
        blank=True,
        help_text="Image width in pixels"
    )
    height = models.IntegerField(
        null=True,
        blank=True,
        help_text="Image height in pixels"
    )

    # Approval workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Approval status"
    )
    is_current = models.BooleanField(
        default=False,
        help_text="Is this the currently active photo for the student?"
    )

    # Audit fields
    uploaded_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos_uploaded',
        help_text="User who uploaded this photo"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos_approved',
        help_text="Admin who approved/rejected this photo"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this photo was approved/rejected"
    )

    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if status is rejected)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['student', 'is_current']),
            models.Index(fields=['status', 'academic_year']),
            models.Index(fields=['is_current']),
            models.Index(fields=['uploaded_at']),
        ]
        verbose_name = "Student Photo"
        verbose_name_plural = "Student Photos"

    def __str__(self):
        status_display = self.get_status_display()
        current = " (Current)" if self.is_current else ""
        return f"{self.student.first_name} {self.student.last_name} - {status_display}{current}"

    def save(self, *args, **kwargs):
        """
        Ensure only one photo is marked as current per student.
        Auto-expire old photos when a new one is approved.
        """
        if self.is_current and self.status == 'approved':
            # Unset is_current on all other photos for this student
            StudentPhoto.objects.filter(
                student=self.student,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)

            # Optionally expire old approved photos from previous years
            StudentPhoto.objects.filter(
                student=self.student,
                status='approved',
                is_current=False
            ).exclude(
                academic_year=self.academic_year
            ).update(status='expired')

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
# PHASE C: TEACHER ASSIGNMENT MODELS
# =============================================================================

class ClassTeacher(models.Model):
    """
    Class teacher assignment to sections.
    Tracks which teacher is responsible for a section in a given academic year.
    Supports primary and assistant class teachers via is_primary flag.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments',
        help_text='Section this class teacher is assigned to'
    )
    teacher = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments',
        help_text='Teacher assigned as class teacher'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments',
        help_text='Academic year for this assignment'
    )

    is_primary = models.BooleanField(
        default=True,
        help_text='Is this the primary class teacher? (False for assistant class teachers)'
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this assignment was created'
    )
    assigned_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_teacher_assignments_created',
        help_text='Admin who created this assignment'
    )

    notes = models.TextField(
        blank=True,
        help_text='Additional notes or remarks about this assignment'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', '-is_primary']
        unique_together = [['section', 'academic_year', 'is_primary']]
        indexes = [
            models.Index(fields=['section', 'academic_year']),
            models.Index(fields=['teacher', 'academic_year']),
            models.Index(fields=['academic_year', 'is_primary']),
        ]
        verbose_name = 'Class Teacher Assignment'
        verbose_name_plural = 'Class Teacher Assignments'

    def __str__(self):
        role = "Primary" if self.is_primary else "Assistant"
        return f"{self.teacher} - {self.section} ({role}) - {self.academic_year.name}"

    def save(self, *args, **kwargs):
        """Ensure only one primary class teacher per section per academic year"""
        if self.is_primary:
            ClassTeacher.objects.filter(
                section=self.section,
                academic_year=self.academic_year,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class SubjectTeacher(models.Model):
    """
    Subject teacher assignment to sections.
    Tracks which teacher teaches which subject to which section in a given academic year.
    Only one teacher can be assigned per subject per section per year.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='subject_teacher_assignments',
        help_text='Section this subject is taught to'
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE,
        related_name='subject_teacher_assignments',
        help_text='Subject being taught'
    )
    teacher = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='subject_teacher_assignments',
        help_text='Teacher assigned to teach this subject'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='subject_teacher_assignments',
        help_text='Academic year for this assignment'
    )

    periods_per_week = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Number of periods per week for this subject (for timetable planning)'
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this assignment was created'
    )
    assigned_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_teacher_assignments_created',
        help_text='Admin who created this assignment'
    )

    is_active = models.BooleanField(
        default=True,
        help_text='Is this assignment currently active?'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', 'subject']
        unique_together = [['section', 'subject', 'academic_year']]
        indexes = [
            models.Index(fields=['section', 'academic_year']),
            models.Index(fields=['teacher', 'academic_year']),
            models.Index(fields=['subject', 'academic_year']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Subject Teacher Assignment'
        verbose_name_plural = 'Subject Teacher Assignments'

    def __str__(self):
        return f"{self.teacher} - {self.subject.name} - {self.section} - {self.academic_year.name}"

    @property
    def section_grade(self):
        """Returns the grade of the section"""
        return self.section.grade


class Student(models.Model):
    """
    Student information with support for enrollment and photo management.
    Students are assigned to sections (e.g., "5A", "7B") which belong to grades.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Current section the student is enrolled in (e.g., "5A", "7B")
    current_section = models.ForeignKey(
        'Section',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text='Current section the student is enrolled in'
    )

    academic_year = models.ForeignKey(
        AcademicYear,
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
    roll_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='Current roll number in current section (supports alphanumeric like 7A01)'
    )
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

    # Media (DEPRECATED - use StudentPhoto model instead)
    photo = models.ImageField(
        upload_to='students/photos/',
        null=True,
        blank=True,
        help_text='DEPRECATED - Use StudentPhoto model for photo management'
    )

    # Status (expanded with new choices from brainstorming)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('graduated', 'Graduated'),
            ('transferred', 'Transferred'),
            ('dropped', 'Dropped'),
        ],
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
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.admission_number}"

    @property
    def full_name(self):
        """Returns student's full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def has_current_photo(self):
        """Check if student has an approved current photo"""
        return self.photos.filter(is_current=True, status='approved').exists()

    @property
    def photo_pending_approval(self):
        """Check if student has a photo pending approval"""
        return self.photos.filter(status='pending').exists()

    @property
    def current_photo_url(self):
        """Get URL of current approved photo"""
        photo = self.photos.filter(is_current=True, status='approved').first()
        return photo.image.url if photo else None

    def get_current_photo(self):
        """
        Returns the current approved photo for the student.
        Returns None if no current photo exists.
        """
        try:
            return self.photos.get(is_current=True, status='approved')
        except StudentPhoto.DoesNotExist:
            return None

    def get_current_enrollment(self):
        """
        Returns the current active enrollment for the student.
        Returns None if no current enrollment exists.
        """
        try:
            return self.enrollments.get(is_current=True)
        except StudentEnrollment.DoesNotExist:
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


class Parent(models.Model):
    """Parent/Guardian information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    students = models.ManyToManyField(
        Student,
        related_name='parents_list',
        through='StudentParent'
    )
    user_profile = models.OneToOneField(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parent_record'
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
            models.Index(fields=['is_active']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relation})"


class StudentParent(models.Model):
    """Junction table for Student-Parent relationship"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['student', 'parent']]
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"{self.student} - {self.parent}"


class Subject(models.Model):
    """Subject/Course subjects"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(models.Model):
    """Course assignment to sections (Phase B: uses Section instead of deprecated Class)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Phase B: Section replaces deprecated Class (temporarily nullable for migration)
    section = models.ForeignKey(
        'Section',
        on_delete=models.CASCADE,
        related_name='courses',
        null=True,
        blank=True,
        help_text='Section this course is assigned to'
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
        ordering = ['section', 'subject']
        unique_together = [['section', 'subject', 'academic_year']]
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.section.full_name}"


# =============================================================================
# ATTENDANCE MODELS
# =============================================================================

class AttendanceSession(models.Model):
    """Attendance session types (morning, afternoon, full-day)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=50)  # 'Morning', 'Afternoon', 'Full Day'
    code = models.CharField(max_length=20, unique=True)  # 'morning', 'afternoon', 'full_day'
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Attendance(models.Model):
    """Individual attendance record for a student (Phase B: uses Section instead of deprecated Class)"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    # Phase B: Section replaces deprecated Class (temporarily nullable for migration)
    section = models.ForeignKey(
        'Section',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        null=True,
        blank=True,
        help_text='Section for attendance tracking'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records'
    )

    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)

    # Audit fields
    marked_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_attendance'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'student__roll_number']
        unique_together = [['student', 'date', 'session']]
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['section', 'date']),
            models.Index(fields=['student', 'date']),
        ]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class AttendanceSettings(models.Model):
    """Global attendance settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    low_attendance_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('75.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage below which attendance is considered low'
    )
    allow_backdated_entry = models.BooleanField(default=True)
    max_backdated_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        help_text='Maximum number of days allowed for backdated attendance entry'
    )
    notify_parents_on_absent = models.BooleanField(
        default=False,
        help_text='Send notification to parents when student is marked absent'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Attendance Settings'

    def __str__(self):
        return f"Attendance Settings (Threshold: {self.low_attendance_threshold}%)"


# =============================================================================
# GRADES / ASSESSMENT MODELS
# =============================================================================

class ExamType(models.Model):
    """Exam type configuration (Unit Test, Half Yearly, Annual, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)  # e.g., "Unit Test 1", "Half Yearly"
    code = models.CharField(max_length=20, unique=True)  # e.g., "UT1", "HY"
    description = models.TextField(blank=True)

    # Configuration
    default_max_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00')
    )
    weightage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text='Weightage for final grade calculation'
    )

    # Ordering
    display_order = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class GradingScale(models.Model):
    """Grade scale configuration (e.g., Standard 10-Point Scale)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)  # e.g., "Standard 10-Point Scale"
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one default grading scale
        if self.is_default:
            GradingScale.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class GradeRange(models.Model):
    """Individual grade ranges within a grading scale"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    grading_scale = models.ForeignKey(
        GradingScale,
        on_delete=models.CASCADE,
        related_name='ranges'
    )

    grade = models.CharField(max_length=5)  # e.g., "A+", "A", "B+"
    min_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Grade point (e.g., 4.0 for A+)'
    )
    description = models.CharField(max_length=100, blank=True)  # e.g., "Excellent"

    class Meta:
        ordering = ['-min_percentage']
        unique_together = [['grading_scale', 'grade']]

    def __str__(self):
        return f"{self.grade} ({self.min_percentage}% - {self.max_percentage}%)"


class Exam(models.Model):
    """Specific exam instance for a section/subject in an academic year (Phase B: uses Section instead of deprecated Class)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='exams'
    )
    # Phase B: Section replaces deprecated Class (temporarily nullable for migration)
    section = models.ForeignKey(
        'Section',
        on_delete=models.CASCADE,
        related_name='exams',
        null=True,
        blank=True,
        help_text='Section for exam assignment'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='exams'
    )

    # Exam details
    name = models.CharField(max_length=200, blank=True)  # Auto-generated or custom
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    passing_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Dates
    exam_date = models.DateField(null=True, blank=True)

    # Status
    is_published = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)  # Prevents further edits

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-academic_year__start_date', 'exam_type__display_order']
        unique_together = [['exam_type', 'academic_year', 'section', 'subject']]

    def __str__(self):
        return self.name or f"{self.exam_type.name} - {self.subject.name} - {self.section.full_name}"

    def save(self, *args, **kwargs):
        # Auto-generate name if not provided
        if not self.name:
            self.name = f"{self.exam_type.name} - {self.subject.name} - {self.section.full_name}"
        super().save(*args, **kwargs)


class StudentMark(models.Model):
    """Individual student marks for an exam"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='marks'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='marks'
    )

    # Marks
    marks_obtained = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_absent = models.BooleanField(default=False)

    # Computed fields (stored for performance)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    grade = models.CharField(max_length=5, blank=True)

    # Remarks
    remarks = models.TextField(blank=True)

    # Audit field
    entered_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='marks_entered'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__roll_number']
        unique_together = [['exam', 'student']]
        indexes = [
            models.Index(fields=['exam', 'student']),
            models.Index(fields=['student', 'exam']),
        ]

    def __str__(self):
        marks = 'Absent' if self.is_absent else f"{self.marks_obtained}"
        return f"{self.student} - {self.exam} - {marks}"

    def calculate_percentage_and_grade(self):
        """Calculate percentage and grade based on marks"""
        if self.is_absent or self.marks_obtained is None:
            self.percentage = None
            self.grade = ''
            return

        if self.exam.max_marks > 0:
            self.percentage = (self.marks_obtained / self.exam.max_marks) * 100
        else:
            self.percentage = Decimal('0.00')

        # Get default grading scale and calculate grade
        try:
            grading_scale = GradingScale.objects.get(is_default=True, is_active=True)
            grade_range = grading_scale.ranges.filter(
                min_percentage__lte=self.percentage,
                max_percentage__gte=self.percentage
            ).first()
            self.grade = grade_range.grade if grade_range else ''
        except GradingScale.DoesNotExist:
            # Fallback grade calculation
            if self.percentage >= 90:
                self.grade = 'A+'
            elif self.percentage >= 80:
                self.grade = 'A'
            elif self.percentage >= 70:
                self.grade = 'B+'
            elif self.percentage >= 60:
                self.grade = 'B'
            elif self.percentage >= 50:
                self.grade = 'C'
            elif self.percentage >= 40:
                self.grade = 'D'
            else:
                self.grade = 'F'

    def save(self, *args, **kwargs):
        self.calculate_percentage_and_grade()
        super().save(*args, **kwargs)


class MarkAuditLog(models.Model):
    """Audit trail for grade changes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student_mark = models.ForeignKey(
        StudentMark,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )

    # Change details
    old_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    new_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    old_grade = models.CharField(max_length=5, blank=True)
    new_grade = models.CharField(max_length=5, blank=True)

    reason = models.TextField(blank=True)

    # Who made the change
    changed_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='mark_changes'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_mark} - Changed from {self.old_marks} to {self.new_marks}"


# =============================================================================
# ROOM LAYOUT & SEATING ARRANGEMENT
# =============================================================================

class RoomLayout(models.Model):
    """
    Reusable room layout template defining desk grid configuration.
    Not tied to any section or academic year — can be shared across sections.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Layout name (e.g., Room 101 Layout)")
    rows = models.PositiveIntegerField(help_text="Number of rows in the grid")
    columns = models.PositiveIntegerField(help_text="Number of columns (desks per row)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rows}×{self.columns})"

    @property
    def total_seats(self):
        """Sum of all active desk capacities."""
        return sum(d.capacity for d in self.desks.filter(is_active=True))

    @property
    def desk_count(self):
        """Number of active desks."""
        return self.desks.filter(is_active=True).count()


class Desk(models.Model):
    """
    A single desk in a room layout grid.
    Each desk has its own capacity (1-3 students).
    Inactive desks represent aisles or empty spaces.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_layout = models.ForeignKey(
        RoomLayout,
        on_delete=models.CASCADE,
        related_name='desks'
    )
    row = models.PositiveIntegerField(help_text="0-indexed row position")
    column = models.PositiveIntegerField(help_text="0-indexed column position")
    capacity = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Number of students this desk can seat (1-3)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="False = aisle or empty space"
    )
    label = models.CharField(
        max_length=20,
        blank=True,
        help_text="Optional label (e.g., R1-C3)"
    )

    class Meta:
        unique_together = [['room_layout', 'row', 'column']]
        ordering = ['row', 'column']

    def __str__(self):
        return f"Desk ({self.row},{self.column}) - cap:{self.capacity}"


class SeatingAssignment(models.Model):
    """
    Links a student to a specific desk position within a section.
    Each student can only have one seat per section.
    Each desk position can only hold one student.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='seating_assignments'
    )
    desk = models.ForeignKey(
        Desk,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='seating_assignments'
    )
    position = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="1-based position within desk (1, 2, or 3)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ['section', 'student'],          # Student sits in one desk per section
            ['desk', 'position', 'section'],  # One student per position per desk
        ]
        ordering = ['desk__row', 'desk__column', 'position']

    def __str__(self):
        return f"{self.student} → Desk({self.desk.row},{self.desk.column}) pos {self.position}"
