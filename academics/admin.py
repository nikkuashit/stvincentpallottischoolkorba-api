"""Django Admin for Academics App"""

from django.contrib import admin
from .models import AcademicYear, Class, Student, Parent, StudentParent, Subject, Course


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'start_date', 'end_date', 'is_current', 'is_active']
    list_filter = ['is_current', 'is_active', 'school', 'organization']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'grade', 'section', 'class_teacher', 'room_number', 'capacity', 'is_active']
    list_filter = ['grade', 'is_active', 'school', 'organization']
    search_fields = ['name', 'section', 'room_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['school', 'grade', 'section']


class StudentParentInline(admin.TabularInline):
    model = StudentParent
    extra = 1
    fields = ['parent', 'is_primary']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'admission_number', 'school', 'current_class', 'status', 'admission_date']
    list_filter = ['status', 'gender', 'school', 'current_class', 'organization']
    search_fields = ['first_name', 'last_name', 'admission_number', 'email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'admission_date'
    inlines = [StudentParentInline]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'relation', 'school', 'email', 'phone', 'is_primary_contact', 'is_active']
    list_filter = ['relation', 'is_primary_contact', 'is_active', 'school', 'organization']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'


@admin.register(StudentParent)
class StudentParentAdmin(admin.ModelAdmin):
    list_display = ['student', 'parent', 'is_primary', 'organization', 'created_at']
    list_filter = ['is_primary', 'organization']
    search_fields = ['student__first_name', 'student__last_name', 'parent__first_name', 'parent__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'school', 'is_active', 'created_at']
    list_filter = ['is_active', 'school', 'organization']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['subject', 'class_assigned', 'teacher', 'academic_year', 'school', 'is_active']
    list_filter = ['is_active', 'academic_year', 'school', 'organization']
    search_fields = ['subject__name', 'class_assigned__name', 'teacher__user__first_name']
    readonly_fields = ['created_at', 'updated_at']
