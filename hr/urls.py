"""
HR URL Configuration

API endpoints for HR management:
- /api/hr/departments/
- /api/hr/designations/
- /api/hr/employees/
- /api/hr/leave-types/
- /api/hr/leave-policies/
- /api/hr/leave-balances/
- /api/hr/leave-requests/
- /api/hr/holidays/
- /api/hr/audit-logs/
- /api/hr/staff-attendance/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet,
    DesignationViewSet,
    EmployeeProfileViewSet,
    LeaveTypeViewSet,
    LeavePolicyViewSet,
    LeaveBalanceViewSet,
    LeaveRequestViewSet,
    LeaveBalanceAuditLogViewSet,
    HolidayViewSet,
    StaffAttendanceViewSet,
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'designations', DesignationViewSet, basename='designation')
router.register(r'employees', EmployeeProfileViewSet, basename='employee')
router.register(r'leave-types', LeaveTypeViewSet, basename='leave-type')
router.register(r'leave-policies', LeavePolicyViewSet, basename='leave-policy')
router.register(r'leave-balances', LeaveBalanceViewSet, basename='leave-balance')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'audit-logs', LeaveBalanceAuditLogViewSet, basename='audit-log')
router.register(r'staff-attendance', StaffAttendanceViewSet, basename='staff-attendance')

urlpatterns = [
    path('', include(router.urls)),
]
