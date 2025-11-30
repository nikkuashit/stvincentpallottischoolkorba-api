"""
Multi-tenant SaaS School ERP Models

This module implements the core database models for a multi-tenant school management system.
All models include organization_id/school_id for tenant isolation.
"""

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


# ==============================================================================
# BASE MODELS
# ==============================================================================

class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(TimeStampedModel):
    """Abstract base model for tenant isolation"""
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )

    class Meta:
        abstract = True


# ==============================================================================
# TENANT MANAGEMENT
# ==============================================================================

class SubscriptionPlan(TimeStampedModel):
    """SaaS subscription plans"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_period = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly')
        ],
        default='monthly'
    )

    # Feature limits
    max_students = models.IntegerField(null=True, blank=True)
    max_staff = models.IntegerField(null=True, blank=True)
    max_storage_gb = models.IntegerField(null=True, blank=True)
    features = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'price']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_period}"


class Organization(TimeStampedModel):
    """Root tenant entity representing a school organization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)

    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    # Metadata
    settings = models.JSONField(default=dict)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['domain']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Subscription(TimeStampedModel):
    """Organization subscription management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('trial', 'Trial'),
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired')
        ],
        default='trial'
    )

    trial_start_date = models.DateField(null=True, blank=True)
    trial_end_date = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=True)

    # Usage tracking
    current_students = models.IntegerField(default=0)
    current_staff = models.IntegerField(default=0)
    current_storage_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.plan.name} ({self.status})"


class School(TenantModel):
    """School entity - 1:1 with Organization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic Information
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    short_name = models.CharField(max_length=100, blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    established_year = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1800), MaxValueValidator(2100)]
    )

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)

    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)

    # Media
    logo = models.ImageField(upload_to='schools/logos/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='schools/banners/', null=True, blank=True)

    # Settings
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    language = models.CharField(max_length=10, default='en')
    currency = models.CharField(max_length=10, default='INR')
    config = models.JSONField(default=dict)

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


# ==============================================================================
# USER MANAGEMENT
# ==============================================================================

class Role(TenantModel):
    """Role-based access control"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)
    is_system_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class UserProfile(TenantModel):
    """Extended user profile with multi-tenancy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='user_profiles',
        null=True,
        blank=True
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='user_profiles'
    )

    # Personal Information
    employee_id = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        blank=True
    )
    phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Profile
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
            models.Index(fields=['employee_id']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name}"


# ==============================================================================
# SCHOOL CONFIGURATION
# ==============================================================================

class ThemeConfig(TenantModel):
    """Theme and branding configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name='theme_config'
    )

    # Colors
    primary_color = models.CharField(max_length=7, default='#1e3a8a')
    secondary_color = models.CharField(max_length=7, default='#64748b')
    accent_color = models.CharField(max_length=7, default='#3b82f6')
    success_color = models.CharField(max_length=7, default='#10b981')
    warning_color = models.CharField(max_length=7, default='#f59e0b')
    destructive_color = models.CharField(max_length=7, default='#ef4444')
    background_color = models.CharField(max_length=7, default='#ffffff')
    foreground_color = models.CharField(max_length=7, default='#0f172a')

    # Typography
    font_family = models.CharField(max_length=100, default='Inter')
    heading_font = models.CharField(max_length=100, blank=True)

    # Layout
    layout_style = models.CharField(
        max_length=20,
        choices=[
            ('boxed', 'Boxed'),
            ('fluid', 'Fluid'),
            ('wide', 'Wide')
        ],
        default='fluid'
    )

    # Additional settings
    custom_css = models.TextField(blank=True)
    settings = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=['organization', 'school']),
        ]

    def __str__(self):
        return f"Theme - {self.school.name}"


class NavigationMenu(TenantModel):
    """Hierarchical navigation menu"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='navigation_menus'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    title = models.CharField(max_length=100)
    slug = models.SlugField()
    href = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    menu_type = models.CharField(
        max_length=20,
        choices=[
            ('page', 'Page'),
            ('section', 'Section'),
            ('dropdown', 'Dropdown'),
            ('external', 'External Link')
        ],
        default='page'
    )

    # External link
    is_external = models.BooleanField(default=False)
    external_url = models.URLField(blank=True)
    open_in_new_tab = models.BooleanField(default=False)

    # Display settings
    show_in_navigation = models.BooleanField(default=True)
    show_in_footer = models.BooleanField(default=False)
    show_in_landing_page = models.BooleanField(default=False)

    # Ordering
    display_order = models.IntegerField(default=0)

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'title']
        unique_together = [['organization', 'school', 'slug', 'parent']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
            models.Index(fields=['parent', 'display_order']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class SocialLinks(TenantModel):
    """Social media links"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name='social_links'
    )

    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    # Additional links
    additional_links = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = "Social Links"
        indexes = [
            models.Index(fields=['organization', 'school']),
        ]

    def __str__(self):
        return f"Social Links - {self.school.name}"


# ==============================================================================
# CONTENT MANAGEMENT
# ==============================================================================

class Page(TenantModel):
    """Static pages"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='pages'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    hero_image = models.ImageField(upload_to='pages/heroes/', null=True, blank=True)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    # Status
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['title']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class Section(TenantModel):
    """Dynamic content sections"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='sections',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    section_type = models.CharField(
        max_length=50,
        choices=[
            ('hero', 'Hero Section'),
            ('about', 'About'),
            ('features', 'Features'),
            ('gallery', 'Gallery'),
            ('news', 'News'),
            ('events', 'Events'),
            ('contact', 'Contact'),
            ('custom', 'Custom')
        ],
        default='custom'
    )

    # Content stored as JSON for flexibility
    content = models.JSONField(default=dict)

    # Display settings
    display_order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    background_color = models.CharField(max_length=7, blank=True)
    background_image = models.ImageField(upload_to='sections/backgrounds/', null=True, blank=True)

    class Meta:
        ordering = ['display_order', 'title']
        unique_together = [['organization', 'school', 'page', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_visible']),
            models.Index(fields=['page', 'display_order']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name}"


# ==============================================================================
# ACADEMIC MANAGEMENT
# ==============================================================================

class AcademicYear(TenantModel):
    """Academic year configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='academic_years'
    )

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = [['organization', 'school', 'name']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_current']),
        ]

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Class(TenantModel):
    """Class/Grade configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classes'
    )

    name = models.CharField(max_length=100)
    grade = models.IntegerField()
    section = models.CharField(max_length=10)
    class_teacher = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_classes'
    )

    room_number = models.CharField(max_length=50, blank=True)
    capacity = models.IntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['grade', 'section']
        unique_together = [['organization', 'school', 'grade', 'section']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class Student(TenantModel):
    """Student information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
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

    class Meta:
        ordering = ['first_name', 'last_name']
        unique_together = [['organization', 'school', 'admission_number']]
        indexes = [
            models.Index(fields=['organization', 'school', 'status']),
            models.Index(fields=['admission_number']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.admission_number}"


class Parent(TenantModel):
    """Parent/Guardian information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
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

    class Meta:
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relation})"


class StudentParent(TenantModel):
    """Junction table for Student-Parent relationship"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = [['organization', 'student', 'parent']]
        indexes = [
            models.Index(fields=['organization', 'student']),
            models.Index(fields=['organization', 'parent']),
        ]

    def __str__(self):
        return f"{self.student} - {self.parent}"


class Subject(TenantModel):
    """Subject/Course subjects"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        unique_together = [['organization', 'school', 'code']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(TenantModel):
    """Course assignment to classes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
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
        UserProfile,
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

    class Meta:
        ordering = ['class_assigned', 'subject']
        unique_together = [['organization', 'school', 'class_assigned', 'subject', 'academic_year']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.class_assigned.name}"


# ==============================================================================
# COMMUNICATION
# ==============================================================================

class News(TenantModel):
    """News articles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='news'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    summary = models.TextField()
    content = models.TextField()

    featured_image = models.ImageField(upload_to='news/images/', null=True, blank=True)

    author = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_articles'
    )

    published_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    views_count = models.IntegerField(default=0)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "News"
        ordering = ['-published_date']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['published_date']),
        ]

    def __str__(self):
        return self.title


class Event(TenantModel):
    """School events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='events'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField()

    event_type = models.CharField(
        max_length=50,
        choices=[
            ('academic', 'Academic'),
            ('sports', 'Sports'),
            ('cultural', 'Cultural'),
            ('holiday', 'Holiday'),
            ('other', 'Other')
        ],
        default='academic'
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)

    featured_image = models.ImageField(upload_to='events/images/', null=True, blank=True)

    organizer = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events'
    )

    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    max_participants = models.IntegerField(null=True, blank=True)
    registration_required = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['start_date']),
        ]

    def __str__(self):
        return self.title


class Announcement(TenantModel):
    """School announcements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='announcements'
    )

    title = models.CharField(max_length=255)
    content = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        default='normal'
    )

    target_audience = models.JSONField(default=dict)

    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements'
    )

    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['published_date', 'expiry_date']),
        ]

    def __str__(self):
        return self.title


class Notification(TenantModel):
    """User notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('info', 'Information'),
            ('warning', 'Warning'),
            ('success', 'Success'),
            ('error', 'Error')
        ],
        default='info'
    )

    link = models.CharField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user}"


# ==============================================================================
# MEDIA MANAGEMENT
# ==============================================================================

class Gallery(TenantModel):
    """Photo galleries"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='galleries'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    cover_image = models.ImageField(upload_to='galleries/covers/', null=True, blank=True)

    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='galleries'
    )

    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_galleries'
    )

    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Galleries"
        ordering = ['-published_date']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
        ]

    def __str__(self):
        return self.title


class GalleryImage(TenantModel):
    """Images in galleries"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='images'
    )

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='galleries/images/')

    display_order = models.IntegerField(default=0)

    uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_images'
    )

    class Meta:
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['organization', 'gallery', 'display_order']),
        ]

    def __str__(self):
        return f"{self.title or 'Image'} - {self.gallery.title}"


class Document(TenantModel):
    """Document management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/')
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=50)

    category = models.CharField(
        max_length=50,
        choices=[
            ('policy', 'Policy'),
            ('form', 'Form'),
            ('syllabus', 'Syllabus'),
            ('report', 'Report'),
            ('other', 'Other')
        ],
        default='other'
    )

    uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )

    is_public = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_public']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title


# ==============================================================================
# SYSTEM MANAGEMENT
# ==============================================================================

class Invoice(TimeStampedModel):
    """Billing invoices"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices'
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )

    invoice_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)

    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.subscription.organization.name}"


class AuditLog(TimeStampedModel):
    """System audit logging"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )

    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_id = models.UUIDField()

    changes = models.JSONField(default=dict)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.action} - {self.model_name} by {self.user}"
