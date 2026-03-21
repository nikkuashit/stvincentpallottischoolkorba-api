"""URL routes for Transport App"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttendanceLocationViewSet,
    VehicleViewSet,
    DriverViewSet,
    BusStopViewSet,
    RouteViewSet,
    RouteStopViewSet,
    StudentStopAssignmentViewSet,
    TripViewSet,
    TripStopLogViewSet,
    StudentBoardingLogViewSet,
)

router = DefaultRouter()
router.register(r'attendance-locations', AttendanceLocationViewSet, basename='attendance-location')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'bus-stops', BusStopViewSet, basename='bus-stop')
router.register(r'routes', RouteViewSet, basename='route')
router.register(r'route-stops', RouteStopViewSet, basename='route-stop')
router.register(r'student-assignments', StudentStopAssignmentViewSet, basename='student-assignment')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'trip-stop-logs', TripStopLogViewSet, basename='trip-stop-log')
router.register(r'boarding-logs', StudentBoardingLogViewSet, basename='boarding-log')

urlpatterns = [
    path('', include(router.urls)),
]
