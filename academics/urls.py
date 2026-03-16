"""
URL configuration for Academics App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AcademicYearViewSet,
    ClassViewSet,
    StudentViewSet,
    ParentViewSet,
    SubjectViewSet,
    CourseViewSet,
    # Attendance ViewSets
    AttendanceSessionViewSet,
    AttendanceSettingsViewSet,
    AttendanceViewSet,
    # Grades ViewSets
    ExamTypeViewSet,
    GradingScaleViewSet,
    ExamViewSet,
    StudentMarkViewSet,
    MarkAuditLogViewSet,
    # Student Admission
    StudentAdmissionViewSet,
    # Phase A: Academic Structure
    SchoolSettingsViewSet,
    GradeViewSet,
    SectionViewSet,
    # Phase B: Student Core
    StudentEnrollmentViewSet,
    StudentPhotoViewSet,
    # Phase C: Teacher Assignment
    ClassTeacherViewSet,
    SubjectTeacherViewSet,
)

router = DefaultRouter()
# Core academics
router.register(r'academic-years', AcademicYearViewSet, basename='academic-year')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'parents', ParentViewSet, basename='parent')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'courses', CourseViewSet, basename='course')

# Attendance
router.register(r'attendance-sessions', AttendanceSessionViewSet, basename='attendance-session')
router.register(r'attendance-settings', AttendanceSettingsViewSet, basename='attendance-settings')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

# Grades / Exams
router.register(r'exam-types', ExamTypeViewSet, basename='exam-type')
router.register(r'grading-scales', GradingScaleViewSet, basename='grading-scale')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'student-marks', StudentMarkViewSet, basename='student-mark')
router.register(r'mark-audit-logs', MarkAuditLogViewSet, basename='mark-audit-log')

# Student Admission workflow
router.register(r'admissions', StudentAdmissionViewSet, basename='admission')

# Phase A: Academic Structure (new)
router.register(r'school-settings', SchoolSettingsViewSet, basename='school-settings')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'sections', SectionViewSet, basename='section')

# Phase B: Student Core (new)
router.register(r'student-enrollments', StudentEnrollmentViewSet, basename='student-enrollment')
router.register(r'student-photos', StudentPhotoViewSet, basename='student-photo')

# Phase C: Teacher Assignment
router.register(r'class-teachers', ClassTeacherViewSet, basename='class-teacher')
router.register(r'subject-teachers', SubjectTeacherViewSet, basename='subject-teacher')

urlpatterns = [
    path('', include(router.urls)),
]
