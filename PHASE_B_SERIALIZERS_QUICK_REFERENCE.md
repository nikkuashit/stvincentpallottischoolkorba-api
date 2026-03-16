# Phase B Serializers - Quick Reference Guide

## StudentEnrollment Serializers

### 1. StudentEnrollmentListSerializer
**Use Case:** List view of enrollments
```python
from academics.serializers import StudentEnrollmentListSerializer

# List all enrollments for a student
enrollments = StudentEnrollment.objects.filter(student=student)
serializer = StudentEnrollmentListSerializer(enrollments, many=True)
```

**Returns:**
```json
{
  "id": "uuid",
  "student": "uuid",
  "student_name": "John Doe",
  "student_admission_number": "SVP25001",
  "section": "uuid",
  "section_name": "5A",
  "academic_year": "uuid",
  "academic_year_name": "2025-26",
  "roll_number": 15,
  "enrolled_date": "2025-06-01",
  "exit_date": null,
  "status": "active",
  "status_display": "Active",
  "is_current": true
}
```

### 2. StudentEnrollmentDetailSerializer
**Use Case:** Detailed view with nested objects
```python
from academics.serializers import StudentEnrollmentDetailSerializer

enrollment = StudentEnrollment.objects.get(id=enrollment_id)
serializer = StudentEnrollmentDetailSerializer(enrollment)
```

**Returns:** All list fields PLUS:
```json
{
  "student_info": {
    "id": "uuid",
    "admission_number": "SVP25001",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "status": "active"
  },
  "section_info": {
    "id": "uuid",
    "name": "A",
    "full_name": "Class 5A",
    "grade_number": 5,
    "grade_name": "Class 5",
    "capacity": 65,
    "current_strength": 45
  },
  "academic_year_info": {
    "id": "uuid",
    "name": "2025-26",
    "start_date": "2025-06-01",
    "end_date": "2026-05-31",
    "status": "active",
    "is_current": true
  },
  "enrolled_by_name": "Admin User",
  "notes": "Regular enrollment"
}
```

### 3. StudentEnrollmentCreateSerializerEnhanced
**Use Case:** Create new enrollment with validation
```python
from academics.serializers import StudentEnrollmentCreateSerializerEnhanced

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
else:
    print(serializer.errors)
```

**Validation Errors:**
- `student`: "Student is already enrolled in 5A for academic year 2025-26"
- `section`: "Section Class 5A is at full capacity (65/65)"
- `academic_year`: "Academic year must match section's academic year (2025-26)"

---

## StudentPhoto Serializers

### 1. StudentPhotoListSerializerEnhanced
**Use Case:** Photo gallery view
```python
from academics.serializers import StudentPhotoListSerializerEnhanced

photos = StudentPhoto.objects.filter(student=student)
serializer = StudentPhotoListSerializerEnhanced(
    photos,
    many=True,
    context={'request': request}
)
```

**Returns:**
```json
{
  "id": "uuid",
  "student": "uuid",
  "student_name": "John Doe",
  "student_admission_number": "SVP25001",
  "image": "/media/students/photos/2025/06/photo.jpg",
  "image_url": "http://localhost:8000/media/students/photos/2025/06/photo.jpg",
  "status": "approved",
  "status_display": "Approved",
  "is_current": true,
  "uploaded_by": "uuid",
  "uploaded_by_name": "Parent User",
  "uploaded_at": "2025-06-15T10:30:00Z",
  "academic_year": "uuid",
  "academic_year_name": "2025-26",
  "width": 800,
  "height": 1000,
  "file_size": 245678
}
```

### 2. StudentPhotoDetailSerializerEnhanced
**Use Case:** Full photo details
```python
from academics.serializers import StudentPhotoDetailSerializerEnhanced

photo = StudentPhoto.objects.get(id=photo_id)
serializer = StudentPhotoDetailSerializerEnhanced(
    photo,
    context={'request': request}
)
```

**Returns:** All list fields PLUS:
```json
{
  "student_info": {
    "id": "uuid",
    "admission_number": "SVP25001",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "current_section": "Class 5A"
  },
  "uploaded_by_info": {
    "id": "uuid",
    "full_name": "Parent User",
    "role": "parent"
  },
  "approved_by_info": {
    "id": "uuid",
    "full_name": "Admin User",
    "role": "school_admin"
  },
  "approved_at": "2025-06-15T14:20:00Z",
  "rejection_reason": ""
}
```

### 3. StudentPhotoUploadSerializerEnhanced
**Use Case:** Upload new photo
```python
from academics.serializers import StudentPhotoUploadSerializerEnhanced

serializer = StudentPhotoUploadSerializerEnhanced(
    data={
        'student': student_id,
        'image': image_file,
        'academic_year': academic_year_id
    },
    context={'request': request}
)

if serializer.is_valid():
    photo = serializer.save()  # Status is automatically 'pending'
else:
    print(serializer.errors)
```

**Validation Errors:**
- `image`: "Image file size (6.50MB) exceeds maximum allowed size (5MB). Please compress the image."
- `image`: "Invalid image format 'application/pdf'. Allowed formats: JPEG, PNG"

**Auto-actions:**
- Sets `uploaded_by` to current user
- Sets `status` to 'pending'
- Extracts width, height, file_size metadata

### 4. StudentPhotoApprovalSerializer
**Use Case:** Approve or reject photo
```python
from academics.serializers import StudentPhotoApprovalSerializer

photo = StudentPhoto.objects.get(id=photo_id)

# Approve
serializer = StudentPhotoApprovalSerializer(
    instance=photo,
    data={
        'status': 'approved',
        'set_as_current': True
    },
    context={'request': request}
)

# Reject
serializer = StudentPhotoApprovalSerializer(
    instance=photo,
    data={
        'status': 'rejected',
        'rejection_reason': 'Photo is blurry, please upload a clearer image'
    },
    context={'request': request}
)

if serializer.is_valid():
    updated_photo = serializer.save()
else:
    print(serializer.errors)
```

**Validation Errors:**
- `rejection_reason`: "Rejection reason is required when rejecting a photo"
- `rejection_reason`: "Rejection reason should not be provided when approving"

**Auto-actions (on approval):**
- Sets `approved_by` to current user
- Sets `approved_at` timestamp
- Sets `is_current=True` (unsets all other photos for student)

---

## Enhanced Student Serializer

### StudentSerializerEnhanced
**Use Case:** Complete student info with Phase B features
```python
from academics.serializers import StudentSerializerEnhanced

student = Student.objects.get(id=student_id)
serializer = StudentSerializerEnhanced(
    student,
    context={'request': request}
)
```

**Returns:** All basic student fields PLUS:
```json
{
  "id": "uuid",
  "admission_number": "SVP25001",
  "full_name": "John Doe",
  "status": "active",
  "status_display": "Active",
  "has_current_photo": true,
  "photo_pending_approval": false,

  "current_section_info": {
    "id": "uuid",
    "name": "A",
    "full_name": "Class 5A",
    "grade_number": 5,
    "grade_name": "Class 5",
    "class_teacher": "Teacher Name"
  },

  "current_photo": {
    "id": "uuid",
    "image_url": "http://localhost:8000/media/students/photos/2025/06/photo.jpg",
    "uploaded_at": "2025-06-15T10:30:00Z",
    "academic_year": "2025-26",
    "width": 800,
    "height": 1000
  },

  "enrollment_history": [
    {
      "id": "uuid",
      "section": "Class 4A",
      "academic_year": "2024-25",
      "roll_number": 12,
      "enrolled_date": "2024-06-01",
      "exit_date": "2025-05-31",
      "status": "Promoted"
    }
  ]
}
```

---

## Common Usage Patterns

### Check if student can be enrolled
```python
from academics.serializers import StudentEnrollmentCreateSerializerEnhanced

serializer = StudentEnrollmentCreateSerializerEnhanced(
    data={
        'student': student_id,
        'section': section_id,
        'academic_year': academic_year_id,
        'roll_number': 15,
        'enrolled_date': '2025-06-01'
    }
)

if serializer.is_valid():
    # Can enroll
    enrollment = serializer.save()
else:
    # Cannot enroll - show errors
    for field, errors in serializer.errors.items():
        print(f"{field}: {errors}")
```

### Get all pending photos for approval
```python
from academics.models import StudentPhoto
from academics.serializers import StudentPhotoListSerializerEnhanced

pending_photos = StudentPhoto.objects.filter(status='pending')
serializer = StudentPhotoListSerializerEnhanced(
    pending_photos,
    many=True,
    context={'request': request}
)

# Use in admin dashboard
pending_count = pending_photos.count()
```

### Get student with current photo and enrollment
```python
from academics.models import Student
from academics.serializers import StudentSerializerEnhanced

student = Student.objects.get(admission_number='SVP25001')
serializer = StudentSerializerEnhanced(
    student,
    context={'request': request}
)

data = serializer.data

# Check if student has photo
if data['has_current_photo']:
    photo_url = data['current_photo']['image_url']
else:
    # Use placeholder image
    photo_url = '/static/images/student-placeholder.png'

# Get current section
current_section = data['current_section_info']['full_name']  # "Class 5A"

# Get enrollment history
history = data['enrollment_history']  # List of past enrollments
```

### Bulk photo approval
```python
from academics.models import StudentPhoto
from academics.serializers import StudentPhotoApprovalSerializer

pending_photos = StudentPhoto.objects.filter(status='pending')

for photo in pending_photos:
    serializer = StudentPhotoApprovalSerializer(
        instance=photo,
        data={
            'status': 'approved',
            'set_as_current': True
        },
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
```

---

## ViewSet Integration (Example)

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import StudentEnrollment, StudentPhoto
from .serializers import (
    StudentEnrollmentListSerializer,
    StudentEnrollmentDetailSerializer,
    StudentEnrollmentCreateSerializerEnhanced,
    StudentPhotoListSerializerEnhanced,
    StudentPhotoApprovalSerializer,
)

class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = StudentEnrollment.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentEnrollmentListSerializer
        elif self.action == 'create':
            return StudentEnrollmentCreateSerializerEnhanced
        else:
            return StudentEnrollmentDetailSerializer


class StudentPhotoViewSet(viewsets.ModelViewSet):
    queryset = StudentPhoto.objects.all()
    serializer_class = StudentPhotoListSerializerEnhanced

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        photo = self.get_object()
        serializer = StudentPhotoApprovalSerializer(
            instance=photo,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        pending = self.queryset.filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)
```

---

## Migration Command

Before using these serializers, run the migration:

```bash
pipenv run python manage.py migrate academics
```

This will create the `StudentEnrollment` and `StudentPhoto` tables and update the `Student` table.
