"""ViewSets for Transport App - Vehicles, Drivers, Routes, Bus Stops"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from cms.permissions import IsAdminOrStaffOrReadOnly
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
from .serializers import (
    AttendanceLocationSerializer, AttendanceLocationListSerializer,
    VehicleSerializer, VehicleListSerializer,
    DriverSerializer, DriverListSerializer,
    BusStopSerializer, BusStopListSerializer,
    RouteSerializer, RouteListSerializer, RouteStopSerializer,
    StudentStopAssignmentSerializer, StudentStopAssignmentListSerializer,
    TripSerializer, TripListSerializer,
    TripStopLogSerializer, StudentBoardingLogSerializer,
)


class AttendanceLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AttendanceLocation (geofence configuration)
    Admin/Staff only for all operations
    """
    queryset = AttendanceLocation.objects.all()
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'is_primary', 'created_at']
    ordering = ['-is_primary', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return AttendanceLocationListSerializer
        return AttendanceLocationSerializer

    def get_queryset(self):
        """Filter by active status"""
        queryset = super().get_queryset()

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by is_primary
        is_primary = self.request.query_params.get('is_primary', None)
        if is_primary is not None:
            queryset = queryset.filter(is_primary=is_primary.lower() == 'true')

        return queryset

    @action(detail=False, methods=['get'])
    def primary(self, request):
        """Get the primary attendance location"""
        queryset = self.get_queryset().filter(is_primary=True, is_active=True)
        location = queryset.first()
        if location:
            serializer = AttendanceLocationSerializer(location)
            return Response(serializer.data)
        return Response({'detail': 'No primary location found'}, status=status.HTTP_404_NOT_FOUND)


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Vehicle management
    Admin/Staff only for all operations
    """
    queryset = Vehicle.objects.all()
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['vehicle_number', 'make', 'model']
    ordering_fields = ['vehicle_number', 'vehicle_type', 'status', 'created_at']
    ordering = ['vehicle_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer

    def get_queryset(self):
        """Filter vehicles based on query parameters"""
        queryset = super().get_queryset()

        # Filter by vehicle_type
        vehicle_type = self.request.query_params.get('vehicle_type', None)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)

        # Filter by status
        vehicle_status = self.request.query_params.get('status', None)
        if vehicle_status:
            queryset = queryset.filter(status=vehicle_status)

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset


class DriverViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Driver management
    Admin/Staff only for all operations
    """
    queryset = Driver.objects.all()
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'phone', 'license_number']
    ordering_fields = ['first_name', 'last_name', 'role', 'created_at']
    ordering = ['first_name', 'last_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return DriverListSerializer
        return DriverSerializer

    def get_queryset(self):
        """Filter drivers based on query parameters"""
        queryset = super().get_queryset()

        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by assigned_vehicle
        has_vehicle = self.request.query_params.get('has_vehicle', None)
        if has_vehicle is not None:
            if has_vehicle.lower() == 'true':
                queryset = queryset.filter(assigned_vehicle__isnull=False)
            else:
                queryset = queryset.filter(assigned_vehicle__isnull=True)

        return queryset


class BusStopViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BusStop (pickup/drop nodal points)
    Admin/Staff only for all operations
    """
    queryset = BusStop.objects.all()
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'address', 'landmark']
    ordering_fields = ['name', 'code', 'stop_type', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return BusStopListSerializer
        return BusStopSerializer

    def get_queryset(self):
        """Filter bus stops based on query parameters"""
        queryset = super().get_queryset()

        # Filter by stop_type
        stop_type = self.request.query_params.get('stop_type', None)
        if stop_type:
            queryset = queryset.filter(stop_type=stop_type)

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset


class RouteStopViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RouteStop (route-stop junction)
    Admin/Staff only for all operations
    """
    queryset = RouteStop.objects.all()
    serializer_class = RouteStopSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['sequence', 'created_at']
    ordering = ['route', 'sequence']

    def get_queryset(self):
        """Filter route stops based on query parameters"""
        queryset = super().get_queryset()

        # Filter by route
        route = self.request.query_params.get('route', None)
        if route:
            queryset = queryset.filter(route_id=route)

        # Filter by bus_stop
        bus_stop = self.request.query_params.get('bus_stop', None)
        if bus_stop:
            queryset = queryset.filter(bus_stop_id=bus_stop)

        return queryset


class RouteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Route management
    Admin/Staff only for all operations
    """
    queryset = Route.objects.all()
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'route_type', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return RouteListSerializer
        return RouteSerializer

    def get_queryset(self):
        """Filter routes based on query parameters"""
        queryset = super().get_queryset().prefetch_related('route_stops', 'route_stops__bus_stop')

        # Filter by route_type
        route_type = self.request.query_params.get('route_type', None)
        if route_type:
            queryset = queryset.filter(route_type=route_type)

        # Filter by vehicle
        vehicle = self.request.query_params.get('vehicle', None)
        if vehicle:
            queryset = queryset.filter(vehicle_id=vehicle)

        # Filter by driver
        driver = self.request.query_params.get('driver', None)
        if driver:
            queryset = queryset.filter(driver_id=driver)

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset


class StudentStopAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentStopAssignment
    Admin/Staff only for all operations
    """
    queryset = StudentStopAssignment.objects.all()
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']
    ordering_fields = ['student__first_name', 'created_at']
    ordering = ['student__first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentStopAssignmentListSerializer
        return StudentStopAssignmentSerializer

    def get_queryset(self):
        """Filter assignments based on query parameters"""
        queryset = super().get_queryset().select_related(
            'student', 'pickup_stop', 'pickup_route', 'drop_stop', 'drop_route', 'academic_year'
        )

        # Filter by student
        student = self.request.query_params.get('student', None)
        if student:
            queryset = queryset.filter(student_id=student)

        # Filter by pickup_stop
        pickup_stop = self.request.query_params.get('pickup_stop', None)
        if pickup_stop:
            queryset = queryset.filter(pickup_stop_id=pickup_stop)

        # Filter by pickup_route
        pickup_route = self.request.query_params.get('pickup_route', None)
        if pickup_route:
            queryset = queryset.filter(pickup_route_id=pickup_route)

        # Filter by academic_year
        academic_year = self.request.query_params.get('academic_year', None)
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset


class TripViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Trip tracking
    Admin/Staff only for all operations
    """
    queryset = Trip.objects.all()
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['route__name', 'notes']
    ordering_fields = ['date', 'start_time', 'status', 'created_at']
    ordering = ['-date', '-start_time']

    def get_serializer_class(self):
        if self.action == 'list':
            return TripListSerializer
        return TripSerializer

    def get_queryset(self):
        """Filter trips based on query parameters"""
        queryset = super().get_queryset().select_related(
            'route', 'vehicle', 'driver', 'helper'
        ).prefetch_related('trip_stop_logs', 'student_boarding_logs')

        # Filter by route
        route = self.request.query_params.get('route', None)
        if route:
            queryset = queryset.filter(route_id=route)

        # Filter by date
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)

        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Filter by trip_type
        trip_type = self.request.query_params.get('trip_type', None)
        if trip_type:
            queryset = queryset.filter(trip_type=trip_type)

        # Filter by status
        trip_status = self.request.query_params.get('status', None)
        if trip_status:
            queryset = queryset.filter(status=trip_status)

        # Filter by driver
        driver = self.request.query_params.get('driver', None)
        if driver:
            queryset = queryset.filter(driver_id=driver)

        # Filter by vehicle
        vehicle = self.request.query_params.get('vehicle', None)
        if vehicle:
            queryset = queryset.filter(vehicle_id=vehicle)

        return queryset

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        """Update trip's current location"""
        trip = self.get_object()
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if latitude is None or longitude is None:
            return Response(
                {'detail': 'latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone
        trip.current_latitude = latitude
        trip.current_longitude = longitude
        trip.last_location_update = timezone.now()
        trip.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])

        return Response({'status': 'location updated'})


class TripStopLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TripStopLog
    Admin/Staff only for all operations
    """
    queryset = TripStopLog.objects.all()
    serializer_class = TripStopLogSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['arrival_time', 'created_at']
    ordering = ['arrival_time']

    def get_queryset(self):
        """Filter trip stop logs based on query parameters"""
        queryset = super().get_queryset().select_related('trip', 'route_stop', 'route_stop__bus_stop')

        # Filter by trip
        trip = self.request.query_params.get('trip', None)
        if trip:
            queryset = queryset.filter(trip_id=trip)

        return queryset


class StudentBoardingLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentBoardingLog
    Admin/Staff only for all operations
    """
    queryset = StudentBoardingLog.objects.all()
    serializer_class = StudentBoardingLogSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__first_name', 'student__last_name']
    ordering_fields = ['boarding_time', 'created_at']
    ordering = ['boarding_time']

    def get_queryset(self):
        """Filter student boarding logs based on query parameters"""
        queryset = super().get_queryset().select_related(
            'trip', 'student', 'boarding_stop', 'boarding_stop__bus_stop', 'marked_by'
        )

        # Filter by trip
        trip = self.request.query_params.get('trip', None)
        if trip:
            queryset = queryset.filter(trip_id=trip)

        # Filter by student
        student = self.request.query_params.get('student', None)
        if student:
            queryset = queryset.filter(student_id=student)

        # Filter by boarding_status
        boarding_status = self.request.query_params.get('boarding_status', None)
        if boarding_status:
            queryset = queryset.filter(boarding_status=boarding_status)

        return queryset
