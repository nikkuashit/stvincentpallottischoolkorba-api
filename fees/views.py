"""
Fee Management Views

ViewSets for fee categories, structures, discounts, student fees, and payments.
Includes reporting endpoints and bulk operations.
"""

from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import (
    FeeCategory,
    FeeStructure,
    FeeDiscount,
    StudentFee,
    FeePayment,
    FeeReminder,
)
from .serializers import (
    FeeCategoryListSerializer,
    FeeCategorySerializer,
    FeeStructureListSerializer,
    FeeStructureDetailSerializer,
    FeeStructureSerializer,
    FeeDiscountListSerializer,
    FeeDiscountSerializer,
    StudentFeeListSerializer,
    StudentFeeDetailSerializer,
    StudentFeeSerializer,
    BulkAssignFeeSerializer,
    FeePaymentListSerializer,
    FeePaymentDetailSerializer,
    FeePaymentSerializer,
    CollectPaymentSerializer,
    FeeReminderSerializer,
    FeeCollectionSummarySerializer,
    GradeWiseFeeReportSerializer,
)


class FeeCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fee categories.

    list: Get all fee categories
    create: Create a new fee category
    retrieve: Get a specific fee category
    update: Update a fee category
    destroy: Delete a fee category (soft delete by setting is_active=False)
    """
    queryset = FeeCategory.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return FeeCategoryListSerializer
        return FeeCategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by mandatory
        is_mandatory = self.request.query_params.get('is_mandatory')
        if is_mandatory is not None:
            queryset = queryset.filter(is_mandatory=is_mandatory.lower() == 'true')

        return queryset

    def destroy(self, request, *args, **kwargs):
        """Soft delete by setting is_active to False."""
        instance = self.get_object()

        # Check if category has active fee structures
        if instance.fee_structures.filter(is_active=True).exists():
            return Response(
                {'error': 'Cannot delete category with active fee structures.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeeStructureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fee structures.

    list: Get all fee structures with filtering
    create: Create a new fee structure
    retrieve: Get detailed fee structure info
    update: Update a fee structure
    destroy: Soft delete fee structure
    """
    queryset = FeeStructure.objects.select_related(
        'academic_year', 'grade', 'category'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'amount', 'created_at', 'academic_year', 'grade']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return FeeStructureListSerializer
        elif self.action == 'retrieve':
            return FeeStructureDetailSerializer
        return FeeStructureSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by academic year
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        # Filter by grade
        grade = self.request.query_params.get('grade')
        if grade:
            queryset = queryset.filter(Q(grade_id=grade) | Q(grade__isnull=True))

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        # Filter by frequency
        frequency = self.request.query_params.get('frequency')
        if frequency:
            queryset = queryset.filter(frequency=frequency)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def destroy(self, request, *args, **kwargs):
        """Soft delete by setting is_active to False."""
        instance = self.get_object()

        # Check if structure has pending student fees
        pending_fees = instance.student_fees.filter(
            status__in=['pending', 'partial', 'overdue']
        )
        if pending_fees.exists():
            return Response(
                {'error': f'Cannot delete fee structure with {pending_fees.count()} pending fees.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a fee structure for a new academic year.
        """
        instance = self.get_object()
        new_academic_year = request.data.get('academic_year')

        if not new_academic_year:
            return Response(
                {'error': 'academic_year is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create duplicate
        new_structure = FeeStructure.objects.create(
            academic_year_id=new_academic_year,
            grade=instance.grade,
            category=instance.category,
            name=f"{instance.name} (Copy)",
            amount=instance.amount,
            frequency=instance.frequency,
            due_day_of_month=instance.due_day_of_month,
            late_fee_type=instance.late_fee_type,
            late_fee_value=instance.late_fee_value,
            grace_period_days=instance.grace_period_days,
            is_refundable=instance.is_refundable,
            description=instance.description,
            is_active=True,
        )

        serializer = FeeStructureSerializer(new_structure)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FeeDiscountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fee discounts.
    """
    queryset = FeeDiscount.objects.prefetch_related('applicable_categories').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'value', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return FeeDiscountListSerializer
        return FeeDiscountSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by criteria
        criteria = self.request.query_params.get('criteria')
        if criteria:
            queryset = queryset.filter(criteria=criteria)

        # Filter by discount type
        discount_type = self.request.query_params.get('discount_type')
        if discount_type:
            queryset = queryset.filter(discount_type=discount_type)

        # Filter by academic year
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            queryset = queryset.filter(
                Q(academic_year_id=academic_year) | Q(academic_year__isnull=True)
            )

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by currently valid
        valid_only = self.request.query_params.get('valid_only')
        if valid_only and valid_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                is_active=True
            ).filter(
                Q(valid_from__isnull=True) | Q(valid_from__lte=today)
            ).filter(
                Q(valid_until__isnull=True) | Q(valid_until__gte=today)
            )

        return queryset


class StudentFeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student fees.

    Includes bulk assignment, payment collection, and status management.
    """
    queryset = StudentFee.objects.select_related(
        'student', 'student__current_section', 'student__current_section__grade',
        'fee_structure', 'fee_structure__category', 'fee_structure__academic_year'
    ).prefetch_related('discounts_applied', 'payments').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'student__first_name', 'student__last_name',
        'student__admission_number', 'fee_structure__name'
    ]
    ordering_fields = ['due_date', 'final_amount', 'status', 'created_at']
    ordering = ['-due_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentFeeListSerializer
        elif self.action == 'retrieve':
            return StudentFeeDetailSerializer
        elif self.action == 'bulk_assign':
            return BulkAssignFeeSerializer
        return StudentFeeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)

        # Filter by fee structure
        fee_structure = self.request.query_params.get('fee_structure')
        if fee_structure:
            queryset = queryset.filter(fee_structure_id=fee_structure)

        # Filter by status
        fee_status = self.request.query_params.get('status')
        if fee_status:
            queryset = queryset.filter(status=fee_status)

        # Filter by academic year
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            queryset = queryset.filter(fee_structure__academic_year_id=academic_year)

        # Filter by grade
        grade = self.request.query_params.get('grade')
        if grade:
            queryset = queryset.filter(student__current_section__grade_id=grade)

        # Filter by section
        section = self.request.query_params.get('section')
        if section:
            queryset = queryset.filter(student__current_section_id=section)

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(fee_structure__category_id=category)

        # Filter by due date range
        due_from = self.request.query_params.get('due_from')
        if due_from:
            queryset = queryset.filter(due_date__gte=due_from)

        due_to = self.request.query_params.get('due_to')
        if due_to:
            queryset = queryset.filter(due_date__lte=due_to)

        # Filter overdue only
        overdue_only = self.request.query_params.get('overdue_only')
        if overdue_only and overdue_only.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                status__in=['pending', 'partial'],
                due_date__lt=today
            )

        return queryset

    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """
        Bulk assign a fee structure to multiple students.
        """
        serializer = BulkAssignFeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        fee_structure = FeeStructure.objects.get(id=data['fee_structure_id'])
        discounts = FeeDiscount.objects.filter(id__in=data.get('discount_ids', []))

        created_fees = []
        errors = []

        for student_id in data['student_ids']:
            try:
                # Calculate discount
                total_discount = Decimal('0.00')
                for discount in discounts:
                    if discount.is_valid():
                        total_discount += discount.calculate_discount(fee_structure.amount)

                # Create student fee
                student_fee = StudentFee.objects.create(
                    student_id=student_id,
                    fee_structure=fee_structure,
                    period_start=data['period_start'],
                    period_end=data['period_end'],
                    due_date=data['due_date'],
                    base_amount=fee_structure.amount,
                    discount_amount=total_discount,
                    final_amount=fee_structure.amount - total_discount,
                )
                student_fee.discounts_applied.set(discounts)
                created_fees.append(str(student_fee.id))

            except Exception as e:
                errors.append({'student_id': str(student_id), 'error': str(e)})

        return Response({
            'created_count': len(created_fees),
            'created_ids': created_fees,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_fees else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def waive(self, request, pk=None):
        """
        Waive a student fee.
        """
        instance = self.get_object()
        reason = request.data.get('reason', '')

        if not reason:
            return Response(
                {'error': 'Waiver reason is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if instance.status == 'paid':
            return Response(
                {'error': 'Cannot waive a fully paid fee.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = 'waived'
        instance.waiver_reason = reason
        instance.save()

        return Response(StudentFeeDetailSerializer(instance).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a student fee.
        """
        instance = self.get_object()

        if instance.paid_amount > 0:
            return Response(
                {'error': 'Cannot cancel a fee with payments. Refund payments first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = 'cancelled'
        instance.save()

        return Response(StudentFeeDetailSerializer(instance).data)

    @action(detail=True, methods=['post'])
    def recalculate_late_fee(self, request, pk=None):
        """
        Recalculate late fee for a student fee.
        """
        instance = self.get_object()
        late_fee = instance.calculate_late_fee()

        return Response({
            'late_fee': str(late_fee),
            'final_amount': str(instance.final_amount),
            'balance_due': str(instance.balance_due),
        })


class FeePaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fee payments.

    Includes receipt generation and payment verification.
    """
    queryset = FeePayment.objects.select_related(
        'student_fee', 'student_fee__student', 'student_fee__fee_structure',
        'created_by', 'verified_by'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'receipt_number', 'transaction_id',
        'student_fee__student__first_name', 'student_fee__student__last_name',
        'student_fee__student__admission_number'
    ]
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date', '-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return FeePaymentListSerializer
        elif self.action == 'retrieve':
            return FeePaymentDetailSerializer
        elif self.action == 'collect':
            return CollectPaymentSerializer
        return FeePaymentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by student fee
        student_fee = self.request.query_params.get('student_fee')
        if student_fee:
            queryset = queryset.filter(student_fee_id=student_fee)

        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_fee__student_id=student)

        # Filter by status
        payment_status = self.request.query_params.get('status')
        if payment_status:
            queryset = queryset.filter(status=payment_status)

        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)

        # Filter by receipt number prefix
        receipt_prefix = self.request.query_params.get('receipt_prefix')
        if receipt_prefix:
            queryset = queryset.filter(receipt_number__startswith=receipt_prefix)

        return queryset

    @action(detail=False, methods=['post'])
    def collect(self, request):
        """
        Collect a fee payment with receipt generation.
        """
        serializer = CollectPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        student_fee = StudentFee.objects.get(id=data['student_fee_id'])

        # Validate amount
        if data['amount'] > student_fee.balance_due:
            return Response(
                {'error': f"Amount ({data['amount']}) exceeds balance due ({student_fee.balance_due})."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create payment
        payment = FeePayment.objects.create(
            student_fee=student_fee,
            amount=data['amount'],
            payment_date=data.get('payment_date', timezone.now().date()),
            payment_method=data['payment_method'],
            transaction_id=data.get('transaction_id', ''),
            cheque_number=data.get('cheque_number', ''),
            cheque_date=data.get('cheque_date'),
            bank_name=data.get('bank_name', ''),
            remarks=data.get('remarks', ''),
            status='completed',
            created_by=request.user.profile if hasattr(request.user, 'profile') else None,
        )

        # Update student fee
        student_fee.paid_amount += payment.amount
        student_fee.update_status()

        return Response(
            FeePaymentDetailSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a payment (e.g., after cheque clearance).
        """
        payment = self.get_object()

        if payment.status == 'completed' and payment.verified_at:
            return Response(
                {'error': 'Payment is already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = 'completed'
        payment.verified_by = request.user.profile if hasattr(request.user, 'profile') else None
        payment.verified_at = timezone.now()
        payment.save()

        return Response(FeePaymentDetailSerializer(payment).data)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Refund a payment.
        """
        payment = self.get_object()
        reason = request.data.get('reason', '')

        if not reason:
            return Response(
                {'error': 'Refund reason is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment.status != 'completed':
            return Response(
                {'error': 'Can only refund completed payments.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update payment
        payment.status = 'refunded'
        payment.refund_reason = reason
        payment.save()

        # Update student fee
        student_fee = payment.student_fee
        student_fee.paid_amount = max(
            student_fee.paid_amount - payment.amount,
            Decimal('0.00')
        )
        student_fee.update_status()

        return Response(FeePaymentDetailSerializer(payment).data)

    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """
        Get receipt data for printing.
        """
        payment = self.get_object()
        student = payment.student_fee.student
        fee_structure = payment.student_fee.fee_structure

        receipt_data = {
            'receipt_number': payment.receipt_number,
            'payment_date': payment.payment_date.isoformat(),
            'student': {
                'name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'grade': student.current_section.grade.number if student.current_section else None,
                'section': student.current_section.name if student.current_section else None,
            },
            'fee_details': {
                'name': fee_structure.name,
                'category': fee_structure.category.name,
                'period': f"{payment.student_fee.period_start} to {payment.student_fee.period_end}",
                'base_amount': str(payment.student_fee.base_amount),
                'discount': str(payment.student_fee.discount_amount),
                'late_fee': str(payment.student_fee.late_fee_amount),
                'total_amount': str(payment.student_fee.final_amount),
            },
            'payment': {
                'amount': str(payment.amount),
                'method': payment.get_payment_method_display(),
                'transaction_id': payment.transaction_id,
                'previous_paid': str(payment.student_fee.paid_amount - payment.amount),
                'balance_due': str(payment.student_fee.balance_due),
            },
            'status': payment.student_fee.get_status_display(),
        }

        return Response(receipt_data)


class FeeReportsViewSet(viewsets.ViewSet):
    """
    ViewSet for fee reports and analytics.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def collection_summary(self, request):
        """
        Get fee collection summary for an academic year.
        """
        academic_year = request.query_params.get('academic_year')

        queryset = StudentFee.objects.all()
        if academic_year:
            queryset = queryset.filter(fee_structure__academic_year_id=academic_year)

        total_expected = queryset.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')
        total_collected = queryset.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        total_outstanding = total_expected - total_collected

        collection_percentage = (
            (total_collected / total_expected * 100) if total_expected > 0 else Decimal('0.00')
        )

        data = {
            'academic_year': academic_year or 'All',
            'total_fees_expected': total_expected,
            'total_fees_collected': total_collected,
            'total_outstanding': total_outstanding,
            'collection_percentage': round(collection_percentage, 2),
            'total_students': queryset.values('student').distinct().count(),
            'fully_paid_count': queryset.filter(status='paid').count(),
            'partial_paid_count': queryset.filter(status='partial').count(),
            'pending_count': queryset.filter(status='pending').count(),
            'overdue_count': queryset.filter(status='overdue').count(),
        }

        serializer = FeeCollectionSummarySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def grade_wise(self, request):
        """
        Get grade-wise fee collection report.
        """
        academic_year = request.query_params.get('academic_year')

        # Import here to avoid circular import
        from academics.models import Grade

        grades = Grade.objects.filter(is_active=True).order_by('number')
        report_data = []

        for grade in grades:
            queryset = StudentFee.objects.filter(
                student__current_section__grade=grade
            )
            if academic_year:
                queryset = queryset.filter(fee_structure__academic_year_id=academic_year)

            total_fees = queryset.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')
            collected = queryset.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
            outstanding = total_fees - collected

            collection_percentage = (
                (collected / total_fees * 100) if total_fees > 0 else Decimal('0.00')
            )

            report_data.append({
                'grade_number': grade.number,
                'grade_name': grade.name,
                'total_students': queryset.values('student').distinct().count(),
                'total_fees': total_fees,
                'collected': collected,
                'outstanding': outstanding,
                'collection_percentage': round(collection_percentage, 2),
            })

        serializer = GradeWiseFeeReportSerializer(report_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def category_wise(self, request):
        """
        Get category-wise fee collection report.
        """
        academic_year = request.query_params.get('academic_year')

        categories = FeeCategory.objects.filter(is_active=True).order_by('display_order')
        report_data = []

        for category in categories:
            queryset = StudentFee.objects.filter(
                fee_structure__category=category
            )
            if academic_year:
                queryset = queryset.filter(fee_structure__academic_year_id=academic_year)

            total_fees = queryset.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')
            collected = queryset.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
            outstanding = total_fees - collected

            collection_percentage = (
                (collected / total_fees * 100) if total_fees > 0 else Decimal('0.00')
            )

            report_data.append({
                'category_id': str(category.id),
                'category_name': category.name,
                'category_code': category.code,
                'total_assigned': queryset.count(),
                'total_fees': float(total_fees),
                'collected': float(collected),
                'outstanding': float(outstanding),
                'collection_percentage': float(round(collection_percentage, 2)),
            })

        return Response(report_data)

    @action(detail=False, methods=['get'])
    def defaulters(self, request):
        """
        Get list of fee defaulters.
        """
        academic_year = request.query_params.get('academic_year')
        grade = request.query_params.get('grade')
        min_days_overdue = int(request.query_params.get('min_days_overdue', 30))

        today = timezone.now().date()
        cutoff_date = today - timezone.timedelta(days=min_days_overdue)

        queryset = StudentFee.objects.filter(
            status__in=['pending', 'partial', 'overdue'],
            due_date__lt=cutoff_date
        ).select_related(
            'student', 'student__current_section', 'student__current_section__grade',
            'fee_structure', 'fee_structure__category'
        )

        if academic_year:
            queryset = queryset.filter(fee_structure__academic_year_id=academic_year)

        if grade:
            queryset = queryset.filter(student__current_section__grade_id=grade)

        # Order by most overdue first
        queryset = queryset.order_by('due_date')

        serializer = StudentFeeListSerializer(queryset[:100], many=True)
        return Response({
            'total_defaulters': queryset.count(),
            'defaulters': serializer.data
        })

    @action(detail=False, methods=['get'])
    def daily_collection(self, request):
        """
        Get daily collection report.
        """
        date_from = request.query_params.get('date_from', str(timezone.now().date()))
        date_to = request.query_params.get('date_to', str(timezone.now().date()))

        payments = FeePayment.objects.filter(
            status='completed',
            payment_date__gte=date_from,
            payment_date__lte=date_to
        ).values('payment_date', 'payment_method').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('payment_date')

        # Group by date
        daily_data = {}
        for item in payments:
            date_str = str(item['payment_date'])
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'total_amount': Decimal('0.00'),
                    'payment_count': 0,
                    'by_method': {}
                }

            daily_data[date_str]['total_amount'] += item['total']
            daily_data[date_str]['payment_count'] += item['count']
            daily_data[date_str]['by_method'][item['payment_method']] = {
                'count': item['count'],
                'amount': float(item['total'])
            }

        # Convert to list and format decimals
        result = []
        for date_str, data in sorted(daily_data.items()):
            result.append({
                'date': data['date'],
                'total_amount': float(data['total_amount']),
                'payment_count': data['payment_count'],
                'by_method': data['by_method']
            })

        return Response(result)
