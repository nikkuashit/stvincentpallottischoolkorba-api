"""
Admin configuration for Accounts App
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = BaseUserAdmin.list_filter + ('profile__role',)
    search_fields = BaseUserAdmin.search_fields + ('profile__phone', 'profile__employee_id')

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return '-'
    get_role.short_description = 'Role'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model"""
    list_display = ('user', 'role', 'phone', 'created_at')
    list_filter = ('role', 'gender')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone', 'employee_id')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('User', {
            'fields': ('user', 'role')
        }),
        ('Personal Information', {
            'fields': ('phone', 'date_of_birth', 'gender', 'avatar', 'bio')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Role-specific', {
            'fields': ('employee_id', 'department', 'designation', 'admission_no', 'roll_no'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
