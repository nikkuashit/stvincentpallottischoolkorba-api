"""
Unit tests for academics models.
"""

import pytest
from datetime import date
from decimal import Decimal

from academics.models import (
    AcademicYear,
    Grade,
    Section,
    Student,
    StudentEnrollment,
    Subject,
    RoomLayout,
    Desk,
    SeatingAssignment,
    StudentPhoto,
)
from tests.factories import (
    AcademicYearFactory,
    GradeFactory,
    SectionFactory,
    StudentFactory,
    SubjectFactory,
    UserProfileFactory,
    RoomLayoutFactory,
    DeskFactory,
    SeatingAssignmentFactory,
    StudentPhotoFactory,
)


@pytest.mark.django_db
class TestAcademicYear:
    """Test cases for AcademicYear model."""

    def test_create_academic_year(self):
        """Test creating an academic year."""
        academic_year = AcademicYearFactory()

        assert academic_year.id is not None
        assert academic_year.name is not None
        assert academic_year.start_date < academic_year.end_date

    def test_academic_year_str(self):
        """Test __str__ method returns expected format."""
        academic_year = AcademicYearFactory(name='2025-26', status='active')

        assert '2025-26' in str(academic_year)
        assert 'Active' in str(academic_year)

    def test_only_one_current_academic_year(self):
        """Test that only one academic year can be marked as current."""
        ay1 = AcademicYearFactory(name='2024-25', is_current=True)
        ay2 = AcademicYearFactory(name='2025-26', is_current=True)

        # Refresh ay1 from database
        ay1.refresh_from_db()

        assert ay1.is_current is False
        assert ay2.is_current is True

    def test_status_choices(self):
        """Test all valid status choices."""
        for status in ['planning', 'active', 'completed']:
            ay = AcademicYearFactory(status=status)
            assert ay.status == status


@pytest.mark.django_db
class TestGrade:
    """Test cases for Grade model."""

    def test_create_grade(self):
        """Test creating a grade."""
        grade = GradeFactory()

        assert grade.id is not None
        assert 1 <= grade.number <= 12
        assert grade.academic_year is not None

    def test_grade_str(self):
        """Test __str__ method returns expected format."""
        academic_year = AcademicYearFactory(name='2025-26')
        grade = GradeFactory(number=5, name='Class 5', academic_year=academic_year)

        assert 'Class 5' in str(grade)
        assert '2025-26' in str(grade)

    def test_auto_generate_name(self):
        """Test that name is auto-generated if not provided."""
        grade = GradeFactory(number=7, name='')
        grade.save()

        assert grade.name == 'Class 7'

    def test_unique_together_academic_year_number(self):
        """Test unique_together constraint for academic_year and number."""
        academic_year = AcademicYearFactory()
        GradeFactory(academic_year=academic_year, number=5)

        # Creating another grade with same academic_year and number should return existing
        grade2 = GradeFactory(academic_year=academic_year, number=5)
        assert Grade.objects.filter(academic_year=academic_year, number=5).count() == 1


@pytest.mark.django_db
class TestSection:
    """Test cases for Section model."""

    def test_create_section(self):
        """Test creating a section."""
        section = SectionFactory()

        assert section.id is not None
        assert section.grade is not None
        assert section.name in ['A', 'B', 'C', 'D']

    def test_section_str(self):
        """Test __str__ method returns expected format."""
        academic_year = AcademicYearFactory(name='2025-26')
        grade = GradeFactory(academic_year=academic_year, number=5)
        section = SectionFactory(grade=grade, name='A', academic_year=academic_year)

        assert '5A' in str(section)
        assert '2025-26' in str(section)

    def test_full_name_property(self):
        """Test full_name property returns correct value."""
        grade = GradeFactory(number=7)
        section = SectionFactory(grade=grade, name='B')

        assert section.full_name == 'Class 7B'

    def test_current_strength_property(self):
        """Test current_strength returns correct count."""
        section = SectionFactory()

        # No students yet
        assert section.current_strength == 0

        # Add active students
        StudentFactory(current_section=section, status='active')
        StudentFactory(current_section=section, status='active')
        StudentFactory(current_section=section, status='inactive')

        assert section.current_strength == 2

    def test_capacity_from_room_layout(self):
        """Test capacity property returns total seats from room layout."""
        layout = RoomLayoutFactory(rows=2, columns=2)
        DeskFactory(room_layout=layout, row=0, column=0, capacity=2)
        DeskFactory(room_layout=layout, row=0, column=1, capacity=2)
        DeskFactory(room_layout=layout, row=1, column=0, capacity=3)
        DeskFactory(room_layout=layout, row=1, column=1, capacity=2, is_active=False)  # aisle

        section = SectionFactory(room_layout=layout)
        # Only active desks count: 2 + 2 + 3 = 7
        assert section.capacity == 7

    def test_capacity_none_without_layout(self):
        """Test capacity returns None when no room layout assigned."""
        section = SectionFactory(room_layout=None)
        assert section.capacity is None

    def test_available_capacity_property(self):
        """Test available_capacity returns correct value."""
        layout = RoomLayoutFactory(rows=1, columns=1)
        DeskFactory(room_layout=layout, row=0, column=0, capacity=3)
        section = SectionFactory(room_layout=layout)
        StudentFactory(current_section=section, status='active')

        assert section.available_capacity == 2


@pytest.mark.django_db
class TestStudent:
    """Test cases for Student model."""

    def test_create_student(self):
        """Test creating a student."""
        student = StudentFactory()

        assert student.id is not None
        assert student.admission_number.startswith('SVP')
        assert student.first_name is not None
        assert student.last_name is not None
        assert student.gender in ['male', 'female', 'other']

    def test_student_str(self):
        """Test __str__ method returns expected format."""
        student = StudentFactory(first_name='John', last_name='Doe')

        assert 'John Doe' in str(student)
        assert student.admission_number in str(student)

    def test_full_name_property(self):
        """Test full_name property returns correct value."""
        student = StudentFactory(first_name='Jane', last_name='Smith')

        assert student.full_name == 'Jane Smith'

    def test_status_choices(self):
        """Test all valid status choices."""
        for status in ['active', 'inactive', 'graduated', 'transferred', 'dropped']:
            student = StudentFactory(status=status)
            assert student.status == status

    def test_with_section_trait(self):
        """Test with_section trait creates student with section assigned."""
        student = StudentFactory(with_section=True)

        assert student.current_section is not None
        assert student.academic_year is not None

    def test_graduated_trait(self):
        """Test graduated trait sets correct status."""
        student = StudentFactory(graduated=True)

        assert student.status == 'graduated'

    def test_transferred_trait(self):
        """Test transferred trait sets correct status."""
        student = StudentFactory(transferred=True)

        assert student.status == 'transferred'

    def test_unique_admission_number(self):
        """Test that admission_number is unique."""
        student1 = StudentFactory()
        student2 = StudentFactory()

        assert student1.admission_number != student2.admission_number


@pytest.mark.django_db
class TestSubject:
    """Test cases for Subject model."""

    def test_create_subject(self):
        """Test creating a subject."""
        subject = SubjectFactory()

        assert subject.id is not None
        assert subject.name is not None
        assert subject.code is not None

    def test_subject_str(self):
        """Test __str__ method returns expected format."""
        subject = SubjectFactory(name='Mathematics', code='MATH101')

        assert 'Mathematics' in str(subject)
        assert 'MATH101' in str(subject)

    def test_unique_code(self):
        """Test that code is unique."""
        subject1 = SubjectFactory(code='UNIQUE001')
        subject2 = SubjectFactory()

        assert subject1.code != subject2.code


@pytest.mark.django_db
class TestRoomLayout:
    """Test cases for RoomLayout model."""

    def test_create_room_layout(self):
        """Test creating a room layout."""
        layout = RoomLayoutFactory()

        assert layout.id is not None
        assert layout.name is not None
        assert layout.rows == 5
        assert layout.columns == 6
        assert layout.is_active is True

    def test_room_layout_str(self):
        """Test __str__ method returns expected format."""
        layout = RoomLayoutFactory(name='Room 101', rows=4, columns=5)

        assert 'Room 101' in str(layout)
        assert '4' in str(layout)
        assert '5' in str(layout)

    def test_total_seats_property(self):
        """Test total_seats sums active desk capacities."""
        layout = RoomLayoutFactory(rows=2, columns=2)
        DeskFactory(room_layout=layout, row=0, column=0, capacity=2)
        DeskFactory(room_layout=layout, row=0, column=1, capacity=3)
        DeskFactory(room_layout=layout, row=1, column=0, capacity=2, is_active=False)

        assert layout.total_seats == 5  # Only active desks: 2 + 3

    def test_desk_count_property(self):
        """Test desk_count returns number of active desks."""
        layout = RoomLayoutFactory(rows=2, columns=2)
        DeskFactory(room_layout=layout, row=0, column=0, capacity=2)
        DeskFactory(room_layout=layout, row=0, column=1, capacity=2)
        DeskFactory(room_layout=layout, row=1, column=0, is_active=False)

        assert layout.desk_count == 2


@pytest.mark.django_db
class TestDesk:
    """Test cases for Desk model."""

    def test_create_desk(self):
        """Test creating a desk."""
        desk = DeskFactory()

        assert desk.id is not None
        assert desk.room_layout is not None
        assert desk.capacity == 2
        assert desk.is_active is True

    def test_desk_str(self):
        """Test __str__ method returns expected format."""
        desk = DeskFactory(row=1, column=2, capacity=3)

        result = str(desk)
        assert '1' in result
        assert '2' in result
        assert '3' in result

    def test_unique_together_constraint(self):
        """Test unique_together constraint for room_layout, row, column."""
        layout = RoomLayoutFactory()
        DeskFactory(room_layout=layout, row=0, column=0)

        with pytest.raises(Exception):
            DeskFactory(room_layout=layout, row=0, column=0)

    def test_capacity_validators(self):
        """Test capacity must be between 1 and 3."""
        from django.core.exceptions import ValidationError

        desk = DeskFactory.build(capacity=0)
        with pytest.raises(ValidationError):
            desk.full_clean()

        desk = DeskFactory.build(capacity=4)
        with pytest.raises(ValidationError):
            desk.full_clean()

    def test_inactive_desk_as_aisle(self):
        """Test inactive desk represents an aisle."""
        desk = DeskFactory(is_active=False)
        assert desk.is_active is False


@pytest.mark.django_db
class TestSeatingAssignment:
    """Test cases for SeatingAssignment model."""

    def test_create_seating_assignment(self):
        """Test creating a seating assignment."""
        layout = RoomLayoutFactory()
        desk = DeskFactory(room_layout=layout, row=0, column=0)
        section = SectionFactory(room_layout=layout)
        student = StudentFactory(current_section=section, status='active')

        assignment = SeatingAssignmentFactory(
            section=section,
            desk=desk,
            student=student,
            position=1
        )

        assert assignment.id is not None
        assert assignment.section == section
        assert assignment.desk == desk
        assert assignment.student == student
        assert assignment.position == 1

    def test_seating_assignment_str(self):
        """Test __str__ method returns meaningful string."""
        layout = RoomLayoutFactory()
        desk = DeskFactory(room_layout=layout, row=2, column=3)
        section = SectionFactory(room_layout=layout)
        student = StudentFactory(first_name='John', last_name='Doe', current_section=section)

        assignment = SeatingAssignmentFactory(
            section=section, desk=desk, student=student, position=1
        )

        result = str(assignment)
        assert 'John Doe' in result

    def test_unique_student_per_section(self):
        """Test a student can only sit in one desk per section."""
        layout = RoomLayoutFactory()
        desk1 = DeskFactory(room_layout=layout, row=0, column=0)
        desk2 = DeskFactory(room_layout=layout, row=0, column=1)
        section = SectionFactory(room_layout=layout)
        student = StudentFactory(current_section=section, status='active')

        SeatingAssignmentFactory(section=section, desk=desk1, student=student, position=1)

        with pytest.raises(Exception):
            SeatingAssignmentFactory(section=section, desk=desk2, student=student, position=1)

    def test_unique_position_per_desk(self):
        """Test only one student per position per desk in a section."""
        layout = RoomLayoutFactory()
        desk = DeskFactory(room_layout=layout, row=0, column=0, capacity=2)
        section = SectionFactory(room_layout=layout)
        student1 = StudentFactory(current_section=section, status='active')
        student2 = StudentFactory(current_section=section, status='active')

        SeatingAssignmentFactory(section=section, desk=desk, student=student1, position=1)

        with pytest.raises(Exception):
            SeatingAssignmentFactory(section=section, desk=desk, student=student2, position=1)

    def test_multiple_positions_on_same_desk(self):
        """Test multiple students can sit at different positions on the same desk."""
        layout = RoomLayoutFactory()
        desk = DeskFactory(room_layout=layout, row=0, column=0, capacity=3)
        section = SectionFactory(room_layout=layout)
        student1 = StudentFactory(current_section=section, status='active')
        student2 = StudentFactory(current_section=section, status='active')

        a1 = SeatingAssignmentFactory(section=section, desk=desk, student=student1, position=1)
        a2 = SeatingAssignmentFactory(section=section, desk=desk, student=student2, position=2)

        assert a1.position == 1
        assert a2.position == 2
        assert desk.assignments.count() == 2


@pytest.mark.django_db
class TestStudentPhoto:
    """Test cases for StudentPhoto model."""

    def test_create_student_photo(self):
        """Test creating a student photo."""
        photo = StudentPhotoFactory()

        assert photo.id is not None
        assert photo.student is not None
        assert photo.image is not None
        assert photo.status == 'approved'
        assert photo.is_current is True

    def test_photo_status_choices(self):
        """Test all valid status choices."""
        for status in ['pending', 'approved', 'rejected', 'expired']:
            photo = StudentPhotoFactory(status=status)
            assert photo.status == status

    def test_current_photo_flag(self):
        """Test is_current flag management."""
        student = StudentFactory()
        photo1 = StudentPhotoFactory(student=student, is_current=True, status='approved')
        photo2 = StudentPhotoFactory(student=student, is_current=False, status='pending')

        assert photo1.is_current is True
        assert photo2.is_current is False

    def test_student_photos_related_name(self):
        """Test student.photos related_name access."""
        student = StudentFactory()
        StudentPhotoFactory(student=student, is_current=True, status='approved')
        StudentPhotoFactory(student=student, is_current=False, status='pending')

        assert student.photos.count() == 2
        assert student.photos.filter(is_current=True, status='approved').count() == 1
