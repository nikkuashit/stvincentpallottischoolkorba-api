"""
Django Admin Configuration for Schools App

This module registers all models with the Django admin panel and configures
their display, filters, search, and inline editing capabilities.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    # Tenant Management
    SubscriptionPlan, Organization, Subscription, School,
    # User Management
    Role, UserProfile,
    # School Configuration
    ThemeConfig, NavigationMenu, SocialLinks,
    # Content Management
    Page, Section,
    # Academic Management
    AcademicYear, Class, Student, Parent, StudentParent, Subject, Course,
    # Communication
    News, Event, Announcement, Notification,
    # Media Management
    Gallery, GalleryImage, Document,
    # System Management
    Invoice, AuditLog
)


# ==============================================================================
# TENANT MANAGEMENT
# ==============================================================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'billing_period', 'max_students', 'max_staff', 'is_active', 'display_order']
    list_filter = ['billing_period', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'price']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'email', 'city', 'country', 'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_verified', 'country', 'state']
    search_fields = ['name', 'slug', 'email', 'domain']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'domain', 'is_active', 'is_verified')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Metadata', {
            'fields': ('settings', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'auto_renew', 'plan']
    search_fields = ['organization__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'city', 'state', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'state', 'country', 'organization']
    search_fields = ['name', 'short_name', 'email', 'city']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Basic Information', {
            'fields': ('name', 'short_name', 'tagline', 'description', 'established_year')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code')
        }),
        ('Media', {
            'fields': ('logo', 'banner_image')
        }),
        ('Settings', {
            'fields': ('timezone', 'language', 'currency', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# USER MANAGEMENT
# ==============================================================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'slug', 'is_system_role', 'is_active', 'created_at']
    list_filter = ['is_system_role', 'is_active', 'organization']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_full_name', 'organization', 'school', 'role', 'employee_id', 'is_active', 'created_at']
    list_filter = ['is_active', 'role', 'gender', 'organization', 'school']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'employee_id', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'last_login_at']

    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'User'


# ==============================================================================
# SCHOOL CONFIGURATION
# ==============================================================================

@admin.register(ThemeConfig)
class ThemeConfigAdmin(admin.ModelAdmin):
    list_display = ['school', 'organization', 'layout_style', 'font_family', 'created_at']
    list_filter = ['layout_style', 'organization']
    search_fields = ['school__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('School', {
            'fields': ('organization', 'school')
        }),
        ('Colors', {
            'fields': (
                'primary_color', 'secondary_color', 'accent_color',
                'success_color', 'warning_color', 'destructive_color',
                'background_color', 'foreground_color'
            )
        }),
        ('Typography', {
            'fields': ('font_family', 'heading_font')
        }),
        ('Layout', {
            'fields': ('layout_style',)
        }),
        ('Custom', {
            'fields': ('custom_css', 'settings'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NavigationMenu)
class NavigationMenuAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'menu_type', 'parent', 'display_order', 'show_in_navigation', 'is_active']
    list_filter = ['menu_type', 'is_external', 'show_in_navigation', 'show_in_footer', 'is_active', 'school']
    search_fields = ['title', 'slug', 'href']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['school', 'display_order', 'title']


@admin.register(SocialLinks)
class SocialLinksAdmin(admin.ModelAdmin):
    list_display = ['school', 'organization', 'has_facebook', 'has_twitter', 'has_instagram', 'created_at']
    list_filter = ['organization', 'school']
    search_fields = ['school__name']
    readonly_fields = ['created_at', 'updated_at']

    def has_facebook(self, obj):
        return bool(obj.facebook)
    has_facebook.boolean = True

    def has_twitter(self, obj):
        return bool(obj.twitter)
    has_twitter.boolean = True

    def has_instagram(self, obj):
        return bool(obj.instagram)
    has_instagram.boolean = True


# ==============================================================================
# CONTENT MANAGEMENT
# ==============================================================================

class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ['title', 'slug', 'section_type', 'display_order', 'is_visible']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'slug', 'is_published', 'published_at', 'created_at']
    list_filter = ['is_published', 'school', 'organization']
    search_fields = ['title', 'slug', 'description', 'meta_title']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_at'
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'page', 'section_type', 'display_order', 'is_visible', 'created_at']
    list_filter = ['section_type', 'is_visible', 'school', 'page']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['page', 'display_order']


# ==============================================================================
# ACADEMIC MANAGEMENT
# ==============================================================================

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'start_date', 'end_date', 'is_current', 'is_active']
    list_filter = ['is_current', 'is_active', 'school', 'organization']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'grade', 'section', 'class_teacher', 'room_number', 'capacity', 'is_active']
    list_filter = ['grade', 'is_active', 'school', 'organization']
    search_fields = ['name', 'section', 'room_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['school', 'grade', 'section']


class StudentParentInline(admin.TabularInline):
    model = StudentParent
    extra = 1
    fields = ['parent', 'is_primary']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'admission_number', 'school', 'current_class', 'status', 'admission_date']
    list_filter = ['status', 'gender', 'school', 'current_class', 'organization']
    search_fields = ['first_name', 'last_name', 'admission_number', 'email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'admission_date'
    inlines = [StudentParentInline]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'

    fieldsets = (
        ('School Information', {
            'fields': ('organization', 'school', 'current_class', 'admission_number', 'roll_number', 'status')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'blood_group', 'photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code')
        }),
        ('Academic Information', {
            'fields': ('admission_date',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'relation', 'school', 'email', 'phone', 'is_primary_contact', 'is_active']
    list_filter = ['relation', 'is_primary_contact', 'is_active', 'school', 'organization']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'


@admin.register(StudentParent)
class StudentParentAdmin(admin.ModelAdmin):
    list_display = ['student', 'parent', 'is_primary', 'organization', 'created_at']
    list_filter = ['is_primary', 'organization']
    search_fields = ['student__first_name', 'student__last_name', 'parent__first_name', 'parent__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'school', 'is_active', 'created_at']
    list_filter = ['is_active', 'school', 'organization']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['subject', 'class_assigned', 'teacher', 'academic_year', 'school', 'is_active']
    list_filter = ['is_active', 'academic_year', 'school', 'organization']
    search_fields = ['subject__name', 'class_assigned__name', 'teacher__user__first_name']
    readonly_fields = ['created_at', 'updated_at']


# ==============================================================================
# COMMUNICATION
# ==============================================================================

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'author', 'published_date', 'is_published', 'is_featured', 'views_count']
    list_filter = ['is_published', 'is_featured', 'school', 'organization']
    search_fields = ['title', 'slug', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    date_hierarchy = 'published_date'

    fieldsets = (
        ('School', {
            'fields': ('organization', 'school')
        }),
        ('Content', {
            'fields': ('title', 'slug', 'summary', 'content', 'featured_image', 'author')
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_date', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'event_type', 'start_date', 'end_date', 'is_published', 'is_featured']
    list_filter = ['event_type', 'is_published', 'is_featured', 'school', 'organization']
    search_fields = ['title', 'slug', 'description', 'location']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'priority', 'created_by', 'is_published', 'published_date', 'expiry_date']
    list_filter = ['priority', 'is_published', 'school', 'organization']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_date'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'organization']
    search_fields = ['title', 'message', 'user__user__first_name', 'user__user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    date_hierarchy = 'created_at'


# ==============================================================================
# MEDIA MANAGEMENT
# ==============================================================================

class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 0
    fields = ['image', 'title', 'display_order']


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'event', 'is_published', 'published_date', 'created_by']
    list_filter = ['is_published', 'school', 'organization']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_date'
    inlines = [GalleryImageInline]


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'title', 'gallery', 'display_order', 'uploaded_by', 'created_at']
    list_filter = ['gallery', 'organization']
    search_fields = ['title', 'description', 'gallery__title']
    readonly_fields = ['created_at', 'updated_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'category', 'file_type', 'file_size_mb', 'is_public', 'download_count', 'uploaded_by']
    list_filter = ['category', 'is_public', 'file_type', 'school', 'organization']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'download_count', 'file_size']

    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'Size'


# ==============================================================================
# SYSTEM MANAGEMENT
# ==============================================================================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'subscription', 'total_amount', 'status', 'invoice_date', 'due_date', 'paid_date']
    list_filter = ['status', 'payment_method']
    search_fields = ['invoice_number', 'subscription__organization__name', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'invoice_date'

    fieldsets = (
        ('Subscription', {
            'fields': ('subscription',)
        }),
        ('Invoice Details', {
            'fields': ('invoice_number', 'amount', 'tax_amount', 'total_amount', 'status')
        }),
        ('Dates', {
            'fields': ('invoice_date', 'due_date', 'paid_date')
        }),
        ('Payment', {
            'fields': ('payment_method', 'transaction_id')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'user', 'organization', 'ip_address', 'created_at']
    list_filter = ['action', 'model_name', 'organization']
    search_fields = ['action', 'model_name', 'user__user__username', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
