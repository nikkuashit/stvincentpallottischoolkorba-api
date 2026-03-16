# Phase B Student Core Serializers - Implementation Summary

**Date:** 2026-03-16
**Context:** Brainstorming session on Academic Structure Planning
**Reference:** `_bmad-output/brainstorming/brainstorming-session-2026-03-16-academic-structure.md`

## Overview

Created Django REST Framework serializers for Phase B Student Core models (StudentEnrollment and StudentPhoto) with comprehensive validation, nested relationships, and approval workflows.

## Models Created

### 1. StudentEnrollment Model
**Location:** `academics/models.py`

Tracks historical enrollment records for students across academic years and sections.

**Key Features:**
- Complete enrollment history with audit trail
- Section-specific roll numbers
- Status tracking (active, promoted, transferred, withdrawn, completed)
- Automatic current enrollment management (only one is_current per student)
- Enrolled by tracking (admin who created enrollment)

**Fields:**
- student (FK to Student)
- section (FK to Section)
- academic_year (FK to AcademicYear)
- roll_number (integer, section-specific)
- enrolled_date, exit_date
- status, is_current
- enrolled_by (FK to UserProfile)
- notes

### 2. StudentPhoto Model
**Location:** `academics/models.py`

Manages student photos with admin approval workflow and history tracking.

**Key Features:**
- Approval workflow (pending → approved/rejected/expired)
- Only one current photo per student
- Photo metadata (dimensions, file size)
- Automatic expiration of old photos when new one is approved
- Audit trail with uploader and approver tracking

**Fields:**
- student (FK to Student)
- academic_year (FK to AcademicYear)
- image (ImageField)
- file_size, width, height (metadata)
- status (pending, approved, rejected, expired)
- is_current (boolean)
- uploaded_by, approved_by (FK to UserProfile)
- uploaded_at, approved_at
- rejection_reason

### 3. Student Model Updates
**Location:** `academics/models.py`

Enhanced existing Student model with Phase B features:

**New Fields:**
- current_section (FK to Section) - replaces current_class
- status expanded to include 'dropped'

**New Properties:**
- full_name - computed property
- has_current_photo - boolean property
- photo_pending_approval - boolean property
- current_photo_url - get URL of current photo

**Deprecated Fields:**
- current_class - kept for backward compatibility
- photo - use StudentPhoto model instead

## Serializers Created

### StudentEnrollment Serializers

#### 1. StudentEnrollmentListSerializer
**Purpose:** Minimal fields for list views
**Fields:** id, student info, section info, academic year, roll number, dates, status

**Features:**
- Computed student_name
- Computed section_name (full name like "5A")
- status_display for human-readable status

#### 2. StudentEnrollmentDetailSerializer
**Purpose:** Full details with nested information
**Fields:** All list fields + nested objects

**Nested Fields:**
- student_info: id, admission_number, full_name, status
- section_info: id, name, full_name, grade info, capacity, current_strength
- academic_year_info: id, name, dates, status, is_current
- enrolled_by_name

#### 3. StudentEnrollmentCreateSerializer (Enhanced)
**Purpose:** Create enrollments with validation

**Validation:**
- ✅ Student not already enrolled in same academic year
- ✅ Section has available capacity
- ✅ Academic year matches section's academic year

**Auto-actions:**
- Sets enrolled_by from request context
- Sets is_current to True
- Updates student's current_section and academic_year

### StudentPhoto Serializers

#### 1. StudentPhotoListSerializer (Enhanced)
**Purpose:** Photo gallery view
**Fields:** id, student info, image, status, uploader, academic year, metadata

**Features:**
- Computed image_url with absolute URL
- student_name, uploaded_by_name
- Dimension and file size info

#### 2. StudentPhotoDetailSerializer (Enhanced)
**Purpose:** Full photo details

**Nested Fields:**
- student_info: id, admission_number, full_name, current_section
- uploaded_by_info: id, full_name, role
- approved_by_info: id, full_name, role
- image_url (absolute URL)

#### 3. StudentPhotoUploadSerializer (Enhanced)
**Purpose:** Upload new photos with validation

**Validation:**
- ✅ Maximum file size: 5MB
- ✅ Allowed formats: JPEG, PNG
- ✅ Rejects invalid image formats

**Auto-actions:**
- Sets uploaded_by from request context
- Sets status to 'pending'
- Extracts image metadata (width, height, file_size)

#### 4. StudentPhotoApprovalSerializer
**Purpose:** Admin approval/rejection workflow

**Validation:**
- ✅ Rejection reason required if rejecting
- ✅ Rejection reason not allowed if approving

**Fields:**
- status: 'approved' or 'rejected'
- rejection_reason: required if rejecting
- set_as_current: boolean (default True)

**Auto-actions:**
- Sets approved_by from request context
- Sets approved_at timestamp
- Sets is_current if approved and set_as_current=True

### Enhanced Student Serializer

#### StudentSerializerEnhanced
**Purpose:** Complete student information with Phase B features

**New Computed Fields:**
- current_section_info - nested section details
- current_photo - nested current approved photo (only approved & is_current)
- enrollment_history - list of past 5 enrollments
- has_current_photo - boolean
- photo_pending_approval - boolean
- status_display - human-readable status

**current_section_info includes:**
- id, name, full_name, grade_number, grade_name, class_teacher

**current_photo includes:**
- id, image_url, uploaded_at, academic_year, width, height

**enrollment_history includes:**
- id, section, academic_year, roll_number, dates, status

## Implementation Details

### File Structure

```
academics/
├── models.py
│   ├── Phase A: SchoolSettings, AcademicYear, Grade, Section
│   ├── Phase B: StudentEnrollment, StudentPhoto (NEW)
│   └── Updated: Student model with new fields
│
├── serializers.py
│   ├── Existing serializers (unchanged)
│   ├── Phase A serializers (from previous work)
│   └── Phase B serializers (NEW):
│       ├── StudentEnrollmentListSerializer
│       ├── StudentEnrollmentDetailSerializer
│       ├── StudentEnrollmentCreateSerializerEnhanced
│       ├── StudentPhotoListSerializerEnhanced
│       ├── StudentPhotoDetailSerializerEnhanced
│       ├── StudentPhotoUploadSerializerEnhanced
│       ├── StudentPhotoApprovalSerializer
│       └── StudentSerializerEnhanced
│
└── migrations/
    └── 0005_studentenrollment_studentphoto_and_more.py (NEW)
```

### Migration Created

**Migration File:** `academics/migrations/0005_studentenrollment_studentphoto_and_more.py`

**Changes:**
- ✅ Create StudentEnrollment model
- ✅ Create StudentPhoto model
- ✅ Add current_section field to Student
- ✅ Update Student.current_class (marked deprecated)
- ✅ Update Student.photo (marked deprecated)
- ✅ Update Student.status (added 'dropped' choice)
- ✅ Create indexes for performance optimization

### Indexes Created

**StudentEnrollment:**
- (student, academic_year)
- (section, academic_year)
- (status)
- (student, is_current)

**StudentPhoto:**
- (student, is_current)
- (status, academic_year)
- (uploaded_at)
- (is_current, status)

**Student:**
- (current_section)

## Validation Rules

### StudentEnrollment Creation
1. Student cannot be enrolled in multiple sections in same academic year
2. Section must have available capacity
3. Academic year must match section's academic year

### StudentPhoto Upload
1. Image file size ≤ 5MB
2. Image format must be JPEG or PNG
3. Status automatically set to 'pending'

### StudentPhoto Approval
1. Rejection reason required when rejecting
2. Only one photo can be is_current=True per student
3. Old approved photos automatically expired when new photo is approved

## Special Features

### Automatic Management

**StudentEnrollment:**
- When created with is_current=True, automatically unsets is_current on other enrollments
- Updates student's current_section and academic_year when created

**StudentPhoto:**
- When approved and set as current, unsets is_current on all other photos
- Automatically expires old approved photos from previous academic years
- Extracts image metadata (width, height, file_size) on upload

### Computed Fields

**Student model now provides:**
```python
student.full_name  # "John Doe"
student.has_current_photo  # True/False
student.photo_pending_approval  # True/False
student.current_photo_url  # URL or None
```

## Usage Examples

### Create Enrollment
```python
serializer = StudentEnrollmentCreateSerializerEnhanced(
    data={
        'student': student_id,
        'section': section_id,
        'academic_year': academic_year_id,
        'roll_number': 15,
        'enrolled_date': '2025-06-01',
        'notes': 'Regular enrollment'
    },
    context={'request': request}
)
if serializer.is_valid():
    enrollment = serializer.save()
```

### Upload Photo
```python
serializer = StudentPhotoUploadSerializerEnhanced(
    data={
        'student': student_id,
        'image': image_file,
        'academic_year': academic_year_id
    },
    context={'request': request}
)
if serializer.is_valid():
    photo = serializer.save()  # Status is 'pending'
```

### Approve Photo
```python
photo = StudentPhoto.objects.get(id=photo_id)
serializer = StudentPhotoApprovalSerializer(
    instance=photo,
    data={
        'status': 'approved',
        'set_as_current': True
    },
    context={'request': request}
)
if serializer.is_valid():
    approved_photo = serializer.save()
```

### Get Student with Full Info
```python
student = Student.objects.get(id=student_id)
serializer = StudentSerializerEnhanced(
    student,
    context={'request': request}
)
data = serializer.data
# Includes: current_section_info, current_photo, enrollment_history
```

## Next Steps

1. **Create ViewSets** for StudentEnrollment and StudentPhoto
2. **Register URLs** in `academics/urls.py`
3. **Add Permissions** (admin-only for approval)
4. **Create Admin Interface** in `academics/admin.py`
5. **Run Migration**: `python manage.py migrate academics`
6. **Test Endpoints** using Swagger UI

## Breaking Changes / Deprecations

### Deprecated Fields (kept for backward compatibility)
- `Student.current_class` → Use `Student.current_section`
- `Student.photo` → Use `StudentPhoto` model

### New Required Behavior
- Students must be enrolled via StudentEnrollment model
- Photos must go through approval workflow
- Only one current enrollment and one current photo per student

## API Patterns to Follow

### Enrollment Endpoints (to be created)
```
GET    /api/academics/enrollments/         - List all enrollments
POST   /api/academics/enrollments/         - Create enrollment
GET    /api/academics/enrollments/{id}/    - Get enrollment detail
PATCH  /api/academics/enrollments/{id}/    - Update enrollment
DELETE /api/academics/enrollments/{id}/    - Delete enrollment
```

### Photo Endpoints (to be created)
```
GET    /api/academics/student-photos/           - List all photos
POST   /api/academics/student-photos/upload/    - Upload photo
GET    /api/academics/student-photos/{id}/      - Get photo detail
POST   /api/academics/student-photos/{id}/approve/  - Approve/reject
GET    /api/academics/student-photos/pending/   - Get pending photos
```

## Testing Checklist

- [ ] Test enrollment validation (duplicate prevention)
- [ ] Test section capacity enforcement
- [ ] Test photo upload with valid/invalid sizes
- [ ] Test photo upload with valid/invalid formats
- [ ] Test photo approval workflow
- [ ] Test rejection requires reason
- [ ] Test only one current enrollment per student
- [ ] Test only one current photo per student
- [ ] Test enrollment updates student's current_section
- [ ] Test photo approval sets is_current
- [ ] Test enrollment history returns correct data
- [ ] Test current_photo returns only approved & current

## References

- **Brainstorming Session:** `_bmad-output/brainstorming/brainstorming-session-2026-03-16-academic-structure.md`
- **Models:** `academics/models.py` (lines 277-516)
- **Serializers:** `academics/serializers.py` (lines 1692-end)
- **Migration:** `academics/migrations/0005_studentenrollment_studentphoto_and_more.py`
