"""ViewSets for CMS App - Simplified without multi-tenancy"""

from django.db import models
from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import NavigationMenu, Page, Section, Gallery, GalleryImage, Document, Slider, Marquee
from .serializers import (
    NavigationMenuSerializer, PageSerializer, SectionSerializer,
    GallerySerializer, GalleryImageSerializer, DocumentSerializer,
    LandingPageSectionSerializer, SliderSerializer, MarqueeSerializer
)
from .permissions import IsAdminOrStaffOrReadOnly


class NavigationMenuViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NavigationMenu
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = NavigationMenu.objects.all()
    serializer_class = NavigationMenuSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug', 'description']
    ordering_fields = ['display_order', 'title', 'created_at']
    ordering = ['display_order', 'title']

    def get_queryset(self):
        """Filter menus based on query parameters"""
        queryset = super().get_queryset()

        # Filter by parent
        parent_id = self.request.query_params.get('parent', None)
        if parent_id == 'null' or parent_id == 'None':
            queryset = queryset.filter(parent__isnull=True)
        elif parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        # Filter by menu_type
        menu_type = self.request.query_params.get('menu_type', None)
        if menu_type:
            queryset = queryset.filter(menu_type=menu_type)

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by show_in_navigation
        show_in_navigation = self.request.query_params.get('show_in_navigation', None)
        if show_in_navigation is not None:
            queryset = queryset.filter(show_in_navigation=show_in_navigation.lower() == 'true')

        # Filter by show_in_footer
        show_in_footer = self.request.query_params.get('show_in_footer', None)
        if show_in_footer is not None:
            queryset = queryset.filter(show_in_footer=show_in_footer.lower() == 'true')

        # Show only active menus for non-staff users
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        return queryset


class PageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Page
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug', 'description', 'meta_title', 'meta_description']
    ordering_fields = ['title', 'published_at', 'created_at']
    ordering = ['title']
    lookup_field = 'slug'

    def get_object(self):
        """
        Override to support lookup by both UUID (id) and slug.
        Tries UUID first, falls back to slug if not a valid UUID.
        """
        import uuid as uuid_module
        lookup_value = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)

        # Try to parse as UUID first
        try:
            uuid_module.UUID(str(lookup_value))
            # It's a valid UUID, look up by id
            self.kwargs['pk'] = lookup_value
            self.lookup_field = 'pk'
        except (ValueError, TypeError):
            # Not a UUID, use slug lookup (default)
            pass

        return super().get_object()

    def get_queryset(self):
        """Show only published pages for non-staff users"""
        queryset = super().get_queryset()

        slug = self.request.query_params.get('slug', None)
        if slug:
            queryset = queryset.filter(slug=slug)

        is_published = self.request.query_params.get('is_published', None)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)

        return queryset


class SectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Section
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug']
    ordering_fields = ['display_order', 'title', 'created_at']
    ordering = ['display_order', 'title']

    def create(self, request, *args, **kwargs):
        """
        Override create to use update_or_create based on unique constraint fields.
        This prevents IntegrityError when a section with the same page/slug exists.
        """
        import re

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

        # Sanitize slug
        if 'slug' in data and data['slug']:
            sanitized_slug = re.sub(r'[^a-zA-Z0-9_-]', '-', data['slug'])
            sanitized_slug = re.sub(r'-+', '-', sanitized_slug).strip('-')
            data['slug'] = sanitized_slug

        # Check for existing section with same unique constraint
        page_id = data.get('page')
        slug = data.get('slug')

        if slug:
            existing = Section.objects.filter(
                page_id=page_id,
                slug=slug
            ).first()

            if existing:
                # Update existing section instead of creating
                serializer = self.get_serializer(existing, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

        # No existing section, proceed with normal create
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        """Show only visible sections for non-staff users"""
        queryset = super().get_queryset()

        # Use 'page_id' instead of 'page' to avoid conflict with DRF pagination
        page_id = self.request.query_params.get('page_id', None)
        if page_id:
            queryset = queryset.filter(page_id=page_id)

        section_type = self.request.query_params.get('section_type', None)
        if section_type:
            queryset = queryset.filter(section_type=section_type)

        is_visible = self.request.query_params.get('is_visible', None)
        if is_visible is not None:
            queryset = queryset.filter(is_visible=is_visible.lower() == 'true')

        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_visible=True)

        return queryset


class GalleryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Gallery
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Gallery.objects.all()
    serializer_class = GallerySerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug', 'description']
    ordering_fields = ['published_date', 'created_at', 'title']
    ordering = ['-published_date']
    lookup_field = 'slug'

    def get_queryset(self):
        """Show only published galleries for non-staff users"""
        queryset = super().get_queryset()

        event_id = self.request.query_params.get('event', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        is_published = self.request.query_params.get('is_published', None)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)

        return queryset


class GalleryImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for GalleryImage
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'created_at']
    ordering = ['display_order', 'created_at']

    def get_queryset(self):
        """Filter images by gallery"""
        queryset = super().get_queryset()

        gallery_id = self.request.query_params.get('gallery', None)
        if gallery_id:
            queryset = queryset.filter(gallery_id=gallery_id)

        return queryset


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document
    GET: Public access (only public documents for non-staff)
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'download_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """Show only public documents for non-staff users"""
        queryset = super().get_queryset()

        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        file_type = self.request.query_params.get('file_type', None)
        if file_type:
            queryset = queryset.filter(file_type=file_type)

        is_public = self.request.query_params.get('is_public', None)
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')

        # Filter by page slug
        page_slug = self.request.query_params.get('page_slug', None)
        if page_slug:
            queryset = queryset.filter(page__slug=page_slug)

        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)

        return queryset


class SliderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Slider
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Slider.objects.all()
    serializer_class = SliderSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'subtitle', 'description']
    ordering_fields = ['display_order', 'created_at']
    ordering = ['display_order', 'created_at']

    def get_queryset(self):
        """Filter sliders based on query parameters"""
        queryset = super().get_queryset()

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Show only active sliders for non-staff users
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        return queryset


class MarqueeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Marquee
    GET: Public access
    POST/PUT/PATCH/DELETE: Admin/Staff only
    """
    queryset = Marquee.objects.all()
    serializer_class = MarqueeSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text']
    ordering_fields = ['display_order', 'created_at']
    ordering = ['display_order', '-created_at']

    def get_queryset(self):
        """Filter marquees based on query parameters"""
        from django.utils import timezone

        queryset = super().get_queryset()

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Show only active and scheduled marquees for non-staff users
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            now = timezone.now()
            queryset = queryset.filter(is_active=True)
            queryset = queryset.filter(
                models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
            ).filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
            )

        return queryset


class LandingPageView(APIView):
    """
    API endpoint to get all sections marked for landing page display.
    Returns sections ordered by landing_page_order.

    GET /api/cms/landing-page/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Get all sections marked for landing page, ordered by landing_page_order
        sections = Section.objects.filter(
            show_in_landing_page=True,
            is_visible=True
        ).select_related('page').order_by('landing_page_order', 'display_order')

        serializer = LandingPageSectionSerializer(sections, many=True, context={'request': request})

        return Response({
            'sections': serializer.data
        })
