"""Django Admin for Communications App"""

from django.contrib import admin
from .models import News, Event, Announcement, Notification


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'author', 'published_date', 'is_published', 'is_featured', 'views_count']
    list_filter = ['is_published', 'is_featured', 'school', 'organization']
    search_fields = ['title', 'slug', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'views_count']
    date_hierarchy = 'published_date'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'event_type', 'start_date', 'end_date', 'is_published', 'is_featured']
    list_filter = ['event_type', 'is_published', 'is_featured', 'school', 'organization']
    search_fields = ['title', 'slug', 'description', 'location']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'school', 'priority', 'created_by', 'is_published', 'published_date', 'expiry_date']
    list_filter = ['priority', 'is_published', 'school', 'organization']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'published_date'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'organization']
    search_fields = ['title', 'message', 'user__user__first_name', 'user__user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    date_hierarchy = 'created_at'
