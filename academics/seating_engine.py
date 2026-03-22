"""
Seating Engine — Multi-Pass Rule Engine for constraint-based auto-assign.

Pure Python module (no Django ORM). Accepts DTOs and returns assignment results.
The view layer converts ORM objects to DTOs and persists results.

Algorithm (5-pass for gendered modes):
1. Partition: Split students by gender
2. Sort: Sort each group by chosen criteria
3. Allocate Zones: Assign desk groups to each gender based on mode
4. Fill: Place students into their zone's desks
5. Overflow: Place remaining students into any available seats
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field


# =============================================================================
# Data Transfer Objects
# =============================================================================

@dataclass
class StudentData:
    id: str
    roll_number: str
    first_name: str
    last_name: str
    gender: str  # 'male', 'female', 'other'


@dataclass
class DeskData:
    id: str
    row: int
    column: int
    capacity: int


@dataclass
class Assignment:
    desk_id: str
    student_id: str
    position: int


@dataclass
class EngineResult:
    assignments: list[Assignment] = field(default_factory=list)
    unassigned: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    constraints_applied: dict = field(default_factory=dict)


# =============================================================================
# Sort Helpers
# =============================================================================

_NUMERIC_RE = re.compile(r'(\d+)')


def _roll_number_sort_key(student: StudentData):
    """
    Sort by roll number with numeric awareness.
    '7A01' → ('7A', 1), '10' → ('', 10), 'abc' → ('abc', 999999)
    """
    rn = student.roll_number or ''
    # Split into text and numeric parts for natural sort
    parts = _NUMERIC_RE.split(rn)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part), ''))
        else:
            key.append((1, 0, part.lower()))
    if not key:
        key = [(2, 999999, '')]
    return (key, student.last_name.lower(), student.first_name.lower())


def _alphabetical_sort_key(student: StudentData):
    """Sort by first name, then last name."""
    return (student.first_name.lower(), student.last_name.lower())


# =============================================================================
# SeatingEngine
# =============================================================================

class SeatingEngine:
    """
    Multi-Pass Rule Engine for constraint-based seating assignment.

    Usage:
        engine = SeatingEngine(students, desks, constraints)
        errors = engine.validate()
        if errors:
            raise ValueError(errors)
        result = engine.run()
    """

    VALID_GENDER_MODES = ('none', 'same_gender_desk', 'gender_columns', 'alternating_rows')
    VALID_PRIORITIES = ('female_first', 'male_first')
    VALID_SORT_BY = ('roll_number', 'alphabetical', 'random')

    def __init__(
        self,
        students: list[StudentData],
        desks: list[DeskData],
        constraints: dict | None = None,
    ):
        self.students = list(students)
        self.desks = sorted(desks, key=lambda d: (d.row, d.column))
        self.constraints = constraints or {}
        self.gender_mode = self.constraints.get('gender_mode', 'none')
        self.gender_priority = self.constraints.get('gender_priority', 'female_first')
        self.sort_by = self.constraints.get('sort_by', 'roll_number')
        self.warnings: list[str] = []

    def validate(self) -> list[str]:
        """Return list of validation errors (empty = valid)."""
        errors = []
        if self.gender_mode not in self.VALID_GENDER_MODES:
            errors.append(f"Invalid gender_mode: {self.gender_mode}")
        if self.gender_priority not in self.VALID_PRIORITIES:
            errors.append(f"Invalid gender_priority: {self.gender_priority}")
        if self.sort_by not in self.VALID_SORT_BY:
            errors.append(f"Invalid sort_by: {self.sort_by}")
        if not self.desks:
            errors.append("No active desks in layout")
        return errors

    def run(self) -> EngineResult:
        """Execute the assignment algorithm and return results."""
        if not self.students:
            return EngineResult(
                constraints_applied=self._constraints_dict(),
            )

        if self.gender_mode == 'none':
            return self._run_simple()
        return self._run_gendered()

    # -------------------------------------------------------------------------
    # Simple mode (no gender constraints)
    # -------------------------------------------------------------------------

    def _run_simple(self) -> EngineResult:
        """Sort students and fill desks sequentially."""
        sorted_students = self._sort_group(self.students)
        assignments, unassigned = self._fill_desks(sorted_students, self.desks)
        return EngineResult(
            assignments=assignments,
            unassigned=[s.id for s in unassigned],
            warnings=list(self.warnings),
            constraints_applied=self._constraints_dict(),
        )

    # -------------------------------------------------------------------------
    # Gendered modes
    # -------------------------------------------------------------------------

    def _run_gendered(self) -> EngineResult:
        """Multi-pass algorithm with gender-based desk allocation."""
        # Pass 1: Partition
        priority_gender, secondary_gender = self._get_gender_order()
        primary_group, secondary_group, other_group = self._partition_by_gender(
            priority_gender, secondary_gender,
        )

        # Warn about 'other' gender
        if other_group:
            self.warnings.append(
                f"{len(other_group)} student(s) with gender='other' "
                f"placed in remaining seats"
            )

        # Pass 2: Sort each group
        primary_sorted = self._sort_group(primary_group)
        secondary_sorted = self._sort_group(secondary_group)
        other_sorted = self._sort_group(other_group)

        # Pass 3: Allocate zones (which desks go to which gender)
        if self.gender_mode == 'same_gender_desk':
            return self._run_same_gender_desk(
                primary_sorted, secondary_sorted, other_sorted,
            )
        elif self.gender_mode == 'gender_columns':
            return self._run_gender_columns(
                primary_sorted, secondary_sorted, other_sorted,
            )
        elif self.gender_mode == 'alternating_rows':
            return self._run_alternating_rows(
                primary_sorted, secondary_sorted, other_sorted,
            )

        # Shouldn't reach here if validated
        return self._run_simple()

    # -------------------------------------------------------------------------
    # same_gender_desk: allocate whole desks to one gender
    # -------------------------------------------------------------------------

    def _run_same_gender_desk(
        self,
        primary: list[StudentData],
        secondary: list[StudentData],
        other: list[StudentData],
    ) -> EngineResult:
        """Allocate consecutive desks to each gender group."""
        all_assignments = []
        remaining_desks = list(self.desks)

        # Fill primary gender into consecutive desks
        primary_assignments, primary_leftover, remaining_desks = \
            self._fill_desks_consume(primary, remaining_desks)
        all_assignments.extend(primary_assignments)

        # Fill secondary gender into next consecutive desks
        secondary_assignments, secondary_leftover, remaining_desks = \
            self._fill_desks_consume(secondary, remaining_desks)
        all_assignments.extend(secondary_assignments)

        # Fill 'other' gender into remaining whole desks
        other_assignments, other_leftover, remaining_desks = \
            self._fill_desks_consume(other, remaining_desks)
        all_assignments.extend(other_assignments)

        # Overflow pass: fill any partially-used desks with leftover students
        overflow = list(primary_leftover) + list(secondary_leftover) + list(other_leftover)
        if overflow:
            partial_desks = self._get_remaining_desks(all_assignments)
            overflow_sorted = self._sort_group(overflow)
            o_assignments, o_leftover = self._fill_desks(overflow_sorted, partial_desks)
            all_assignments.extend(o_assignments)
            overflow = o_leftover

        unassigned = [s.id for s in overflow]

        # Sort assignments by desk order for consistent output
        all_assignments.sort(key=lambda a: self._desk_order(a.desk_id))

        return EngineResult(
            assignments=all_assignments,
            unassigned=unassigned,
            warnings=list(self.warnings),
            constraints_applied=self._constraints_dict(),
        )

    # -------------------------------------------------------------------------
    # gender_columns: split columns by gender
    # -------------------------------------------------------------------------

    def _run_gender_columns(
        self,
        primary: list[StudentData],
        secondary: list[StudentData],
        other: list[StudentData],
    ) -> EngineResult:
        """Left columns for primary gender, right columns for secondary."""
        # Get unique column indices sorted
        columns = sorted({d.column for d in self.desks})
        if not columns:
            return self._empty_result()

        # Split columns: first half for primary, second half for secondary
        mid = max(1, (len(columns) + 1) // 2)
        primary_cols = set(columns[:mid])
        secondary_cols = set(columns[mid:])

        primary_desks = [d for d in self.desks if d.column in primary_cols]
        secondary_desks = [d for d in self.desks if d.column in secondary_cols]

        all_assignments = []

        # Fill primary into primary columns
        p_assignments, p_leftover = self._fill_desks(primary, primary_desks)
        all_assignments.extend(p_assignments)

        # Fill secondary into secondary columns
        s_assignments, s_leftover = self._fill_desks(secondary, secondary_desks)
        all_assignments.extend(s_assignments)

        # Overflow: place leftover primary into secondary desks (and vice versa)
        remaining_desks = self._get_remaining_desks(all_assignments)
        overflow = list(p_leftover) + list(s_leftover) + list(other)
        overflow_sorted = self._sort_group(overflow)
        o_assignments, o_leftover = self._fill_desks(overflow_sorted, remaining_desks)
        all_assignments.extend(o_assignments)

        unassigned = [s.id for s in o_leftover]

        all_assignments.sort(key=lambda a: self._desk_order(a.desk_id))

        return EngineResult(
            assignments=all_assignments,
            unassigned=unassigned,
            warnings=list(self.warnings),
            constraints_applied=self._constraints_dict(),
        )

    # -------------------------------------------------------------------------
    # alternating_rows: even rows = primary, odd rows = secondary
    # -------------------------------------------------------------------------

    def _run_alternating_rows(
        self,
        primary: list[StudentData],
        secondary: list[StudentData],
        other: list[StudentData],
    ) -> EngineResult:
        """Even rows for primary gender, odd rows for secondary."""
        primary_desks = [d for d in self.desks if d.row % 2 == 0]
        secondary_desks = [d for d in self.desks if d.row % 2 == 1]

        all_assignments = []

        # Fill primary into even rows
        p_assignments, p_leftover = self._fill_desks(primary, primary_desks)
        all_assignments.extend(p_assignments)

        # Fill secondary into odd rows
        s_assignments, s_leftover = self._fill_desks(secondary, secondary_desks)
        all_assignments.extend(s_assignments)

        # Overflow into remaining seats
        remaining_desks = self._get_remaining_desks(all_assignments)
        overflow = list(p_leftover) + list(s_leftover) + list(other)
        overflow_sorted = self._sort_group(overflow)
        o_assignments, o_leftover = self._fill_desks(overflow_sorted, remaining_desks)
        all_assignments.extend(o_assignments)

        unassigned = [s.id for s in o_leftover]

        all_assignments.sort(key=lambda a: self._desk_order(a.desk_id))

        return EngineResult(
            assignments=all_assignments,
            unassigned=unassigned,
            warnings=list(self.warnings),
            constraints_applied=self._constraints_dict(),
        )

    # -------------------------------------------------------------------------
    # Shared helpers
    # -------------------------------------------------------------------------

    def _get_gender_order(self) -> tuple[str, str]:
        """Return (priority_gender, secondary_gender) based on gender_priority."""
        if self.gender_priority == 'male_first':
            return ('male', 'female')
        return ('female', 'male')

    def _partition_by_gender(
        self, primary_gender: str, secondary_gender: str,
    ) -> tuple[list[StudentData], list[StudentData], list[StudentData]]:
        """Split students into primary, secondary, and other gender groups."""
        primary = []
        secondary = []
        other = []
        for s in self.students:
            if s.gender == primary_gender:
                primary.append(s)
            elif s.gender == secondary_gender:
                secondary.append(s)
            else:
                other.append(s)
        return primary, secondary, other

    def _sort_group(self, students: list[StudentData]) -> list[StudentData]:
        """Sort a group of students based on the sort_by constraint."""
        if not students:
            return []
        if self.sort_by == 'random':
            result = list(students)
            random.shuffle(result)
            return result
        elif self.sort_by == 'alphabetical':
            return sorted(students, key=_alphabetical_sort_key)
        else:
            # Default: roll_number
            return sorted(students, key=_roll_number_sort_key)

    def _fill_desks(
        self,
        students: list[StudentData],
        desks: list[DeskData],
    ) -> tuple[list[Assignment], list[StudentData]]:
        """
        Fill desks sequentially with students.
        Returns (assignments, leftover_students).
        """
        assignments = []
        student_iter = iter(students)
        leftover = []
        done = False

        for desk in desks:
            if done:
                break
            for pos in range(1, desk.capacity + 1):
                try:
                    student = next(student_iter)
                    assignments.append(Assignment(
                        desk_id=desk.id,
                        student_id=student.id,
                        position=pos,
                    ))
                except StopIteration:
                    done = True
                    break

        # Remaining students
        leftover = list(student_iter)
        return assignments, leftover

    def _fill_desks_consume(
        self,
        students: list[StudentData],
        available_desks: list[DeskData],
    ) -> tuple[list[Assignment], list[StudentData], list[DeskData]]:
        """
        Fill desks and return the remaining (unused) desks.
        Only uses complete desks — doesn't partially fill the last desk
        unless all students fit.
        """
        assignments = []
        student_idx = 0
        desks_used = 0

        for desk in available_desks:
            if student_idx >= len(students):
                break
            desk_assignments = []
            for pos in range(1, desk.capacity + 1):
                if student_idx >= len(students):
                    break
                desk_assignments.append(Assignment(
                    desk_id=desk.id,
                    student_id=students[student_idx].id,
                    position=pos,
                ))
                student_idx += 1
            assignments.extend(desk_assignments)
            desks_used += 1

        leftover = students[student_idx:]
        remaining_desks = available_desks[desks_used:]
        return assignments, leftover, remaining_desks

    def _get_remaining_desks(self, current_assignments: list[Assignment]) -> list[DeskData]:
        """
        Get desks that still have available seats after current assignments.
        Returns new DeskData objects with reduced capacity for partially filled desks.
        """
        # Count seats used per desk
        seats_used: dict[str, int] = {}
        for a in current_assignments:
            seats_used[a.desk_id] = seats_used.get(a.desk_id, 0) + 1

        remaining = []
        for desk in self.desks:
            used = seats_used.get(desk.id, 0)
            available = desk.capacity - used
            if available > 0:
                remaining.append(DeskData(
                    id=desk.id,
                    row=desk.row,
                    column=desk.column,
                    capacity=available,
                ))
        return remaining

    def _desk_order(self, desk_id: str) -> tuple[int, int]:
        """Get (row, column) tuple for sorting by desk position."""
        for d in self.desks:
            if d.id == desk_id:
                return (d.row, d.column)
        return (999, 999)

    def _constraints_dict(self) -> dict:
        """Return the effective constraints as a dict."""
        return {
            'gender_mode': self.gender_mode,
            'gender_priority': self.gender_priority,
            'sort_by': self.sort_by,
        }

    def _empty_result(self) -> EngineResult:
        """Return an empty result."""
        return EngineResult(
            unassigned=[s.id for s in self.students],
            warnings=list(self.warnings),
            constraints_applied=self._constraints_dict(),
        )
