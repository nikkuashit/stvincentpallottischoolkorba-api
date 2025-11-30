"""URL Configuration for CMS App"""

from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import (
    NavigationMenuViewSet, PageViewSet, SectionViewSet,
    GalleryViewSet, GalleryImageViewSet, DocumentViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'navigation-menus', NavigationMenuViewSet, basename='navigationmenu')
router.register(r'pages', PageViewSet, basename='page')
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'galleries', GalleryViewSet, basename='gallery')
router.register(r'gallery-images', GalleryImageViewSet, basename='galleryimage')
router.register(r'documents', DocumentViewSet, basename='document')

# Custom URL pattern for pages to handle slugs with slashes
# Note: This pattern should NOT match UUIDs (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
# We exclude UUIDs by using a negative lookahead
page_detail_urlpatterns = [
    re_path(
        r'^pages/(?![\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}/$)(?P<slug>[\w\-\/]+)/$',
        PageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='page-detail-slug'
    ),
]

# Router URLs first (handles UUIDs), then custom slug patterns
urlpatterns = [
    path('', include(router.urls)),
] + page_detail_urlpatterns
