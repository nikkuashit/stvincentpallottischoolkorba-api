"""Django Admin for Accounts App"""

from django.contrib import admin
from .models import Role, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'slug', 'is_system_role', 'is_active', 'created_at']
    list_filter = ['is_system_role', 'is_active', 'organization']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_full_name', 'organization', 'school', 'role', 'employee_id', 'is_active', 'created_at']
    list_filter = ['is_active', 'role', 'gender', 'organization', 'school']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'employee_id', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'last_login_at']

    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'User'
