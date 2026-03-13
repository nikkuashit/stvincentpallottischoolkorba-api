"""
Workflows Views

API endpoints for request types, workflows, requests, approvals, and clearances.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.utils import timezone
from django.db.models import Q

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
    can_bypass_approval,
    process_bypass,
)
from .serializers import (
    RequestTypeListSerializer,
    RequestTypeDetailSerializer,
    ApprovalWorkflowSerializer,
    ApprovalStepSerializer,
    ClearanceTypeSerializer,
    RequestListSerializer,
    RequestDetailSerializer,
    RequestCreateSerializer,
    RequestSubmitSerializer,
    RequestApprovalSerializer,
    RequestClearanceSerializer,
    RequestAttachmentSerializer,
    RequestHistorySerializer,
    ApprovalActionSerializer,
    ClearanceActionSerializer,
    BypassActionSerializer,
)


# ==============================================================================
# REQUEST TYPE VIEWS
# ==============================================================================

class RequestTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving request types.
    Read-only for all authenticated users.
    """
    queryset = RequestType.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order', 'name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RequestTypeDetailSerializer
        return RequestTypeListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by user role (only show allowed request types)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            user_role = self.request.user.profile.role
            # Filter request types that include this role in allowed_roles
            # or have empty allowed_roles (available to all)
            queryset = queryset.filter(
                Q(allowed_roles__contains=[user_role]) |
                Q(allowed_roles=[])
            )

        return queryset


# ==============================================================================
# APPROVAL WORKFLOW VIEWS
# ==============================================================================

class ApprovalWorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing approval workflows"""
    queryset = ApprovalWorkflow.objects.filter(is_active=True)
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [IsAuthenticated]


# ==============================================================================
# CLEARANCE TYPE VIEWS
# ==============================================================================

class ClearanceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing clearance types"""
    queryset = ClearanceType.objects.filter(is_active=True).order_by('clearance_order')
    serializer_class = ClearanceTypeSerializer
    permission_classes = [IsAuthenticated]


# ==============================================================================
# REQUEST VIEWS
# ==============================================================================

class RequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing requests.

    - Parents can create/view their own requests
    - Staff can view/process requests assigned to them
    - Admins can view all requests
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['request_number', 'title', 'description']
    ordering_fields = ['created_at', 'submitted_at', 'priority']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return RequestCreateSerializer
        if self.action in ['retrieve', 'update', 'partial_update']:
            return RequestDetailSerializer
        return RequestListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Request.objects.all()

        # Role-based filtering
        if hasattr(user, 'profile'):
            role = user.profile.role
            if role in ['super_admin', 'school_admin']:
                # Admins see all requests
                pass
            elif role == 'school_staff':
                # Staff see requests they need to approve or their own
                queryset = queryset.filter(
                    Q(submitted_by=user) |
                    Q(approvals__approval_step__approver_role=role, approvals__status='pending') |
                    Q(clearances__clearance_type__clearance_role=role, clearances__status='pending')
                ).distinct()
            else:
                # Parents/students see only their own requests
                queryset = queryset.filter(submitted_by=user)
        else:
            queryset = queryset.filter(submitted_by=user)

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        request_type = self.request.query_params.get('request_type')
        if request_type:
            queryset = queryset.filter(request_type__slug=request_type)

        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter for pending approvals (staff dashboard)
        pending_my_approval = self.request.query_params.get('pending_my_approval')
        if pending_my_approval == 'true' and hasattr(user, 'profile'):
            role = user.profile.role
            queryset = queryset.filter(
                approvals__approval_step__approver_role=role,
                approvals__status='pending'
            ).distinct()

        # Filter for pending clearances (staff dashboard)
        pending_my_clearance = self.request.query_params.get('pending_my_clearance')
        if pending_my_clearance == 'true' and hasattr(user, 'profile'):
            role = user.profile.role
            queryset = queryset.filter(
                clearances__clearance_type__clearance_role=role,
                clearances__status='pending'
            ).distinct()

        return queryset

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a draft request for processing"""
        instance = self.get_object()

        if instance.submitted_by != request.user:
            return Response(
                {'error': 'You can only submit your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RequestSubmitSerializer(
            instance,
            data={},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(RequestDetailSerializer(instance, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve or reject a pending approval step"""
        instance = self.get_object()
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']
        comments = serializer.validated_data.get('comments', '')

        # Find the pending approval for this user
        user = request.user
        user_role = getattr(user.profile, 'role', None) if hasattr(user, 'profile') else None

        pending_approval = instance.approvals.filter(
            status='pending',
            approval_step__approver_role=user_role
        ).first()

        if not pending_approval:
            return Response(
                {'error': 'No pending approval found for your role'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process the action
        if action_type == 'approve':
            pending_approval.status = 'approved'
            history_action = 'approval_given'
        elif action_type == 'reject':
            pending_approval.status = 'rejected'
            instance.status = 'rejected'
            history_action = 'approval_rejected'
        elif action_type == 'skip':
            if not pending_approval.approval_step.is_optional:
                return Response(
                    {'error': 'This step cannot be skipped'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            pending_approval.status = 'skipped'
            history_action = 'approval_given'

        pending_approval.approved_by = user
        pending_approval.actioned_at = timezone.now()
        pending_approval.comments = comments
        pending_approval.save()

        # Check if all approvals are done
        if action_type != 'reject':
            pending_count = instance.approvals.filter(status='pending').count()
            if pending_count == 0:
                # Check clearances
                if instance.request_type.requires_clearance:
                    pending_clearances = instance.clearances.filter(status='pending').count()
                    if pending_clearances > 0:
                        instance.status = 'pending_clearance'
                    else:
                        instance.status = 'approved'
                else:
                    instance.status = 'approved'

                if instance.status == 'approved':
                    instance.completed_at = timezone.now()
            else:
                # Move to next step
                next_approval = instance.approvals.filter(status='pending').order_by('approval_step__step_order').first()
                if next_approval:
                    instance.current_step = next_approval.approval_step

        instance.save()

        # Create history entry
        RequestHistory.objects.create(
            request=instance,
            action=history_action,
            action_by=user,
            previous_status=instance.status,
            new_status=instance.status,
            comments=comments,
            details={'approval_step': pending_approval.approval_step.name}
        )

        return Response(RequestDetailSerializer(instance, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def clearance(self, request, pk=None):
        """Process a clearance step"""
        instance = self.get_object()
        serializer = ClearanceActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']
        verification_notes = serializer.validated_data.get('verification_notes', '')
        pending_dues = serializer.validated_data.get('pending_dues')
        pending_items = serializer.validated_data.get('pending_items', '')

        user = request.user
        user_role = getattr(user.profile, 'role', None) if hasattr(user, 'profile') else None

        # Find pending clearance for this user's role
        pending_clearance = instance.clearances.filter(
            status='pending',
            clearance_type__clearance_role=user_role
        ).order_by('clearance_type__clearance_order').first()

        if not pending_clearance:
            return Response(
                {'error': 'No pending clearance found for your role'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process the action
        if action_type == 'clear':
            pending_clearance.status = 'cleared'
            history_action = 'clearance_given'
        else:
            pending_clearance.status = 'not_cleared'
            history_action = 'clearance_denied'

        pending_clearance.cleared_by = user
        pending_clearance.actioned_at = timezone.now()
        pending_clearance.verification_notes = verification_notes
        pending_clearance.pending_dues = pending_dues
        pending_clearance.pending_items = pending_items
        pending_clearance.save()

        # Check if all clearances are done
        if action_type == 'clear':
            pending_count = instance.clearances.filter(status='pending').count()
            if pending_count == 0:
                # Move to approval workflow or complete
                if instance.request_type.approval_workflow:
                    pending_approvals = instance.approvals.filter(status='pending').count()
                    if pending_approvals > 0:
                        instance.status = 'pending_approval'
                    else:
                        instance.status = 'approved'
                        instance.completed_at = timezone.now()
                else:
                    instance.status = 'approved'
                    instance.completed_at = timezone.now()
        else:
            # Clearance denied - request needs attention
            instance.status = 'pending_clearance'

        instance.save()

        # Create history entry
        RequestHistory.objects.create(
            request=instance,
            action=history_action,
            action_by=user,
            previous_status=instance.status,
            new_status=instance.status,
            comments=verification_notes,
            details={
                'clearance_type': pending_clearance.clearance_type.name,
                'pending_dues': str(pending_dues) if pending_dues else None,
                'pending_items': pending_items
            }
        )

        return Response(RequestDetailSerializer(instance, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def bypass(self, request, pk=None):
        """Bypass all pending approvals (admin only)"""
        instance = self.get_object()
        serializer = BypassActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        reason = serializer.validated_data['reason']

        if not can_bypass_approval(user):
            return Response(
                {'error': 'You do not have permission to bypass approvals'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            process_bypass(instance, user, reason)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(RequestDetailSerializer(instance, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a request"""
        instance = self.get_object()

        if instance.submitted_by != request.user and not can_bypass_approval(request.user):
            return Response(
                {'error': 'You can only cancel your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        if instance.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel a {instance.status} request'},
                status=status.HTTP_400_BAD_REQUEST
            )

        previous_status = instance.status
        instance.status = 'cancelled'
        instance.save()

        RequestHistory.objects.create(
            request=instance,
            action='cancelled',
            action_by=request.user,
            previous_status=previous_status,
            new_status='cancelled',
            comments=request.data.get('reason', 'Request cancelled by user')
        )

        return Response(RequestDetailSerializer(instance, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """Add an attachment to a request"""
        instance = self.get_object()

        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        description = request.data.get('description', '')

        attachment = RequestAttachment.objects.create(
            request=instance,
            file=file,
            file_name=file.name,
            file_type=file.content_type,
            file_size=file.size,
            uploaded_by=request.user,
            description=description
        )

        # Update attachment count
        instance.attachments_count = instance.attachments.count()
        instance.save(update_fields=['attachments_count'])

        # Create history entry
        RequestHistory.objects.create(
            request=instance,
            action='attachment_added',
            action_by=request.user,
            details={'file_name': file.name}
        )

        return Response(
            RequestAttachmentSerializer(attachment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's requests"""
        queryset = Request.objects.filter(submitted_by=request.user).order_by('-created_at')
        serializer = RequestListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_actions(self, request):
        """Get requests pending user's action (approval or clearance)"""
        user = request.user
        user_role = getattr(user.profile, 'role', None) if hasattr(user, 'profile') else None

        if not user_role:
            return Response([])

        # Get requests pending approval
        pending_approvals = Request.objects.filter(
            approvals__approval_step__approver_role=user_role,
            approvals__status='pending',
            status='pending_approval'
        ).distinct()

        # Get requests pending clearance
        pending_clearances = Request.objects.filter(
            clearances__clearance_type__clearance_role=user_role,
            clearances__status='pending',
            status='pending_clearance'
        ).distinct()

        # Combine and deduplicate
        combined = pending_approvals | pending_clearances
        serializer = RequestListSerializer(combined.distinct(), many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get request statistics for dashboard"""
        user = request.user
        user_role = getattr(user.profile, 'role', None) if hasattr(user, 'profile') else None

        # Base queryset based on role
        if user_role in ['super_admin', 'school_admin']:
            base_qs = Request.objects.all()
        elif user_role == 'school_staff':
            base_qs = Request.objects.filter(
                Q(submitted_by=user) |
                Q(approvals__approval_step__approver_role=user_role) |
                Q(clearances__clearance_type__clearance_role=user_role)
            ).distinct()
        else:
            base_qs = Request.objects.filter(submitted_by=user)

        stats = {
            'total': base_qs.count(),
            'draft': base_qs.filter(status='draft').count(),
            'pending': base_qs.filter(status__in=['submitted', 'pending_approval', 'pending_clearance']).count(),
            'approved': base_qs.filter(status='approved').count(),
            'rejected': base_qs.filter(status='rejected').count(),
            'completed': base_qs.filter(status='completed').count(),
        }

        # Add pending actions for staff
        if user_role in ['school_staff', 'school_admin']:
            stats['pending_my_approval'] = Request.objects.filter(
                approvals__approval_step__approver_role=user_role,
                approvals__status='pending',
                status='pending_approval'
            ).distinct().count()

            stats['pending_my_clearance'] = Request.objects.filter(
                clearances__clearance_type__clearance_role=user_role,
                clearances__status='pending',
                status='pending_clearance'
            ).distinct().count()

        return Response(stats)
