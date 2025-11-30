# Role-Based Access Control (RBAC) System Design

## Executive Summary

This document defines the comprehensive RBAC system for the multi-tenant School Management SaaS platform. The system supports hierarchical permissions across organizations, schools, and individual users.

---

## Role Hierarchy & Structure

### Proposed Roles (Improved)

| Role Level | Role Name | Scope | Description |
|------------|-----------|-------|-------------|
| **Platform** | `super_admin` | Global (All Organizations) | Platform owner, full system access |
| **Platform** | `platform_staff` | Global (Read-mostly) | Platform support staff, analytics |
| **Organization** | `org_admin` | Organization-wide | Organization owner, manages all schools |
| **Organization** | `org_staff` | Organization-wide | Organization employees (HR, Finance) |
| **School** | `school_admin` | School-specific | Principal/Head, manages one school |
| **School** | `school_staff` | School-specific | Teachers, staff at specific school |
| **School** | `parent` | School-specific | Student guardian with limited access |
| **School** | `student` | School-specific | Student with minimal access |

### Improvements Over Original:

1. **Added `platform_staff`**: Separates support staff from super admin (security best practice)
2. **Split `org staff` → `org_staff`**: Clarified as organization-level employees
3. **Added `school_admin`**: Critical role for principals (distinct from org admin)
4. **Added `school_staff`**: Teachers and school employees (not just org employees)
5. **Renamed `sas staff` → `platform_staff`**: More intuitive naming
6. **Kept `parent` and `student`**: Essential school-specific roles

---

## Detailed Role Definitions

### 1. Super Admin (`super_admin`)
**Scope**: Global Platform Access

**Capabilities**:
- ✅ Full CRUD on all models across all organizations
- ✅ Create/delete organizations and schools
- ✅ Manage platform-level settings
- ✅ Access all audit logs and analytics
- ✅ Manage subscription plans and billing
- ✅ Override any permission
- ✅ Impersonate any user (with audit trail)

**Restrictions**:
- ⚠️ Actions are logged in audit trail
- ⚠️ Cannot be deleted (system-protected)

**Use Cases**:
- Platform maintenance and debugging
- Onboarding new organizations
- Resolving critical issues

---

### 2. Platform Staff (`platform_staff`)
**Scope**: Global Read Access + Limited Write

**Capabilities**:
- ✅ View all organizations and schools (read-only)
- ✅ View analytics and reports across platform
- ✅ Create support tickets and notes
- ✅ View audit logs (cannot delete)
- ✅ Assist users with troubleshooting
- ❌ Cannot modify subscriptions or billing
- ❌ Cannot delete organizations or schools
- ❌ Cannot access user passwords or sensitive data

**Use Cases**:
- Customer support
- Platform monitoring
- Generating reports for business insights

---

### 3. Organization Admin (`org_admin`)
**Scope**: All Schools Within Organization

**Capabilities**:
- ✅ Full CRUD on all schools within organization
- ✅ Create/delete schools under organization
- ✅ Manage organization-level settings
- ✅ View/manage all users across all schools
- ✅ Assign roles (except super_admin)
- ✅ Manage organization subscription
- ✅ View consolidated analytics across schools
- ✅ Manage organization-level navigation and branding
- ❌ Cannot access other organizations
- ❌ Cannot modify platform settings

**Use Cases**:
- Multi-school organization management
- Consolidated reporting
- Organization-wide policy enforcement

---

### 4. Organization Staff (`org_staff`)
**Scope**: Organization-wide (Limited)

**Capabilities**:
- ✅ View all schools in organization (read-only)
- ✅ View organization-level reports
- ✅ Manage specific modules based on assignment (HR, Finance)
- ✅ Create announcements across schools
- ❌ Cannot create/delete schools
- ❌ Cannot manage subscriptions
- ❌ Cannot assign roles

**Modules** (assigned by org_admin):
- **HR Module**: Manage staff hiring, contracts
- **Finance Module**: View invoices, payments
- **Academics Module**: View consolidated academic reports

**Use Cases**:
- Organization HR managing teachers across schools
- Finance team managing billing
- Curriculum coordinators overseeing academics

---

### 5. School Admin (`school_admin`)
**Scope**: Single School (Full Access)

**Capabilities**:
- ✅ Full CRUD on school data (students, staff, classes)
- ✅ Manage school-specific users (teachers, parents, students)
- ✅ Assign roles within school (school_staff, parent, student)
- ✅ Manage CMS content for school website
- ✅ Manage school-specific navigation menu
- ✅ Create/manage academic years, classes, subjects
- ✅ Approve/reject admissions
- ✅ Manage school events, news, gallery
- ✅ View school analytics and reports
- ❌ Cannot delete school
- ❌ Cannot access other schools (unless explicitly granted)
- ❌ Cannot modify organization settings

**Use Cases**:
- Principal managing day-to-day operations
- School-level administrative decisions
- Content management for school website

---

### 6. School Staff (`school_staff`)
**Scope**: Single School (Module-Based)

**Capabilities**:
- ✅ View assigned classes and students
- ✅ Manage attendance for assigned classes
- ✅ Grade assignments and exams
- ✅ Upload course materials
- ✅ Communicate with parents
- ✅ View school announcements and events
- ❌ Cannot modify school settings
- ❌ Cannot create/delete users
- ❌ Cannot access other teachers' classes (unless co-teacher)

**Sub-roles** (managed via permissions):
- **Teacher**: Manages classes, grades, attendance
- **Counselor**: Access student records, meetings
- **Librarian**: Manage library, book loans
- **Lab Assistant**: Manage lab equipment, schedules

**Use Cases**:
- Teachers managing their classes
- Support staff with specific responsibilities
- Department-specific access

---

### 7. Parent (`parent`)
**Scope**: Own Children Only

**Capabilities**:
- ✅ View own children's information
- ✅ View children's attendance, grades, assignments
- ✅ View school announcements and events
- ✅ Download documents (report cards, circulars)
- ✅ Communicate with teachers (messages)
- ✅ Update own profile and contact information
- ❌ Cannot view other students' data
- ❌ Cannot modify school content
- ❌ Cannot access admin features

**Use Cases**:
- Monitoring child's academic progress
- Communication with school
- Staying informed about school activities

---

### 8. Student (`student`)
**Scope**: Own Data Only

**Capabilities**:
- ✅ View own attendance and grades
- ✅ Download assignments and study materials
- ✅ View school announcements and events
- ✅ Access class schedules and timetable
- ✅ View school gallery and news
- ✅ Submit assignments (if feature enabled)
- ❌ Cannot view other students' data
- ❌ Cannot modify any school content
- ❌ Cannot communicate with parents (separate accounts)

**Use Cases**:
- Accessing study materials
- Checking grades and attendance
- Staying updated with school activities

---

## Permission Matrix

### Notation
- ✅ **Full Access**: Create, Read, Update, Delete
- 👁️ **Read Only**: View only, no modifications
- 🔒 **Own Data**: Access limited to user's own data
- 📝 **Limited Write**: Can create/update, cannot delete
- ❌ **No Access**: Completely restricted

### Core Entities Permission Matrix

| Entity | Super Admin | Platform Staff | Org Admin | Org Staff | School Admin | School Staff | Parent | Student |
|--------|------------|----------------|-----------|-----------|-------------|--------------|--------|---------|
| **Organizations** | ✅ | 👁️ | 👁️ (own) | 👁️ (own) | 👁️ (own) | 👁️ (own) | ❌ | ❌ |
| **Schools** | ✅ | 👁️ | ✅ (own org) | 👁️ (own org) | 👁️ (own) | 👁️ (own) | 👁️ (own) | 👁️ (own) |
| **Users** | ✅ | 👁️ | ✅ (own org) | 👁️ (own org) | ✅ (own school) | 👁️ (colleagues) | 🔒 | 🔒 |
| **Students** | ✅ | 👁️ | 👁️ (own org) | 👁️ (own org) | ✅ (own school) | 👁️ (assigned) | 👁️ (own children) | 🔒 |
| **Parents** | ✅ | 👁️ | 👁️ (own org) | 👁️ (own org) | ✅ (own school) | 👁️ (assigned) | 🔒 | ❌ |
| **Classes** | ✅ | 👁️ | 👁️ (own org) | 👁️ (own org) | ✅ (own school) | 👁️ (assigned) | 👁️ (children's) | 👁️ (own) |
| **Subjects** | ✅ | 👁️ | 👁️ (own org) | 👁️ (own org) | ✅ (own school) | 📝 (assigned) | 👁️ | 👁️ |
| **Attendance** | ✅ | 👁️ | 👁️ (own org) | 👁️ (own org) | ✅ (own school) | 📝 (assigned classes) | 👁️ (children) | 👁️ (own) |
| **Grades** | ✅ | 👁️ | 👁️ (own org) | 👁️ (own org) | ✅ (own school) | 📝 (assigned classes) | 👁️ (children) | 👁️ (own) |
| **CMS Pages** | ✅ | 👁️ | ✅ (own org) | 📝 (own org) | ✅ (own school) | 📝 (own school) | 👁️ | 👁️ |
| **Navigation Menu** | ✅ | 👁️ | ✅ (own org) | ❌ | ✅ (own school) | ❌ | 👁️ | 👁️ |
| **News** | ✅ | 👁️ | ✅ (own org) | 📝 (own org) | ✅ (own school) | 📝 (own school) | 👁️ | 👁️ |
| **Events** | ✅ | 👁️ | ✅ (own org) | 📝 (own org) | ✅ (own school) | 📝 (own school) | 👁️ | 👁️ |
| **Announcements** | ✅ | 👁️ | ✅ (own org) | 📝 (own org) | ✅ (own school) | 📝 (own school) | 👁️ | 👁️ |
| **Gallery** | ✅ | 👁️ | ✅ (own org) | 📝 (own org) | ✅ (own school) | 📝 (own school) | 👁️ | 👁️ |
| **Documents** | ✅ | 👁️ | ✅ (own org) | 📝 (own org) | ✅ (own school) | 📝 (assigned) | 👁️ (public) | 👁️ (public) |
| **Subscriptions** | ✅ | 👁️ | ✅ (own) | 👁️ (own) | 👁️ (own school) | ❌ | ❌ | ❌ |
| **Audit Logs** | ✅ | 👁️ | 👁️ (own org) | ❌ | 👁️ (own school) | ❌ | ❌ | ❌ |
| **Analytics** | ✅ | 👁️ | 👁️ (own org) | 👁️ (assigned) | 👁️ (own school) | 👁️ (assigned) | ❌ | ❌ |

---

## Permission Groups & Granular Permissions

### Module-Based Permissions

Instead of monolithic roles, permissions are grouped by module:

#### **Academic Module**
- `academics.view_student`
- `academics.add_student`
- `academics.change_student`
- `academics.delete_student`
- `academics.view_class`
- `academics.manage_attendance`
- `academics.manage_grades`

#### **CMS Module**
- `cms.view_page`
- `cms.add_page`
- `cms.change_page`
- `cms.delete_page`
- `cms.publish_page`
- `cms.manage_navigation`

#### **Communications Module**
- `communications.view_news`
- `communications.add_news`
- `communications.publish_news`
- `communications.view_announcement`
- `communications.add_announcement`

#### **User Management Module**
- `accounts.view_user`
- `accounts.add_user`
- `accounts.change_user`
- `accounts.delete_user`
- `accounts.assign_role`

#### **Configuration Module**
- `config.view_theme`
- `config.change_theme`
- `config.manage_navigation`

---

## Role Assignment & Hierarchy

### Inheritance Rules

1. **Super Admin** inherits ALL permissions
2. **Platform Staff** inherits read permissions across platform
3. **Org Admin** inherits all permissions within organization scope
4. **School Admin** inherits all permissions within school scope
5. **Lower roles** have explicitly assigned permissions only

### Multi-Role Support

Users can have multiple roles in different contexts:

**Example 1**: Organization Admin who is also a Teacher
- `org_admin` at Organization ABC
- `school_staff` (teacher) at School XYZ
- Context determines active permissions

**Example 2**: Parent who is also a Teacher
- `parent` (viewing own child's data)
- `school_staff` (teaching other students)
- Separate contexts prevent conflicts

---

## Data Isolation & Security

### Multi-Tenancy Isolation

Every model includes:
```python
organization = ForeignKey('Organization')  # Tenant isolation
school = ForeignKey('School')  # Sub-tenant (optional)
```

### Row-Level Security (RLS)

Django querysets automatically filter by:
1. **Organization**: User can only see data from their organization
2. **School**: User can only see data from their school (if role is school-scoped)
3. **Ownership**: Some roles can only see data they own (parents, students)

### Example Queryset Filters:
```python
# Super Admin: No filter (sees all)
Student.objects.all()

# Org Admin: Filtered by organization
Student.objects.filter(organization=user.organization)

# School Admin: Filtered by school
Student.objects.filter(school=user.school)

# Parent: Filtered by children
Student.objects.filter(id__in=user.children_ids)

# Student: Only own record
Student.objects.filter(id=user.student_profile.id)
```

---

## Implementation Strategy

### Phase 1: Core RBAC (Current)
- ✅ Role model with permissions field
- ✅ User-Role assignment
- ✅ Basic permission checks in views

### Phase 2: Permission Middleware (Next)
- 🔄 Custom permission backend
- 🔄 Decorator-based permission checks
- 🔄 Django Guardian for object-level permissions

### Phase 3: Advanced Features
- ⏳ Dynamic permission assignment
- ⏳ Permission delegation
- ⏳ Temporary role elevation
- ⏳ Audit trail for permission changes

---

## Django Models Schema

### Updated Role Model

```python
class Role(models.Model):
    """
    Flexible role system with hierarchical permissions
    """
    ROLE_LEVELS = [
        ('platform', 'Platform Level'),
        ('organization', 'Organization Level'),
        ('school', 'School Level'),
    ]

    SYSTEM_ROLES = [
        ('super_admin', 'Super Administrator'),
        ('platform_staff', 'Platform Staff'),
        ('org_admin', 'Organization Administrator'),
        ('org_staff', 'Organization Staff'),
        ('school_admin', 'School Administrator'),
        ('school_staff', 'School Staff'),
        ('parent', 'Parent'),
        ('student', 'Student'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    # System vs Custom Role
    is_system_role = models.BooleanField(default=False)
    system_role_type = models.CharField(
        max_length=50,
        choices=SYSTEM_ROLES,
        blank=True
    )

    # Hierarchical Level
    role_level = models.CharField(max_length=20, choices=ROLE_LEVELS)

    # Permissions (JSONField for flexibility)
    permissions = models.JSONField(default=dict)
    # Example: {
    #   "academics": ["view_student", "add_student"],
    #   "cms": ["view_page", "change_page"]
    # }

    # Status
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Updated UserProfile Model

```python
class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    school = models.ForeignKey('School', on_delete=models.SET_NULL, null=True)

    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    # Additional role contexts (for multi-role users)
    additional_roles = models.ManyToManyField(
        Role,
        through='UserRoleAssignment',
        related_name='additional_users'
    )

    # Active role context (for multi-role users)
    active_role_context = models.JSONField(default=dict)
    # Example: {"role_id": "uuid", "school_id": "uuid"}
```

---

## Permission Checking Examples

### Decorator-Based Checks

```python
from functools import wraps
from django.core.exceptions import PermissionDenied

def require_permission(module, permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_profile = request.user.userprofile

            if not user_profile.has_permission(module, permission):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_permission('academics', 'view_student')
def student_list(request):
    students = Student.objects.filter(school=request.user.school)
    return render(request, 'students.html', {'students': students})
```

### ViewSet-Level Permissions

```python
from rest_framework import viewsets, permissions

class IsSchoolAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.userprofile.role.system_role_type == 'school_admin'

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    permission_classes = [IsSchoolAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        # Filter based on role
        if user.userprofile.is_super_admin():
            return Student.objects.all()
        elif user.userprofile.is_org_admin():
            return Student.objects.filter(organization=user.organization)
        elif user.userprofile.is_school_admin():
            return Student.objects.filter(school=user.school)
        elif user.userprofile.is_parent():
            return Student.objects.filter(parents=user.userprofile.parent_profile)
        else:
            return Student.objects.none()
```

---

## Best Practices

### 1. Principle of Least Privilege
- Assign minimum permissions required for job function
- Review permissions regularly
- Remove permissions when no longer needed

### 2. Separation of Duties
- No single role should have complete control
- Critical actions require multiple approvals
- Audit trails for sensitive operations

### 3. Security Guidelines
- Never hardcode role checks (use permission system)
- Always validate at both API and database level
- Log all permission changes and access attempts
- Implement rate limiting for sensitive operations

### 4. Testing Permissions
- Test each role's access boundaries
- Test cross-organization/school isolation
- Test permission inheritance
- Test multi-role scenarios

---

## Migration Path

### From Current System:
1. Create system roles in database
2. Assign existing users to appropriate roles
3. Migrate custom permissions to new format
4. Update all views to use permission decorators
5. Test thoroughly before production

### Backward Compatibility:
- Keep existing `is_staff` and `is_superuser` flags
- Map to `super_admin` role automatically
- Gradual migration over 2-3 releases

---

## Appendix: Permission Audit Checklist

### Before Launching:
- [ ] All system roles created in database
- [ ] Permission matrix tested for each role
- [ ] Row-level security verified
- [ ] Cross-tenant access blocked
- [ ] Audit logging enabled
- [ ] Documentation updated
- [ ] Admin users trained on role management
- [ ] Emergency access procedures defined

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Authors**: System Architect
**Review Status**: Draft - Pending Review
