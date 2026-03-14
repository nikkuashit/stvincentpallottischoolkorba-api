"""
Workflows Serializers

Serializers for request types, workflows, requests, approvals, and clearances.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    RequestType,
    ApprovalWorkflow,
    ApprovalStep,
    ClearanceType,
    Request,
    RequestApproval,
    RequestClearance,
    RequestAttachment,
    RequestHistory,
)


# ==============================================================================
# USER SERIALIZER (MINIMAL)
# ==============================================================================

class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


# ==============================================================================
# REQUEST TYPE SERIALIZERS
# ==============================================================================

class RequestTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing request types"""
    class Meta:
        model = RequestType
        fields = [
            'id', 'name', 'slug', 'description', 'category',
            'requires_clearance', 'requires_payment', 'payment_amount',
            'is_active', 'display_order'
        ]


class RequestTypeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with form schema"""
    workflow_name = serializers.CharField(source='approval_workflow.name', read_only=True, allow_null=True)

    class Meta:
        model = RequestType
        fields = [
            'id', 'name', 'slug', 'description', 'category',
            'requires_clearance', 'requires_payment', 'payment_amount',
            'form_schema', 'allowed_roles', 'approval_workflow', 'workflow_name',
            'is_active', 'display_order', 'created_at', 'updated_at'
        ]


# ==============================================================================
# APPROVAL WORKFLOW SERIALIZERS
# ==============================================================================

class ApprovalStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalStep
        fields = [
            'id', 'name', 'description', 'step_order',
            'approver_type', 'approver_role', 'department',
            'is_optional', 'can_reject', 'requires_comment',
            'auto_approve_after_days', 'is_active'
        ]


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    steps = ApprovalStepSerializer(many=True, read_only=True)
    step_count = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalWorkflow
        fields = [
            'id', 'name', 'slug', 'description',
            'is_sequential', 'is_active', 'steps', 'step_count',
            'created_at', 'updated_at'
        ]

    def get_step_count(self, obj):
        return obj.steps.filter(is_active=True).count()


# ==============================================================================
# CLEARANCE TYPE SERIALIZERS
# ==============================================================================

class ClearanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClearanceType
        fields = [
            'id', 'name', 'slug', 'description', 'department',
            'clearance_role', 'clearance_order', 'check_description',
            'is_active'
        ]


# ==============================================================================
# REQUEST SERIALIZERS
# ==============================================================================

class RequestApprovalSerializer(serializers.ModelSerializer):
    step_name = serializers.CharField(source='approval_step.name', read_only=True)
    step_order = serializers.IntegerField(source='approval_step.step_order', read_only=True)
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RequestApproval
        fields = [
            'id', 'approval_step', 'step_name', 'step_order',
            'status', 'approved_by', 'approved_by_name',
            'comments', 'actioned_at', 'due_date',
            'created_at', 'updated_at'
        ]

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None


class RequestClearanceSerializer(serializers.ModelSerializer):
    clearance_name = serializers.CharField(source='clearance_type.name', read_only=True)
    department = serializers.CharField(source='clearance_type.department', read_only=True)
    clearance_order = serializers.IntegerField(source='clearance_type.clearance_order', read_only=True)
    cleared_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RequestClearance
        fields = [
            'id', 'clearance_type', 'clearance_name', 'department', 'clearance_order',
            'status', 'cleared_by', 'cleared_by_name',
            'verification_notes', 'pending_dues', 'pending_items',
            'actioned_at', 'created_at', 'updated_at'
        ]

    def get_cleared_by_name(self, obj):
        if obj.cleared_by:
            return obj.cleared_by.get_full_name() or obj.cleared_by.username
        return None


class RequestAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = RequestAttachment
        fields = [
            'id', 'file', 'file_url', 'file_name', 'file_type', 'file_size',
            'uploaded_by', 'uploaded_by_name', 'description', 'created_at'
        ]
        read_only_fields = ['file_name', 'file_type', 'file_size', 'uploaded_by']

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class RequestHistorySerializer(serializers.ModelSerializer):
    action_by_name = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = RequestHistory
        fields = [
            'id', 'action', 'action_display', 'action_by', 'action_by_name',
            'previous_status', 'new_status', 'details', 'comments',
            'created_at'
        ]

    def get_action_by_name(self, obj):
        if obj.action_by:
            return obj.action_by.get_full_name() or obj.action_by.username
        return None


class StudentMinimalSerializer(serializers.Serializer):
    """Minimal serializer for student info"""
    id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    admission_number = serializers.CharField()
    current_class_name = serializers.SerializerMethodField()

    def get_current_class_name(self, obj):
        if obj.current_class:
            return obj.current_class.name
        return None


class RequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing requests"""
    request_type_name = serializers.CharField(source='request_type.name', read_only=True)
    submitted_by_name = serializers.SerializerMethodField()
    student_names = serializers.SerializerMethodField()
    students_data = StudentMinimalSerializer(source='students', many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Request
        fields = [
            'id', 'request_number', 'title', 'request_type', 'request_type_name',
            'submitted_by', 'submitted_by_name', 'students', 'student_names', 'students_data',
            'status', 'status_display', 'priority', 'priority_display',
            'is_bypassed', 'payment_status', 'attachments_count',
            'submitted_at', 'completed_at', 'created_at', 'updated_at'
        ]

    def get_submitted_by_name(self, obj):
        return obj.submitted_by.get_full_name() or obj.submitted_by.username

    def get_student_names(self, obj):
        students = obj.students.all()
        if students:
            return ", ".join([f"{s.first_name} {s.last_name}" for s in students])
        return None


class RequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all related data"""
    request_type_data = RequestTypeListSerializer(source='request_type', read_only=True)
    submitted_by_data = UserMinimalSerializer(source='submitted_by', read_only=True)
    bypassed_by_data = UserMinimalSerializer(source='bypassed_by', read_only=True)
    current_step_data = ApprovalStepSerializer(source='current_step', read_only=True)
    approvals = RequestApprovalSerializer(many=True, read_only=True)
    clearances = RequestClearanceSerializer(many=True, read_only=True)
    attachments = RequestAttachmentSerializer(many=True, read_only=True)
    history = RequestHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    student_names = serializers.SerializerMethodField()
    students_data = StudentMinimalSerializer(source='students', many=True, read_only=True)

    class Meta:
        model = Request
        fields = [
            'id', 'request_number', 'title', 'description', 'form_data',
            'request_type', 'request_type_data',
            'submitted_by', 'submitted_by_data',
            'students', 'student_names', 'students_data',
            'status', 'status_display', 'priority', 'priority_display',
            'current_step', 'current_step_data',
            'is_bypassed', 'bypassed_by', 'bypassed_by_data', 'bypassed_at', 'bypass_reason',
            'payment_status', 'payment_amount', 'payment_transaction_id',
            'attachments_count', 'admin_notes',
            'submitted_at', 'completed_at', 'created_at', 'updated_at',
            'approvals', 'clearances', 'attachments', 'history'
        ]

    def get_student_names(self, obj):
        students = obj.students.all()
        if students:
            return ", ".join([f"{s.first_name} {s.last_name}" for s in students])
        return None


class RequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new requests"""
    students = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text="List of student IDs this request is for"
    )

    class Meta:
        model = Request
        fields = [
            'request_type', 'title', 'description', 'form_data',
            'students', 'priority'
        ]

    def to_representation(self, instance):
        """Use RequestListSerializer for response"""
        return RequestListSerializer(instance, context=self.context).data

    def create(self, validated_data):
        from academics.models import Student

        user = self.context['request'].user
        student_ids = validated_data.pop('students', [])

        validated_data['submitted_by'] = user

        # Check payment requirements
        request_type = validated_data['request_type']
        if request_type.requires_payment:
            validated_data['payment_status'] = 'pending'
            validated_data['payment_amount'] = request_type.payment_amount

        request_obj = super().create(validated_data)

        # Add students (ManyToMany relationship)
        if student_ids:
            students = Student.objects.filter(id__in=student_ids)
            request_obj.students.set(students)

        # Create approval records if workflow exists
        if request_type.approval_workflow:
            workflow = request_type.approval_workflow
            steps = workflow.steps.filter(is_active=True).order_by('step_order')
            for step in steps:
                RequestApproval.objects.create(
                    request=request_obj,
                    approval_step=step,
                    status='pending'
                )
            # Set first step as current
            first_step = steps.first()
            if first_step:
                request_obj.current_step = first_step
                request_obj.save(update_fields=['current_step'])

        # Create clearance records if required
        if request_type.requires_clearance:
            clearance_types = ClearanceType.objects.filter(is_active=True).order_by('clearance_order')
            for clearance_type in clearance_types:
                RequestClearance.objects.create(
                    request=request_obj,
                    clearance_type=clearance_type,
                    status='pending'
                )

        # Create history entry
        RequestHistory.objects.create(
            request=request_obj,
            action='created',
            action_by=user,
            new_status='draft',
            comments='Request created'
        )

        return request_obj


class RequestSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a draft request"""
    def update(self, instance, validated_data):
        from django.utils import timezone
        from notifications.models import send_request_notification
        user = self.context['request'].user

        if instance.status != 'draft':
            raise serializers.ValidationError("Only draft requests can be submitted")

        instance.status = 'submitted'
        instance.submitted_at = timezone.now()

        # Determine next status based on workflow
        if instance.request_type.requires_clearance:
            instance.status = 'pending_clearance'
        elif instance.request_type.approval_workflow:
            instance.status = 'pending_approval'

        instance.save()

        # Create history entry
        RequestHistory.objects.create(
            request=instance,
            action='submitted',
            action_by=user,
            previous_status='draft',
            new_status=instance.status,
            comments='Request submitted for processing'
        )

        # Send notifications to approvers/clearance staff
        if instance.status == 'pending_approval':
            send_request_notification(instance, 'request_pending_approval')
        elif instance.status == 'pending_clearance':
            send_request_notification(instance, 'request_pending_clearance')

        return instance


class ApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval/rejection actions"""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'skip'])
    comments = serializers.CharField(required=False, allow_blank=True)


class ClearanceActionSerializer(serializers.Serializer):
    """Serializer for clearance actions"""
    action = serializers.ChoiceField(choices=['clear', 'deny'])
    verification_notes = serializers.CharField(required=False, allow_blank=True)
    pending_dues = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    pending_items = serializers.CharField(required=False, allow_blank=True)


class BypassActionSerializer(serializers.Serializer):
    """Serializer for bypass action"""
    reason = serializers.CharField(required=True, min_length=10)
