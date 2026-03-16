# Phase B Student Core Models - Implementation Summary

## ✅ IMPLEMENTATION COMPLETE

All Phase B Student Core models have been successfully created/modified in the Django API according to the brainstorming session specifications.

## Location

**File:** `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models.py`

## Models Implemented

### 1. StudentEnrollment (Line 281) - NEW MODEL ✅

Tracks complete student enrollment history across academic years.

**Key Fields:**
- `student` (FK to Student)
- `section` (FK to Section)
- `academic_year` (FK to AcademicYear)
- `roll_number` (IntegerField) - Roll number for this enrollment
- `enrolled_date` (DateField) - When student joined section
- `exit_date` (DateField, nullable) - When student left section
- `exit_reason` (CharField) - Choices: promoted, transferred, dropped, graduated
- `is_current` (BooleanField) - Only one per student can be true

**Unique Constraint:** `[['student', 'academic_year']]` - One enrollment per student per year

**Key Methods:**
- `save()` - Auto-manages `is_current` constraint (sets others to False when one is True)
- `__str__()` - Returns readable representation with roll number

### 2. StudentPhoto (Line 368) - NEW MODEL ✅

Manages student photos with approval workflow and annual refresh tracking.

**Key Fields:**
- `student` (FK to Student)
- `image` (ImageField, upload_to='student_photos/')
- `status` (CharField) - Choices: pending, approved, rejected, expired
- `rejection_reason` (TextField, nullable)
- `uploaded_by` (FK to UserProfile)
- `approved_by` (FK to UserProfile, nullable)
- `uploaded_at` (DateTimeField)
- `approved_at` (DateTimeField, nullable)
- `is_current` (BooleanField) - Only one per student can be true
- `academic_year` (FK to AcademicYear) - For annual refresh tracking

**Key Methods:**
- `save()` - Auto-manages `is_current` constraint, expires old pending photos (>30 days)
- `approve(approved_by_user)` - Approve photo and set as current
- `reject(rejected_by_user, reason)` - Reject photo with reason
- `__str__()` - Returns readable representation with status

### 3. Student (Line 565) - MODIFIED MODEL ✅

Enhanced with Phase B fields and helper methods.

**New/Modified Fields:**
- `current_section` (FK to Section, nullable) - NEW: Current section (replaces current_class)
- `admission_number` (CharField, unique) - UPDATED help text to reference SchoolSettings format
- `roll_number` (IntegerField, nullable) - CHANGED from CharField to IntegerField
- `status` (CharField) - ENHANCED with 'dropped' choice added

**Kept for Backward Compatibility:**
- `current_class` (FK to Class, nullable, DEPRECATED) - Will be removed after migration

**New Helper Methods:**
```python
# Properties
@property full_name -> str
@property has_current_photo -> bool
@property photo_pending_approval -> bool
@property current_photo_url -> str | None

# Methods
def get_current_photo() -> StudentPhoto | None
def get_current_enrollment() -> StudentEnrollment | None
def has_photo_for_year(academic_year) -> bool
def get_enrollment_history() -> QuerySet
```

## Data Flow

```
Student Registration Flow:
1. Create Student with admission_number
2. Create StudentEnrollment with section, academic_year, roll_number, is_current=True
3. Upload StudentPhoto (status='pending')
4. Admin approves photo → status='approved', is_current=True
5. Student now has current section and current photo

Annual Refresh Flow:
1. New academic year created
2. Students promoted to new sections
3. New StudentEnrollment created (is_current=True, old one set to is_current=False with exit_reason)
4. Request new StudentPhoto for new academic year
5. Admin approves new photo → old photo is_current=False, new is_current=True
```

## Constraints & Validations

1. **Unique Constraints:**
   - `Student.admission_number` - Unique across school
   - `StudentEnrollment[student, academic_year]` - One enrollment per student per year

2. **is_current Constraints (enforced in save()):**
   - Only ONE `StudentEnrollment` per student can have `is_current=True`
   - Only ONE `StudentPhoto` per student can have `is_current=True`

3. **Field Validations:**
   - `StudentEnrollment.roll_number` - MinValueValidator(1)
   - `Student.roll_number` - MinValueValidator(1)
   - `StudentPhoto.status` - Must be one of: pending, approved, rejected, expired
   - `StudentEnrollment.exit_reason` - Must be one of: promoted, transferred, dropped, graduated

## Indexes (for Performance)

**StudentEnrollment:**
- `['student', 'is_current']` - Fast lookup of current enrollment
- `['section', 'academic_year']` - Fast section roster queries
- `['academic_year', 'roll_number']` - Sorted class lists
- `['is_current']` - Current enrollments only

**StudentPhoto:**
- `['student', 'is_current']` - Fast current photo lookup
- `['student', 'status']` - Filter by approval status
- `['status']` - Approval queue
- `['academic_year']` - Year-wise photo management
- `['uploaded_by']` - Track who uploaded

**Student:**
- `['status']` - Filter active students
- `['admission_number']` - Fast admission number lookup
- `['current_section']` - Section roster queries
- `['academic_year']` - Year-wise student lists
- `['first_name', 'last_name']` - Alphabetical sorting

## Next Steps

### Immediate Actions Required:

1. **Create Migrations:**
   ```bash
   cd /Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api
   pipenv run python manage.py makemigrations academics
   ```

2. **Review Migration:**
   - Check that roll_number field type change is handled correctly
   - Verify unique_together constraint update
   - Ensure no data loss

3. **Apply Migrations:**
   ```bash
   pipenv run python manage.py migrate academics
   ```

4. **Register in Admin:** (See PHASE_B_COMPLETE.md for code)
   - StudentEnrollmentAdmin
   - StudentPhotoAdmin

5. **Create API Endpoints:** (See PHASE_B_COMPLETE.md for code)
   - StudentEnrollmentSerializer
   - StudentPhotoSerializer
   - ViewSets and URLs

6. **Test Models:**
   - Test enrollment creation and is_current constraint
   - Test photo approval/rejection workflow
   - Test helper methods
   - Test unique constraints

### Future Phases:

**Phase C: Teacher Assignment**
- SubjectTeacher model (teacher + subject + section + academic_year)
- Update Section.class_teacher relationship

**Phase D: Utilities**
- Roll Number Calculator Service
- Year Clone Wizard Service
- Student Promotion Service

## Documentation Files

1. **PHASE_B_COMPLETE.md** - Complete implementation details, testing guide, admin setup
2. **PHASE_B_IMPLEMENTATION_NOTES.md** - Original change notes
3. **models_phase_b.py** - Reference implementation
4. **README_PHASE_B.md** - This file (quick reference)

## Backup

Original file backed up to:
`/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models.py.backup`

## Reference

Brainstorming session document:
`/Users/ashitrai/Development/study/personal/school-website/_bmad-output/brainstorming/brainstorming-session-2026-03-16-academic-structure.md`

## Model Count

```
Phase A Models (Foundation):  4 ✅
  - SchoolSettings
  - AcademicYear
  - Grade
  - Section

Phase B Models (Student Core): 3 ✅
  - StudentEnrollment (NEW)
  - StudentPhoto (NEW)
  - Student (MODIFIED)
```

---

**Status:** ✅ Code Complete - Ready for Migration

**Next Task:** Run `makemigrations` and `migrate` commands
