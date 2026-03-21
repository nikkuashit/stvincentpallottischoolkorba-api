"""
Serializers for Transport App - Vehicles, Drivers, Routes, Bus Stops
"""

from rest_framework import serializers
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


# =============================================================================
# ATTENDANCE LOCATION (GEOFENCE) SERIALIZERS
# =============================================================================

class AttendanceLocationSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceLocation (geofence) model"""

    class Meta:
        model = AttendanceLocation
        fields = [
            'id', 'name', 'description',
            'latitude', 'longitude', 'radius_meters',
            'is_primary', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceLocationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing attendance locations"""

    class Meta:
        model = AttendanceLocation
        fields = [
            'id', 'name', 'latitude', 'longitude', 'radius_meters',
            'is_primary', 'is_active'
        ]


# =============================================================================
# VEHICLE SERIALIZERS
# =============================================================================

class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for Vehicle model"""

    class Meta:
        model = Vehicle
        fields = [
            'id', 'vehicle_number', 'vehicle_type',
            'make', 'model', 'year_of_manufacture', 'seating_capacity',
            'registration_expiry', 'insurance_expiry', 'fitness_expiry', 'pollution_expiry',
            'is_gps_enabled', 'gps_device_id', 'status', 'is_active', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing vehicles"""

    class Meta:
        model = Vehicle
        fields = [
            'id', 'vehicle_number', 'vehicle_type', 'make', 'model',
            'seating_capacity', 'status', 'is_active'
        ]


# =============================================================================
# DRIVER SERIALIZERS
# =============================================================================

class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver model"""
    full_name = serializers.SerializerMethodField()
    assigned_vehicle_number = serializers.CharField(
        source='assigned_vehicle.vehicle_number', read_only=True
    )

    class Meta:
        model = Driver
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'phone', 'email', 'address', 'role', 'license_number', 'license_expiry',
            'assigned_vehicle', 'assigned_vehicle_number',
            'emergency_contact_name', 'emergency_contact_phone',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class DriverListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing drivers"""
    full_name = serializers.SerializerMethodField()
    assigned_vehicle_number = serializers.CharField(
        source='assigned_vehicle.vehicle_number', read_only=True
    )

    class Meta:
        model = Driver
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'phone', 'role',
            'assigned_vehicle', 'assigned_vehicle_number', 'is_active'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


# =============================================================================
# BUS STOP SERIALIZERS
# =============================================================================

class BusStopSerializer(serializers.ModelSerializer):
    """Serializer for BusStop model"""

    class Meta:
        model = BusStop
        fields = [
            'id', 'name', 'code', 'address', 'landmark',
            'latitude', 'longitude', 'stop_type', 'max_students',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BusStopListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing bus stops"""

    class Meta:
        model = BusStop
        fields = [
            'id', 'name', 'code', 'stop_type', 'latitude', 'longitude',
            'max_students', 'is_active'
        ]


# =============================================================================
# ROUTE SERIALIZERS
# =============================================================================

class RouteStopSerializer(serializers.ModelSerializer):
    """Serializer for RouteStop junction table"""
    bus_stop_name = serializers.CharField(source='bus_stop.name', read_only=True)
    bus_stop_code = serializers.CharField(source='bus_stop.code', read_only=True)
    bus_stop_latitude = serializers.DecimalField(
        source='bus_stop.latitude', max_digits=10, decimal_places=7, read_only=True
    )
    bus_stop_longitude = serializers.DecimalField(
        source='bus_stop.longitude', max_digits=10, decimal_places=7, read_only=True
    )

    class Meta:
        model = RouteStop
        fields = [
            'id', 'route', 'bus_stop', 'bus_stop_name', 'bus_stop_code',
            'bus_stop_latitude', 'bus_stop_longitude',
            'sequence', 'pickup_time', 'drop_time', 'distance_from_previous',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model"""
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)
    driver_name = serializers.SerializerMethodField()
    helper_name = serializers.SerializerMethodField()
    stops = RouteStopSerializer(source='route_stops', many=True, read_only=True)
    stop_count = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = [
            'id', 'name', 'code', 'description',
            'route_type', 'vehicle', 'vehicle_number',
            'driver', 'driver_name', 'helper', 'helper_name',
            'pickup_start_time', 'drop_start_time',
            'stops', 'stop_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_driver_name(self, obj):
        if obj.driver:
            return f"{obj.driver.first_name} {obj.driver.last_name}"
        return None

    def get_helper_name(self, obj):
        if obj.helper:
            return f"{obj.helper.first_name} {obj.helper.last_name}"
        return None

    def get_stop_count(self, obj):
        return obj.route_stops.count()


class RouteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing routes"""
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)
    driver_name = serializers.SerializerMethodField()
    stop_count = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = [
            'id', 'name', 'code', 'route_type', 'vehicle', 'vehicle_number',
            'driver', 'driver_name', 'pickup_start_time', 'drop_start_time',
            'stop_count', 'is_active'
        ]

    def get_driver_name(self, obj):
        if obj.driver:
            return f"{obj.driver.first_name} {obj.driver.last_name}"
        return None

    def get_stop_count(self, obj):
        return obj.route_stops.count()


# =============================================================================
# STUDENT STOP ASSIGNMENT SERIALIZERS
# =============================================================================

class StudentStopAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for StudentStopAssignment model"""
    student_name = serializers.SerializerMethodField()
    student_admission_number = serializers.CharField(
        source='student.admission_number', read_only=True
    )
    pickup_stop_name = serializers.CharField(source='pickup_stop.name', read_only=True)
    pickup_route_name = serializers.CharField(source='pickup_route.name', read_only=True)
    drop_stop_name = serializers.CharField(source='drop_stop.name', read_only=True)
    drop_route_name = serializers.CharField(source='drop_route.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)

    class Meta:
        model = StudentStopAssignment
        fields = [
            'id', 'student', 'student_name', 'student_admission_number',
            'pickup_stop', 'pickup_stop_name', 'pickup_route', 'pickup_route_name',
            'drop_stop', 'drop_stop_name', 'drop_route', 'drop_route_name',
            'academic_year', 'academic_year_name',
            'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class StudentStopAssignmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing student stop assignments"""
    student_name = serializers.SerializerMethodField()
    pickup_stop_name = serializers.CharField(source='pickup_stop.name', read_only=True)
    drop_stop_name = serializers.CharField(source='drop_stop.name', read_only=True)

    class Meta:
        model = StudentStopAssignment
        fields = [
            'id', 'student', 'student_name',
            'pickup_stop', 'pickup_stop_name',
            'drop_stop', 'drop_stop_name',
            'is_active'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


# =============================================================================
# TRIP SERIALIZERS
# =============================================================================

class TripStopLogSerializer(serializers.ModelSerializer):
    """Serializer for TripStopLog"""
    stop_name = serializers.CharField(source='route_stop.bus_stop.name', read_only=True)
    stop_sequence = serializers.IntegerField(source='route_stop.sequence', read_only=True)

    class Meta:
        model = TripStopLog
        fields = [
            'id', 'trip', 'route_stop', 'stop_name', 'stop_sequence',
            'arrival_time', 'departure_time',
            'arrival_latitude', 'arrival_longitude',
            'passengers_boarded', 'passengers_alighted',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentBoardingLogSerializer(serializers.ModelSerializer):
    """Serializer for StudentBoardingLog"""
    student_name = serializers.SerializerMethodField()
    stop_name = serializers.CharField(source='boarding_stop.bus_stop.name', read_only=True)

    class Meta:
        model = StudentBoardingLog
        fields = [
            'id', 'trip', 'student', 'student_name',
            'boarding_status', 'boarding_stop', 'stop_name',
            'boarding_time', 'boarding_latitude', 'boarding_longitude',
            'marked_by', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class TripSerializer(serializers.ModelSerializer):
    """Serializer for Trip model"""
    route_name = serializers.CharField(source='route.name', read_only=True)
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)
    driver_name = serializers.SerializerMethodField()
    helper_name = serializers.SerializerMethodField()
    stop_logs = TripStopLogSerializer(source='trip_stop_logs', many=True, read_only=True)
    boarding_logs = StudentBoardingLogSerializer(source='student_boarding_logs', many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'route', 'route_name', 'date', 'trip_type',
            'driver', 'driver_name', 'helper', 'helper_name',
            'vehicle', 'vehicle_number',
            'status', 'start_time', 'end_time',
            'start_odometer', 'end_odometer',
            'current_latitude', 'current_longitude', 'last_location_update',
            'notes', 'stop_logs', 'boarding_logs',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_driver_name(self, obj):
        if obj.driver:
            return f"{obj.driver.first_name} {obj.driver.last_name}"
        return None

    def get_helper_name(self, obj):
        if obj.helper:
            return f"{obj.helper.first_name} {obj.helper.last_name}"
        return None


class TripListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing trips"""
    route_name = serializers.CharField(source='route.name', read_only=True)
    vehicle_number = serializers.CharField(source='vehicle.vehicle_number', read_only=True)
    driver_name = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id', 'route', 'route_name', 'date', 'trip_type',
            'driver', 'driver_name', 'vehicle', 'vehicle_number',
            'status', 'start_time', 'end_time'
        ]

    def get_driver_name(self, obj):
        if obj.driver:
            return f"{obj.driver.first_name} {obj.driver.last_name}"
        return None
