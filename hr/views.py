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
)


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
        """Get current user's leave balances."""
        try:
            employee = request.user.employee_profile
            year = int(request.query_params.get('year', date.today().year))

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

    @action(detail=False, methods=['get'])
    def my_summary(self, request):
        """Get current user's leave balance summary."""
        try:
            employee = request.user.employee_profile
            year = int(request.query_params.get('year', date.today().year))

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
