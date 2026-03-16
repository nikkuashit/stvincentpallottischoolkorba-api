# Phase B Student Core Models - IMPLEMENTATION COMPLETE

## Summary

Phase B Student Core models have been successfully implemented in `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models.py`.

## Changes Made

### 1. StudentEnrollment Model (Lines ~281-362)

**Status:** ✅ COMPLETE

**Changes:**
- Changed `unique_together` from `[['student', 'section', 'academic_year']]` to `[['student', 'academic_year']]` (one enrollment per student per year)
- Added `exit_reason` field with choices: promoted, transferred, dropped, graduated
- Changed `roll_number` from nullable CharField to required IntegerField with MinValueValidator(1)
- Removed `status`, `enrolled_by`, and `notes` fields (simplified per spec)
- Updated `__str__` method to include roll number
- Updated Meta ordering to `['-academic_year__start_date', '-enrolled_date']`
- Added proper indexes for performance

**Key Features:**
- Tracks complete enrollment history across academic years
- `is_current` flag ensures only one current enrollment per student
- `save()` method auto-manages `is_current` constraint
- `exit_reason` tracks why student left section

### 2. StudentPhoto Model (Lines ~368-527)

**Status:** ✅ COMPLETE

**Changes:**
- Added `approve(approved_by_user)` helper method
- Added `reject(rejected_by_user, reason)` helper method
- Kept extra metadata fields (file_size, width, height) as useful additions
- `is_current` flag ensures only one current photo per student
- `save()` method auto-manages `is_current` constraint and expires old pending photos

**Key Features:**
- Full approval workflow (pending → approved/rejected/expired)
- Tracks uploader and approver with timestamps
- Annual refresh tracking via `academic_year` FK
- Helper methods simplify photo management workflow
- Auto-expires pending photos older than 30 days (in save method)

### 3. Student Model (Lines ~565-758)

**Status:** ✅ COMPLETE

**Changes:**
- Added `current_section` FK to Section model (Phase B upgrade)
- Changed `roll_number` from CharField to IntegerField with validators
- Updated `admission_number` help text to reference SchoolSettings format
- Enhanced `status` choices to include 'dropped'
- Kept `current_class` FK as DEPRECATED for backward compatibility

**New Helper Methods:**
```python
@property
def full_name(self):
    """Returns full name of the student"""

@property
def has_current_photo(self):
    """Check if student has an approved current photo"""

@property
def photo_pending_approval(self):
    """Check if student has a photo pending approval"""

@property
def current_photo_url(self):
    """Get URL of current approved photo"""

def get_current_photo(self):
    """Returns the current approved photo for the student. Returns None if no current photo exists."""

def get_current_enrollment(self):
    """Returns the current active enrollment for the student. Returns None if no current enrollment exists."""

def has_photo_for_year(self, academic_year):
    """Check if student has an approved photo for the given academic year."""

def get_enrollment_history(self):
    """Returns complete enrollment history ordered by most recent first."""
```

**Key Features:**
- Dual identifiers: `admission_number` (permanent) and `roll_number` (temporal, section-specific)
- 5 status states: active, inactive, graduated, transferred, dropped
- Rich helper methods for common operations
- Support for enrollment history and photo management

### 4. Cleanup

**Status:** ✅ COMPLETE

**Changes:**
- Removed duplicate `StudentEnrollment` and `StudentPhoto` models (former lines 1357-1521)
- Removed duplicate `Class` model (kept only DEPRECATED version for migration support)

## Model Relationships

```
Student (1) ←→ (N) StudentEnrollment ←→ (1) Section ←→ (1) Grade
   ↓
   ↓ (1) ←→ (N)
   ↓
StudentPhoto ←→ (1) AcademicYear
```

**Constraints:**
- `StudentEnrollment.unique_together = [['student', 'academic_year']]` - One enrollment per student per year
- Only one `StudentEnrollment.is_current=True` per student (enforced in save())
- Only one `StudentPhoto.is_current=True` per student (enforced in save())
- `Student.roll_number` must be ≥ 1 (MinValueValidator)

## Next Steps

### 1. Create Migrations

```bash
cd /Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api
pipenv run python manage.py makemigrations academics
```

**Expected Migration Operations:**
- Add `exit_reason` field to StudentEnrollment
- Change StudentEnrollment.roll_number from CharField to IntegerField
- Change StudentEnrollment.unique_together constraint
- Add `current_section` FK to Student model
- Change Student.roll_number from CharField to IntegerField
- Add Student helper methods (no migration needed - code only)
- Add StudentPhoto helper methods (no migration needed - code only)

### 2. Review Migration

```bash
# Check the generated migration file
ls -la academics/migrations/
cat academics/migrations/0XXX_phase_b_student_core.py
```

**Review Checklist:**
- [ ] roll_number field type change handled correctly (data migration may be needed)
- [ ] unique_together constraint update is safe
- [ ] No data loss from removed fields
- [ ] FK relationships are correct

### 3. Apply Migration

```bash
pipenv run python manage.py migrate academics
```

### 4. Test Models

```python
pipenv run python manage.py shell

from academics.models import Student, StudentEnrollment, StudentPhoto, AcademicYear, Section, Grade
from accounts.models import UserProfile

# Get or create test data
year = AcademicYear.objects.first()
grade = Grade.objects.filter(academic_year=year).first()
section = Section.objects.filter(grade=grade).first()

# Test Student creation
student = Student.objects.create(
    admission_number='SVP25001',
    first_name='Test',
    last_name='Student',
    date_of_birth='2010-01-01',
    gender='male',
    address_line1='Test Address',
    city='Test City',
    state='Test State',
    postal_code='123456',
    admission_date='2025-04-01',
    current_section=section,
    roll_number=1,
    status='active'
)

# Test StudentEnrollment creation
enrollment = StudentEnrollment.objects.create(
    student=student,
    section=section,
    academic_year=year,
    roll_number=1,
    enrolled_date='2025-04-01',
    is_current=True
)

# Test StudentPhoto creation
admin = UserProfile.objects.filter(is_staff=True).first()
photo = StudentPhoto.objects.create(
    student=student,
    academic_year=year,
    image='path/to/photo.jpg',  # You'll need an actual file
    uploaded_by=admin,
    status='pending'
)

# Test helper methods
print(student.full_name)
print(student.get_current_enrollment())
print(student.get_current_photo())
print(student.has_photo_for_year(year))
print(student.get_enrollment_history())

# Test photo workflow
photo.approve(admin)
print(photo.status)  # Should be 'approved'
print(photo.is_current)  # Should be True

# Test second enrollment constraint
try:
    StudentEnrollment.objects.create(
        student=student,
        section=section,
        academic_year=year,  # Same year - should fail unique constraint
        roll_number=2,
        enrolled_date='2025-04-01'
    )
except Exception as e:
    print(f"Expected error: {e}")
```

### 5. Register Models in Admin

Update `academics/admin.py` to register the new models:

```python
from django.contrib import admin
from .models import StudentEnrollment, StudentPhoto

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'academic_year', 'roll_number', 'is_current', 'enrolled_date')
    list_filter = ('academic_year', 'is_current', 'exit_reason')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StudentPhoto)
class StudentPhotoAdmin(admin.ModelAdmin):
    list_display = ('student', 'status', 'is_current', 'uploaded_at', 'uploaded_by')
    list_filter = ('status', 'is_current', 'academic_year')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    readonly_fields = ('uploaded_at', 'approved_at', 'created_at', 'updated_at')
    actions = ['approve_photos', 'reject_photos']

    def approve_photos(self, request, queryset):
        for photo in queryset:
            photo.approve(request.user.userprofile)
        self.message_user(request, f"{queryset.count()} photos approved.")

    def reject_photos(self, request, queryset):
        for photo in queryset:
            photo.reject(request.user.userprofile, "Rejected via admin action")
        self.message_user(request, f"{queryset.count()} photos rejected.")
```

### 6. Update Serializers (DRF)

Create serializers for the new models in `academics/serializers.py`:

```python
from rest_framework import serializers
from .models import StudentEnrollment, StudentPhoto

class StudentEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    section_name = serializers.CharField(source='section.full_name', read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class StudentPhotoSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.user.username', read_only=True)

    class Meta:
        model = StudentPhoto
        fields = '__all__'
        read_only_fields = ('uploaded_at', 'approved_at', 'created_at', 'updated_at')
```

## Implementation Completion Checklist

- [x] StudentEnrollment model created with all required fields
- [x] StudentPhoto model created with all required fields
- [x] Student model updated with new fields (current_section, roll_number as IntegerField)
- [x] Student model helper methods added
- [x] StudentPhoto helper methods added (approve, reject)
- [x] Duplicate models removed
- [x] Proper Meta classes with ordering, indexes, unique_together
- [x] __str__ methods implemented
- [x] save() overrides for is_current constraint enforcement
- [ ] Migrations created and applied
- [ ] Models registered in admin.py
- [ ] Serializers created (DRF)
- [ ] ViewSets created (DRF)
- [ ] URLs configured
- [ ] Models tested in Django shell
- [ ] API endpoints tested

## Files Modified

- `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models.py` - Main changes

## Files Created

- `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models_phase_b.py` - Reference implementation
- `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/PHASE_B_IMPLEMENTATION_NOTES.md` - Implementation notes
- `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/PHASE_B_COMPLETE.md` - This file

## Backup Created

- `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models.py.backup` - Backup before changes

## Reference

Brainstorming session: `/Users/ashitrai/Development/study/personal/school-website/_bmad-output/brainstorming/brainstorming-session-2026-03-16-academic-structure.md`

Phase A models (already implemented): SchoolSettings, AcademicYear, Grade, Section

Phase C (next): SubjectTeacher model, Roll Number Calculator Service, Year Clone Wizard Service
