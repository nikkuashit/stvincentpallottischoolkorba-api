# 🏢 Multi-Tenant School ERP - Entity Relationship Diagram

## 🎯 SaaS Architecture Overview

This is a **multi-tenant SaaS application** where:
- Multiple schools use the same application instance
- Each school's data is completely isolated
- Shared infrastructure, separate data
- Subscription-based access model

---

## 📊 Core Entity Categories

### 1. **Tenant Management** (Multi-tenancy Core)
### 2. **User Management** (Authentication & Authorization)
### 3. **School Configuration** (Branding & Settings)
### 4. **Content Management** (Website Content)
### 5. **Academic Management** (Students, Classes, etc.)
### 6. **Communication** (News, Events, Announcements)
### 7. **Media Management** (Images, Documents)
### 8. **System Management** (Subscriptions, Billing)

---

## 🗂️ Detailed ER Diagram

### **1. TENANT MANAGEMENT (Multi-tenancy Core)**

```
┌─────────────────────────────────────┐
│         ORGANIZATION                │  ← Root tenant entity
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│     name                  VARCHAR   │
│     slug                  VARCHAR   │  ← Unique identifier (subdomain)
│     domain                VARCHAR   │  ← Custom domain (optional)
│     is_active             BOOLEAN   │
│     subscription_status   ENUM      │  ← active, trial, expired, suspended
│     subscription_plan     FK        │  → SubscriptionPlan
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
│     owner                 FK        │  → User (org admin)
└─────────────────────────────────────┘
           │
           │ 1:1
           ▼
┌─────────────────────────────────────┐
│         SCHOOL                      │  ← Main school entity
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  organization_id       UUID      │  → Organization
│     name                  VARCHAR   │
│     short_name            VARCHAR   │
│     tagline               TEXT      │
│     email                 EMAIL     │
│     phone                 VARCHAR   │
│     address               TEXT      │
│     website_url           VARCHAR   │
│     established_year      INTEGER   │
│     affiliation           VARCHAR   │  ← CBSE, ICSE, etc.
│     board_code            VARCHAR   │
│     school_code           VARCHAR   │
│     principal_name        VARCHAR   │
│     logo                  FILE      │
│     is_published          BOOLEAN   │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘
```

---

### **2. USER MANAGEMENT**

```
┌─────────────────────────────────────┐
│         USER (Django Auth)          │  ← Extends Django User
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│     username              VARCHAR   │
│     email                 EMAIL     │
│     password              VARCHAR   │
│     first_name            VARCHAR   │
│     last_name             VARCHAR   │
│     is_active             BOOLEAN   │
│     is_staff              BOOLEAN   │
│     is_superuser          BOOLEAN   │
│     date_joined           DATETIME  │
│     last_login            DATETIME  │
└─────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────┐
│         USER_PROFILE                │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  user_id               UUID      │  → User
│ FK  organization_id       UUID      │  → Organization (tenant)
│     role                  ENUM      │  ← org_admin, school_admin, teacher, staff, parent, student
│     phone                 VARCHAR   │
│     avatar                FILE      │
│     department            VARCHAR   │
│     designation           VARCHAR   │
│     employee_id           VARCHAR   │
│     date_of_birth         DATE      │
│     gender                ENUM      │
│     address               TEXT      │
│     bio                   TEXT      │
│     is_active             BOOLEAN   │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘
           │
           │ M:N
           ▼
┌─────────────────────────────────────┐
│         ROLE                        │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  organization_id       UUID      │  → Organization
│     name                  VARCHAR   │
│     slug                  VARCHAR   │
│     description           TEXT      │
│     permissions           JSON      │  ← Permission matrix
│     is_system_role        BOOLEAN   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘
```

---

### **3. SCHOOL CONFIGURATION**

```
┌─────────────────────────────────────┐
│         THEME_CONFIG                │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     primary_color         VARCHAR   │
│     secondary_color       VARCHAR   │
│     accent_color          VARCHAR   │
│     font_family           VARCHAR   │
│     logo                  FILE      │
│     favicon               FILE      │
│     custom_css            TEXT      │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         NAVIGATION_MENU             │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     title                 VARCHAR   │
│     slug                  VARCHAR   │
│     type                  ENUM      │  ← page, section, dropdown, external
│     order                 INTEGER   │
│     parent_id             UUID      │  → NavigationMenu (self-reference)
│     icon                  VARCHAR   │
│     url                   VARCHAR   │
│     is_active             BOOLEAN   │
│     show_in_navigation    BOOLEAN   │
│     show_in_footer        BOOLEAN   │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         SOCIAL_LINKS                │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     platform              VARCHAR   │  ← facebook, twitter, instagram, etc.
│     url                   VARCHAR   │
│     icon                  VARCHAR   │
│     order                 INTEGER   │
│     is_active             BOOLEAN   │
└─────────────────────────────────────┘
```

---

### **4. CONTENT MANAGEMENT**

```
┌─────────────────────────────────────┐
│         PAGE                        │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     title                 VARCHAR   │
│     slug                  VARCHAR   │
│     content               TEXT      │
│     meta_title            VARCHAR   │
│     meta_description      TEXT      │
│     featured_image        FILE      │
│     status                ENUM      │  ← draft, published, archived
│     is_homepage           BOOLEAN   │
│     show_in_landing       BOOLEAN   │
│     order                 INTEGER   │
│     created_by            FK        │  → User
│     updated_by            FK        │  → User
│     published_at          DATETIME  │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         SECTION                     │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│ FK  page_id               UUID      │  → Page (optional)
│ FK  menu_item_id          UUID      │  → NavigationMenu (optional)
│     title                 VARCHAR   │
│     subtitle              TEXT      │
│     type                  ENUM      │  ← hero, about, news, events, gallery, courses, etc.
│     content               JSON      │  ← Dynamic content based on type
│     order                 INTEGER   │
│     layout                VARCHAR   │  ← grid, list, carousel, etc.
│     is_enabled            BOOLEAN   │
│     show_in_landing       BOOLEAN   │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘
```

---

### **5. ACADEMIC MANAGEMENT**

```
┌─────────────────────────────────────┐
│         ACADEMIC_YEAR               │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     name                  VARCHAR   │  ← "2024-2025"
│     start_date            DATE      │
│     end_date              DATE      │
│     is_current            BOOLEAN   │
│     is_active             BOOLEAN   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────┐
│         CLASS                       │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│ FK  academic_year_id      UUID      │  → AcademicYear
│     name                  VARCHAR   │  ← "Class 10", "Grade 5"
│     section               VARCHAR   │  ← "A", "B", "C"
│     capacity              INTEGER   │
│     room_number           VARCHAR   │
│     class_teacher_id      FK        │  → User
│     is_active             BOOLEAN   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────┐
│         STUDENT                     │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│ FK  user_id               UUID      │  → User (optional - if student has login)
│     admission_number      VARCHAR   │  ← Unique
│     roll_number           VARCHAR   │
│     first_name            VARCHAR   │
│     last_name             VARCHAR   │
│     date_of_birth         DATE      │
│     gender                ENUM      │
│     blood_group           VARCHAR   │
│     photo                 FILE      │
│     admission_date        DATE      │
│     status                ENUM      │  ← active, inactive, graduated, transferred
│     current_class_id      FK        │  → Class
│     address               TEXT      │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘
           │
           │ M:N
           ▼
┌─────────────────────────────────────┐
│         PARENT                      │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│ FK  user_id               UUID      │  → User (for parent portal access)
│     first_name            VARCHAR   │
│     last_name             VARCHAR   │
│     relationship          ENUM      │  ← father, mother, guardian
│     occupation            VARCHAR   │
│     phone                 VARCHAR   │
│     email                 EMAIL     │
│     address               TEXT      │
│     is_primary_contact    BOOLEAN   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘
           │
           │ M:N
           └──────────────────┐
                             ▼
┌─────────────────────────────────────┐
│         STUDENT_PARENT              │  ← Junction table
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  student_id            UUID      │  → Student
│ FK  parent_id             UUID      │  → Parent
│     relationship          ENUM      │
│     is_primary            BOOLEAN   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         SUBJECT                     │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     name                  VARCHAR   │
│     code                  VARCHAR   │
│     description           TEXT      │
│     icon                  VARCHAR   │
│     image                 FILE      │
│     is_active             BOOLEAN   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         COURSE                      │  ← Maps subjects to classes
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│ FK  class_id              UUID      │  → Class
│ FK  subject_id            UUID      │  → Subject
│ FK  teacher_id            UUID      │  → User (teacher)
│     syllabus              TEXT      │
│     schedule              JSON      │  ← Timetable
│     is_active             BOOLEAN   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘
```

---

### **6. COMMUNICATION**

```
┌─────────────────────────────────────┐
│         NEWS                        │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     title                 VARCHAR   │
│     slug                  VARCHAR   │
│     content               TEXT      │
│     excerpt               TEXT      │
│     type                  ENUM      │  ← announcement, event, achievement, academic
│     featured_image        FILE      │
│     status                ENUM      │  ← draft, published, archived
│     is_featured           BOOLEAN   │
│     publish_date          DATETIME  │
│     created_by            FK        │  → User
│     updated_by            FK        │  → User
│     views_count           INTEGER   │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         EVENT                       │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     title                 VARCHAR   │
│     slug                  VARCHAR   │
│     description           TEXT      │
│     category              ENUM      │  ← cultural, sports, academic, other
│     event_date            DATE      │
│     event_time            TIME      │
│     end_date              DATE      │  ← For multi-day events
│     location              VARCHAR   │
│     venue                 TEXT      │
│     featured_image        FILE      │
│     registration_required BOOLEAN   │
│     registration_link     VARCHAR   │
│     max_participants      INTEGER   │
│     status                ENUM      │  ← upcoming, ongoing, completed, cancelled
│     is_featured           BOOLEAN   │
│     created_by            FK        │  → User
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         ANNOUNCEMENT                │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     title                 VARCHAR   │
│     content               TEXT      │
│     type                  ENUM      │  ← urgent, important, general
│     target_audience       JSON      │  ← all, students, parents, teachers, specific classes
│     priority              ENUM      │  ← high, medium, low
│     start_date            DATETIME  │
│     end_date              DATETIME  │
│     is_active             BOOLEAN   │
│     created_by            FK        │  → User
│     created_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         NOTIFICATION                │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│ FK  user_id               UUID      │  → User (recipient)
│     title                 VARCHAR   │
│     message               TEXT      │
│     type                  ENUM      │  ← info, warning, success, error
│     link                  VARCHAR   │
│     is_read               BOOLEAN   │
│     read_at               DATETIME  │
│     created_at            DATETIME  │
└─────────────────────────────────────┘
```

---

### **7. MEDIA MANAGEMENT**

```
┌─────────────────────────────────────┐
│         GALLERY                     │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     name                  VARCHAR   │
│     description           TEXT      │
│     cover_image           FILE      │
│     is_featured           BOOLEAN   │
│     order                 INTEGER   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────┐
│         GALLERY_IMAGE               │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  gallery_id            UUID      │  → Gallery
│ FK  school_id             UUID      │  → School
│     title                 VARCHAR   │
│     caption               TEXT      │
│     image                 FILE      │
│     thumbnail             FILE      │
│     order                 INTEGER   │
│     uploaded_by           FK        │  → User
│     created_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         DOCUMENT                    │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     title                 VARCHAR   │
│     description           TEXT      │
│     file                  FILE      │
│     category              ENUM      │  ← syllabus, circular, form, report, other
│     academic_year_id      FK        │  → AcademicYear (optional)
│     class_id              FK        │  → Class (optional)
│     file_size             INTEGER   │
│     file_type             VARCHAR   │
│     downloads_count       INTEGER   │
│     is_public             BOOLEAN   │
│     uploaded_by           FK        │  → User
│     created_at            DATETIME  │
└─────────────────────────────────────┘
```

---

### **8. SYSTEM MANAGEMENT**

```
┌─────────────────────────────────────┐
│         SUBSCRIPTION_PLAN           │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│     name                  VARCHAR   │  ← "Basic", "Pro", "Enterprise"
│     slug                  VARCHAR   │
│     description           TEXT      │
│     price_monthly         DECIMAL   │
│     price_yearly          DECIMAL   │
│     max_students          INTEGER   │
│     max_teachers          INTEGER   │
│     max_storage_gb        INTEGER   │
│     features              JSON      │  ← Feature list
│     is_active             BOOLEAN   │
│     trial_days            INTEGER   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         SUBSCRIPTION                │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  organization_id       UUID      │  → Organization
│ FK  plan_id               UUID      │  → SubscriptionPlan
│     status                ENUM      │  ← trial, active, expired, cancelled
│     start_date            DATETIME  │
│     end_date              DATETIME  │
│     auto_renew            BOOLEAN   │
│     payment_method        VARCHAR   │
│     created_at            DATETIME  │
│     updated_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         INVOICE                     │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  subscription_id       UUID      │  → Subscription
│ FK  organization_id       UUID      │  → Organization
│     invoice_number        VARCHAR   │
│     amount                DECIMAL   │
│     tax                   DECIMAL   │
│     total                 DECIMAL   │
│     status                ENUM      │  ← pending, paid, failed, refunded
│     payment_date          DATETIME  │
│     payment_method        VARCHAR   │
│     payment_reference     VARCHAR   │
│     created_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         AUDIT_LOG                   │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  organization_id       UUID      │  → Organization
│ FK  user_id               UUID      │  → User
│     action                VARCHAR   │
│     entity_type           VARCHAR   │
│     entity_id             UUID      │
│     changes               JSON      │
│     ip_address            VARCHAR   │
│     user_agent            TEXT      │
│     created_at            DATETIME  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         SYSTEM_SETTING              │
├─────────────────────────────────────┤
│ PK  id                    UUID      │
│ FK  school_id             UUID      │  → School
│     key                   VARCHAR   │
│     value                 JSON      │
│     category              VARCHAR   │  ← general, email, sms, payment, etc.
│     is_public             BOOLEAN   │
│     updated_by            FK        │  → User
│     updated_at            DATETIME  │
└─────────────────────────────────────┘
```

---

## 🔐 Multi-Tenancy Strategy

### **Shared Database with Tenant Isolation**

All tables include `organization_id` or `school_id` foreign key for tenant isolation:

```python
# Every model includes:
organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
# OR
school = models.ForeignKey('School', on_delete=models.CASCADE)
```

### **Middleware-based Tenant Resolution**

1. Extract tenant from:
   - Subdomain (e.g., `school1.yourplatform.com`)
   - Custom domain (e.g., `www.school1.com`)
   - URL path (e.g., `/tenant/school1/...`)
   - Header (e.g., `X-Tenant-ID`)

2. All queries automatically filtered by tenant

### **Data Isolation Levels**

- **Organization Level**: Billing, subscription, organization settings
- **School Level**: Academic data, content, users (if org has multiple schools)

---

## 📈 Relationships Summary

### **One-to-One (1:1)**
- Organization ↔ School
- User ↔ UserProfile

### **One-to-Many (1:N)**
- Organization → Users
- School → Pages
- School → News
- School → Events
- School → Classes
- Class → Students
- School → Subjects
- AcademicYear → Classes
- Gallery → GalleryImages

### **Many-to-Many (M:N)**
- Students ↔ Parents (through StudentParent)
- Users ↔ Roles
- Classes ↔ Subjects (through Course)
- Events ↔ Participants

---

## 🎯 Key Design Decisions

### ✅ **Multi-Tenancy**
- Shared database with row-level tenant isolation
- `organization_id` on all tenant-specific tables
- Middleware enforces tenant context

### ✅ **Flexibility**
- JSON fields for dynamic content (Section.content)
- Polymorphic relationships where needed
- Extensible through custom fields

### ✅ **Security**
- Role-based access control (RBAC)
- Audit logging for all changes
- Data isolation at database level

### ✅ **Scalability**
- UUID primary keys
- Indexed foreign keys
- Optimized for read-heavy workloads
- Caching strategy ready

### ✅ **SaaS Features**
- Subscription management
- Usage tracking
- Billing integration ready
- Trial period support

---

## 📊 Index Strategy

### **Critical Indexes**
```sql
-- Tenant isolation (most important!)
CREATE INDEX idx_organization_id ON * (organization_id);
CREATE INDEX idx_school_id ON * (school_id);

-- Authentication
CREATE INDEX idx_user_email ON user (email);
CREATE INDEX idx_user_username ON user (username);

-- Lookups
CREATE INDEX idx_student_admission_number ON student (admission_number);
CREATE INDEX idx_slug ON page (slug);

-- Filtering
CREATE INDEX idx_status ON news (status);
CREATE INDEX idx_publish_date ON news (publish_date);
CREATE INDEX idx_is_active ON class (is_active);
```

---

## 🚀 Next Steps

1. **Create Django Models** from this ER diagram
2. **Implement Multi-Tenancy Middleware**
3. **Setup Row-Level Security**
4. **Create API Serializers**
5. **Build ViewSets & Endpoints**
6. **Add Permissions & Authorization**
7. **Implement Subscription Logic**

---

This ER diagram provides a **complete SaaS school ERP foundation** with:
- ✅ Multi-tenancy built-in
- ✅ Subscription management
- ✅ Academic management
- ✅ Content management
- ✅ User management
- ✅ Communication features
- ✅ Media handling
- ✅ Audit & security

Ready to implement! 🎉
