"""
Unit tests for the SeatingEngine (pure Python, no Django ORM required).

Tests cover:
- Validation of constraint parameters
- Simple mode (no gender constraints): roll_number, alphabetical, random sort
- same_gender_desk mode: same-gender students grouped per desk
- gender_columns mode: columns allocated by gender
- alternating_rows mode: rows alternate by gender
- 'other' gender handling and warnings
- Edge cases: empty students, single student, overflow, capacity=1 desks
"""

import pytest

from academics.seating_engine import (
    StudentData,
    DeskData,
    Assignment,
    EngineResult,
    SeatingEngine,
)


# =============================================================================
# Helpers
# =============================================================================

def make_students(specs):
    """
    Create StudentData list from compact specs.
    specs: list of (roll_number, first_name, last_name, gender)
    """
    return [
        StudentData(
            id=f'student-{i}',
            roll_number=s[0],
            first_name=s[1],
            last_name=s[2],
            gender=s[3],
        )
        for i, s in enumerate(specs)
    ]


def make_grid(rows, cols, capacity=2):
    """Create a grid of DeskData objects."""
    desks = []
    for r in range(rows):
        for c in range(cols):
            desks.append(DeskData(
                id=f'desk-{r}-{c}',
                row=r,
                column=c,
                capacity=capacity,
            ))
    return desks


def assigned_student_ids(result: EngineResult) -> list[str]:
    """Get ordered list of assigned student IDs."""
    return [a.student_id for a in result.assignments]


def assignments_by_desk(result: EngineResult) -> dict[str, list[str]]:
    """Group student IDs by desk ID."""
    by_desk = {}
    for a in result.assignments:
        by_desk.setdefault(a.desk_id, []).append(a.student_id)
    return by_desk


def get_student_gender(students, student_id):
    """Get gender for a student ID from the student list."""
    for s in students:
        if s.id == student_id:
            return s.gender
    return None


# =============================================================================
# TestEngineValidation
# =============================================================================

class TestEngineValidation:
    """Tests for constraint validation."""

    def test_valid_defaults(self):
        """Default constraints should pass validation."""
        engine = SeatingEngine([], [DeskData('d1', 0, 0, 2)])
        assert engine.validate() == []

    def test_invalid_gender_mode(self):
        students = make_students([('1', 'A', 'B', 'male')])
        desks = [DeskData('d1', 0, 0, 2)]
        engine = SeatingEngine(students, desks, {'gender_mode': 'invalid'})
        errors = engine.validate()
        assert any('gender_mode' in e for e in errors)

    def test_invalid_gender_priority(self):
        desks = [DeskData('d1', 0, 0, 2)]
        engine = SeatingEngine([], desks, {'gender_priority': 'other_first'})
        errors = engine.validate()
        assert any('gender_priority' in e for e in errors)

    def test_invalid_sort_by(self):
        desks = [DeskData('d1', 0, 0, 2)]
        engine = SeatingEngine([], desks, {'sort_by': 'height'})
        errors = engine.validate()
        assert any('sort_by' in e for e in errors)

    def test_no_desks(self):
        students = make_students([('1', 'A', 'B', 'male')])
        engine = SeatingEngine(students, [])
        errors = engine.validate()
        assert any('desks' in e.lower() for e in errors)

    def test_multiple_errors(self):
        engine = SeatingEngine([], [], {
            'gender_mode': 'bad',
            'sort_by': 'bad',
        })
        errors = engine.validate()
        assert len(errors) >= 2


# =============================================================================
# TestSimpleMode (gender_mode='none')
# =============================================================================

class TestSimpleMode:
    """Tests for simple mode (no gender constraints)."""

    def test_roll_number_sort(self):
        """Students should be assigned in roll number order."""
        students = make_students([
            ('3', 'Charlie', 'C', 'male'),
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
        ])
        desks = make_grid(1, 2, capacity=2)  # 4 seats
        engine = SeatingEngine(students, desks, {'sort_by': 'roll_number'})
        result = engine.run()

        assert result.constraints_applied['sort_by'] == 'roll_number'
        assert result.constraints_applied['gender_mode'] == 'none'
        ids = assigned_student_ids(result)
        # Student with roll 1 first, then 2, then 3
        assert ids == ['student-1', 'student-2', 'student-0']
        assert len(result.unassigned) == 0

    def test_alphabetical_sort(self):
        """Students should be assigned in alphabetical order (first name, then last name)."""
        students = make_students([
            ('3', 'Charlie', 'C', 'male'),
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
        ])
        desks = make_grid(1, 2, capacity=2)
        engine = SeatingEngine(students, desks, {'sort_by': 'alphabetical'})
        result = engine.run()

        ids = assigned_student_ids(result)
        # Alice, Bob, Charlie
        assert ids == ['student-1', 'student-2', 'student-0']

    def test_random_sort(self):
        """Random sort should assign all students (order not deterministic)."""
        students = make_students([
            (str(i), f'Student{i}', 'X', 'male')
            for i in range(10)
        ])
        desks = make_grid(2, 3, capacity=2)  # 12 seats
        engine = SeatingEngine(students, desks, {'sort_by': 'random'})
        result = engine.run()

        assert len(result.assignments) == 10
        assert len(result.unassigned) == 0
        assert result.constraints_applied['sort_by'] == 'random'

    def test_overflow(self):
        """More students than seats should leave some unassigned."""
        students = make_students([
            (str(i), f'S{i}', 'X', 'female') for i in range(5)
        ])
        desks = [DeskData('d1', 0, 0, 2)]  # Only 2 seats
        engine = SeatingEngine(students, desks)
        result = engine.run()

        assert len(result.assignments) == 2
        assert len(result.unassigned) == 3

    def test_empty_students(self):
        """No students should produce empty result."""
        desks = make_grid(2, 2)
        engine = SeatingEngine([], desks)
        result = engine.run()

        assert len(result.assignments) == 0
        assert len(result.unassigned) == 0

    def test_single_student(self):
        """Single student should be assigned to first desk, position 1."""
        students = make_students([('1', 'Solo', 'S', 'male')])
        desks = make_grid(1, 2)
        engine = SeatingEngine(students, desks)
        result = engine.run()

        assert len(result.assignments) == 1
        assert result.assignments[0].desk_id == 'desk-0-0'
        assert result.assignments[0].position == 1

    def test_fills_positions_sequentially(self):
        """Desks should fill positions 1, 2, ... up to capacity before moving on."""
        students = make_students([
            (str(i), f'S{i}', 'X', 'male') for i in range(4)
        ])
        desks = [
            DeskData('d1', 0, 0, 2),
            DeskData('d2', 0, 1, 2),
        ]
        engine = SeatingEngine(students, desks)
        result = engine.run()

        desk_map = assignments_by_desk(result)
        assert len(desk_map['d1']) == 2
        assert len(desk_map['d2']) == 2

    def test_no_constraints_default_behavior(self):
        """No constraints at all should default to roll_number sort, no gender mode."""
        students = make_students([
            ('2', 'B', 'B', 'male'),
            ('1', 'A', 'A', 'female'),
        ])
        desks = [DeskData('d1', 0, 0, 2)]
        engine = SeatingEngine(students, desks)
        result = engine.run()

        assert result.constraints_applied['gender_mode'] == 'none'
        assert result.constraints_applied['sort_by'] == 'roll_number'
        # Roll 1 first
        assert result.assignments[0].student_id == 'student-1'

    def test_numeric_roll_number_sort(self):
        """Roll numbers should be sorted numerically, not lexicographically."""
        students = make_students([
            ('10', 'Ten', 'T', 'male'),
            ('2', 'Two', 'T', 'male'),
            ('1', 'One', 'O', 'male'),
        ])
        desks = make_grid(1, 2, capacity=2)
        engine = SeatingEngine(students, desks, {'sort_by': 'roll_number'})
        result = engine.run()

        ids = assigned_student_ids(result)
        # 1, 2, 10 (numeric order)
        assert ids == ['student-2', 'student-1', 'student-0']


# =============================================================================
# TestSameGenderDesk
# =============================================================================

class TestSameGenderDesk:
    """Tests for same_gender_desk mode: each desk should have only one gender."""

    def test_basic_separation(self):
        """2 females and 1 male → desk1=[F,F], desk2=[M]."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Carol', 'C', 'female'),
        ])
        desks = make_grid(1, 2, capacity=2)  # 2 desks, 2 seats each
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'female_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        assert len(result.assignments) == 3
        desk_map = assignments_by_desk(result)

        # Each desk should have students of only one gender
        for desk_id, student_ids in desk_map.items():
            genders = {get_student_gender(students, sid) for sid in student_ids}
            assert len(genders) == 1, f"Desk {desk_id} has mixed genders: {genders}"

    def test_female_first_priority(self):
        """With female_first, female students should fill earlier desks."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Carol', 'C', 'female'),
            ('4', 'Dan', 'D', 'male'),
        ])
        desks = [
            DeskData('d0', 0, 0, 2),
            DeskData('d1', 0, 1, 2),
        ]
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'female_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        desk_map = assignments_by_desk(result)
        # First desk should have females
        d0_genders = {get_student_gender(students, sid) for sid in desk_map['d0']}
        assert d0_genders == {'female'}

    def test_male_first_priority(self):
        """With male_first, male students should fill earlier desks."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Carol', 'C', 'female'),
            ('4', 'Dan', 'D', 'male'),
        ])
        desks = [
            DeskData('d0', 0, 0, 2),
            DeskData('d1', 0, 1, 2),
        ]
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'male_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        desk_map = assignments_by_desk(result)
        d0_genders = {get_student_gender(students, sid) for sid in desk_map['d0']}
        assert d0_genders == {'male'}

    def test_all_same_gender(self):
        """All female students should still fill correctly."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Carol', 'C', 'female'),
            ('3', 'Eve', 'E', 'female'),
        ])
        desks = make_grid(1, 2, capacity=2)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'female_first',
        })
        result = engine.run()

        assert len(result.assignments) == 3
        assert len(result.unassigned) == 0

    def test_unequal_ratio_overflow(self):
        """With 5F and 1M, capacity=2 desks: all should be assigned when enough seats.
        Overflow male fills remaining seat in partially-filled female desk."""
        students = make_students([
            ('1', 'A', 'A', 'female'),
            ('2', 'B', 'B', 'female'),
            ('3', 'C', 'C', 'female'),
            ('4', 'D', 'D', 'female'),
            ('5', 'E', 'E', 'female'),
            ('6', 'F', 'F', 'male'),
        ])
        desks = make_grid(1, 3, capacity=2)  # 6 seats total
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'female_first',
        })
        result = engine.run()

        assert len(result.assignments) == 6
        assert len(result.unassigned) == 0

        # First two desks should be fully female (no overflow needed)
        desk_map = assignments_by_desk(result)
        d0_genders = {get_student_gender(students, sid) for sid in desk_map['desk-0-0']}
        d1_genders = {get_student_gender(students, sid) for sid in desk_map['desk-0-1']}
        assert d0_genders == {'female'}
        assert d1_genders == {'female'}


# =============================================================================
# TestGenderColumns
# =============================================================================

class TestGenderColumns:
    """Tests for gender_columns mode: columns allocated by gender."""

    def test_basic_column_separation(self):
        """Priority gender in left columns, other in right columns."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Carol', 'C', 'female'),
            ('4', 'Dan', 'D', 'male'),
        ])
        # 2 rows, 2 columns
        desks = make_grid(2, 2, capacity=1)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'gender_columns',
            'gender_priority': 'female_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        assert len(result.assignments) == 4

        # Check column 0 has females, column 1 has males
        for a in result.assignments:
            desk_col = int(a.desk_id.split('-')[2])  # desk-R-C format
            gender = get_student_gender(students, a.student_id)
            if desk_col == 0:
                assert gender == 'female', f"Column 0 should be female, got {gender}"
            else:
                assert gender == 'male', f"Column 1 should be male, got {gender}"

    def test_male_first_columns(self):
        """With male_first, males should be in left columns."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Carol', 'C', 'female'),
            ('4', 'Dan', 'D', 'male'),
        ])
        desks = make_grid(2, 2, capacity=1)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'gender_columns',
            'gender_priority': 'male_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        for a in result.assignments:
            desk_col = int(a.desk_id.split('-')[2])
            gender = get_student_gender(students, a.student_id)
            if desk_col == 0:
                assert gender == 'male'
            else:
                assert gender == 'female'

    def test_uneven_split_overflow_to_other_columns(self):
        """When one gender has more students than their column capacity, overflow to other columns."""
        students = make_students([
            ('1', 'A', 'A', 'female'),
            ('2', 'B', 'B', 'female'),
            ('3', 'C', 'C', 'female'),
            ('4', 'D', 'D', 'male'),
        ])
        # 2 rows, 2 columns, capacity=1 → 2 seats per column
        desks = make_grid(2, 2, capacity=1)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'gender_columns',
            'gender_priority': 'female_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        # All 4 should be assigned (3F fill col0 + overflow to col1, 1M fills remaining)
        assert len(result.assignments) == 4
        assert len(result.unassigned) == 0


# =============================================================================
# TestAlternatingRows
# =============================================================================

class TestAlternatingRows:
    """Tests for alternating_rows mode: rows alternate by gender."""

    def test_basic_alternating(self):
        """Even rows = priority gender, odd rows = other gender."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Carol', 'C', 'female'),
            ('4', 'Dan', 'D', 'male'),
        ])
        # 2 rows, 2 columns, capacity=1
        desks = make_grid(2, 2, capacity=1)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'alternating_rows',
            'gender_priority': 'female_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        assert len(result.assignments) == 4

        for a in result.assignments:
            desk_row = int(a.desk_id.split('-')[1])
            gender = get_student_gender(students, a.student_id)
            if desk_row % 2 == 0:
                assert gender == 'female', f"Row {desk_row} should be female"
            else:
                assert gender == 'male', f"Row {desk_row} should be male"

    def test_male_first_alternating(self):
        """With male_first, even rows should have males."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Carol', 'C', 'female'),
            ('4', 'Dan', 'D', 'male'),
        ])
        desks = make_grid(2, 2, capacity=1)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'alternating_rows',
            'gender_priority': 'male_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        for a in result.assignments:
            desk_row = int(a.desk_id.split('-')[1])
            gender = get_student_gender(students, a.student_id)
            if desk_row % 2 == 0:
                assert gender == 'male'
            else:
                assert gender == 'female'

    def test_single_row_fallback(self):
        """With only 1 row, priority gender fills it; other gender overflows."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
        ])
        desks = make_grid(1, 2, capacity=1)  # 1 row, 2 seats
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'alternating_rows',
            'gender_priority': 'female_first',
            'sort_by': 'roll_number',
        })
        result = engine.run()

        # Both should be assigned (female fills row 0, male overflows into remaining seats)
        assert len(result.assignments) == 2
        assert len(result.unassigned) == 0


# =============================================================================
# TestOtherGenderHandling
# =============================================================================

class TestOtherGenderHandling:
    """Tests for students with gender='other'."""

    def test_other_gender_placed_in_remaining_seats(self):
        """Students with gender='other' should be placed in remaining seats."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Bob', 'B', 'male'),
            ('3', 'Pat', 'P', 'other'),
        ])
        desks = make_grid(1, 2, capacity=2)  # 4 seats
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'female_first',
        })
        result = engine.run()

        assert len(result.assignments) == 3
        assert len(result.unassigned) == 0

    def test_other_gender_produces_warning(self):
        """When 'other' gender students exist with gender constraints, a warning should be issued."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Pat', 'P', 'other'),
        ])
        desks = make_grid(1, 2, capacity=2)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
        })
        result = engine.run()

        assert len(result.warnings) > 0
        assert any('other' in w.lower() for w in result.warnings)

    def test_no_warning_in_none_mode(self):
        """No warning should be issued in gender_mode='none' even with 'other' gender."""
        students = make_students([
            ('1', 'Alice', 'A', 'female'),
            ('2', 'Pat', 'P', 'other'),
        ])
        desks = make_grid(1, 1, capacity=2)
        engine = SeatingEngine(students, desks, {'gender_mode': 'none'})
        result = engine.run()

        assert len(result.warnings) == 0


# =============================================================================
# TestEdgeCases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_all_desks_capacity_one(self):
        """Each desk holds exactly 1 student."""
        students = make_students([
            ('1', 'A', 'A', 'female'),
            ('2', 'B', 'B', 'male'),
        ])
        desks = make_grid(1, 2, capacity=1)
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'female_first',
        })
        result = engine.run()

        assert len(result.assignments) == 2
        desk_map = assignments_by_desk(result)
        for student_ids in desk_map.values():
            assert len(student_ids) == 1

    def test_mixed_capacity_desks(self):
        """Desks with different capacities should be handled correctly."""
        students = make_students([
            (str(i), f'S{i}', 'X', 'female') for i in range(5)
        ])
        desks = [
            DeskData('d0', 0, 0, 3),  # 3 seats
            DeskData('d1', 0, 1, 1),  # 1 seat
            DeskData('d2', 1, 0, 2),  # 2 seats
        ]
        engine = SeatingEngine(students, desks)
        result = engine.run()

        assert len(result.assignments) == 5
        desk_map = assignments_by_desk(result)
        assert len(desk_map['d0']) == 3
        assert len(desk_map['d1']) == 1
        assert len(desk_map['d2']) == 1  # Only 1 left after filling d0(3)+d1(1)

    def test_desks_not_in_order(self):
        """Engine should sort desks by (row, column) regardless of input order."""
        students = make_students([('1', 'A', 'A', 'male')])
        desks = [
            DeskData('d-1-1', 1, 1, 2),
            DeskData('d-0-0', 0, 0, 2),
            DeskData('d-0-1', 0, 1, 2),
        ]
        engine = SeatingEngine(students, desks)
        result = engine.run()

        # Student should be in desk-0-0 (first by row, column)
        assert result.assignments[0].desk_id == 'd-0-0'

    def test_position_values(self):
        """Positions should be 1-based and sequential within a desk."""
        students = make_students([
            ('1', 'A', 'A', 'male'),
            ('2', 'B', 'B', 'male'),
            ('3', 'C', 'C', 'male'),
        ])
        desks = [DeskData('d0', 0, 0, 3)]
        engine = SeatingEngine(students, desks)
        result = engine.run()

        positions = [a.position for a in result.assignments]
        assert positions == [1, 2, 3]

    def test_constraints_applied_echoed(self):
        """Result should echo the constraints that were applied."""
        students = make_students([('1', 'A', 'A', 'male')])
        desks = [DeskData('d0', 0, 0, 2)]
        engine = SeatingEngine(students, desks, {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'male_first',
            'sort_by': 'alphabetical',
        })
        result = engine.run()

        assert result.constraints_applied == {
            'gender_mode': 'same_gender_desk',
            'gender_priority': 'male_first',
            'sort_by': 'alphabetical',
        }

    def test_alphanumeric_roll_number_sort(self):
        """Alphanumeric roll numbers should sort numerically where possible."""
        students = make_students([
            ('7A03', 'C', 'C', 'male'),
            ('7A01', 'A', 'A', 'male'),
            ('7A02', 'B', 'B', 'male'),
        ])
        desks = make_grid(1, 2, capacity=2)
        engine = SeatingEngine(students, desks, {'sort_by': 'roll_number'})
        result = engine.run()

        ids = assigned_student_ids(result)
        assert ids == ['student-1', 'student-2', 'student-0']
