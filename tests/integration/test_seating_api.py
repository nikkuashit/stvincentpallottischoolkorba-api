"""
Integration tests for seating arrangement API endpoints.

Tests cover:
- Section seating endpoint (GET /academics/sections/{id}/seating/)
- Auto-assign endpoint (POST /academics/seating-assignments/auto-assign/)
- Swap seats endpoint (POST /academics/seating-assignments/swap/)
- Clear seating endpoint (POST /academics/seating-assignments/clear/)
- Photo URL inclusion in seating responses
"""

import pytest
from rest_framework import status

from tests.factories import (
    AcademicYearFactory,
    GradeFactory,
    SectionFactory,
    StudentFactory,
    RoomLayoutFactory,
    DeskFactory,
    SeatingAssignmentFactory,
    StudentPhotoFactory,
)


@pytest.mark.django_db
@pytest.mark.integration
class TestSectionSeatingAPI:
    """Tests for the section seating endpoint."""

    def _create_section_with_layout(self):
        """Helper to create a section with room layout and desks."""
        ay = AcademicYearFactory(name='2025-26')
        grade = GradeFactory(academic_year=ay, number=5)
        layout = RoomLayoutFactory(rows=2, columns=2)
        DeskFactory(room_layout=layout, row=0, column=0, capacity=2)
        DeskFactory(room_layout=layout, row=0, column=1, capacity=2)
        DeskFactory(room_layout=layout, row=1, column=0, capacity=2)
        DeskFactory(room_layout=layout, row=1, column=1, capacity=2)
        section = SectionFactory(
            grade=grade,
            academic_year=ay,
            name='A',
            room_layout=layout,
        )
        return section, layout

    def test_seating_returns_layout_and_desks(self, admin_client):
        """Test seating endpoint returns room layout with desks."""
        section, layout = self._create_section_with_layout()

        response = admin_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['room_layout'] is not None
        assert response.data['room_layout']['id'] == str(layout.id)
        assert len(response.data['room_layout']['desks']) == 4

    def test_seating_without_layout(self, admin_client):
        """Test seating endpoint when section has no room layout."""
        section = SectionFactory(room_layout=None)

        response = admin_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['room_layout'] is None
        assert response.data['seating_assignments'] == []

    def test_seating_shows_assignments(self, admin_client):
        """Test seating endpoint returns seating assignments."""
        section, layout = self._create_section_with_layout()
        desk = layout.desks.first()
        student = StudentFactory(current_section=section, status='active')
        SeatingAssignmentFactory(
            section=section, desk=desk, student=student, position=1,
        )

        response = admin_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['seating_assignments']) == 1
        assignment = response.data['seating_assignments'][0]
        assert assignment['student_info']['id'] == str(student.id)
        assert assignment['student_info']['first_name'] == student.first_name

    def test_seating_shows_unassigned_students(self, admin_client):
        """Test seating endpoint returns unassigned students."""
        section, layout = self._create_section_with_layout()
        student = StudentFactory(
            current_section=section, status='active',
            first_name='Unassigned', last_name='Student',
        )

        response = admin_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['unassigned_students']) == 1
        assert response.data['unassigned_students'][0]['first_name'] == 'Unassigned'

    def test_seating_includes_photo_url_in_assignments(self, admin_client):
        """Test photo_url is included in assignment student_info."""
        section, layout = self._create_section_with_layout()
        desk = layout.desks.first()
        student = StudentFactory(current_section=section, status='active')
        StudentPhotoFactory(student=student, is_current=True, status='approved')
        SeatingAssignmentFactory(
            section=section, desk=desk, student=student, position=1,
        )

        response = admin_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_200_OK
        assignment = response.data['seating_assignments'][0]
        assert assignment['student_info']['photo_url'] is not None
        assert 'test_photo' in assignment['student_info']['photo_url']

    def test_seating_photo_url_none_without_photo(self, admin_client):
        """Test photo_url is None when student has no approved photo."""
        section, layout = self._create_section_with_layout()
        desk = layout.desks.first()
        student = StudentFactory(current_section=section, status='active')
        SeatingAssignmentFactory(
            section=section, desk=desk, student=student, position=1,
        )

        response = admin_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_200_OK
        assignment = response.data['seating_assignments'][0]
        assert assignment['student_info']['photo_url'] is None

    def test_seating_includes_photo_url_in_unassigned(self, admin_client):
        """Test photo_url is included in unassigned_students."""
        section, layout = self._create_section_with_layout()
        student = StudentFactory(current_section=section, status='active')
        StudentPhotoFactory(student=student, is_current=True, status='approved')

        response = admin_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_200_OK
        unassigned = response.data['unassigned_students'][0]
        assert unassigned['photo_url'] is not None

    def test_seating_requires_auth(self, api_client):
        """Test seating endpoint requires authentication."""
        section = SectionFactory()

        response = api_client.get(f'/academics/sections/{section.id}/seating/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.integration
class TestAutoAssignAPI:
    """Tests for the auto-assign seating endpoint."""

    def _create_section_with_students(self, num_students=3):
        """Helper to create a section with layout, desks, and students."""
        ay = AcademicYearFactory(name='2025-26')
        grade = GradeFactory(academic_year=ay, number=5)
        layout = RoomLayoutFactory(rows=1, columns=2)
        DeskFactory(room_layout=layout, row=0, column=0, capacity=2)
        DeskFactory(room_layout=layout, row=0, column=1, capacity=2)
        section = SectionFactory(
            grade=grade, academic_year=ay, name='A', room_layout=layout,
        )
        students = []
        for i in range(num_students):
            students.append(StudentFactory(
                current_section=section,
                status='active',
                roll_number=str(i + 1),
            ))
        return section, layout, students

    def test_auto_assign_success(self, admin_client):
        """Test auto-assign assigns students to desks in roll number order."""
        section, layout, students = self._create_section_with_students(3)

        response = admin_client.post(
            '/academics/seating-assignments/auto-assign/',
            {'section_id': str(section.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['assigned_count'] == 3
        assert response.data['unassigned_count'] == 0
        assert len(response.data['assignments']) == 3

    def test_auto_assign_overflow(self, admin_client):
        """Test auto-assign reports unassigned students when overflow."""
        section, layout, students = self._create_section_with_students(6)

        response = admin_client.post(
            '/academics/seating-assignments/auto-assign/',
            {'section_id': str(section.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['assigned_count'] == 4  # 2 desks × 2 capacity
        assert response.data['unassigned_count'] == 2

    def test_auto_assign_without_layout(self, admin_client):
        """Test auto-assign fails when section has no room layout."""
        section = SectionFactory(room_layout=None)

        response = admin_client.post(
            '/academics/seating-assignments/auto-assign/',
            {'section_id': str(section.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_auto_assign_missing_section_id(self, admin_client):
        """Test auto-assign fails without section_id."""
        response = admin_client.post(
            '/academics/seating-assignments/auto-assign/',
            {},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_auto_assign_includes_photo_url(self, admin_client):
        """Test auto-assign response includes photo_url in assignments."""
        section, layout, students = self._create_section_with_students(2)
        StudentPhotoFactory(student=students[0], is_current=True, status='approved')

        response = admin_client.post(
            '/academics/seating-assignments/auto-assign/',
            {'section_id': str(section.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        # Find the assignment for student with photo
        found = False
        for a in response.data['assignments']:
            if a['student_info']['id'] == str(students[0].id):
                assert a['student_info']['photo_url'] is not None
                found = True
            else:
                assert a['student_info']['photo_url'] is None
        assert found


@pytest.mark.django_db
@pytest.mark.integration
class TestSwapSeatsAPI:
    """Tests for the swap seats endpoint."""

    def test_swap_success(self, admin_client):
        """Test swapping two students' seats."""
        layout = RoomLayoutFactory()
        desk1 = DeskFactory(room_layout=layout, row=0, column=0)
        desk2 = DeskFactory(room_layout=layout, row=0, column=1)
        section = SectionFactory(room_layout=layout)
        student1 = StudentFactory(current_section=section, status='active')
        student2 = StudentFactory(current_section=section, status='active')

        a1 = SeatingAssignmentFactory(section=section, desk=desk1, student=student1, position=1)
        a2 = SeatingAssignmentFactory(section=section, desk=desk2, student=student2, position=1)

        response = admin_client.post(
            '/academics/seating-assignments/swap/',
            {'assignment_id_1': str(a1.id), 'assignment_id_2': str(a2.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Seats swapped successfully'
        # Verify students were swapped
        assert response.data['assignment_1']['student_info']['id'] == str(student2.id)
        assert response.data['assignment_2']['student_info']['id'] == str(student1.id)

    def test_swap_missing_ids(self, admin_client):
        """Test swap fails when IDs are missing."""
        response = admin_client.post(
            '/academics/seating-assignments/swap/',
            {'assignment_id_1': 'some-id'},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_swap_different_sections(self, admin_client):
        """Test swap fails when assignments are from different sections."""
        layout1 = RoomLayoutFactory()
        layout2 = RoomLayoutFactory()
        desk1 = DeskFactory(room_layout=layout1, row=0, column=0)
        desk2 = DeskFactory(room_layout=layout2, row=0, column=0)
        section1 = SectionFactory(room_layout=layout1)
        section2 = SectionFactory(room_layout=layout2)
        student1 = StudentFactory(current_section=section1, status='active')
        student2 = StudentFactory(current_section=section2, status='active')

        a1 = SeatingAssignmentFactory(section=section1, desk=desk1, student=student1, position=1)
        a2 = SeatingAssignmentFactory(section=section2, desk=desk2, student=student2, position=1)

        response = admin_client.post(
            '/academics/seating-assignments/swap/',
            {'assignment_id_1': str(a1.id), 'assignment_id_2': str(a2.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.integration
class TestClearSeatingAPI:
    """Tests for the clear seating endpoint."""

    def test_clear_success(self, admin_client):
        """Test clearing all seating assignments for a section."""
        layout = RoomLayoutFactory()
        desk = DeskFactory(room_layout=layout, row=0, column=0, capacity=2)
        section = SectionFactory(room_layout=layout)
        student1 = StudentFactory(current_section=section, status='active')
        student2 = StudentFactory(current_section=section, status='active')

        SeatingAssignmentFactory(section=section, desk=desk, student=student1, position=1)
        SeatingAssignmentFactory(section=section, desk=desk, student=student2, position=2)

        response = admin_client.post(
            '/academics/seating-assignments/clear/',
            {'section_id': str(section.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_clear_missing_section_id(self, admin_client):
        """Test clear fails without section_id."""
        response = admin_client.post(
            '/academics/seating-assignments/clear/',
            {},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
