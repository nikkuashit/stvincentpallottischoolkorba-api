"""
Config App - School Configuration & Branding

This module handles:
- Theme configuration and colors
- Social media links
"""

import uuid
from django.db import models


class ThemeConfig(models.Model):
    """Theme and branding configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='theme_configs'
    )
    school = models.OneToOneField(
        'tenants.School',
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['organization', 'school']),
        ]

    def __str__(self):
        return f"Theme - {self.school.name}"


class SocialLinks(models.Model):
    """Social media links"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='social_links'
    )
    school = models.OneToOneField(
        'tenants.School',
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Social Links"
        indexes = [
            models.Index(fields=['organization', 'school']),
        ]

    def __str__(self):
        return f"Social Links - {self.school.name}"
