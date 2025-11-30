"""ViewSets for CMS App"""

from rest_framework import viewsets, filters
from .models import NavigationMenu, Page, Section, Gallery, GalleryImage, Document
from .serializers import (
    NavigationMenuSerializer, PageSerializer, SectionSerializer,
    GallerySerializer, GalleryImageSerializer, DocumentSerializer
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

        # Filter by school
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

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

    def get_queryset(self):
        """Show only published pages for non-staff users"""
        queryset = super().get_queryset()

        # Manual filtering
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

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

    def get_queryset(self):
        """Show only visible sections for non-staff users"""
        queryset = super().get_queryset()

        # Manual filtering
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        page_id = self.request.query_params.get('page', None)
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

        # Manual filtering
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

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

        # Manual filtering
        school_id = self.request.query_params.get('school', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        file_type = self.request.query_params.get('file_type', None)
        if file_type:
            queryset = queryset.filter(file_type=file_type)

        is_public = self.request.query_params.get('is_public', None)
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')

        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)

        return queryset
