"""
Academic factories for testing (AcademicYear, Grade, Section, Student,
RoomLayout, Desk, SeatingAssignment, StudentPhoto).
"""

import factory
from faker import Faker
from datetime import date, timedelta

from academics.models import (
    AcademicYear, Grade, Section, Student, Subject,
    RoomLayout, Desk, SeatingAssignment, StudentPhoto,
)

fake = Faker()


class AcademicYearFactory(factory.django.DjangoModelFactory):
    """Factory for creating AcademicYear instances."""

    class Meta:
        model = AcademicYear
        django_get_or_create = ('name',)

    name = factory.LazyFunction(lambda: f"{date.today().year}-{str(date.today().year + 1)[-2:]}")
    start_date = factory.LazyFunction(lambda: date(date.today().year, 4, 1))
    end_date = factory.LazyFunction(lambda: date(date.today().year + 1, 3, 31))
    status = 'active'
    is_current = True
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Ensure unique name by appending random suffix if needed."""
        name = kwargs.get('name')
        if name and model_class.objects.filter(name=name).exists():
            kwargs['name'] = f"{name}-{fake.random_int(min=1, max=999)}"
        return super()._create(model_class, *args, **kwargs)


class SubjectFactory(factory.django.DjangoModelFactory):
    """Factory for creating Subject instances."""

    class Meta:
        model = Subject
        django_get_or_create = ('code',)

    name = factory.Faker('random_element', elements=[
        'Mathematics', 'Science', 'English', 'Hindi', 'Social Studies',
        'Computer Science', 'Physical Education', 'Art', 'Music'
    ])
    code = factory.LazyAttribute(lambda obj: obj.name[:3].upper() + str(fake.random_int(min=100, max=999)))
    description = factory.Faker('paragraph')
    is_active = True


class GradeFactory(factory.django.DjangoModelFactory):
    """Factory for creating Grade instances."""

    class Meta:
        model = Grade

    academic_year = factory.SubFactory(AcademicYearFactory)
    number = factory.Faker('random_int', min=1, max=12)
    name = factory.LazyAttribute(lambda obj: f"Class {obj.number}")
    description = factory.Faker('sentence')
    display_order = factory.LazyAttribute(lambda obj: obj.number)
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Handle unique_together constraint for academic_year and number."""
        academic_year = kwargs.get('academic_year')
        number = kwargs.get('number')

        if academic_year and number:
            existing = model_class.objects.filter(
                academic_year=academic_year,
                number=number
            ).first()
            if existing:
                return existing

        return super()._create(model_class, *args, **kwargs)


class SectionFactory(factory.django.DjangoModelFactory):
    """Factory for creating Section instances."""

    class Meta:
        model = Section

    grade = factory.SubFactory(GradeFactory)
    academic_year = factory.LazyAttribute(lambda obj: obj.grade.academic_year)
    name = factory.Faker('random_element', elements=['A', 'B', 'C', 'D'])
    room_number = factory.LazyFunction(lambda: f"Room-{fake.random_int(min=101, max=999)}")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Handle unique_together constraint for grade, name, academic_year."""
        grade = kwargs.get('grade')
        name = kwargs.get('name')
        academic_year = kwargs.get('academic_year')

        if grade and name and academic_year:
            existing = model_class.objects.filter(
                grade=grade,
                name=name,
                academic_year=academic_year
            ).first()
            if existing:
                return existing

        return super()._create(model_class, *args, **kwargs)


class StudentFactory(factory.django.DjangoModelFactory):
    """Factory for creating Student instances."""

    class Meta:
        model = Student
        django_get_or_create = ('admission_number',)

    admission_number = factory.LazyFunction(
        lambda: f"SVP{date.today().year % 100}{fake.random_int(min=10000, max=99999)}"
    )
    roll_number = factory.LazyFunction(lambda: str(fake.random_int(min=1, max=60)))
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=5, maximum_age=18)
    gender = factory.Faker('random_element', elements=['male', 'female'])
    email = factory.LazyAttribute(lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@student.example.com")
    phone = factory.Faker('phone_number')
    address_line1 = factory.Faker('street_address')
    address_line2 = factory.Faker('secondary_address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    country = 'India'
    postal_code = factory.Faker('postcode')
    admission_date = factory.Faker('date_between', start_date='-5y', end_date='today')
    blood_group = factory.Faker('random_element', elements=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
    status = 'active'

    # Optional relationships
    current_section = None
    academic_year = None
    user_profile = None

    class Params:
        """Traits for different student states."""
        with_section = factory.Trait(
            current_section=factory.SubFactory(SectionFactory),
            academic_year=factory.LazyAttribute(lambda obj: obj.current_section.academic_year if obj.current_section else None)
        )
        graduated = factory.Trait(
            status='graduated'
        )
        transferred = factory.Trait(
            status='transferred'
        )
        inactive = factory.Trait(
            status='inactive'
        )


class RoomLayoutFactory(factory.django.DjangoModelFactory):
    """Factory for creating RoomLayout instances."""

    class Meta:
        model = RoomLayout

    name = factory.LazyFunction(lambda: f"Room {fake.random_int(min=101, max=999)} Layout")
    rows = 5
    columns = 6
    description = factory.Faker('sentence')
    is_active = True


class DeskFactory(factory.django.DjangoModelFactory):
    """Factory for creating Desk instances."""

    class Meta:
        model = Desk

    room_layout = factory.SubFactory(RoomLayoutFactory)
    row = 0
    column = 0
    capacity = 2
    is_active = True
    label = factory.LazyAttribute(lambda obj: f"R{obj.row + 1}-C{obj.column + 1}")


class SeatingAssignmentFactory(factory.django.DjangoModelFactory):
    """Factory for creating SeatingAssignment instances."""

    class Meta:
        model = SeatingAssignment

    section = factory.SubFactory(SectionFactory)
    desk = factory.SubFactory(DeskFactory)
    student = factory.SubFactory(StudentFactory)
    position = 1


class StudentPhotoFactory(factory.django.DjangoModelFactory):
    """Factory for creating StudentPhoto instances."""

    class Meta:
        model = StudentPhoto

    student = factory.SubFactory(StudentFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    image = factory.django.ImageField(filename='test_photo.jpg', width=200, height=200)
    status = 'approved'
    is_current = True
