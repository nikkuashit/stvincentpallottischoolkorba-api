# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-tenant School Management SaaS API built with Django REST Framework. Provides comprehensive CMS functionality, navigation management, authentication (JWT), and multi-school data isolation. Designed to support multiple schools under single organizations with role-based access control.

## Development Commands

### Core Development
```bash
# Activate virtual environment and run server
pipenv run python manage.py runserver
# Server runs at http://127.0.0.1:8000/

# Or enter shell and run commands
pipenv shell
python manage.py runserver
```

### Database Management
```bash
# Create migrations after model changes
pipenv run python manage.py makemigrations

# Apply migrations
pipenv run python manage.py migrate

# Create database backup (SQLite)
cp db.sqlite3 db.sqlite3.backup

# Reset database (careful - deletes all data!)
rm db.sqlite3
pipenv run python manage.py migrate
pipenv run python create_superuser.py
```

### User Management
```bash
# Create superuser (use script with defaults)
pipenv run python create_superuser.py
# Creates: username=admin, password=admin123

# Create superuser (interactive)
pipenv run python manage.py createsuperuser
```

### Django Shell
```bash
# Open Django shell for interactive queries
pipenv run python manage.py shell

# Example shell commands for testing:
from tenants.models import Organization, School
from cms.models import NavigationMenu
orgs = Organization.objects.all()
```

### Testing & Quality
```bash
# Run tests (when test suite is created)
pipenv run python manage.py test

# Check for issues
pipenv run python manage.py check

# Validate models
pipenv run python manage.py validate
```

### Data Management
```bash
# Load fixtures (seed data)
pipenv run python manage.py loaddata <fixture_file>

# Dump data to fixtures
pipenv run python manage.py dumpdata <app_name> > <fixture_file>.json
```

## Architecture

### Multi-Tenant SaaS Structure

**Three-tier tenant hierarchy:**

1. **Organization** (Root tenant entity)
   - Represents school system/group
   - Has subscription plan
   - Isolated data boundary
   - Example: "St. Vincent Pallotti School System"

2. **School** (1:1 with Organization currently)
   - Individual school entity
   - Has configuration, branding, navigation
   - Example: "St. Vincent Pallotti School Korba"

3. **Users** (Scoped to Organization/School)
   - Staff, teachers, parents, students
   - Role-based permissions (RBAC)

### App Structure (Django Apps)

```
stvincentpallottischoolkorba-api/
├── school_api/          # Main project settings & URLs
├── tenants/             # Organization, School, Subscription models
├── accounts/            # UserProfile, Role, RBAC
├── cms/                 # NavigationMenu, Page, Section, Gallery
├── config/              # Theme, NavigationConfig (future)
├── academics/           # Student, Class, Course (future)
└── communications/      # News, Events, Announcements (future)
```

**Key Design Principle:** Each app is self-contained with models, views, serializers, permissions, and URLs.

### Database Models (Key Entities)

#### Tenants App
- **Organization**: Root tenant with subscription management
- **School**: School entity (1:1 with Organization)
- **SubscriptionPlan**: SaaS subscription tiers

#### Accounts App
- **UserProfile**: Extends Django User, links to Organization/School
- **Role**: RBAC roles (see RBAC_DESIGN.md for complete hierarchy)

#### CMS App
- **NavigationMenu**: Hierarchical menus (parent-child relationships)
- **Page**: Static content pages
- **Section**: Dynamic page sections
- **Gallery**: Image galleries
- **GalleryImage**: Individual gallery images
- **Document**: Downloadable documents

**All models include:**
- UUID primary keys
- Foreign keys to Organization & School (multi-tenancy)
- Timestamp fields (created_at, updated_at)
- is_active flags

### URL Structure & API Endpoints

**Base URL:** `http://127.0.0.1:8000/`

#### Documentation
```
GET  /swagger/          - Swagger UI (interactive API docs)
GET  /redoc/            - ReDoc alternative documentation
GET  /swagger.json      - OpenAPI schema (JSON)
GET  /swagger.yaml      - OpenAPI schema (YAML)
```

#### Authentication
```
POST /api/auth/registration/     - Register new user
POST /api/auth/login/            - Login (returns JWT tokens)
POST /api/auth/logout/           - Logout
POST /api/auth/token/refresh/    - Refresh access token
POST /api/auth/token/verify/     - Verify token validity
```

#### CMS Endpoints
```
# Navigation Menus
GET    /api/cms/navigation-menus/          - List all menus
POST   /api/cms/navigation-menus/          - Create menu (admin)
GET    /api/cms/navigation-menus/{id}/     - Get specific menu
PUT    /api/cms/navigation-menus/{id}/     - Update menu (admin)
PATCH  /api/cms/navigation-menus/{id}/     - Partial update (admin)
DELETE /api/cms/navigation-menus/{id}/     - Delete menu (admin)

# Pages
GET/POST    /api/cms/pages/                - List/create pages
GET/PUT/DELETE /api/cms/pages/{id}/        - Get/update/delete page

# Sections
GET/POST    /api/cms/sections/             - List/create sections
GET/PUT/DELETE /api/cms/sections/{id}/     - Get/update/delete section

# Galleries
GET/POST    /api/cms/galleries/            - List/create galleries
GET/PUT/DELETE /api/cms/galleries/{id}/    - Get/update/delete gallery

# Gallery Images
GET/POST    /api/cms/gallery-images/       - List/create images
GET/PUT/DELETE /api/cms/gallery-images/{id}/ - Get/update/delete image

# Documents
GET/POST    /api/cms/documents/            - List/create documents
GET/PUT/DELETE /api/cms/documents/{id}/    - Get/update/delete document
```

#### Admin Panel
```
GET  /admin/             - Django admin interface
```

### Query Parameters (Navigation Menus)

Navigation menu endpoints support extensive filtering:

```
?school=<uuid>                  - Filter by school ID
?parent=null                    - Top-level menus only
?parent=<uuid>                  - Children of specific parent
?menu_type=page                 - Filter by type (page/section/dropdown/external)
?is_active=true                 - Show only active/inactive
?show_in_navigation=true        - Navigation visibility
?show_in_footer=true            - Footer visibility
?search=<term>                  - Search in title, slug, description
?ordering=display_order         - Sort by field (prefix with '-' for desc)
?page=1                         - Pagination (20 items per page)
```

**Example:**
```bash
GET /api/cms/navigation-menus/?school=abc-123&parent=null&show_in_navigation=true&ordering=display_order
```

### Authentication & Permissions

#### JWT Token Flow
1. **Register/Login**: Get access token (1hr) & refresh token (7 days)
2. **API Requests**: Include `Authorization: Bearer <access_token>` header
3. **Token Refresh**: Use refresh token to get new access token when expired
4. **Logout**: Blacklist tokens (ROTATE_REFRESH_TOKENS enabled)

#### Permission Classes

**Custom Permission:** `IsAdminOrStaffOrReadOnly` (cms/permissions.py)
- **GET requests**: Public access (read-only)
- **POST/PUT/PATCH/DELETE**: Requires `is_staff=True` or `is_superuser=True`

**Applied to all CMS ViewSets:**
- NavigationMenuViewSet
- PageViewSet
- SectionViewSet
- GalleryViewSet
- DocumentViewSet

#### Role-Based Access Control (RBAC)

See `RBAC_DESIGN.md` for complete role hierarchy. Key roles:

- **super_admin**: Platform owner, global access
- **platform_staff**: Support staff, read-mostly
- **org_admin**: Organization owner, manages schools
- **school_admin**: Principal, manages one school
- **school_staff**: Teachers, staff at school
- **parent**: Limited access to student info
- **student**: Minimal access

### REST Framework Configuration

**Key Settings** (school_api/settings.py):

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}
```

**JWT Token Settings:**
- Access token: 1 hour lifetime
- Refresh token: 7 days lifetime
- Automatic rotation enabled
- Blacklist after rotation (security)

### CORS Configuration

**Development:** All origins allowed (`CORS_ALLOW_ALL_ORIGINS = True`)

**Production:** Configure specific origins:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Frontend dev
    "https://yourdomain.com",  # Production frontend
]
```

### ViewSet Patterns

**Standard ViewSet Structure:**

```python
class NavigationMenuViewSet(viewsets.ModelViewSet):
    queryset = NavigationMenu.objects.all()
    serializer_class = NavigationMenuSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'slug', 'description']
    ordering_fields = ['display_order', 'title']

    def get_queryset(self):
        # Custom filtering logic
        # Filter by school, parent, type, etc.
        pass
```

**All ViewSets use:**
- ModelViewSet for full CRUD
- Custom permission classes
- Search and ordering filters
- Query parameter filtering in `get_queryset()`

### Serializer Patterns

**Key Features:**
- Nested relationships (e.g., NavigationMenu includes children)
- Read-only computed fields (e.g., child_count, has_children)
- Foreign key representation (UUID strings)
- Validation in serializer layer

**Example:**
```python
class NavigationMenuSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    child_count = serializers.SerializerMethodField()

    def get_children(self, obj):
        # Recursively serialize children
        children = obj.children.filter(is_active=True)
        return NavigationMenuSerializer(children, many=True).data
```

## Key Files & Their Purpose

### Project Configuration
- `school_api/settings.py`: Django settings, DRF config, JWT, CORS
- `school_api/urls.py`: Main URL routing, Swagger setup
- `.env`: Environment variables (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- `Pipfile`/`Pipfile.lock`: Python dependencies (pipenv)

### App Structure (Each App)
- `models.py`: Django ORM models
- `serializers.py`: DRF serializers for JSON conversion
- `views.py`: ViewSets and API endpoints
- `permissions.py`: Custom permission classes
- `urls.py`: URL routing for app endpoints
- `admin.py`: Django admin configuration
- `migrations/`: Database migration files

### Scripts
- `manage.py`: Django management script (run all commands through this)
- `create_superuser.py`: Automated superuser creation script

### Documentation
- `README.md`: Setup and basic usage
- `ER_DIAGRAM.md`: Complete database schema and relationships
- `RBAC_DESIGN.md`: Role-based access control system design
- `FRONTEND_BACKEND_ANALYSIS.md`: API integration guide
- `STUDENT_TRANSFER_WORKFLOW.md`: Student transfer process
- `PARENT_ONBOARDING_SYSTEM.md`: Parent registration workflow

## Important Patterns & Conventions

### Model Conventions
1. **Always use UUID primary keys**: `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
2. **Multi-tenancy fields**: Include `organization` and `school` foreign keys on all models
3. **Timestamps**: Include `created_at` and `updated_at` on all models
4. **Soft deletes**: Use `is_active` boolean instead of deleting records
5. **Ordering**: Define default ordering in `Meta` class

### API Response Format

**List Response** (paginated):
```json
{
  "count": 50,
  "next": "http://api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

**Detail Response**:
```json
{
  "id": "uuid-here",
  "field1": "value",
  "nested_relation": {...},
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Response**:
```json
{
  "detail": "Error message",
  "field_name": ["Field-specific error"]
}
```

### Testing API Endpoints

#### Using Swagger UI (Recommended)
1. Visit http://127.0.0.1:8000/swagger/
2. Click "Authorize" button
3. Login to get JWT token
4. Test endpoints interactively

#### Using cURL
```bash
# Register user
curl -X POST http://127.0.0.1:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password1":"testpass123","password2":"testpass123"}'

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"testpass123"}'

# Use token in requests
curl -X GET http://127.0.0.1:8000/api/cms/navigation-menus/ \
  -H "Authorization: Bearer <your_token>"
```

#### Using Django Shell
```bash
pipenv run python manage.py shell

# Example: Create navigation menu programmatically
from cms.models import NavigationMenu
from tenants.models import Organization, School

org = Organization.objects.first()
school = School.objects.first()

menu = NavigationMenu.objects.create(
    organization=org,
    school=school,
    title="About Us",
    slug="about-us",
    href="/about-us",
    menu_type="page",
    display_order=1
)
```

## Common Workflows

### Adding New Model

1. **Define model** in `app/models.py`:
```python
class NewModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('tenants.Organization', on_delete=models.CASCADE)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    # ... fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

2. **Create serializer** in `app/serializers.py`
3. **Create viewset** in `app/views.py`
4. **Register in router** in `app/urls.py`
5. **Register in admin** in `app/admin.py`
6. **Create migrations**: `pipenv run python manage.py makemigrations`
7. **Apply migrations**: `pipenv run python manage.py migrate`

### Modifying Existing Model

1. Edit model in `models.py`
2. **Create migrations**: `pipenv run python manage.py makemigrations`
3. **Review migration file** in `migrations/` directory
4. **Apply migrations**: `pipenv run python manage.py migrate`
5. Update serializer if new fields need API exposure
6. Update admin.py if new fields need admin interface

### Creating Test Data

Use Django shell for quick test data creation:
```bash
pipenv run python manage.py shell

from tenants.models import Organization, School
from cms.models import NavigationMenu

# Create organization
org = Organization.objects.create(
    name="Test School System",
    slug="test-school",
    email="admin@test.com"
)

# Create school
school = School.objects.create(
    organization=org,
    name="Test School",
    short_name="TS",
    email="school@test.com"
)

# Create menus
menu = NavigationMenu.objects.create(...)
```

## Security Considerations

### Production Checklist
- [ ] Change `SECRET_KEY` in .env
- [ ] Set `DEBUG=False` in .env
- [ ] Configure specific `ALLOWED_HOSTS`
- [ ] Set specific `CORS_ALLOWED_ORIGINS` (disable CORS_ALLOW_ALL_ORIGINS)
- [ ] Enable `JWT_AUTH_HTTPONLY=True` for cookie security
- [ ] Use HTTPS (configure SSL/TLS)
- [ ] Configure proper database (PostgreSQL/MySQL, not SQLite)
- [ ] Set up static file serving (WhiteNoise or CDN)
- [ ] Configure media file storage (S3 or equivalent)
- [ ] Enable rate limiting for API endpoints
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for database

### Common Security Patterns
1. **Never expose sensitive data**: Filter out passwords, secrets in serializers
2. **Validate user permissions**: Check organization/school ownership in viewsets
3. **Audit trails**: Log all admin actions (use AuditLog model)
4. **Input validation**: Use DRF serializer validation
5. **SQL injection prevention**: Use Django ORM (never raw SQL without params)

## Common Pitfalls

1. **Forgetting migrations**: Always run `makemigrations` after model changes
2. **Missing multi-tenancy fields**: All models must have organization/school foreign keys
3. **Permission issues**: Ensure viewsets have proper permission_classes
4. **CORS errors**: Frontend can't connect if CORS not configured
5. **Token expiration**: Access tokens expire in 1hr, must refresh
6. **Circular imports**: Avoid importing models between apps (use string references)
7. **Unique constraints**: Remember unique_together constraints (org+school+slug)
8. **Query performance**: Use select_related/prefetch_related for nested queries

## Dependencies

### Core Framework
- **django**: Web framework (5.2.7)
- **djangorestframework**: REST API framework
- **djangorestframework-simplejwt**: JWT authentication

### Authentication & Auth
- **dj-rest-auth**: Authentication endpoints
- **django-allauth**: User registration and social auth

### API Documentation
- **drf-yasg**: Swagger/OpenAPI documentation generation

### Utilities
- **django-cors-headers**: CORS handling for frontend integration
- **python-decouple**: Environment variable management
- **pillow**: Image processing for uploads
- **requests**: HTTP library for external API calls

### Development
- **SQLite**: Development database (switch to PostgreSQL in production)
- **Pipenv**: Dependency and virtual environment management

## Future Enhancements (Roadmap)

Refer to documentation files for detailed designs:
- Student management system (academics app)
- Parent onboarding workflow (PARENT_ONBOARDING_SYSTEM.md)
- Student transfer process (STUDENT_TRANSFER_WORKFLOW.md)
- Attendance tracking
- Grade management
- Fee management and billing
- Communication system (notifications, messages)
- Reports and analytics
