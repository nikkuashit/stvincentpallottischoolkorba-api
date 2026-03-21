"""
Fee Management Serializers

Provides serialization for fee categories, structures, discounts, payments, and reports.
"""

from decimal import Decimal
from rest_framework import serializers
from django.utils import timezone

from .models import (
    FeeCategory,
    FeeStructure,
    FeeDiscount,
    StudentFee,
    FeePayment,
    FeeReminder,
)


# =============================================================================
# FEE CATEGORY SERIALIZERS
# =============================================================================

class FeeCategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing fee categories."""
    fee_structure_count = serializers.SerializerMethodField()

    class Meta:
        model = FeeCategory
        fields = [
            'id', 'name', 'code', 'description',
            'display_order', 'is_mandatory', 'is_active',
            'fee_structure_count'
        ]

    def get_fee_structure_count(self, obj):
        return obj.fee_structures.filter(is_active=True).count()


class FeeCategorySerializer(serializers.ModelSerializer):
    """Full serializer for fee category CRUD operations."""

    class Meta:
        model = FeeCategory
        fields = [
            'id', 'name', 'code', 'description',
            'display_order', 'is_mandatory', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        """Ensure code is uppercase."""
        return value.upper()


# =============================================================================
# FEE STRUCTURE SERIALIZERS
# =============================================================================

class FeeStructureListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing fee structures."""
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    grade_name = serializers.SerializerMethodField()
    grade_number = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_code = serializers.CharField(source='category.code', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    late_fee_type_display = serializers.CharField(source='get_late_fee_type_display', read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = FeeStructure
        fields = [
            'id', 'name', 'academic_year', 'academic_year_name',
            'grade', 'grade_name', 'grade_number',
            'category', 'category_name', 'category_code',
            'amount', 'frequency', 'frequency_display',
            'due_day_of_month', 'late_fee_type', 'late_fee_type_display',
            'late_fee_value', 'grace_period_days',
            'is_refundable', 'is_active', 'student_count'
        ]

    def get_grade_name(self, obj):
        return obj.grade.name if obj.grade else 'All Grades'

    def get_grade_number(self, obj):
        return obj.grade.number if obj.grade else None

    def get_student_count(self, obj):
        return obj.student_fees.count()


class FeeStructureDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for fee structure with full info."""
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    grade_info = serializers.SerializerMethodField()
    category_info = FeeCategoryListSerializer(source='category', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    late_fee_type_display = serializers.CharField(source='get_late_fee_type_display', read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = FeeStructure
        fields = [
            'id', 'name', 'description',
            'academic_year', 'academic_year_name',
            'grade', 'grade_info',
            'category', 'category_info',
            'amount', 'frequency', 'frequency_display',
            'due_day_of_month', 'late_fee_type', 'late_fee_type_display',
            'late_fee_value', 'grace_period_days',
            'is_refundable', 'is_active',
            'stats', 'created_at', 'updated_at'
        ]

    def get_grade_info(self, obj):
        if obj.grade:
            return {
                'id': str(obj.grade.id),
                'number': obj.grade.number,
                'name': obj.grade.name,
            }
        return None

    def get_stats(self, obj):
        student_fees = obj.student_fees.all()
        return {
            'total_assigned': student_fees.count(),
            'pending': student_fees.filter(status='pending').count(),
            'partial': student_fees.filter(status='partial').count(),
            'paid': student_fees.filter(status='paid').count(),
            'overdue': student_fees.filter(status='overdue').count(),
            'total_expected': float(sum(sf.final_amount for sf in student_fees)),
            'total_collected': float(sum(sf.paid_amount for sf in student_fees)),
        }


class FeeStructureSerializer(serializers.ModelSerializer):
    """Unified serializer for fee structure CRUD operations."""
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    grade_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)

    class Meta:
        model = FeeStructure
        fields = [
            'id', 'name', 'description',
            'academic_year', 'academic_year_name',
            'grade', 'grade_name',
            'category', 'category_name',
            'amount', 'frequency', 'frequency_display',
            'due_day_of_month', 'late_fee_type', 'late_fee_value', 'grace_period_days',
            'is_refundable', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_grade_name(self, obj):
        return obj.grade.name if obj.grade else 'All Grades'

    def validate(self, data):
        """Validate fee structure data."""
        late_fee_type = data.get('late_fee_type', 'none')
        late_fee_value = data.get('late_fee_value', Decimal('0.00'))

        if late_fee_type != 'none' and late_fee_value <= 0:
            raise serializers.ValidationError({
                'late_fee_value': 'Late fee value must be greater than 0 when late fee is enabled.'
            })

        if late_fee_type == 'percentage' and late_fee_value > 100:
            raise serializers.ValidationError({
                'late_fee_value': 'Percentage cannot exceed 100.'
            })

        return data


# =============================================================================
# FEE DISCOUNT SERIALIZERS
# =============================================================================

class FeeDiscountListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing fee discounts."""
    criteria_display = serializers.CharField(source='get_criteria_display', read_only=True)
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    academic_year_name = serializers.SerializerMethodField()
    is_currently_valid = serializers.SerializerMethodField()
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = FeeDiscount
        fields = [
            'id', 'name', 'code', 'description',
            'discount_type', 'discount_type_display',
            'value', 'max_discount_amount',
            'criteria', 'criteria_display',
            'academic_year', 'academic_year_name',
            'valid_from', 'valid_until',
            'is_combinable', 'is_active', 'is_currently_valid',
            'usage_count'
        ]

    def get_academic_year_name(self, obj):
        return obj.academic_year.name if obj.academic_year else 'All Years'

    def get_is_currently_valid(self, obj):
        return obj.is_valid()

    def get_usage_count(self, obj):
        return obj.student_fees.count()


class FeeDiscountSerializer(serializers.ModelSerializer):
    """Unified serializer for fee discount CRUD operations."""
    criteria_display = serializers.CharField(source='get_criteria_display', read_only=True)
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    applicable_category_ids = serializers.PrimaryKeyRelatedField(
        queryset=FeeCategory.objects.all(),
        many=True,
        required=False,
        write_only=True,
        source='applicable_categories'
    )
    applicable_categories_info = FeeCategoryListSerializer(
        source='applicable_categories',
        many=True,
        read_only=True
    )

    class Meta:
        model = FeeDiscount
        fields = [
            'id', 'name', 'code', 'description',
            'discount_type', 'discount_type_display',
            'value', 'max_discount_amount',
            'criteria', 'criteria_display',
            'applicable_category_ids', 'applicable_categories_info',
            'academic_year', 'valid_from', 'valid_until',
            'is_combinable', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        """Ensure code is uppercase."""
        return value.upper()

    def validate(self, data):
        """Validate discount data."""
        discount_type = data.get('discount_type', 'percentage')
        value = data.get('value', Decimal('0.00'))

        if discount_type == 'percentage' and value > 100:
            raise serializers.ValidationError({
                'value': 'Percentage discount cannot exceed 100.'
            })

        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')

        if valid_from and valid_until and valid_from > valid_until:
            raise serializers.ValidationError({
                'valid_until': 'End date must be after start date.'
            })

        return data


# =============================================================================
# STUDENT FEE SERIALIZERS
# =============================================================================

class StudentFeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing student fees."""
    student_name = serializers.SerializerMethodField()
    student_admission_number = serializers.CharField(
        source='student.admission_number', read_only=True
    )
    student_grade = serializers.SerializerMethodField()
    student_section = serializers.SerializerMethodField()
    fee_name = serializers.CharField(source='fee_structure.name', read_only=True)
    category_name = serializers.CharField(source='fee_structure.category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.SerializerMethodField()

    class Meta:
        model = StudentFee
        fields = [
            'id', 'student', 'student_name', 'student_admission_number',
            'student_grade', 'student_section',
            'fee_structure', 'fee_name', 'category_name',
            'period_start', 'period_end', 'due_date',
            'base_amount', 'discount_amount', 'late_fee_amount',
            'final_amount', 'paid_amount', 'balance_due',
            'status', 'status_display', 'is_overdue', 'days_overdue'
        ]

    def get_student_name(self, obj):
        student = obj.student
        return f"{student.first_name} {student.last_name}"

    def get_student_grade(self, obj):
        if obj.student.current_section and obj.student.current_section.grade:
            return obj.student.current_section.grade.number
        return None

    def get_student_section(self, obj):
        if obj.student.current_section:
            return obj.student.current_section.name
        return None

    def get_days_overdue(self, obj):
        if obj.is_overdue:
            return (timezone.now().date() - obj.due_date).days
        return 0


class StudentFeeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for student fee with payments."""
    student_info = serializers.SerializerMethodField()
    fee_structure_info = FeeStructureListSerializer(source='fee_structure', read_only=True)
    discounts_applied_info = FeeDiscountListSerializer(
        source='discounts_applied',
        many=True,
        read_only=True
    )
    payments = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = StudentFee
        fields = [
            'id', 'student', 'student_info',
            'fee_structure', 'fee_structure_info',
            'period_start', 'period_end', 'due_date',
            'base_amount', 'discount_amount', 'late_fee_amount',
            'final_amount', 'paid_amount', 'balance_due',
            'discounts_applied', 'discounts_applied_info',
            'status', 'status_display',
            'remarks', 'waiver_reason',
            'payments', 'created_at', 'updated_at'
        ]

    def get_student_info(self, obj):
        student = obj.student
        section = student.current_section
        return {
            'id': str(student.id),
            'name': f"{student.first_name} {student.last_name}",
            'admission_number': student.admission_number,
            'grade': section.grade.number if section and section.grade else None,
            'section': section.name if section else None,
        }

    def get_payments(self, obj):
        return FeePaymentListSerializer(
            obj.payments.filter(status='completed'),
            many=True
        ).data


class StudentFeeSerializer(serializers.ModelSerializer):
    """Unified serializer for student fee CRUD operations."""
    student_name = serializers.SerializerMethodField()
    fee_name = serializers.CharField(source='fee_structure.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_ids = serializers.PrimaryKeyRelatedField(
        queryset=FeeDiscount.objects.all(),
        many=True,
        required=False,
        write_only=True,
        source='discounts_applied'
    )

    class Meta:
        model = StudentFee
        fields = [
            'id', 'student', 'student_name',
            'fee_structure', 'fee_name',
            'period_start', 'period_end', 'due_date',
            'base_amount', 'discount_amount', 'late_fee_amount',
            'final_amount', 'paid_amount', 'balance_due',
            'discount_ids', 'discounts_applied',
            'status', 'status_display',
            'remarks', 'waiver_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'paid_amount', 'late_fee_amount',
            'created_at', 'updated_at'
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def validate(self, data):
        """Validate student fee data."""
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        due_date = data.get('due_date')

        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError({
                'period_end': 'End date must be after start date.'
            })

        if due_date and period_end and due_date < period_start:
            raise serializers.ValidationError({
                'due_date': 'Due date cannot be before period start.'
            })

        return data

    def create(self, validated_data):
        """Create student fee and calculate discount."""
        discounts = validated_data.pop('discounts_applied', [])
        fee_structure = validated_data['fee_structure']

        # Set base amount from fee structure
        validated_data['base_amount'] = fee_structure.amount

        # Calculate discount
        total_discount = Decimal('0.00')
        for discount in discounts:
            if discount.is_valid():
                total_discount += discount.calculate_discount(fee_structure.amount)

        validated_data['discount_amount'] = total_discount
        validated_data['final_amount'] = fee_structure.amount - total_discount

        instance = super().create(validated_data)
        instance.discounts_applied.set(discounts)
        return instance


class BulkAssignFeeSerializer(serializers.Serializer):
    """Serializer for bulk assigning fees to students."""
    fee_structure_id = serializers.UUIDField()
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    due_date = serializers.DateField()
    discount_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=[]
    )

    def validate(self, data):
        if data['period_start'] > data['period_end']:
            raise serializers.ValidationError({
                'period_end': 'End date must be after start date.'
            })
        return data


# =============================================================================
# FEE PAYMENT SERIALIZERS
# =============================================================================

class FeePaymentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing payments."""
    student_name = serializers.SerializerMethodField()
    fee_name = serializers.CharField(
        source='student_fee.fee_structure.name', read_only=True
    )
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = FeePayment
        fields = [
            'id', 'student_fee', 'student_name', 'fee_name',
            'amount', 'payment_date', 'payment_method', 'payment_method_display',
            'receipt_number', 'transaction_id',
            'status', 'status_display',
            'created_at', 'created_by_name'
        ]

    def get_student_name(self, obj):
        student = obj.student_fee.student
        return f"{student.first_name} {student.last_name}"

    def get_created_by_name(self, obj):
        if obj.created_by:
            user = obj.created_by.user
            return f"{user.first_name} {user.last_name}"
        return None


class FeePaymentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for payment with full info."""
    student_fee_info = StudentFeeListSerializer(source='student_fee', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    verified_by_info = serializers.SerializerMethodField()

    class Meta:
        model = FeePayment
        fields = [
            'id', 'student_fee', 'student_fee_info',
            'amount', 'payment_date', 'payment_method', 'payment_method_display',
            'receipt_number', 'transaction_id',
            'cheque_number', 'cheque_date', 'bank_name',
            'status', 'status_display',
            'verified_by', 'verified_by_info', 'verified_at',
            'remarks', 'refund_reason',
            'created_at', 'updated_at',
            'created_by', 'created_by_info'
        ]

    def get_created_by_info(self, obj):
        if obj.created_by:
            user = obj.created_by.user
            return {
                'id': str(obj.created_by.id),
                'name': f"{user.first_name} {user.last_name}",
            }
        return None

    def get_verified_by_info(self, obj):
        if obj.verified_by:
            user = obj.verified_by.user
            return {
                'id': str(obj.verified_by.id),
                'name': f"{user.first_name} {user.last_name}",
            }
        return None


class FeePaymentSerializer(serializers.ModelSerializer):
    """Unified serializer for payment CRUD operations."""
    receipt_number = serializers.CharField(read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )

    class Meta:
        model = FeePayment
        fields = [
            'id', 'student_fee', 'amount', 'payment_date',
            'payment_method', 'payment_method_display',
            'receipt_number', 'transaction_id',
            'cheque_number', 'cheque_date', 'bank_name',
            'status', 'remarks',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'receipt_number', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate payment data."""
        student_fee = data.get('student_fee') or self.instance.student_fee
        amount = data.get('amount')

        # Check if payment exceeds balance due
        if amount and student_fee:
            balance = student_fee.balance_due
            if amount > balance:
                raise serializers.ValidationError({
                    'amount': f'Payment amount ({amount}) exceeds balance due ({balance}).'
                })

        # Validate cheque details
        payment_method = data.get('payment_method', 'cash')
        if payment_method == 'cheque':
            if not data.get('cheque_number'):
                raise serializers.ValidationError({
                    'cheque_number': 'Cheque number is required for cheque payments.'
                })
            if not data.get('cheque_date'):
                raise serializers.ValidationError({
                    'cheque_date': 'Cheque date is required for cheque payments.'
                })
            if not data.get('bank_name'):
                raise serializers.ValidationError({
                    'bank_name': 'Bank name is required for cheque payments.'
                })

        return data

    def create(self, validated_data):
        """Create payment and set created_by from request."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile'):
            validated_data['created_by'] = request.user.profile
        return super().create(validated_data)


class CollectPaymentSerializer(serializers.Serializer):
    """Serializer for fee collection workflow."""
    student_fee_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=FeePayment.PAYMENT_METHOD_CHOICES)
    payment_date = serializers.DateField(default=timezone.now().date)
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    cheque_number = serializers.CharField(required=False, allow_blank=True)
    cheque_date = serializers.DateField(required=False, allow_null=True)
    bank_name = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)


# =============================================================================
# FEE REMINDER SERIALIZERS
# =============================================================================

class FeeReminderSerializer(serializers.ModelSerializer):
    """Serializer for fee reminders."""
    reminder_type_display = serializers.CharField(
        source='get_reminder_type_display', read_only=True
    )
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = FeeReminder
        fields = [
            'id', 'student_fee', 'student_name',
            'reminder_type', 'reminder_type_display',
            'channel', 'channel_display',
            'sent_at', 'sent_to',
            'is_delivered', 'delivered_at',
            'message_content', 'error_message'
        ]
        read_only_fields = ['id', 'sent_at']

    def get_student_name(self, obj):
        student = obj.student_fee.student
        return f"{student.first_name} {student.last_name}"


# =============================================================================
# REPORT SERIALIZERS
# =============================================================================

class FeeCollectionSummarySerializer(serializers.Serializer):
    """Serializer for fee collection summary reports."""
    academic_year = serializers.CharField()
    total_fees_expected = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_fees_collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    collection_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_students = serializers.IntegerField()
    fully_paid_count = serializers.IntegerField()
    partial_paid_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()


class GradeWiseFeeReportSerializer(serializers.Serializer):
    """Serializer for grade-wise fee collection report."""
    grade_number = serializers.IntegerField()
    grade_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_fees = serializers.DecimalField(max_digits=15, decimal_places=2)
    collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    collection_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
