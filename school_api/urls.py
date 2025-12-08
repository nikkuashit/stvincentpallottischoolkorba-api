"""
URL configuration for school_api project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="School Management API",
        default_version='v1',
        description="""
        # School Management System API

        A comprehensive REST API for managing multi-school data including:
        - School configuration and settings
        - Navigation menu management
        - Content sections (About, News, Events, Gallery, etc.)
        - Media file uploads
        - User authentication with JWT tokens

        ## Authentication
        Use JWT Bearer token in the Authorization header:
        ```
        Authorization: Bearer <your_token_here>
        ```

        ## Get Started
        1. Register a new user at `/api/auth/registration/`
        2. Login to get your JWT tokens at `/api/auth/login/`
        3. Use the access token for authenticated requests
        """,
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="contact@schoolapi.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin panel
    path("admin/", admin.site.urls),

    # API Documentation - Swagger UI
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('swagger/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),

    # API Documentation - ReDoc
    path('redoc/',
         schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),

    # Authentication endpoints
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # Accounts API endpoints (User Management)
    path('api/accounts/', include('accounts.urls')),

    # CMS API endpoints
    path('api/cms/', include('cms.urls')),
]

# Serve media files (user uploads)
# Whitenoise handles static files, but media files need to be served separately
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# In development, also serve static files via Django
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "School Management Admin"
admin.site.site_title = "School Admin Portal"
admin.site.index_title = "Welcome to School Management System"
