"""Django Admin for CMS App - Simplified without multi-tenancy"""

from django.contrib import admin
from django.utils.html import format_html
from .models import NavigationMenu, Page, Section, Gallery, GalleryImage, Document, Slider, Marquee


@admin.register(NavigationMenu)
class NavigationMenuAdmin(admin.ModelAdmin):
    list_display = ['title', 'menu_type', 'parent', 'display_order', 'show_in_navigation', 'is_active']
    list_filter = ['menu_type', 'is_external', 'show_in_navigation', 'show_in_footer', 'is_active']
    search_fields = ['title', 'slug', 'href']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['display_order', 'title']


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ['title', 'slug', 'section_type', 'display_order', 'is_visible', 'show_in_landing_page', 'landing_page_order']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'published_at', 'created_at']
    list_filter = ['is_published']
    search_fields = ['title', 'slug', 'description', 'meta_title']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_at'
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'page', 'section_type', 'display_order', 'is_visible', 'show_in_landing_page', 'landing_page_order', 'created_at']
    list_filter = ['section_type', 'is_visible', 'show_in_landing_page', 'page']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['page', 'display_order']
    fieldsets = (
        (None, {
            'fields': ('page', 'title', 'slug', 'section_type')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_visible', 'background_color', 'background_image')
        }),
        ('Landing Page', {
            'fields': ('show_in_landing_page', 'landing_page_order', 'landing_page_width'),
            'description': 'Configure how this section appears on the landing page'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 0
    fields = ['image', 'title', 'display_order']


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'is_published', 'published_date', 'created_by']
    list_filter = ['is_published']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_date'
    inlines = [GalleryImageInline]


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'title', 'gallery', 'display_order', 'uploaded_by', 'created_at']
    list_filter = ['gallery']
    search_fields = ['title', 'description', 'gallery__title']
    readonly_fields = ['created_at', 'updated_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'page', 'category', 'file_type', 'file_size_mb', 'is_public', 'download_count', 'uploaded_by']
    list_filter = ['category', 'is_public', 'file_type', 'page']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'download_count', 'file_size']

    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'Size'


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'subtitle', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['display_order']


@admin.register(Marquee)
class MarqueeAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'display_order', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active']
    search_fields = ['text']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['display_order']

    def text_preview(self, obj):
        return f"{obj.text[:50]}..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'
