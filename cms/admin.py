"""Django Admin for CMS App"""

from django.contrib import admin
from django.utils.html import format_html
from .models import NavigationMenu, Page, Section, Gallery, GalleryImage, Document


@admin.register(NavigationMenu)
class NavigationMenuAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'menu_type', 'parent', 'display_order', 'show_in_navigation', 'is_active']
    list_filter = ['menu_type', 'is_external', 'show_in_navigation', 'show_in_footer', 'is_active', 'school']
    search_fields = ['title', 'slug', 'href']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['school', 'display_order', 'title']


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
