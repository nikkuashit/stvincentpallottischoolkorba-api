"""
Transport Management Models

Simplified without multi-tenancy.
This module implements models for school transport management including:
- Vehicles (buses)
- Drivers and helpers
- Bus stops/nodal points
- Routes and route planning
- Student-stop assignments
- Trip tracking
- Geofence configurations for attendance
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


# ==============================================================================
# BASE MODEL
# ==============================================================================

class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ==============================================================================
# GEOFENCE CONFIGURATION
# ==============================================================================

class AttendanceLocation(TimeStampedModel):
    """
    Geofence location for staff attendance check-in.
    Admin can configure multiple attendance check-in zones.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, help_text="Location name (e.g., 'Main Campus', 'Sports Ground')")
    description = models.TextField(blank=True)

    # Geolocation
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="Latitude coordinate"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text="Longitude coordinate"
    )
    radius_meters = models.PositiveIntegerField(
        default=500,
        validators=[MinValueValidator(50), MaxValueValidator(5000)],
        help_text="Geofence radius in meters (50-5000)"
    )

    # Configuration
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary location used as default for attendance"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Attendance Location")
        verbose_name_plural = _("Attendance Locations")
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"

    def save(self, *args, **kwargs):
        # Ensure only one primary location
        if self.is_primary:
            AttendanceLocation.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


# ==============================================================================
# VEHICLE MANAGEMENT
# ==============================================================================

class Vehicle(TimeStampedModel):
    """School vehicle (bus) management"""

    VEHICLE_TYPE_CHOICES = [
        ('bus', 'Bus'),
        ('mini_bus', 'Mini Bus'),
        ('van', 'Van'),
        ('tempo', 'Tempo Traveller'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
        ('inactive', 'Inactive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    vehicle_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Vehicle registration number"
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        default='bus'
    )

    # Vehicle details
    make = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    year_of_manufacture = models.PositiveIntegerField(null=True, blank=True)
    seating_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    # Compliance dates
    registration_expiry = models.DateField(null=True, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    fitness_expiry = models.DateField(null=True, blank=True)
    pollution_expiry = models.DateField(null=True, blank=True)

    # GPS tracking
    is_gps_enabled = models.BooleanField(default=False)
    gps_device_id = models.CharField(max_length=100, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        ordering = ['vehicle_number']

    def __str__(self):
        return f"{self.vehicle_number} ({self.get_vehicle_type_display()})"


# ==============================================================================
# DRIVER MANAGEMENT
# ==============================================================================

class Driver(TimeStampedModel):
    """Driver and helper management"""

    ROLE_CHOICES = [
        ('driver', 'Driver'),
        ('helper', 'Helper/Attendant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Role and assignment
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='driver')
    assigned_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_personnel'
    )

    # License info (for drivers)
    license_number = models.CharField(max_length=50, blank=True)
    license_expiry = models.DateField(null=True, blank=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Driver")
        verbose_name_plural = _("Drivers")
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"


# ==============================================================================
# BUS STOPS / NODAL POINTS
# ==============================================================================

class BusStop(TimeStampedModel):
    """Bus stop / pickup-drop nodal points"""

    STOP_TYPE_CHOICES = [
        ('pickup', 'Pickup Only'),
        ('drop', 'Drop Only'),
        ('both', 'Pickup & Drop'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, help_text="Stop name")
    code = models.CharField(max_length=20, unique=True, help_text="Unique stop code (e.g., ST01)")
    address = models.TextField(blank=True)
    landmark = models.CharField(max_length=200, blank=True)

    # Geolocation
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        null=True,
        blank=True
    )

    stop_type = models.CharField(max_length=10, choices=STOP_TYPE_CHOICES, default='both')
    max_students = models.PositiveIntegerField(default=50, help_text="Maximum students at this stop")

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Bus Stop")
        verbose_name_plural = _("Bus Stops")
        ordering = ['name']

    def __str__(self):
        return f"{self.code}: {self.name}"


# ==============================================================================
# ROUTES
# ==============================================================================

class Route(TimeStampedModel):
    """Bus route definition"""

    ROUTE_TYPE_CHOICES = [
        ('pickup', 'Pickup Route'),
        ('drop', 'Drop Route'),
        ('both', 'Pickup & Drop Route'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, help_text="Route name (e.g., 'Route 1 - North')")
    code = models.CharField(max_length=20, unique=True, help_text="Unique route code")
    description = models.TextField(blank=True)

    route_type = models.CharField(max_length=10, choices=ROUTE_TYPE_CHOICES, default='both')

    # Assignment
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='routes'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='routes_as_driver',
        limit_choices_to={'role': 'driver'}
    )
    helper = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='routes_as_helper',
        limit_choices_to={'role': 'helper'}
    )

    # Schedule
    pickup_start_time = models.TimeField(null=True, blank=True, help_text="Pickup route start time")
    drop_start_time = models.TimeField(null=True, blank=True, help_text="Drop route start time")

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Route")
        verbose_name_plural = _("Routes")
        ordering = ['name']

    def __str__(self):
        return f"{self.code}: {self.name}"


class RouteStop(TimeStampedModel):
    """Junction table connecting Route and BusStop with sequence"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_stops')
    bus_stop = models.ForeignKey(BusStop, on_delete=models.CASCADE, related_name='stop_routes')

    sequence = models.PositiveIntegerField(help_text="Order of this stop in the route")

    # Timing
    pickup_time = models.TimeField(null=True, blank=True, help_text="Expected pickup time")
    drop_time = models.TimeField(null=True, blank=True, help_text="Expected drop time")

    # Distance from previous stop (optional, for route optimization)
    distance_from_previous = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distance from previous stop in km"
    )

    class Meta:
        verbose_name = _("Route Stop")
        verbose_name_plural = _("Route Stops")
        ordering = ['route', 'sequence']
        unique_together = [['route', 'bus_stop'], ['route', 'sequence']]

    def __str__(self):
        return f"{self.route.name} - Stop {self.sequence}: {self.bus_stop.name}"


# ==============================================================================
# STUDENT ASSIGNMENTS
# ==============================================================================

class StudentStopAssignment(TimeStampedModel):
    """Assignment of students to bus stops for pickup/drop"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='transport_assignments'
    )
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.CASCADE,
        related_name='transport_assignments'
    )

    # Pickup assignment
    pickup_stop = models.ForeignKey(
        BusStop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pickup_students'
    )
    pickup_route = models.ForeignKey(
        Route,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pickup_students'
    )

    # Drop assignment (can be different from pickup)
    drop_stop = models.ForeignKey(
        BusStop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drop_students'
    )
    drop_route = models.ForeignKey(
        Route,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drop_students'
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Student Stop Assignment")
        verbose_name_plural = _("Student Stop Assignments")
        unique_together = [['student', 'academic_year']]

    def __str__(self):
        return f"{self.student} - {self.pickup_stop or 'No pickup'}"


# ==============================================================================
# TRIP TRACKING
# ==============================================================================

class Trip(TimeStampedModel):
    """Daily trip records for tracking"""

    TRIP_TYPE_CHOICES = [
        ('pickup', 'Pickup'),
        ('drop', 'Drop'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trips')
    date = models.DateField()
    trip_type = models.CharField(max_length=10, choices=TRIP_TYPE_CHOICES)

    # Assignment (can override route defaults)
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips'
    )
    helper = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips_as_helper'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips'
    )

    # Timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # Odometer readings
    start_odometer = models.PositiveIntegerField(null=True, blank=True)
    end_odometer = models.PositiveIntegerField(null=True, blank=True)

    # Real-time tracking
    current_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Trip")
        verbose_name_plural = _("Trips")
        ordering = ['-date', 'trip_type']
        unique_together = [['route', 'date', 'trip_type']]

    def __str__(self):
        return f"{self.route.name} - {self.date} ({self.get_trip_type_display()})"


class TripStopLog(TimeStampedModel):
    """Log of when a bus arrives/departs each stop during a trip"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='trip_stop_logs')
    route_stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE, related_name='trip_logs')

    arrival_time = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)

    # GPS coordinates at arrival
    arrival_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    arrival_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Student counts
    passengers_boarded = models.PositiveIntegerField(default=0)
    passengers_alighted = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Trip Stop Log")
        verbose_name_plural = _("Trip Stop Logs")
        ordering = ['trip', 'arrival_time']
        unique_together = [['trip', 'route_stop']]

    def __str__(self):
        return f"{self.trip} - {self.route_stop.bus_stop.name}"


class StudentBoardingLog(TimeStampedModel):
    """Log of student boarding/alighting during trips"""

    BOARDING_STATUS_CHOICES = [
        ('boarded', 'Boarded'),
        ('alighted', 'Alighted'),
        ('absent', 'Absent'),
        ('not_applicable', 'Not Applicable'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='student_boarding_logs')
    student = models.ForeignKey(
        'academics.Student',
        on_delete=models.CASCADE,
        related_name='boarding_logs'
    )

    boarding_status = models.CharField(max_length=20, choices=BOARDING_STATUS_CHOICES)
    boarding_stop = models.ForeignKey(
        RouteStop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='boarding_logs'
    )
    boarding_time = models.DateTimeField(null=True, blank=True)

    # GPS at boarding
    boarding_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    boarding_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Marked by (driver/helper)
    marked_by = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_boardings'
    )

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Student Boarding Log")
        verbose_name_plural = _("Student Boarding Logs")
        ordering = ['trip', 'boarding_time']
        unique_together = [['trip', 'student']]

    def __str__(self):
        return f"{self.trip} - {self.student} ({self.get_boarding_status_display()})"
