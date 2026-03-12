"""Django Admin for Config App - Simplified without multi-tenancy"""

from django.contrib import admin
from .models import ThemeConfig, SocialLinks


@admin.register(ThemeConfig)
class ThemeConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'layout_style', 'font_family', 'primary_color', 'created_at']
    list_filter = ['layout_style']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Colors', {
            'fields': ('primary_color', 'secondary_color', 'accent_color', 'success_color', 'warning_color', 'destructive_color', 'background_color', 'foreground_color')
        }),
        ('Typography', {
            'fields': ('font_family', 'heading_font')
        }),
        ('Layout', {
            'fields': ('layout_style',)
        }),
        ('Advanced', {
            'fields': ('custom_css', 'settings'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SocialLinks)
class SocialLinksAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'has_facebook', 'has_twitter', 'has_instagram', 'has_youtube', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Social Networks', {
            'fields': ('facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'whatsapp')
        }),
        ('Additional Links', {
            'fields': ('additional_links',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_facebook(self, obj):
        return bool(obj.facebook)
    has_facebook.boolean = True

    def has_twitter(self, obj):
        return bool(obj.twitter)
    has_twitter.boolean = True

    def has_instagram(self, obj):
        return bool(obj.instagram)
    has_instagram.boolean = True

    def has_youtube(self, obj):
        return bool(obj.youtube)
    has_youtube.boolean = True
