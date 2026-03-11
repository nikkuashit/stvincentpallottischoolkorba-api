"""
CMS App - Content Management System

This module handles:
- Navigation menus (hierarchical)
- Static pages
- Dynamic sections
- Galleries and images
- Documents
"""

import uuid
from django.db import models


class NavigationMenu(models.Model):
    """Hierarchical navigation menu"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='navigation_menus'
    )
    school = models.ForeignKey(
        'tenants.School',
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'title']
        unique_together = [['organization', 'school', 'slug', 'parent']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
            models.Index(fields=['parent', 'display_order']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class Page(models.Model):
    """Static pages"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='pages'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='pages'
    )

    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, db_index=True)  # CharField to allow slashes in paths
    description = models.TextField(blank=True)
    hero_image = models.ImageField(upload_to='pages/heroes/', null=True, blank=True)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    # Status
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class Section(models.Model):
    """Dynamic content sections"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='sections'
    )
    school = models.ForeignKey(
        'tenants.School',
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
            ('principal', 'Principal Message'),
            ('courses', 'Courses'),
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

    # Landing page settings
    show_in_landing_page = models.BooleanField(default=False)
    landing_page_order = models.IntegerField(default=0, help_text="Order of section on landing page")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'title']
        unique_together = [['organization', 'school', 'page', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_visible']),
            models.Index(fields=['page', 'display_order']),
            models.Index(fields=['organization', 'school', 'show_in_landing_page', 'landing_page_order']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class Gallery(models.Model):
    """Photo galleries"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='galleries'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='galleries'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    cover_image = models.ImageField(upload_to='galleries/covers/', null=True, blank=True)

    event = models.ForeignKey(
        'communications.Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='galleries'
    )

    created_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_galleries'
    )

    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Galleries"
        ordering = ['-published_date']
        unique_together = [['organization', 'school', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'school', 'is_published']),
        ]

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    """Images in galleries"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
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
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_images'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['organization', 'gallery', 'display_order']),
        ]

    def __str__(self):
        return f"{self.title or 'Image'} - {self.gallery.title}"


class Document(models.Model):
    """Document management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        help_text="Optional: Link document to a specific page"
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
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents'
    )

    is_public = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_public']),
            models.Index(fields=['category']),
            models.Index(fields=['page']),
        ]

    def __str__(self):
        return self.title


class Slider(models.Model):
    """Hero slider/carousel for landing page"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='sliders'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='sliders'
    )

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='sliders/')

    # Call to action
    cta_text = models.CharField(max_length=100, blank=True)
    cta_link = models.CharField(max_length=255, blank=True)

    # Display settings
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
            models.Index(fields=['display_order']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class Marquee(models.Model):
    """Scrolling announcement/marquee text"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='marquees'
    )
    school = models.ForeignKey(
        'tenants.School',
        on_delete=models.CASCADE,
        related_name='marquees'
    )

    text = models.TextField()
    link = models.CharField(max_length=255, blank=True)

    # Display settings
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Optional scheduling
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'school', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.text[:50]}... - {self.school.name}"
