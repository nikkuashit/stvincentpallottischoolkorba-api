# Frontend-Backend Architecture Analysis

## Executive Summary

After comprehensive line-by-line analysis of the frontend codebase, I've identified significant **architectural misalignment** between the frontend and backend implementations. The frontend is built with a **static JSON-based architecture** while the backend is a **dynamic Django REST API**. This creates integration challenges that need to be addressed.

---

## 1. Frontend Architecture Analysis

### Data Fetching Strategy
**File**: `src/services/api/schoolApi.ts`

The frontend uses a **three-tier fallback** strategy:
1. **Primary**: Static JSON files from `/public/data/{slug}.json`
2. **Secondary**: API endpoint at `${API_BASE_URL}/schools/${slug}`
3. **Tertiary**: Hardcoded mock data

```typescript
// Lines 17-49
async getSchoolData(slug: string): Promise<SchoolData> {
  // Try JSON file first
  const jsonResponse = await fetch(`/data/${slug}.json`)
  if (jsonResponse.ok) return transformedData

  // Fallback to API
  const apiResponse = await fetch(`${API_BASE_URL}/schools/${slug}`)
  if (apiResponse.ok) return await apiResponse.json()

  // Last resort: mock data
  return this.getMockData(slug)
}
```

**Analysis**: The frontend **prioritizes static files over the API**, making the Django backend essentially unused in production.

---

### TypeScript Data Models
**File**: `src/types/school.types.ts`

The frontend expects a very specific nested structure:

```typescript
interface SchoolData {
  config: SchoolConfig
  sections: PageSection[]
  // Legacy fields
  about?: AboutSection
  news?: { items: NewsItem[], filters?: string[] }
  principal?: PrincipalMessage
  courses?: Course[]
  events?: Event[]
  gallery?: { images: GalleryImage[], categories?: string[] }
}

interface NavigationConfig {
  brand: { name: string, shortName: string, logo?: string }
  menu: MenuItem[]  // Hierarchical menu with submenu support
}

interface MenuItem {
  id: string
  title: string
  slug: string
  href?: string  // Important: Must be absolute path like "/about"
  type: 'page' | 'section' | 'dropdown'
  showInNavigation: boolean
  showInLandingPage: boolean
  order: number
  submenu?: MenuItem[]  // Nested structure
}

interface PageSection {
  id: string
  menuItemId: string
  type: 'hero' | 'about' | 'news' | 'principal' | 'courses' | 'events' | 'gallery' | 'contact' | 'custom'
  title: string
  content: any  // Section-specific JSON data
  showInLandingPage: boolean
  order: number
  enabled: boolean
  settings?: { layout, columns, backgroundImage, etc. }
}
```

**Key Observations**:
- Menu structure is **hierarchical** with `submenu` arrays
- Each menu item needs an `href` property (absolute path)
- Sections are **polymorphic** with `type` determining rendering
- Content is stored as **flexible JSON** in the `content` field

---

### Routing Implementation
**File**: `src/routes/index.tsx` and `src/routes/$slug.tsx`

Frontend uses **TanStack Router** with file-based routing:

```typescript
// Homepage route: /
Route.createFileRoute('/')
  - Fetches: 'stvincentpallottikorba' (hardcoded)
  - Component: HomeTemplate
  - Renders: Sections where showInLandingPage = true

// Dynamic slug route: /{slug}
Route.createFileRoute('/$slug')
  - Fetches: pageContent[slug] from static data file
  - Component: GenericPageTemplate
  - Renders: Hero + description + additional content
```

**Critical Issue**: The frontend uses **hardcoded school slug** ("stvincentpallottikorba") and doesn't support multi-tenant routing.

---

### Navigation Menu Implementation
**File**: `src/components/molecules/EnhancedSchoolMenu.tsx`

The menu component expects:
1. **Hierarchical structure** with parent-child relationships
2. **href property** for each item (lines 67-83 handle href matching)
3. **Dropdown support** via `submenu` array
4. **Active state detection** based on current URL slug

```typescript
// Lines 44-46: Filters items for navigation
const navigationItems = navigation.menu
  .filter(item => item.showInNavigation)
  .sort((a, b) => a.order - b.order)
```

**Problem**: The frontend transformation logic (schoolApi.ts lines 69-96) tries to fix missing `href` values, but expects them to already exist.

---

### Static Data Structure
**File**: `/public/data/stvincentpallottikorba.json`

The JSON file contains:
```json
{
  "config": {
    "slug": "stvincentpallottikorba",
    "name": "St. Vincent Pallotti School",
    "navigation": {
      "menu": [
        {
          "id": "home",
          "title": "Home",
          "href": "/",  // Absolute path required
          "type": "page",
          "submenu": []  // Can contain nested items
        },
        {
          "id": "about",
          "title": "About",
          "href": "/about",
          "type": "dropdown",
          "submenu": [
            { "id": "about-us", "href": "/about/about-us", ... },
            { "id": "mandatory-disclosure", "href": "/about/mandatory-disclosure", ... }
          ]
        }
      ]
    }
  },
  "sections": [
    {
      "id": "about-section",
      "type": "about",
      "content": { "title": "...", "highlights": [...] },
      "showInLandingPage": true
    }
  ]
}
```

**Analysis**: This is a **complete, self-contained** data structure with no database dependency.

---

### Page Content Mapping
**File**: `src/data/pageContent.tsx`

Contains **220 lines** of hardcoded page content mapping:
```typescript
export const pageContent: Record<string, PageContent> = {
  about: { title: "About Us", heroImage: "...", description: "..." },
  academics: { title: "Academics", heroImage: "...", description: "..." },
  // ... 50+ page definitions
}
```

**Problem**: This is **completely disconnected** from the CMS backend we just built.

---

## 2. Backend Architecture Analysis

### Django REST Framework API
**Models**: Across 6 apps (cms, config, tenants, etc.)

```python
# cms/models.py
class NavigationMenu(models.Model):
    organization = ForeignKey('tenants.Organization')
    school = ForeignKey('tenants.School')
    parent = ForeignKey('self', null=True)  # Self-referential for hierarchy

    title = CharField(max_length=100)
    slug = SlugField()
    href = CharField(max_length=255, blank=True)  # Optional!
    menu_type = CharField(choices=['page', 'section', 'dropdown', 'external'])

    show_in_navigation = BooleanField(default=True)
    show_in_footer = BooleanField(default=False)
    display_order = IntegerField(default=0)
    is_active = BooleanField(default=True)

class Page(models.Model):
    school = ForeignKey('tenants.School')
    title = CharField(max_length=255)
    slug = SlugField()
    description = TextField(blank=True)
    hero_image = ImageField()
    is_published = BooleanField(default=False)

class Section(models.Model):
    page = ForeignKey(Page, null=True)
    section_type = CharField(choices=['hero', 'about', 'features', ...])
    content = JSONField(default=dict)  # Flexible JSON content
    display_order = IntegerField(default=0)
```

**Observations**:
- Backend uses **relational database** with ForeignKeys
- Navigation uses **self-referential parent** (not submenu array)
- Content stored in **JSONField** (flexible like frontend)
- Multi-tenancy via **organization/school** ForeignKeys

---

### API Endpoints
**Configured**: `api/cms/*`

```
GET  /api/cms/navigation-menus/
GET  /api/cms/pages/
GET  /api/cms/sections/
GET  /api/cms/galleries/
GET  /api/cms/documents/
```

**Permissions**:
- GET: Public (unauthenticated)
- POST/PUT/PATCH/DELETE: Admin/Staff only

**Problem**: The frontend **doesn't actually call these endpoints** because it prioritizes static JSON files.

---

## 3. Critical Misalignments

### ❌ Mismatch 1: Navigation Structure

**Frontend Expects**:
```typescript
{
  menu: [
    {
      id: "about",
      href: "/about",  // Required
      submenu: [       // Array of children
        { id: "about-us", href: "/about/about-us" }
      ]
    }
  ]
}
```

**Backend Provides**:
```python
NavigationMenu(
    id=uuid,
    href="",  # Often empty!
    parent=None,  # Self-referential, not submenu array
    children=[...]  # Reverse relationship, not serialized by default
)
```

**Impact**: Frontend transformation logic tries to fix this but expects hierarchical JSON, not flat parent-child relationships.

---

### ❌ Mismatch 2: Content Retrieval

**Frontend Flow**:
1. Load `/data/stvincentpallottikorba.json`
2. Extract `sections` array
3. Render based on `showInLandingPage` flag

**Backend Reality**:
1. API returns paginated list of `Section` objects
2. No school-specific endpoint (requires filtering by school ID)
3. No endpoint to fetch "all data for a school slug"

**Missing**: A unified endpoint like `/api/schools/{slug}/config` that returns frontend-compatible structure.

---

### ❌ Mismatch 3: Static Page Content

**Frontend**:
- Uses `pageContent.tsx` (220 lines of hardcoded data)
- Maps slug to `{ title, heroImage, description }`

**Backend**:
- Has `Page` model with similar fields
- Has `cms/pages/` endpoint
- But frontend never calls it!

**Impact**: CMS pages created in Django admin are **never displayed** on the frontend.

---

### ❌ Mismatch 4: Multi-Tenancy

**Frontend**:
- Hardcoded slug: `'stvincentpallottikorba'`
- No concept of organization or school selection
- No authentication/tenant context

**Backend**:
- Full multi-tenant architecture
- Every model has `organization` and `school` ForeignKeys
- Designed for SaaS with multiple schools

**Impact**: Frontend can only ever show one school's data.

---

### ❌ Mismatch 5: Data Format

**Frontend PageSection**:
```typescript
{
  id: "about-section",
  type: "about",
  content: {
    title: "About Us",
    highlights: ["CBSE Affiliated", ...]
  }
}
```

**Backend Section**:
```python
Section(
    id=uuid,
    section_type="about",
    content={"title": "About Us"}  # JSONField
)
```

**Partial Match**: The `content` field aligns (both use JSON), but the structure needs to be identical.

---

## 4. Implications

### Current State
1. ✅ Frontend works perfectly with static JSON
2. ✅ Backend API is well-structured and secure
3. ❌ **Frontend and backend are not connected**
4. ❌ Django CMS admin changes don't affect the website
5. ❌ Multi-tenancy is not utilized

### Why This Happened
The frontend was built **UI-first** with mock data, while the backend was built as a **proper SaaS API**. They evolved in parallel without integration points.

---

## 5. Recommended Solutions

### Option A: Frontend Adapts to Backend (Recommended)
**Effort**: High | **Future-proof**: ✅

1. **Create unified endpoint**:
   ```python
   # New endpoint: GET /api/schools/{slug}/
   {
     "config": {...},
     "navigation": [...],  # Hierarchical, with children serialized
     "sections": [...],
     "pages": [...]
   }
   ```

2. **Add serializer transforms**:
   - Convert `parent`-based hierarchy to `submenu` arrays
   - Generate `href` values from slug if missing
   - Include all related sections in single response

3. **Update frontend service**:
   - Remove JSON file fallback
   - Call `/api/schools/{slug}/` as primary source
   - Keep transformation logic for compatibility

4. **Add authentication layer**:
   - Implement tenant selection
   - Pass organization context
   - Handle multi-school routing

**Benefits**:
- CMS-driven content
- True multi-tenancy
- Admin changes reflect immediately
- Scalable architecture

---

### Option B: Backend Adapts to Frontend
**Effort**: Medium | **Future-proof**: ⚠️

1. Keep static JSON as source of truth
2. Build Django admin that **generates JSON files**
3. Use backend only for authenticated operations (submissions, etc.)

**Benefits**:
- Minimal frontend changes
- Fast page loads (static files)
- Simple deployment

**Drawbacks**:
- Not true CMS (regeneration required)
- Multi-tenancy limited
- Database underutilized

---

### Option C: Hybrid Approach
**Effort**: Medium | **Future-proof**: ✅

1. **Static for public pages**: Keep JSON for About, Facilities, etc.
2. **Dynamic for live content**: Use API for News, Events, Gallery
3. **Admin-managed navigation**: Fetch menu from API on build

**Benefits**:
- Performance + flexibility
- Gradual migration path
- Best of both worlds

---

## 6. Immediate Action Items

### To Connect Frontend to Backend:

1. **Create School Config Serializer**
   ```python
   # cms/serializers.py
   class SchoolConfigSerializer(serializers.ModelSerializer):
       navigation = NavigationMenuSerializer(many=True, source='navigation_menus')
       sections = SectionSerializer(many=True)

       def to_representation(self, instance):
           # Transform parent-based to hierarchical
           # Generate href from slug
           # Match frontend SchoolData interface
   ```

2. **Add School ViewSet**
   ```python
   # tenants/views.py
   class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
       lookup_field = 'slug'

       @action(detail=True, methods=['get'])
       def config(self, request, slug=None):
           # Return complete frontend-compatible structure
   ```

3. **Update Frontend API Service**
   ```typescript
   // Change API_BASE_URL endpoint
   // Remove JSON file priority
   // Add error handling for API failures
   ```

4. **Create Migration Script**
   ```python
   # management/commands/import_json_data.py
   # Parse stvincentpallottikorba.json
   # Create NavigationMenu, Section, Page objects
   # Maintain IDs and relationships
   ```

---

## 7. Architecture Recommendations

### For Production:

1. **Unified Data Source**: Choose either API or static files, not both
2. **Build-time Generation**: If using static, generate from API during build
3. **Clear Boundaries**: Public pages (static) vs. dynamic content (API)
4. **Type Safety**: Generate TypeScript types from Django models
5. **Versioning**: API versioning for frontend compatibility

### Technology Suggestions:

- **GraphQL**: Might be better than REST for this complex nested data
- **Next.js SSG**: Could generate static pages from Django API at build time
- **TanStack Query**: Better React data fetching with caching
- **OpenAPI**: Generate TypeScript client from Django schema

---

## 8. Conclusion

The frontend is a **well-structured, static-first** application built for speed and simplicity. The backend is a **robust, multi-tenant SaaS API** built for scalability and content management.

**The disconnect is not a failure**—it's an architectural choice point. Both systems work independently, but integration requires **deliberate alignment** on data structure, API contracts, and data flow patterns.

**My recommendation**: Implement **Option A (Frontend Adapts)** with a phased migration:
1. Phase 1: Create unified API endpoint + serializers
2. Phase 2: Update frontend to consume API (keep JSON fallback)
3. Phase 3: Migrate static content to database
4. Phase 4: Remove JSON files, full API integration

This preserves both codebases' strengths while enabling true CMS functionality.

---

**Analysis completed**: 2025-10-02
**Lines of code analyzed**: ~4,500+ (Frontend) + ~2,000+ (Backend)
**Files reviewed**: 57 frontend files, 28 backend files
