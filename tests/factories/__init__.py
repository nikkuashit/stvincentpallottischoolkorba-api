"""
Test factories for creating test data.

Usage:
    from tests.factories import UserFactory, StudentFactory

    user = UserFactory()
    student = StudentFactory(first_name="John")

Traits:
    UserProfileFactory(admin=True)  # Creates a super_admin user
    UserProfileFactory(teacher=True)  # Creates a teacher with employee_id
    StudentFactory(with_section=True)  # Creates student with section assigned
"""

from tests.factories.user_factories import UserFactory, UserProfileFactory
from tests.factories.tenant_factories import (
    OrganizationFactory,
    SchoolFactory,
    SubscriptionPlanFactory,
    SubscriptionFactory
)
from tests.factories.academic_factories import (
    AcademicYearFactory,
    GradeFactory,
    SectionFactory,
    StudentFactory,
    SubjectFactory,
    RoomLayoutFactory,
    DeskFactory,
    SeatingAssignmentFactory,
    StudentPhotoFactory,
)
from tests.factories.cms_factories import (
    NavigationMenuFactory,
    PageFactory,
    SectionModelFactory,
    GalleryFactory,
    SliderFactory,
    MarqueeFactory
)

__all__ = [
    # User factories
    'UserFactory',
    'UserProfileFactory',
    # Tenant factories
    'OrganizationFactory',
    'SchoolFactory',
    'SubscriptionPlanFactory',
    'SubscriptionFactory',
    # Academic factories
    'AcademicYearFactory',
    'GradeFactory',
    'SectionFactory',
    'StudentFactory',
    'SubjectFactory',
    'RoomLayoutFactory',
    'DeskFactory',
    'SeatingAssignmentFactory',
    'StudentPhotoFactory',
    # CMS factories
    'NavigationMenuFactory',
    'PageFactory',
    'SectionModelFactory',
    'GalleryFactory',
    'SliderFactory',
    'MarqueeFactory',
]
