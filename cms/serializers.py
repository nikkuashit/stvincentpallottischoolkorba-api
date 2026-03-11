"""Serializers for CMS App"""

from rest_framework import serializers
from .models import NavigationMenu, Page, Section, Gallery, GalleryImage, Document, Slider, Marquee


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
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def get_children(self, obj):
        """Get child menu items"""
        children = obj.children.filter(is_active=True)
        return NavigationMenuSerializer(children, many=True, context=self.context).data

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for Section model"""

    class Meta:
        model = Section
        fields = [
            'id', 'organization', 'school', 'page', 'title', 'slug',
            'section_type', 'content', 'display_order', 'is_visible',
            'background_color', 'background_image',
            'show_in_landing_page', 'landing_page_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)


class LandingPageSectionSerializer(serializers.ModelSerializer):
    """Serializer for landing page sections with page info"""
    page_title = serializers.CharField(source='page.title', read_only=True, allow_null=True)
    page_slug = serializers.CharField(source='page.slug', read_only=True, allow_null=True)

    class Meta:
        model = Section
        fields = [
            'id', 'title', 'slug', 'section_type', 'content',
            'background_color', 'background_image',
            'landing_page_order', 'page', 'page_title', 'page_slug'
        ]
        read_only_fields = ['id']


class PageSerializer(serializers.ModelSerializer):
    """Serializer for Page model"""
    sections = SectionSerializer(many=True, read_only=True)
    # Override slug to allow slashes for nested page paths
    slug = serializers.CharField(max_length=255)

    class Meta:
        model = Page
        fields = [
            'id', 'organization', 'school', 'title', 'slug', 'description',
            'hero_image', 'meta_title', 'meta_description', 'meta_keywords',
            'is_published', 'published_at', 'created_at', 'updated_at', 'sections'
        ]
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)


class GalleryImageSerializer(serializers.ModelSerializer):
    """Serializer for GalleryImage model"""

    class Meta:
        model = GalleryImage
        fields = [
            'id', 'organization', 'gallery', 'title', 'description', 'image',
            'display_order', 'uploaded_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Auto-assign default organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['organization'] = school.organization
        return super().create(validated_data)


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
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def get_image_count(self, obj):
        """Get total number of images in gallery"""
        return obj.images.count()

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)


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
            'id', 'organization', 'school', 'title', 'subtitle', 'description',
            'image', 'cta_text', 'cta_link', 'display_order', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)


class MarqueeSerializer(serializers.ModelSerializer):
    """Serializer for Marquee model"""
    is_new = serializers.SerializerMethodField()

    class Meta:
        model = Marquee
        fields = [
            'id', 'organization', 'school', 'text', 'link', 'display_order',
            'is_active', 'start_date', 'end_date', 'created_at', 'updated_at', 'is_new'
        ]
        read_only_fields = ['id', 'organization', 'school', 'created_at', 'updated_at']

    def get_is_new(self, obj):
        """Return True if marquee was created within the last 10 days"""
        from django.utils import timezone
        from datetime import timedelta
        return obj.created_at >= timezone.now() - timedelta(days=10)

    def create(self, validated_data):
        # Auto-assign default school and organization
        from tenants.models import School
        school = School.objects.first()
        if school:
            validated_data['school'] = school
            validated_data['organization'] = school.organization
        return super().create(validated_data)
