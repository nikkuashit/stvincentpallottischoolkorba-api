"""Serializers for CMS App - Simplified without multi-tenancy"""

from rest_framework import serializers
from .models import NavigationMenu, Page, Section, Gallery, GalleryImage, Document, Slider, Marquee


class NavigationMenuSerializer(serializers.ModelSerializer):
    """Serializer for NavigationMenu model"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = NavigationMenu
        fields = [
            'id', 'parent', 'title', 'slug', 'href',
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
    slug = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = Section
        fields = [
            'id', 'page', 'title', 'slug',
            'section_type', 'content', 'display_order', 'is_visible',
            'background_color', 'background_image',
            'show_in_landing_page', 'landing_page_order', 'landing_page_width',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_slug(self, value):
        """Sanitize slug to ensure it only contains valid characters"""
        import re
        if value:
            sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', value)
            sanitized = re.sub(r'-+', '-', sanitized)
            sanitized = sanitized.strip('-')
            return sanitized
        return value


class LandingPageSectionSerializer(serializers.ModelSerializer):
    """Serializer for landing page sections with page info"""
    page_title = serializers.CharField(source='page.title', read_only=True, allow_null=True)
    page_slug = serializers.CharField(source='page.slug', read_only=True, allow_null=True)
    page_description = serializers.CharField(source='page.description', read_only=True, allow_null=True)
    page_hero_image = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            'id', 'title', 'slug', 'section_type', 'content',
            'background_color', 'background_image',
            'landing_page_order', 'landing_page_width', 'page', 'page_title', 'page_slug', 'page_description',
            'page_hero_image', 'display_title', 'attachments'
        ]
        read_only_fields = ['id']

    def get_page_hero_image(self, obj):
        """Get the page's hero image URL if available"""
        if obj.page and obj.page.hero_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.page.hero_image.url)
            return obj.page.hero_image.url
        return None

    def get_display_title(self, obj):
        """Return a user-friendly display title for landing page sections."""
        type_title_map = {
            'events': 'Upcoming Events',
            'news': 'Latest News',
            'gallery': 'Photo Gallery',
            'principal': "Principal's Message",
            'courses': 'Our Courses',
            'contact': 'Contact Us',
        }

        if obj.section_type in type_title_map:
            return type_title_map[obj.section_type]

        return obj.title or (obj.page.title if obj.page else 'Section')

    def get_attachments(self, obj):
        """Get public attachments/documents from the linked page"""
        if not obj.page:
            return []

        documents = obj.page.documents.filter(is_public=True)
        request = self.context.get('request')

        attachments = []
        for doc in documents:
            file_url = doc.file.url if doc.file else None
            if file_url and request:
                file_url = request.build_absolute_uri(file_url)

            attachments.append({
                'id': str(doc.id),
                'title': doc.title,
                'description': doc.description,
                'file': file_url,
                'file_size': doc.file_size,
                'file_type': doc.file_type,
                'category': doc.category,
            })

        return attachments

    def get_content(self, obj):
        """Return section content, merging page description if section content is empty."""
        content = obj.content or {}

        if obj.page:
            is_empty = (
                not content or
                (isinstance(content, dict) and not any(v for v in content.values() if v))
            )

            if is_empty and obj.page.description:
                return {
                    'content': obj.page.description,
                    'description': obj.page.description
                }

        return content


class PageSerializer(serializers.ModelSerializer):
    """Serializer for Page model"""
    sections = SectionSerializer(many=True, read_only=True)
    slug = serializers.CharField(max_length=255)

    class Meta:
        model = Page
        fields = [
            'id', 'title', 'slug', 'description',
            'hero_image', 'meta_title', 'meta_description', 'meta_keywords',
            'is_published', 'published_at', 'created_at', 'updated_at', 'sections'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GalleryImageSerializer(serializers.ModelSerializer):
    """Serializer for GalleryImage model"""

    class Meta:
        model = GalleryImage
        fields = [
            'id', 'gallery', 'title', 'description', 'image',
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
            'id', 'title', 'slug', 'description',
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
    page_slug = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        allow_blank=True
    )

    class Meta:
        model = Document
        fields = [
            'id', 'page', 'page_slug', 'title', 'description', 'file',
            'file_size', 'file_size_mb', 'file_type', 'category', 'uploaded_by',
            'is_public', 'download_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'download_count']

    def get_file_size_mb(self, obj):
        """Get file size in MB"""
        return round(obj.file_size / (1024 * 1024), 2)

    def to_representation(self, instance):
        """Include page_slug in read responses"""
        data = super().to_representation(instance)
        data['page_slug'] = instance.page.slug if instance.page else None
        return data

    def validate(self, attrs):
        """Convert page_slug to page object"""
        page_slug = attrs.pop('page_slug', None)
        if page_slug:
            try:
                page = Page.objects.get(slug=page_slug)
                attrs['page'] = page
            except Page.DoesNotExist:
                raise serializers.ValidationError({'page_slug': f'Page with slug "{page_slug}" not found'})
        return attrs


class SliderSerializer(serializers.ModelSerializer):
    """Serializer for Slider model"""

    class Meta:
        model = Slider
        fields = [
            'id', 'title', 'subtitle', 'description',
            'image', 'cta_text', 'cta_link', 'display_order', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MarqueeSerializer(serializers.ModelSerializer):
    """Serializer for Marquee model"""
    is_new = serializers.SerializerMethodField()

    class Meta:
        model = Marquee
        fields = [
            'id', 'text', 'link', 'display_order',
            'is_active', 'start_date', 'end_date', 'created_at', 'updated_at', 'is_new'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_new(self, obj):
        """Return True if marquee was created within the last 10 days"""
        from django.utils import timezone
        from datetime import timedelta
        return obj.created_at >= timezone.now() - timedelta(days=10)
