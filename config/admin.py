"""Django Admin for Config App"""

from django.contrib import admin
from .models import ThemeConfig, SocialLinks


@admin.register(ThemeConfig)
class ThemeConfigAdmin(admin.ModelAdmin):
    list_display = ['school', 'organization', 'layout_style', 'font_family', 'created_at']
    list_filter = ['layout_style', 'organization']
    search_fields = ['school__name']
    readonly_fields = ['created_at', 'updated_at']


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
