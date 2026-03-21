"""
HR Serializers

Serializers for HR management API endpoints:
- Departments and Designations
- Employee Profiles with reporting structure
- Leave Types, Policies, and Balances
- Leave Requests with approval workflow
"""

from decimal import Decimal
from datetime import date
from rest_framework import serializers
from django.contrib.auth.models import User
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


# =============================================================================
# DEPARTMENT SERIALIZERS
# =============================================================================

class DepartmentSerializer(serializers.ModelSerializer):
    """Basic department serializer."""
    employee_count = serializers.SerializerMethodField()
    head = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'department_type', 'description',
            'is_active', 'employee_count', 'head', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()

    def get_head(self, obj):
        head = obj.employees.filter(is_department_head=True, employment_status='active').first()
        if head:
            return {
                'id': str(head.id),
                'name': head.full_name,
                'employee_code': head.employee_code
            }
        return None


# =============================================================================
# DESIGNATION SERIALIZERS
# =============================================================================

class DesignationSerializer(serializers.ModelSerializer):
    """Basic designation serializer."""
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Designation
        fields = [
            'id', 'name', 'code', 'category', 'level', 'description',
            'can_approve_leave', 'can_manage_department', 'is_active',
            'employee_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()


# =============================================================================
# EMPLOYEE PROFILE SERIALIZERS
# =============================================================================

class EmployeeMinimalSerializer(serializers.ModelSerializer):
    """Minimal employee info for references."""
    name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = ['id', 'employee_code', 'name', 'department_name', 'designation_name']

    def get_name(self, obj):
        return obj.full_name


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Full employee profile serializer."""
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    reports_to_name = serializers.SerializerMethodField()
    tenure_months = serializers.IntegerField(read_only=True)
    tenure_years = serializers.IntegerField(read_only=True)
    subordinate_count = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'employee_code', 'name', 'email',
            'department', 'department_name',
            'designation', 'designation_name',
            'is_department_head',
            'reports_to', 'reports_to_name',
            'joining_date', 'confirmation_date',
            'employment_status', 'employment_type',
            'work_days_per_week',
            'resignation_date', 'last_working_date', 'exit_reason',
            'tenure_months', 'tenure_years', 'subordinate_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenure_months', 'tenure_years']

    def get_name(self, obj):
        return obj.full_name

    def get_reports_to_name(self, obj):
        if obj.reports_to:
            return obj.reports_to.full_name
        return None

    def get_subordinate_count(self, obj):
        return obj.subordinates.filter(employment_status='active').count()


class EmployeeHierarchySerializer(serializers.ModelSerializer):
    """Employee with reporting chain and subordinates."""
    name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    reporting_chain = serializers.SerializerMethodField()
    direct_subordinates = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'employee_code', 'name',
            'department', 'department_name',
            'designation', 'designation_name',
            'is_department_head',
            'reporting_chain', 'direct_subordinates'
        ]

    def get_name(self, obj):
        return obj.full_name

    def get_reporting_chain(self, obj):
        chain = obj.get_reporting_chain()
        return [
            {
                'id': str(emp.id),
                'name': emp.full_name,
                'designation': emp.designation.name if emp.designation else None,
                'can_approve_leave': emp.designation.can_approve_leave if emp.designation else False
            }
            for emp in chain
        ]

    def get_direct_subordinates(self, obj):
        subordinates = obj.subordinates.filter(employment_status='active')
        return [
            {
                'id': str(emp.id),
                'name': emp.full_name,
                'designation': emp.designation.name if emp.designation else None
            }
            for emp in subordinates
        ]


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating employee profiles."""
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            'user_id', 'employee_code', 'department', 'designation',
            'is_department_head', 'reports_to', 'joining_date',
            'confirmation_date', 'employment_status', 'employment_type',
            'work_days_per_week'
        ]

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if hasattr(user, 'employee_profile'):
                raise serializers.ValidationError("This user already has an employee profile.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        return EmployeeProfile.objects.create(user=user, **validated_data)


# =============================================================================
# LEAVE TYPE SERIALIZERS
# =============================================================================

class LeaveTypeSerializer(serializers.ModelSerializer):
    """Leave type serializer."""
    class Meta:
        model = LeaveType
        fields = [
            'id', 'name', 'code', 'description',
            'is_paid', 'requires_document', 'min_days_notice',
            'max_consecutive_days', 'applicable_gender', 'color',
            'is_applyable', 'is_active', 'display_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# LEAVE POLICY SERIALIZERS
# =============================================================================

class LeavePolicySerializer(serializers.ModelSerializer):
    """Leave policy serializer."""
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    applicable_designation_names = serializers.SerializerMethodField()

    class Meta:
        model = LeavePolicy
        fields = [
            'id', 'name', 'leave_type', 'leave_type_name', 'leave_type_code',
            'applicable_to_all', 'applicable_designations', 'applicable_designation_names',
            'annual_quota', 'proration_method', 'accrual_type',
            'carryforward_type', 'max_carryforward_days', 'carryforward_expiry_months',
            'allow_encashment', 'min_balance_for_encashment', 'max_encashment_days',
            'effective_from', 'effective_to', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_applicable_designation_names(self, obj):
        return list(obj.applicable_designations.values_list('name', flat=True))


# =============================================================================
# LEAVE BALANCE SERIALIZERS
# =============================================================================

class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Leave balance serializer."""
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    leave_type_color = serializers.CharField(source='leave_type.color', read_only=True)
    total_available = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    available_balance = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'leave_type', 'leave_type_name', 'leave_type_code', 'leave_type_color',
            'year', 'opening_balance', 'annual_quota', 'adjustment',
            'used', 'pending', 'encashed', 'lapsed',
            'total_available', 'available_balance',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_available', 'available_balance']

    def get_employee_name(self, obj):
        return obj.employee.full_name


class LeaveBalanceSummarySerializer(serializers.Serializer):
    """Summary of all leave balances for an employee."""
    year = serializers.IntegerField()
    balances = LeaveBalanceSerializer(many=True)
    total_available = serializers.DecimalField(max_digits=6, decimal_places=1)
    total_used = serializers.DecimalField(max_digits=6, decimal_places=1)
    total_pending = serializers.DecimalField(max_digits=6, decimal_places=1)


class LeaveBalanceAdjustmentSerializer(serializers.Serializer):
    """Serializer for manual balance adjustments."""
    employee_id = serializers.UUIDField()
    leave_type_id = serializers.UUIDField()
    year = serializers.IntegerField()
    adjustment = serializers.DecimalField(max_digits=5, decimal_places=1)
    notes = serializers.CharField(max_length=500)


# =============================================================================
# LEAVE REQUEST SERIALIZERS
# =============================================================================

class LeaveApprovalSerializer(serializers.ModelSerializer):
    """Leave approval record serializer."""
    approver_name = serializers.SerializerMethodField()
    approver_designation = serializers.SerializerMethodField()

    class Meta:
        model = LeaveApproval
        fields = [
            'id', 'approver', 'approver_name', 'approver_designation',
            'sequence', 'status', 'comments', 'acted_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_approver_name(self, obj):
        return obj.approver.full_name

    def get_approver_designation(self, obj):
        if obj.approver.designation:
            return obj.approver.designation.name
        return None


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Leave request serializer for list views."""
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    leave_type_color = serializers.CharField(source='leave_type.color', read_only=True)
    current_approver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'leave_type', 'leave_type_name', 'leave_type_code', 'leave_type_color',
            'start_date', 'end_date', 'start_duration_type', 'end_duration_type',
            'total_days', 'reason', 'contact_during_leave', 'document',
            'status', 'status_display',
            'current_approver', 'current_approver_name',
            'submitted_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_days', 'submitted_at', 'created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name

    def get_current_approver_name(self, obj):
        if obj.current_approver:
            return obj.current_approver.full_name
        return None


class LeaveRequestDetailSerializer(LeaveRequestSerializer):
    """Detailed leave request with approvals."""
    approvals = LeaveApprovalSerializer(many=True, read_only=True)
    final_approver_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    designation_name = serializers.CharField(source='employee.designation.name', read_only=True)

    class Meta(LeaveRequestSerializer.Meta):
        fields = LeaveRequestSerializer.Meta.fields + [
            'approvals', 'final_approver', 'final_approver_name',
            'department_name', 'designation_name'
        ]

    def get_final_approver_name(self, obj):
        if obj.final_approver:
            return obj.final_approver.full_name
        return None


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leave requests."""
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_type', 'start_date', 'end_date',
            'start_duration_type', 'end_duration_type',
            'reason', 'contact_during_leave', 'document'
        ]

    def validate(self, data):
        # Validate dates
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError({
                'end_date': 'End date cannot be before start date.'
            })

        # Validate leave type constraints
        leave_type = data['leave_type']
        start_date = data['start_date']

        # Check minimum notice days
        if leave_type.min_days_notice > 0:
            days_notice = (start_date - date.today()).days
            if days_notice < leave_type.min_days_notice:
                raise serializers.ValidationError({
                    'start_date': f'This leave type requires at least {leave_type.min_days_notice} days notice.'
                })

        # Check max consecutive days
        if leave_type.max_consecutive_days:
            request_days = (data['end_date'] - data['start_date']).days + 1
            if request_days > leave_type.max_consecutive_days:
                raise serializers.ValidationError({
                    'end_date': f'Maximum {leave_type.max_consecutive_days} consecutive days allowed for this leave type.'
                })

        return data

    def create(self, validated_data):
        # Get employee from request context
        request = self.context.get('request')
        employee = request.user.employee_profile

        # Create the leave request
        leave_request = LeaveRequest.objects.create(
            employee=employee,
            **validated_data
        )

        return leave_request


class LeaveApprovalActionSerializer(serializers.Serializer):
    """Serializer for approve/reject actions."""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comments = serializers.CharField(max_length=1000, required=False, allow_blank=True)


# =============================================================================
# LEAVE BALANCE AUDIT LOG SERIALIZERS
# =============================================================================

class LeaveBalanceAuditLogSerializer(serializers.ModelSerializer):
    """Leave balance audit log serializer."""
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_balance.leave_type.name', read_only=True)
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalanceAuditLog
        fields = [
            'id', 'employee_name', 'leave_type_name',
            'action', 'days_change', 'balance_before', 'balance_after',
            'reference', 'notes', 'performed_by', 'performed_by_name',
            'created_at'
        ]

    def get_employee_name(self, obj):
        return obj.leave_balance.employee.full_name

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name() or obj.performed_by.username
        return None


# =============================================================================
# HOLIDAY SERIALIZERS
# =============================================================================

class HolidaySerializer(serializers.ModelSerializer):
    """Holiday serializer."""
    applicable_department_names = serializers.SerializerMethodField()

    class Meta:
        model = Holiday
        fields = [
            'id', 'name', 'date', 'holiday_type', 'description',
            'is_optional', 'applicable_departments', 'applicable_department_names',
            'year', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'year', 'created_at', 'updated_at']

    def get_applicable_department_names(self, obj):
        return list(obj.applicable_departments.values_list('name', flat=True))


# =============================================================================
# ANALYTICS SERIALIZERS
# =============================================================================

class LeaveAnalyticsSerializer(serializers.Serializer):
    """Leave analytics summary."""
    total_employees = serializers.IntegerField()
    total_leave_taken = serializers.DecimalField(max_digits=10, decimal_places=1)
    total_leave_pending = serializers.DecimalField(max_digits=10, decimal_places=1)
    avg_leave_per_employee = serializers.DecimalField(max_digits=5, decimal_places=1)
    leave_by_type = serializers.ListField()
    leave_by_department = serializers.ListField()
    leave_trend = serializers.ListField()


class EmployeeLeaveReportSerializer(serializers.Serializer):
    """Individual employee leave report."""
    employee = EmployeeMinimalSerializer()
    balances = LeaveBalanceSerializer(many=True)
    requests = LeaveRequestSerializer(many=True)
    total_taken = serializers.DecimalField(max_digits=5, decimal_places=1)
    total_pending = serializers.DecimalField(max_digits=5, decimal_places=1)
    total_available = serializers.DecimalField(max_digits=5, decimal_places=1)


# =============================================================================
# STAFF ATTENDANCE SERIALIZERS
# =============================================================================

class StaffAttendanceSerializer(serializers.ModelSerializer):
    """Staff attendance record serializer for list views."""
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    hours_worked_display = serializers.CharField(read_only=True)
    check_in_location = serializers.DictField(read_only=True)
    check_out_location = serializers.DictField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StaffAttendance
        fields = [
            'id', 'employee', 'employee_name', 'employee_code', 'date',
            'check_in_time', 'check_in_photo', 'check_in_latitude', 'check_in_longitude',
            'check_in_location', 'check_in_within_geofence',
            'check_out_time', 'check_out_photo', 'check_out_latitude', 'check_out_longitude',
            'check_out_location', 'check_out_within_geofence',
            'hours_worked', 'hours_worked_display',
            'status', 'status_display', 'sync_status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'hours_worked', 'created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name


class StaffAttendanceCheckInSerializer(serializers.Serializer):
    """Serializer for check-in request with base64 photo."""
    photo = serializers.CharField(help_text="Base64 encoded photo data")
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    within_geofence = serializers.BooleanField(default=True)

    def validate_photo(self, value):
        # Remove data URL prefix if present
        if value.startswith('data:image'):
            # Extract base64 data after the comma
            parts = value.split(',')
            if len(parts) == 2:
                return parts[1]
        return value


class StaffAttendanceCheckOutSerializer(serializers.Serializer):
    """Serializer for check-out request with base64 photo."""
    photo = serializers.CharField(help_text="Base64 encoded photo data")
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    within_geofence = serializers.BooleanField(default=True)

    def validate_photo(self, value):
        # Remove data URL prefix if present
        if value.startswith('data:image'):
            # Extract base64 data after the comma
            parts = value.split(',')
            if len(parts) == 2:
                return parts[1]
        return value


class StaffAttendanceSummarySerializer(serializers.Serializer):
    """Summary of attendance for a period."""
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    on_leave_days = serializers.IntegerField()
    half_days = serializers.IntegerField()
    total_hours_worked = serializers.DecimalField(max_digits=6, decimal_places=2)
    avg_hours_per_day = serializers.DecimalField(max_digits=4, decimal_places=2)
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
