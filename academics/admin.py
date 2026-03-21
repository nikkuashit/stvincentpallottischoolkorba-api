"""Django Admin for Academics App - Simplified without multi-tenancy"""

from django.contrib import admin
from .models import (
    GradeType, AcademicYear, Grade, Section, Student, Parent, StudentParent, Subject, Course,
    # Attendance models
    AttendanceSession, Attendance, AttendanceSettings,
    # Grades models
    ExamType, Exam, GradingScale, GradeRange, StudentMark, MarkAuditLog,
)


@admin.register(GradeType)
class GradeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'number', 'short_name', 'category', 'display_order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'short_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['display_order', 'number']
    fieldsets = (
        (None, {
            'fields': ('number', 'name', 'short_name', 'category')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current', 'is_active']
    list_filter = ['is_current', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'number', 'academic_year', 'is_active', 'created_at']
    list_filter = ['academic_year', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['academic_year', 'number']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'grade', 'class_teacher', 'capacity', 'current_strength', 'academic_year', 'is_active']
    list_filter = ['grade', 'academic_year', 'is_active']
    search_fields = ['name', 'grade__name', 'room_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['grade', 'name']


class StudentParentInline(admin.TabularInline):
    model = StudentParent
    extra = 1
    fields = ['parent', 'is_primary']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'admission_number', 'section_name', 'status', 'admission_date']
    list_filter = ['status', 'gender', 'current_section__grade', 'current_section']
    search_fields = ['first_name', 'last_name', 'admission_number', 'email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'admission_date'
    inlines = [StudentParentInline]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'

    def section_name(self, obj):
        return obj.current_section.full_name if obj.current_section else '-'
    section_name.short_description = 'Section'


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'relation', 'email', 'phone', 'is_primary_contact', 'is_active']
    list_filter = ['relation', 'is_primary_contact', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'


@admin.register(StudentParent)
class StudentParentAdmin(admin.ModelAdmin):
    list_display = ['student', 'parent', 'is_primary', 'created_at']
    list_filter = ['is_primary']
    search_fields = ['student__first_name', 'student__last_name', 'parent__first_name', 'parent__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['subject', 'section', 'teacher', 'academic_year', 'is_active']
    list_filter = ['is_active', 'academic_year']
    search_fields = ['subject__name', 'section__name', 'teacher__user__first_name']
    readonly_fields = ['created_at', 'updated_at']


# =============================================================================
# ATTENDANCE ADMIN
# =============================================================================

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'start_time', 'end_time', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['display_order', 'name']


@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = ['low_attendance_threshold', 'allow_backdated_entry', 'max_backdated_days', 'notify_parents_on_absent']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'section', 'date', 'session', 'status', 'marked_by']
    list_filter = ['status', 'date', 'section', 'session']
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date', 'student__roll_number']


# =============================================================================
# GRADES / EXAM ADMIN
# =============================================================================

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'default_max_marks', 'weightage', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['display_order', 'name']


class GradeRangeInline(admin.TabularInline):
    model = GradeRange
    extra = 1
    fields = ['grade', 'min_percentage', 'max_percentage', 'grade_point', 'description']


@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [GradeRangeInline]


@admin.register(GradeRange)
class GradeRangeAdmin(admin.ModelAdmin):
    list_display = ['grading_scale', 'grade', 'min_percentage', 'max_percentage', 'grade_point']
    list_filter = ['grading_scale']
    search_fields = ['grade', 'description']
    ordering = ['grading_scale', '-min_percentage']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'exam_type', 'section', 'subject', 'academic_year', 'max_marks', 'is_published', 'is_locked']
    list_filter = ['exam_type', 'academic_year', 'is_published', 'is_locked', 'is_active']
    search_fields = ['name', 'section__name', 'subject__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'exam_date'


@admin.register(StudentMark)
class StudentMarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'marks_obtained', 'percentage', 'grade', 'is_absent', 'entered_by']
    list_filter = ['exam__exam_type', 'is_absent', 'grade']
    search_fields = ['student__first_name', 'student__last_name', 'exam__name']
    readonly_fields = ['percentage', 'grade', 'created_at', 'updated_at']


@admin.register(MarkAuditLog)
class MarkAuditLogAdmin(admin.ModelAdmin):
    list_display = ['student_mark', 'old_marks', 'new_marks', 'old_grade', 'new_grade', 'changed_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['student_mark__student__first_name', 'student_mark__student__last_name', 'reason']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
