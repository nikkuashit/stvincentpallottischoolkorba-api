"""
HR Views

API ViewSets for HR management:
- Departments and Designations (Admin management)
- Employee Profiles (Admin management with hierarchy view)
- Leave Types, Policies (Admin configuration)
- Leave Balances (Admin management, Staff view)
- Leave Requests (Staff apply, Managers approve)
"""

from decimal import Decimal
from datetime import date
from django.db.models import Sum, Q, Count
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import (
    Department,
    Designation,
    EmployeeProfile,
    LeaveType,
    LeavePolicy,
    LeaveBalance,
    LeaveRequest,
    LeaveApproval,
    LeaveBalanceAuditLog,
    Holiday,
    StaffAttendance,
)
from .serializers import (
    DepartmentSerializer,
    DesignationSerializer,
    EmployeeProfileSerializer,
    EmployeeHierarchySerializer,
    EmployeeCreateSerializer,
    EmployeeMinimalSerializer,
    LeaveTypeSerializer,
    LeavePolicySerializer,
    LeaveBalanceSerializer,
    LeaveBalanceSummarySerializer,
    LeaveBalanceAdjustmentSerializer,
    LeaveRequestSerializer,
    LeaveRequestDetailSerializer,
    LeaveRequestCreateSerializer,
    LeaveApprovalActionSerializer,
    LeaveBalanceAuditLogSerializer,
    HolidaySerializer,
    StaffAttendanceSerializer,
    StaffAttendanceCheckInSerializer,
    StaffAttendanceCheckOutSerializer,
    StaffAttendanceSummarySerializer,
)
import base64
import re


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def decode_base64_photo(photo_data: str) -> bytes:
    """
    Decode base64 photo data, handling data URI format.
    Accepts either raw base64 or data URI (e.g., "data:image/jpeg;base64,...")
    """
    # Strip data URI prefix if present
    if photo_data.startswith('data:'):
        # Handle format: data:image/jpeg;base64,<base64_data>
        match = re.match(r'data:[^;]+;base64,(.+)', photo_data, re.DOTALL)
        if match:
            photo_data = match.group(1)

    # Remove any whitespace, newlines, or other non-base64 characters
    # Keep only valid base64 characters: A-Z, a-z, 0-9, +, /, =
    photo_data = re.sub(r'[^A-Za-z0-9+/=]', '', photo_data)

    # Fix padding - base64 must be multiple of 4
    # If length % 4 == 1, it's invalid - trim the last character
    remainder = len(photo_data) % 4
    if remainder == 1:
        # Invalid length - trim last char (likely corruption)
        photo_data = photo_data[:-1]
    elif remainder == 2:
        photo_data += '=='
    elif remainder == 3:
        photo_data += '='

    return base64.b64decode(photo_data)


# =============================================================================
# DEPARTMENT VIEWSET
# =============================================================================

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments.
    Admin users can CRUD, others can only read.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'department_type', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by type
        dept_type = self.request.query_params.get('type')
        if dept_type:
            queryset = queryset.filter(department_type=dept_type)

        return queryset

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in a department."""
        department = self.get_object()
        employees = department.employees.filter(employment_status='active')
        serializer = EmployeeMinimalSerializer(employees, many=True)
        return Response(serializer.data)


# =============================================================================
# DESIGNATION VIEWSET
# =============================================================================

class DesignationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing designations.
    Admin users can CRUD, others can only read.
    """
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'level', 'category']
    ordering = ['-level', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by approval permission
        can_approve = self.request.query_params.get('can_approve_leave')
        if can_approve is not None:
            queryset = queryset.filter(can_approve_leave=can_approve.lower() == 'true')

        return queryset.filter(is_active=True)


# =============================================================================
# EMPLOYEE PROFILE VIEWSET
# =============================================================================

class EmployeeProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee profiles.
    """
    queryset = EmployeeProfile.objects.select_related(
        'user', 'department', 'designation', 'reports_to'
    )
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_code', 'user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['user__first_name', 'joining_date', 'employee_code']
    ordering = ['user__first_name', 'user__last_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeeCreateSerializer
        if self.action == 'hierarchy':
            return EmployeeHierarchySerializer
        return EmployeeProfileSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'hierarchy', 'my_profile', 'my_subordinates']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by department
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        # Filter by designation
        designation_id = self.request.query_params.get('designation')
        if designation_id:
            queryset = queryset.filter(designation_id=designation_id)

        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(employment_status=status_param)
        else:
            # Default to active employees
            queryset = queryset.filter(employment_status='active')

        # Filter by reports_to
        reports_to = self.request.query_params.get('reports_to')
        if reports_to:
            queryset = queryset.filter(reports_to_id=reports_to)

        return queryset

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's employee profile."""
        try:
            employee = request.user.employee_profile
            serializer = EmployeeProfileSerializer(employee)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def my_subordinates(self, request):
        """Get current user's subordinates."""
        try:
            employee = request.user.employee_profile
            subordinates = employee.subordinates.filter(employment_status='active')

            # Optional: include indirect reports
            include_indirect = request.query_params.get('include_indirect', 'false').lower() == 'true'
            if include_indirect:
                subordinates = employee.get_subordinates(include_indirect=True)
                serializer = EmployeeMinimalSerializer(subordinates, many=True)
            else:
                serializer = EmployeeMinimalSerializer(subordinates, many=True)

            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Get employee's reporting hierarchy."""
        employee = self.get_object()
        serializer = EmployeeHierarchySerializer(employee)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def org_chart(self, request):
        """Get organizational chart data."""
        # Get top-level employees (no reports_to)
        top_employees = EmployeeProfile.objects.filter(
            reports_to__isnull=True,
            employment_status='active'
        ).select_related('department', 'designation')

        def build_tree(employee):
            subordinates = employee.subordinates.filter(
                employment_status='active'
            ).select_related('department', 'designation')
            return {
                'id': str(employee.id),
                'name': employee.full_name,
                'designation': employee.designation.name if employee.designation else None,
                'department': employee.department.name if employee.department else None,
                'is_department_head': employee.is_department_head,
                'subordinates': [build_tree(sub) for sub in subordinates]
            }

        org_chart = [build_tree(emp) for emp in top_employees]
        return Response(org_chart)


# =============================================================================
# LEAVE TYPE VIEWSET
# =============================================================================

class LeaveTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave types."""
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by active
        is_active = self.request.query_params.get('is_active', 'true')
        if is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)

        # Filter by applyable - by default only show applyable leave types for non-admin
        # Admin can use ?is_applyable=all to see all leave types
        is_applyable = self.request.query_params.get('is_applyable', None)
        if is_applyable == 'all':
            # Admin wants to see all leave types (for calendar management)
            pass
        elif is_applyable == 'false':
            # Only calendar-only leave types
            queryset = queryset.filter(is_applyable=False)
        else:
            # Default: only show applyable leave types for staff applying leaves
            queryset = queryset.filter(is_applyable=True)

        # Filter by gender if user has employee profile
        if hasattr(self.request.user, 'profile'):
            gender = self.request.user.profile.gender
            if gender:
                queryset = queryset.filter(
                    Q(applicable_gender='all') | Q(applicable_gender=gender)
                )

        return queryset


# =============================================================================
# LEAVE POLICY VIEWSET
# =============================================================================

class LeavePolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave policies."""
    queryset = LeavePolicy.objects.select_related('leave_type').prefetch_related('applicable_designations')
    serializer_class = LeavePolicySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'leave_type__name']
    ordering = ['leave_type__name', '-effective_from']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_policies']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by leave type
        leave_type_id = self.request.query_params.get('leave_type')
        if leave_type_id:
            queryset = queryset.filter(leave_type_id=leave_type_id)

        # Filter by active and current date
        if self.request.query_params.get('current', 'false').lower() == 'true':
            today = date.today()
            queryset = queryset.filter(
                is_active=True,
                effective_from__lte=today
            ).filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=today)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def my_policies(self, request):
        """Get leave policies applicable to current user."""
        try:
            employee = request.user.employee_profile
            today = date.today()

            # Get applicable policies
            policies = LeavePolicy.objects.filter(
                is_active=True,
                effective_from__lte=today
            ).filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=today)
            ).filter(
                Q(applicable_to_all=True) | Q(applicable_designations=employee.designation)
            ).select_related('leave_type').distinct()

            serializer = LeavePolicySerializer(policies, many=True)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# =============================================================================
# LEAVE BALANCE VIEWSET
# =============================================================================

class LeaveBalanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave balances."""
    queryset = LeaveBalance.objects.select_related('employee__user', 'leave_type')
    serializer_class = LeaveBalanceSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-year', 'leave_type__name']

    def get_permissions(self):
        if self.action in ['my_balances', 'my_summary']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by employee
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=int(year))

        # Filter by leave type
        leave_type_id = self.request.query_params.get('leave_type')
        if leave_type_id:
            queryset = queryset.filter(leave_type_id=leave_type_id)

        return queryset

    @action(detail=False, methods=['get'])
    def my_balances(self, request):
        """Get current user's leave balances. Auto-initializes from policies if none exist."""
        try:
            employee = request.user.employee_profile
            year = int(request.query_params.get('year', date.today().year))

            # Check if balances exist for this employee and year
            balances = LeaveBalance.objects.filter(
                employee=employee,
                year=year
            ).select_related('leave_type')

            # If no balances exist, auto-initialize from applicable policies
            if not balances.exists():
                self._initialize_employee_balances(employee, year, request.user)
                # Re-fetch after initialization
                balances = LeaveBalance.objects.filter(
                    employee=employee,
                    year=year
                ).select_related('leave_type')

            serializer = LeaveBalanceSerializer(balances, many=True)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def _initialize_employee_balances(self, employee, year, user):
        """Initialize leave balances for a single employee based on applicable policies."""
        today = date.today()

        # Get current active leave policies
        policies = LeavePolicy.objects.filter(
            is_active=True,
            effective_from__lte=today
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=today)
        ).select_related('leave_type')

        for policy in policies:
            # Check if policy applies to this employee
            if not policy.is_applicable_to(employee):
                continue

            # Check if balance already exists
            if LeaveBalance.objects.filter(
                employee=employee,
                leave_type=policy.leave_type,
                year=year
            ).exists():
                continue

            # Calculate accrued quota based on accrual_type (yearly/monthly/quarterly)
            # This respects the credit policy set by admin
            annual_quota = policy.calculate_accrued_quota(employee.joining_date, year)

            # Get carryforward from previous year
            opening_balance = Decimal('0')
            if policy.carryforward_type != 'none':
                try:
                    prev_balance = LeaveBalance.objects.get(
                        employee=employee,
                        leave_type=policy.leave_type,
                        year=year - 1
                    )
                    carryforward = prev_balance.available_balance
                    if policy.carryforward_type == 'partial' and policy.max_carryforward_days:
                        carryforward = min(carryforward, policy.max_carryforward_days)
                    opening_balance = max(Decimal('0'), carryforward)
                except LeaveBalance.DoesNotExist:
                    pass

            # Create balance
            LeaveBalance.objects.create(
                employee=employee,
                leave_type=policy.leave_type,
                year=year,
                opening_balance=opening_balance,
                annual_quota=annual_quota,
                last_updated_by=user
            )

    @action(detail=False, methods=['get'])
    def my_summary(self, request):
        """Get current user's leave balance summary. Auto-initializes from policies if none exist."""
        try:
            employee = request.user.employee_profile
            year = int(request.query_params.get('year', date.today().year))

            # Check if balances exist for this employee and year
            balances = LeaveBalance.objects.filter(
                employee=employee,
                year=year
            ).select_related('leave_type')

            # If no balances exist, auto-initialize from applicable policies
            if not balances.exists():
                self._initialize_employee_balances(employee, year, request.user)
                # Re-fetch after initialization
                balances = LeaveBalance.objects.filter(
                    employee=employee,
                    year=year
                ).select_related('leave_type')

            total_available = sum(b.available_balance for b in balances)
            total_used = sum(b.used for b in balances)
            total_pending = sum(b.pending for b in balances)

            return Response({
                'year': year,
                'balances': LeaveBalanceSerializer(balances, many=True).data,
                'total_available': float(total_available),
                'total_used': float(total_used),
                'total_pending': float(total_pending)
            })
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def adjust(self, request):
        """Manual balance adjustment (Admin only)."""
        serializer = LeaveBalanceAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            balance = LeaveBalance.objects.get(
                employee_id=data['employee_id'],
                leave_type_id=data['leave_type_id'],
                year=data['year']
            )
        except LeaveBalance.DoesNotExist:
            return Response(
                {'error': 'Leave balance not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Record audit log
        balance_before = balance.available_balance
        balance.adjustment += data['adjustment']
        balance.last_updated_by = request.user
        balance.save()

        LeaveBalanceAuditLog.objects.create(
            leave_balance=balance,
            action='adjusted',
            days_change=data['adjustment'],
            balance_before=balance_before,
            balance_after=balance.available_balance,
            notes=data['notes'],
            performed_by=request.user
        )

        return Response(LeaveBalanceSerializer(balance).data)

    @action(detail=False, methods=['post'])
    def initialize_year(self, request):
        """Initialize leave balances for a new year (Admin only)."""
        year = int(request.data.get('year', date.today().year))

        # Get all active employees
        employees = EmployeeProfile.objects.filter(employment_status='active')

        # Get current leave policies
        today = date.today()
        policies = LeavePolicy.objects.filter(
            is_active=True,
            effective_from__lte=today
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=today)
        ).select_related('leave_type')

        created_count = 0

        for employee in employees:
            for policy in policies:
                # Check if policy applies to this employee
                if not policy.is_applicable_to(employee):
                    continue

                # Check if balance already exists
                if LeaveBalance.objects.filter(
                    employee=employee,
                    leave_type=policy.leave_type,
                    year=year
                ).exists():
                    continue

                # Calculate prorated quota
                annual_quota = policy.calculate_prorated_quota(employee.joining_date, year)

                # Get carryforward from previous year
                opening_balance = Decimal('0')
                if policy.carryforward_type != 'none':
                    try:
                        prev_balance = LeaveBalance.objects.get(
                            employee=employee,
                            leave_type=policy.leave_type,
                            year=year - 1
                        )
                        carryforward = prev_balance.available_balance
                        if policy.carryforward_type == 'partial' and policy.max_carryforward_days:
                            carryforward = min(carryforward, policy.max_carryforward_days)
                        opening_balance = max(Decimal('0'), carryforward)
                    except LeaveBalance.DoesNotExist:
                        pass

                # Create balance
                LeaveBalance.objects.create(
                    employee=employee,
                    leave_type=policy.leave_type,
                    year=year,
                    opening_balance=opening_balance,
                    annual_quota=annual_quota,
                    last_updated_by=request.user
                )
                created_count += 1

        return Response({
            'message': f'Initialized {created_count} leave balances for year {year}'
        })


# =============================================================================
# LEAVE REQUEST VIEWSET
# =============================================================================

class LeaveRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for leave requests."""
    queryset = LeaveRequest.objects.select_related(
        'employee__user', 'employee__department', 'employee__designation',
        'leave_type', 'current_approver__user'
    )
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        if self.action == 'retrieve':
            return LeaveRequestDetailSerializer
        return LeaveRequestSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # If not admin, limit to own requests or requests pending approval
        if not user.is_staff:
            try:
                employee = user.employee_profile
                queryset = queryset.filter(
                    Q(employee=employee) | Q(current_approver=employee)
                )
            except EmployeeProfile.DoesNotExist:
                queryset = queryset.none()

        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by employee
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's leave requests."""
        try:
            employee = request.user.employee_profile
            queryset = LeaveRequest.objects.filter(employee=employee)

            # Filter by status
            status_param = request.query_params.get('status')
            if status_param:
                queryset = queryset.filter(status=status_param)

            # Filter by year
            year = request.query_params.get('year')
            if year:
                queryset = queryset.filter(start_date__year=int(year))

            serializer = LeaveRequestSerializer(queryset, many=True)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get leave requests pending current user's approval."""
        try:
            employee = request.user.employee_profile
            queryset = LeaveRequest.objects.filter(
                current_approver=employee,
                status='pending'
            ).select_related('employee__user', 'leave_type')

            serializer = LeaveRequestSerializer(queryset, many=True)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a draft leave request."""
        leave_request = self.get_object()

        if leave_request.status != 'draft':
            return Response(
                {'error': 'Only draft requests can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check balance
        try:
            balance = LeaveBalance.objects.get(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=leave_request.start_date.year
            )
            if balance.available_balance < leave_request.total_days:
                return Response(
                    {'error': 'Insufficient leave balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except LeaveBalance.DoesNotExist:
            return Response(
                {'error': 'No leave balance found for this leave type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Submit and create approval chain
        leave_request.submit(user=request.user)

        # Create approval records
        approval_chain = leave_request.get_approval_chain()
        for i, approver in enumerate(approval_chain):
            LeaveApproval.objects.create(
                leave_request=leave_request,
                approver=approver,
                sequence=i + 1
            )

        serializer = LeaveRequestDetailSerializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Approve or reject a leave request."""
        leave_request = self.get_object()

        # Validate action
        action_serializer = LeaveApprovalActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)

        action = action_serializer.validated_data['action']
        comments = action_serializer.validated_data.get('comments', '')

        # Check if current user is the approver
        try:
            employee = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if leave_request.current_approver != employee and not request.user.is_staff:
            return Response(
                {'error': 'You are not authorized to process this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the approval record
        try:
            approval = LeaveApproval.objects.get(
                leave_request=leave_request,
                approver=employee,
                status='pending'
            )
        except LeaveApproval.DoesNotExist:
            # Admin bypass
            if request.user.is_staff:
                approval = LeaveApproval.objects.filter(
                    leave_request=leave_request,
                    status='pending'
                ).first()
                if not approval:
                    return Response(
                        {'error': 'No pending approval found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'No pending approval found for you'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Process the action
        if action == 'approve':
            approval.approve(comments=comments)
        else:
            approval.reject(comments=comments)

        serializer = LeaveRequestDetailSerializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a leave request."""
        leave_request = self.get_object()

        # Check ownership or admin
        try:
            employee = request.user.employee_profile
            is_owner = leave_request.employee == employee
        except EmployeeProfile.DoesNotExist:
            is_owner = False

        if not is_owner and not request.user.is_staff:
            return Response(
                {'error': 'You are not authorized to cancel this request'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Can only cancel draft or pending requests
        if leave_request.status not in ['draft', 'pending']:
            return Response(
                {'error': 'Only draft or pending requests can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Release pending balance if submitted
        if leave_request.status == 'pending':
            try:
                balance = LeaveBalance.objects.get(
                    employee=leave_request.employee,
                    leave_type=leave_request.leave_type,
                    year=leave_request.start_date.year
                )
                balance.pending -= leave_request.total_days
                balance.save()
            except LeaveBalance.DoesNotExist:
                pass

        leave_request.status = 'cancelled'
        leave_request.save()

        serializer = LeaveRequestDetailSerializer(leave_request)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def team_calendar(self, request):
        """Get team leave calendar for managers."""
        try:
            employee = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get subordinates
        subordinates = employee.get_subordinates(include_indirect=True)
        subordinate_ids = [s.id for s in subordinates]

        # Get date range
        start_date = request.query_params.get('start_date', date.today().replace(day=1).isoformat())
        end_date = request.query_params.get('end_date')

        # Get approved leaves
        queryset = LeaveRequest.objects.filter(
            employee_id__in=subordinate_ids,
            status='approved',
            start_date__gte=start_date
        )
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        serializer = LeaveRequestSerializer(queryset, many=True)
        return Response(serializer.data)


# =============================================================================
# LEAVE BALANCE AUDIT LOG VIEWSET
# =============================================================================

class LeaveBalanceAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing leave balance audit logs (Admin only)."""
    queryset = LeaveBalanceAuditLog.objects.select_related(
        'leave_balance__employee__user', 'leave_balance__leave_type', 'performed_by'
    )
    serializer_class = LeaveBalanceAuditLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by employee
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(leave_balance__employee_id=employee_id)

        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        return queryset


# =============================================================================
# HOLIDAY VIEWSET
# =============================================================================

class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing holidays."""
    queryset = Holiday.objects.prefetch_related('applicable_departments')
    serializer_class = HolidaySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'upcoming']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=int(year))

        # Filter by type
        holiday_type = self.request.query_params.get('type')
        if holiday_type:
            queryset = queryset.filter(holiday_type=holiday_type)

        return queryset

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming holidays."""
        today = date.today()
        limit = int(request.query_params.get('limit', 5))

        holidays = Holiday.objects.filter(
            date__gte=today
        ).order_by('date')[:limit]

        serializer = HolidaySerializer(holidays, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """Get all holidays grouped by year."""
        years = Holiday.objects.values_list('year', flat=True).distinct().order_by('-year')

        result = {}
        for year in years:
            holidays = Holiday.objects.filter(year=year)
            result[year] = HolidaySerializer(holidays, many=True).data

        return Response(result)


# =============================================================================
# STAFF ATTENDANCE VIEWSET
# =============================================================================

import base64
from django.core.files.base import ContentFile

class StaffAttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for staff attendance with geo-selfie check-in/check-out.

    Endpoints:
    - GET /api/hr/staff-attendance/ - List attendance (admin sees all, staff sees own)
    - GET /api/hr/staff-attendance/my_attendance/ - Current user's attendance records
    - GET /api/hr/staff-attendance/today/ - Today's attendance record
    - POST /api/hr/staff-attendance/check_in/ - Check in with photo and location
    - POST /api/hr/staff-attendance/check_out/ - Check out with photo and location
    - GET /api/hr/staff-attendance/summary/ - Attendance summary for a period
    """
    queryset = StaffAttendance.objects.select_related('employee__user', 'employee__department')
    serializer_class = StaffAttendanceSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-date', '-check_in_time']

    def get_permissions(self):
        # All authenticated users can access their own attendance
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Admin sees all, staff sees only their own
        if not user.is_staff:
            try:
                employee = user.employee_profile
                queryset = queryset.filter(employee=employee)
            except EmployeeProfile.DoesNotExist:
                queryset = queryset.none()

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Filter by employee (admin only)
        employee_id = self.request.query_params.get('employee')
        if employee_id and user.is_staff:
            queryset = queryset.filter(employee_id=employee_id)

        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    @action(detail=False, methods=['get'])
    def my_attendance(self, request):
        """Get current user's attendance records."""
        try:
            employee = request.user.employee_profile
            queryset = StaffAttendance.objects.filter(employee=employee)

            # Filter by date range
            start_date = request.query_params.get('start_date')
            if start_date:
                queryset = queryset.filter(date__gte=start_date)

            end_date = request.query_params.get('end_date')
            if end_date:
                queryset = queryset.filter(date__lte=end_date)

            # Default to current month
            if not start_date and not end_date:
                today = date.today()
                queryset = queryset.filter(
                    date__year=today.year,
                    date__month=today.month
                )

            queryset = queryset.order_by('-date')
            serializer = StaffAttendanceSerializer(queryset, many=True)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's attendance record for current user."""
        try:
            employee = request.user.employee_profile
            today = date.today()

            try:
                attendance = StaffAttendance.objects.get(
                    employee=employee,
                    date=today
                )
                serializer = StaffAttendanceSerializer(attendance)
                return Response(serializer.data)
            except StaffAttendance.DoesNotExist:
                return Response({
                    'has_checked_in': False,
                    'has_checked_out': False,
                    'date': today.isoformat(),
                    'message': 'No attendance record for today'
                })
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        """Check in with photo and geolocation."""
        try:
            employee = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        today = date.today()

        # Check if already checked in today
        existing = StaffAttendance.objects.filter(
            employee=employee,
            date=today
        ).first()

        if existing and existing.check_in_time:
            return Response(
                {'error': 'Already checked in today', 'attendance': StaffAttendanceSerializer(existing).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate request data
        serializer = StaffAttendanceCheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Process base64 photo (handles data URI format)
        photo_data = data['photo']
        photo_file = ContentFile(
            decode_base64_photo(photo_data),
            name=f'checkin_{employee.employee_code}_{today.isoformat()}.jpg'
        )

        # Create or update attendance record
        if existing:
            attendance = existing
            attendance.check_in_time = timezone.now()
            attendance.check_in_photo = photo_file
            attendance.check_in_latitude = data['latitude']
            attendance.check_in_longitude = data['longitude']
            attendance.check_in_within_geofence = data['within_geofence']
            attendance.status = 'checked_in'
            attendance.save()
        else:
            attendance = StaffAttendance.objects.create(
                employee=employee,
                date=today,
                check_in_time=timezone.now(),
                check_in_photo=photo_file,
                check_in_latitude=data['latitude'],
                check_in_longitude=data['longitude'],
                check_in_within_geofence=data['within_geofence'],
                status='checked_in'
            )

        return Response(
            StaffAttendanceSerializer(attendance).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        """Check out with photo and geolocation."""
        try:
            employee = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        today = date.today()

        # Check if checked in today
        try:
            attendance = StaffAttendance.objects.get(
                employee=employee,
                date=today
            )
        except StaffAttendance.DoesNotExist:
            return Response(
                {'error': 'No check-in record found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not attendance.check_in_time:
            return Response(
                {'error': 'You must check in before checking out'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.check_out_time:
            return Response(
                {'error': 'Already checked out today', 'attendance': StaffAttendanceSerializer(attendance).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate request data
        serializer = StaffAttendanceCheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Process base64 photo (handles data URI format)
        photo_data = data['photo']
        photo_file = ContentFile(
            decode_base64_photo(photo_data),
            name=f'checkout_{employee.employee_code}_{today.isoformat()}.jpg'
        )

        # Update attendance record
        attendance.check_out_time = timezone.now()
        attendance.check_out_photo = photo_file
        attendance.check_out_latitude = data['latitude']
        attendance.check_out_longitude = data['longitude']
        attendance.check_out_within_geofence = data['within_geofence']
        attendance.status = 'checked_out'

        # Calculate hours worked
        if attendance.check_in_time and attendance.check_out_time:
            duration = attendance.check_out_time - attendance.check_in_time
            hours = Decimal(str(duration.total_seconds() / 3600))
            attendance.hours_worked = round(hours, 2)

        attendance.save()

        return Response(StaffAttendanceSerializer(attendance).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get attendance summary for current user."""
        try:
            employee = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'error': 'Employee profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get date range (default to current month)
        today = date.today()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date:
            start_date = today.replace(day=1)
        else:
            start_date = date.fromisoformat(start_date)

        if not end_date:
            end_date = today
        else:
            end_date = date.fromisoformat(end_date)

        # Get attendance records
        records = StaffAttendance.objects.filter(
            employee=employee,
            date__gte=start_date,
            date__lte=end_date
        )

        # Calculate summary
        total_days = (end_date - start_date).days + 1
        present_days = records.filter(status__in=['checked_in', 'checked_out']).count()
        absent_days = records.filter(status='absent').count()
        on_leave_days = records.filter(status='on_leave').count()
        half_days = records.filter(status='half_day').count()

        # Calculate total hours
        total_hours = records.exclude(hours_worked__isnull=True).aggregate(
            total=Sum('hours_worked')
        )['total'] or Decimal('0')

        avg_hours = total_hours / present_days if present_days > 0 else Decimal('0')

        # Working days calculation (assuming 5-day work week)
        working_days = sum(
            1 for i in range(total_days)
            if (start_date + timezone.timedelta(days=i)).weekday() < 5
        )

        attendance_percentage = (present_days / working_days * 100) if working_days > 0 else Decimal('0')

        summary_data = {
            'total_days': total_days,
            'working_days': working_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'on_leave_days': on_leave_days,
            'half_days': half_days,
            'total_hours_worked': float(total_hours),
            'avg_hours_per_day': float(round(avg_hours, 2)),
            'attendance_percentage': float(round(attendance_percentage, 2)),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

        return Response(summary_data)
