# CMS System Guide - WordPress-like Content Management

## Overview

The St. Vincent Pallotti School website has been successfully transformed from a static content system to a dynamic, WordPress-like CMS. All page content is now stored in the database and can be managed dynamically through API endpoints.

## What Was Accomplished

### 1. Database Schema Updates
- Added `slug` and `config` fields to the School model in `tenants/models.py`
- These fields enable unique identification and flexible configuration for each school

### 2. Content Migration
- Created a management command to migrate all 52 static pages from `pageContent.tsx` to the database
- All pages are now stored in the `cms_page` table with proper organization and school associations

### 3. API Endpoints
- Full CRUD API endpoints available at `/api/cms/pages/`
- Pages can be retrieved by slug: `/api/cms/pages/{slug}/`
- Filtering capabilities: by school, published status, search text
- Public read access, admin/staff write access

## Architecture

### Models

```
Organization (Root Tenant)
    ↓
School (1:1 with Organization)
    ↓
├── NavigationMenu (Hierarchical menus)
├── Page (Static page content)
│   └── Section (Dynamic content sections)
├── Gallery (Photo galleries)
└── Document (File uploads)
```

### Key Models

**Page Model** (`cms/models.py`):
- `title` - Page title
- `slug` - URL-friendly identifier (unique per school)
- `description` - Page content/description
- `hero_image` - Optional hero image
- `meta_title`, `meta_description`, `meta_keywords` - SEO fields
- `is_published` - Visibility control
- `published_at` - Publication timestamp

**NavigationMenu Model** (`cms/models.py`):
- Hierarchical structure (parent-child relationships)
- Multiple menu types: page, section, dropdown, external
- Display control: navigation, footer, landing page
- Ordering and visibility options

## API Usage

### Get All Pages

```bash
GET /api/cms/pages/
```

**Response**:
```json
[
    {
        "id": "uuid",
        "title": "About Us",
        "slug": "about",
        "description": "...",
        "hero_image": null,
        "is_published": true,
        "sections": []
    }
]
```

### Get Page by Slug

```bash
GET /api/cms/pages/about/
```

### Filter Pages

```bash
# By school
GET /api/cms/pages/?school={school_id}

# Search pages
GET /api/cms/pages/?search=library

# Only published
GET /api/cms/pages/?is_published=true
```

### Create New Page (Admin only)

```bash
POST /api/cms/pages/
Content-Type: application/json
Authorization: Bearer {token}

{
    "organization": "uuid",
    "school": "uuid",
    "title": "New Page",
    "slug": "new-page",
    "description": "Page content...",
    "is_published": true
}
```

### Update Page (Admin only)

```bash
PATCH /api/cms/pages/{slug}/
Content-Type: application/json
Authorization: Bearer {token}

{
    "title": "Updated Title",
    "description": "Updated content..."
}
```

### Delete Page (Admin only)

```bash
DELETE /api/cms/pages/{slug}/
Authorization: Bearer {token}
```

## Managing Content

### Adding New Pages

**Option 1: Via API** (Recommended for dynamic additions)
```bash
curl -X POST http://localhost:8000/api/cms/pages/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "organization": "c549b38e-cee9-4036-a2d4-58bc43a2494c",
    "school": "aded93c5-4cb0-4be2-bdff-0a0b02764a0e",
    "title": "New Page Title",
    "slug": "new-page-slug",
    "description": "Page content here...",
    "meta_title": "New Page Title",
    "meta_description": "SEO description...",
    "is_published": true
  }'
```

**Option 2: Via Django Admin**
1. Navigate to `http://localhost:8000/admin/`
2. Go to CMS → Pages
3. Click "Add Page"
4. Fill in the form and save

**Option 3: Via Management Command** (For bulk additions)
Update `/cms/management/commands/migrate_static_pages.py` with new page data and run:
```bash
python manage.py migrate_static_pages --overwrite
```

### Managing Navigation Menus

**Get Navigation Menus**:
```bash
GET /api/cms/navigation-menus/?school={school_id}&show_in_navigation=true&is_active=true
```

**Create Menu Item**:
```bash
POST /api/cms/navigation-menus/
{
    "organization": "uuid",
    "school": "uuid",
    "title": "New Menu",
    "slug": "new-menu",
    "href": "/new-page",
    "menu_type": "page",
    "show_in_navigation": true,
    "display_order": 10,
    "is_active": true
}
```

**Create Submenu** (with parent):
```bash
POST /api/cms/navigation-menus/
{
    "parent": "parent_menu_uuid",
    "title": "Submenu Item",
    ...
}
```

### Adding Dynamic Sections to Pages

Sections allow you to add structured content blocks to pages:

```bash
POST /api/cms/sections/
{
    "organization": "uuid",
    "school": "uuid",
    "page": "page_uuid",
    "title": "Section Title",
    "slug": "section-slug",
    "section_type": "features",  // hero, about, features, gallery, etc.
    "content": {
        "heading": "Features",
        "items": [
            {"title": "Feature 1", "description": "..."},
            {"title": "Feature 2", "description": "..."}
        ]
    },
    "display_order": 1,
    "is_visible": true
}
```

## Management Commands

### Migrate Static Pages

Migrate page content from frontend to database:

```bash
# Default (stvincentpallottikorba school)
python manage.py migrate_static_pages

# For specific school
python manage.py migrate_static_pages --school-slug another-school

# Overwrite existing pages
python manage.py migrate_static_pages --overwrite
```

## Frontend Integration

### React/TypeScript Integration

**Current Status**: The frontend still uses static `pageContent.tsx`.

**Next Steps** for complete CMS integration:

1. **Create API Service** (`src/services/api/pageService.ts`):
```typescript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/cms';

export interface Page {
  id: string;
  title: string;
  slug: string;
  description: string;
  hero_image: string | null;
  is_published: boolean;
  sections: Section[];
}

export const pageService = {
  async getPageBySlug(slug: string): Promise<Page> {
    const response = await axios.get(`${API_BASE}/pages/${slug}/`);
    return response.data;
  },

  async getAllPages(): Promise<Page[]> {
    const response = await axios.get(`${API_BASE}/pages/`);
    return response.data;
  }
};
```

2. **Update Route Components** (Example: `about.$subsection.tsx`):
```typescript
import { useQuery } from '@tanstack/react-query';
import { pageService } from '../services/api/pageService';

function AboutPage() {
  const { subsection } = Route.useParams();
  const fullPath = `about/${subsection}`;

  // Fetch from API instead of static data
  const { data: pageData, loading, error } = useQuery({
    queryKey: ['page', fullPath],
    queryFn: () => pageService.getPageBySlug(fullPath)
  });

  if (loading) return <LoadingSpinner />;
  if (error || !pageData) return <ErrorMessage />;

  return (
    <GenericPageTemplate
      content={{
        title: pageData.title,
        heroImage: pageData.hero_image || defaultImage,
        description: pageData.description
      }}
      schoolData={schoolData}
      currentSlug={fullPath}
    />
  );
}
```

3. **Environment Configuration** (`.env`):
```
VITE_API_BASE_URL=http://localhost:8000/api
```

## Security & Permissions

### Permission Classes

The CMS uses `IsAdminOrStaffOrReadOnly` permission class:
- **Public Users**: Read-only access to published content
- **Authenticated Staff**: Full CRUD operations
- **Admin**: Full access including unpublished content

### Authentication

Use JWT tokens for authenticated requests:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/cms/pages/
```

## Database Schema

### Page Table (`cms_page`)
- `id` (UUID)
- `organization_id` (FK)
- `school_id` (FK)
- `title` (VARCHAR 255)
- `slug` (SlugField) - Indexed, unique per school
- `description` (TEXT)
- `hero_image` (ImageField)
- `meta_title`, `meta_description`, `meta_keywords`
- `is_published` (BOOLEAN)
- `published_at` (DATETIME)
- `created_at`, `updated_at` (DATETIME)

**Indexes**:
- `organization_id, school_id, is_published`
- `slug`

## Scalability Features

### Multi-Tenant Support
- Every piece of content is isolated by organization and school
- Supports multiple schools in a single database
- Tenant filtering at the query level

### Caching Strategy
- Implement Redis caching for frequently accessed pages
- Cache key format: `page:{school_id}:{slug}`
- Cache invalidation on page updates

### CDN Integration
- Hero images and media can be served from CDN
- Configure `MEDIA_URL` to point to CDN in production

## Development Workflow

### Adding a New Content Type

1. **Create Model** (in appropriate app, e.g., `cms/models.py`)
2. **Create Serializer** (`cms/serializers.py`)
3. **Create ViewSet** (`cms/views.py`)
4. **Register URL** (`cms/urls.py`)
5. **Run Migrations**
6. **Test API endpoints**
7. **Update Frontend to consume**

### Example: Adding "Testimonials"

```python
# 1. Model (cms/models.py)
class Testimonial(models.Model):
    organization = models.ForeignKey('tenants.Organization', on_delete=models.CASCADE)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
    author_name = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_published = models.BooleanField(default=False)

# 2. Serializer (cms/serializers.py)
class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'

# 3. ViewSet (cms/views.py)
class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]

# 4. URL (cms/urls.py)
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
```

## Monitoring & Maintenance

### Database Queries
Monitor slow queries on:
- Page lookup by slug
- Navigation menu hierarchical queries
- Section loading for pages

### Regular Tasks
- **Weekly**: Review unpublished content
- **Monthly**: Archive old pages
- **Quarterly**: Optimize database indexes

## API Documentation

Full API documentation available at:
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Troubleshooting

### Page Not Found
1. Check if page exists: `python manage.py shell -c "from cms.models import Page; print(Page.objects.filter(slug='page-slug').values())"`
2. Verify school association
3. Check `is_published` status

### API Returns 403 Forbidden
- Verify JWT token is valid
- Check user has staff permissions
- Review permission class configuration

### Migration Issues
- Run: `python manage.py migrate --fake cms zero` then `python manage.py migrate cms`
- Check for conflicting slugs across schools

## Next Steps

1. ✅ Database schema with slug and config fields
2. ✅ Static content migrated to database (52 pages)
3. ✅ API endpoints fully functional
4. 🔄 Update frontend to fetch from API (In Progress)
5. ⏳ Add admin interface customizations
6. ⏳ Implement caching layer
7. ⏳ Add image upload functionality
8. ⏳ Create content editing UI

## Support

For questions or issues:
- Check API documentation at `/swagger/`
- Review Django admin at `/admin/`
- Check application logs
