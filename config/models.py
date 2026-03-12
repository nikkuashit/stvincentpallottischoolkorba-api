"""
Config App - School Configuration & Branding

Simplified without multi-tenancy.
This module handles:
- Theme configuration and colors
- Social media links
"""

import uuid
from django.db import models


class ThemeConfig(models.Model):
    """Theme and branding configuration (singleton)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Theme Configuration"
        verbose_name_plural = "Theme Configuration"

    def __str__(self):
        return "Theme Configuration"


class SocialLinks(models.Model):
    """Social media links (singleton)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    # Additional links
    additional_links = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Social Links"
        verbose_name_plural = "Social Links"

    def __str__(self):
        return "Social Links"
