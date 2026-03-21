"""Django Admin for Transport App"""

from django.contrib import admin
from .models import (
    AttendanceLocation,
    Vehicle,
    Driver,
    BusStop,
    Route,
    RouteStop,
    StudentStopAssignment,
    Trip,
    TripStopLog,
    StudentBoardingLog,
)


@admin.register(AttendanceLocation)
class AttendanceLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'radius_meters', 'is_primary', 'is_active']
    list_filter = ['is_primary', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-is_primary', 'name']

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'radius_meters')
        }),
        ('Status', {
            'fields': ('is_primary', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_number', 'vehicle_type', 'seating_capacity', 'status', 'is_gps_enabled', 'is_active']
    list_filter = ['vehicle_type', 'status', 'is_gps_enabled', 'is_active']
    search_fields = ['vehicle_number', 'model', 'make']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'insurance_expiry'
    ordering = ['vehicle_number']

    fieldsets = (
        (None, {
            'fields': ('vehicle_number', 'vehicle_type')
        }),
        ('Vehicle Details', {
            'fields': ('make', 'model', 'year_of_manufacture', 'seating_capacity')
        }),
        ('Compliance', {
            'fields': ('registration_expiry', 'insurance_expiry', 'fitness_expiry', 'pollution_expiry')
        }),
        ('Tracking', {
            'fields': ('is_gps_enabled', 'gps_device_id')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'role', 'assigned_vehicle', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone', 'license_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'license_expiry'
    ordering = ['first_name', 'last_name']

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'

    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'phone', 'email')
        }),
        ('Role & Assignment', {
            'fields': ('role', 'assigned_vehicle')
        }),
        ('License', {
            'fields': ('license_number', 'license_expiry')
        }),
        ('Address', {
            'fields': ('address',),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BusStop)
class BusStopAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'stop_type', 'latitude', 'longitude', 'max_students', 'is_active']
    list_filter = ['stop_type', 'is_active']
    search_fields = ['name', 'code', 'address', 'landmark']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'stop_type')
        }),
        ('Location', {
            'fields': ('address', 'landmark', 'latitude', 'longitude')
        }),
        ('Capacity', {
            'fields': ('max_students',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = ['bus_stop', 'sequence', 'pickup_time', 'drop_time', 'distance_from_previous']
    ordering = ['sequence']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'route_type', 'vehicle', 'driver', 'pickup_start_time', 'is_active']
    list_filter = ['route_type', 'is_active']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    inlines = [RouteStopInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'route_type')
        }),
        ('Assignment', {
            'fields': ('vehicle', 'driver', 'helper')
        }),
        ('Schedule', {
            'fields': ('pickup_start_time', 'drop_start_time')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['route', 'bus_stop', 'sequence', 'pickup_time', 'drop_time']
    list_filter = ['route']
    search_fields = ['route__name', 'bus_stop__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['route', 'sequence']


@admin.register(StudentStopAssignment)
class StudentStopAssignmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'pickup_stop', 'pickup_route', 'drop_stop', 'drop_route', 'academic_year', 'is_active']
    list_filter = ['is_active', 'academic_year', 'pickup_route', 'drop_route']
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['student', 'pickup_stop', 'drop_stop', 'pickup_route', 'drop_route']

    fieldsets = (
        (None, {
            'fields': ('student', 'academic_year')
        }),
        ('Pickup Assignment', {
            'fields': ('pickup_stop', 'pickup_route')
        }),
        ('Drop Assignment', {
            'fields': ('drop_stop', 'drop_route')
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['route', 'date', 'trip_type', 'status', 'driver', 'vehicle', 'start_time', 'end_time']
    list_filter = ['trip_type', 'status', 'date']
    search_fields = ['route__name', 'driver__first_name', 'driver__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date', '-start_time']

    fieldsets = (
        (None, {
            'fields': ('route', 'date', 'trip_type')
        }),
        ('Assignment', {
            'fields': ('driver', 'helper', 'vehicle')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Current Location', {
            'fields': ('current_latitude', 'current_longitude', 'last_location_update'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Odometer', {
            'fields': ('start_odometer', 'end_odometer'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TripStopLog)
class TripStopLogAdmin(admin.ModelAdmin):
    list_display = ['trip', 'route_stop', 'arrival_time', 'departure_time', 'passengers_boarded', 'passengers_alighted']
    list_filter = ['trip__date']
    search_fields = ['trip__route__name', 'route_stop__bus_stop__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-trip__date', 'arrival_time']


@admin.register(StudentBoardingLog)
class StudentBoardingLogAdmin(admin.ModelAdmin):
    list_display = ['trip', 'student', 'boarding_status', 'boarding_stop', 'boarding_time']
    list_filter = ['boarding_status', 'trip__date']
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'trip__date'
    ordering = ['-trip__date', 'boarding_time']
