# Phase B Student Core Models - Implementation Notes

## Status: PARTIALLY COMPLETE

The models.py file at `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models.py` has Phase B models implemented, but requires the following corrections:

## Changes Required

### 1. Remove Duplicate Models (Lines 1314-1521)
**Current Issue:** The file contains duplicate definitions of `StudentEnrollment` and `StudentPhoto` models starting at line 1314.

**Action Required:** Delete lines 1314-1521 (duplicate Phase B models section)

**Command to fix:**
```bash
# Create backup first
cp academics/models.py academics/models.py.pre-phase-b-cleanup

# Remove duplicate lines
sed -i.bak '1314,1521d' academics/models.py
```

### 2. Update StudentEnrollment Model (Line 281-382)

**Current State:** Model has `status` field with choices, but missing `exit_reason` field per spec.

**Required Changes:**
- Add `exit_reason` field with EXIT_REASON_CHOICES = [('promoted', 'Promoted'), ('transferred', 'Transferred'), ('dropped', 'Dropped'), ('graduated', 'Graduated')]
- Ensure `unique_together = [['student', 'academic_year']]` (currently has `[['student', 'section', 'academic_year']]`)
- Update `__str__` method to show roll number

**Current (Line 286-336):**
```python
STATUS_CHOICES = [
    ('active', 'Active'),
    ('promoted', 'Promoted'),
    ('transferred', 'Transferred'),
    ('withdrawn', 'Withdrawn'),
    ('completed', 'Completed'),
]

status = models.CharField(...)
```

**Should be:**
```python
EXIT_REASON_CHOICES = [
    ('promoted', 'Promoted'),
    ('transferred', 'Transferred'),
    ('dropped', 'Dropped'),
    ('graduated', 'Graduated'),
]

exit_reason = models.CharField(
    max_length=20,
    choices=EXIT_REASON_CHOICES,
    blank=True,
    help_text='Reason for exiting this section'
)
```

Also change:
- Line 361: `unique_together = [['student', 'section', 'academic_year']]` → `[['student', 'academic_year']]`

### 3. Update Student Model (Line 597-732)

**Issue 1: roll_number field type**
- Line 644-648: Currently `CharField`, should be `IntegerField`

**Current:**
```python
roll_number = models.CharField(
    max_length=50,
    blank=True,
    help_text='Current section-specific roll number'
)
```

**Should be:**
```python
roll_number = models.IntegerField(
    null=True,
    blank=True,
    validators=[MinValueValidator(1)],
    help_text='Current roll number in current section (shortcut field)'
)
```

**Issue 2: Missing helper methods**
The model has some @property methods but missing these required methods:

```python
def get_current_photo(self):
    """
    Returns the current approved photo for the student.
    Returns None if no current photo exists.
    """
    try:
        return self.photos.get(is_current=True, status='approved')
    except StudentPhoto.DoesNotExist:
        return None

def get_current_enrollment(self):
    """
    Returns the current active enrollment for the student.
    Returns None if no current enrollment exists.
    """
    try:
        return self.enrollments.get(is_current=True)
    except StudentEnrollment.DoesNotExist:
        return None

def has_photo_for_year(self, academic_year):
    """
    Check if student has an approved photo for the given academic year.
    """
    return self.photos.filter(
        academic_year=academic_year,
        status='approved'
    ).exists()

def get_enrollment_history(self):
    """
    Returns complete enrollment history ordered by most recent first.
    """
    return self.enrollments.all().order_by('-academic_year__start_date', '-enrolled_date')
```

Add these methods after line 732 (after the `current_photo_url` property).

### 4. Update StudentPhoto Model (Line 384-596)

**Current Issues:**
- Has extra metadata fields (file_size, width, height) - These are OK to keep but not in original spec
- Upload path is 'students/photos/%Y/%m/' - spec says 'student_photos/'

**Recommended Change:**
- Line 413: Change upload path from `'students/photos/%Y/%m/'` to `'student_photos/'` to match spec

**Add helper methods:**
Add these methods at the end of StudentPhoto model (around line 596):

```python
def approve(self, approved_by_user):
    """Approve this photo and set it as current"""
    from django.utils import timezone
    self.status = 'approved'
    self.approved_by = approved_by_user
    self.approved_at = timezone.now()
    self.is_current = True
    self.save()

def reject(self, rejected_by_user, reason):
    """Reject this photo with a reason"""
    from django.utils import timezone
    self.status = 'rejected'
    self.approved_by = rejected_by_user
    self.approved_at = timezone.now()
    self.rejection_reason = reason
    self.is_current = False
    self.save()
```

## Summary of Model Status

### ✅ StudentPhoto Model (Line 384-596)
- **Status:** 95% COMPLETE
- **Action:** Add `approve()` and `reject()` methods, optionally change upload path
- **Note:** Has extra metadata fields (file_size, width, height) which are useful additions beyond spec

### ⚠️ StudentEnrollment Model (Line 281-382)
- **Status:** 85% COMPLETE
- **Action:**
  1. Add `exit_reason` field
  2. Change unique_together constraint
  3. Update __str__ method

### ⚠️ Student Model (Line 597-732)
- **Status:** 90% COMPLETE
- **Action:**
  1. Change `roll_number` from CharField to IntegerField
  2. Add helper methods: get_current_photo(), get_current_enrollment(), has_photo_for_year(), get_enrollment_history()

### ❌ Duplicate Models (Line 1314-1521)
- **Status:** MUST DELETE
- **Action:** Remove entire duplicate section

## Post-Cleanup Actions Required

After making these changes:

1. **Create migrations:**
   ```bash
   pipenv run python manage.py makemigrations academics
   ```

2. **Review migration file** to ensure:
   - roll_number field changes from CharField to IntegerField
   - exit_reason field is added to StudentEnrollment
   - No conflicts with existing data

3. **Apply migrations:**
   ```bash
   pipenv run python manage.py migrate academics
   ```

4. **Test models in Django shell:**
   ```bash
   pipenv run python manage.py shell

   from academics.models import Student, StudentEnrollment, StudentPhoto, AcademicYear, Section

   # Test creating records
   # Test helper methods
   # Verify constraints work
   ```

## Files Created

- `/Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api/academics/models_phase_b.py` - Reference implementation of correct Phase B models
- This file - Implementation notes and required changes

## Next Steps

Refer to brainstorming session document for Phase C (Teacher Assignment) implementation after Phase B is complete and tested.
