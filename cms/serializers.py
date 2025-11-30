"""Serializers for CMS App"""

from rest_framework import serializers
from .models import NavigationMenu, Page, Section, Gallery, GalleryImage, Document


class NavigationMenuSerializer(serializers.ModelSerializer):
    """Serializer for NavigationMenu model"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = NavigationMenu
        fields = [
            'id', 'organization', 'school', 'parent', 'title', 'slug', 'href',
            'icon', 'description', 'menu_type', 'is_external', 'external_url',
            'open_in_new_tab', 'show_in_navigation', 'show_in_footer',
            'show_in_landing_page', 'display_order', 'is_active',
            'created_at', 'updated_at', 'children'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_children(self, obj):
        """Get child menu items"""
        children = obj.children.filter(is_active=True)
        return NavigationMenuSerializer(children, many=True, context=self.context).data


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for Section model"""

    class Meta:
        model = Section
        fields = [
            'id', 'organization', 'school', 'page', 'title', 'slug',
            'section_type', 'content', 'display_order', 'is_visible',
            'background_color', 'background_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PageSerializer(serializers.ModelSerializer):
    """Serializer for Page model"""
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = [
            'id', 'organization', 'school', 'title', 'slug', 'description',
            'hero_image', 'meta_title', 'meta_description', 'meta_keywords',
            'is_published', 'published_at', 'created_at', 'updated_at', 'sections'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GalleryImageSerializer(serializers.ModelSerializer):
    """Serializer for GalleryImage model"""

    class Meta:
        model = GalleryImage
        fields = [
            'id', 'organization', 'gallery', 'title', 'description', 'image',
            'display_order', 'uploaded_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GallerySerializer(serializers.ModelSerializer):
    """Serializer for Gallery model"""
    images = GalleryImageSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = Gallery
        fields = [
            'id', 'organization', 'school', 'title', 'slug', 'description',
            'cover_image', 'event', 'created_by', 'is_published',
            'published_date', 'created_at', 'updated_at', 'images', 'image_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_count(self, obj):
        """Get total number of images in gallery"""
        return obj.images.count()


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'organization', 'school', 'title', 'description', 'file',
            'file_size', 'file_size_mb', 'file_type', 'category', 'uploaded_by',
            'is_public', 'download_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'download_count', 'file_size']

    def get_file_size_mb(self, obj):
        """Get file size in MB"""
        return round(obj.file_size / (1024 * 1024), 2)
