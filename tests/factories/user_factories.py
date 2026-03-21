"""
User and UserProfile factories for testing.
"""

import factory
from faker import Faker
from django.contrib.auth import get_user_model

from accounts.models import UserProfile

fake = Faker()
User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating Django User instances."""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.LazyFunction(lambda: fake.user_name() + str(fake.random_int(min=1, max=9999)))
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password for the user."""
        password = extracted or 'testpass123'
        self.set_password(password)
        if create:
            self.save()

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to handle password properly."""
        password = kwargs.pop('password', 'testpass123')
        user = super()._create(model_class, *args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating UserProfile instances."""

    class Meta:
        model = UserProfile
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    role = 'school_staff'
    phone = factory.Faker('phone_number')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=65)
    gender = factory.Faker('random_element', elements=['male', 'female', 'other'])
    address = factory.Faker('address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    postal_code = factory.Faker('postcode')
    bio = factory.Faker('paragraph')

    class Params:
        """Traits for different user types."""
        admin = factory.Trait(
            role='super_admin',
            user=factory.SubFactory(UserFactory, is_staff=True, is_superuser=True)
        )
        school_admin = factory.Trait(
            role='school_admin',
            user=factory.SubFactory(UserFactory, is_staff=True)
        )
        teacher = factory.Trait(
            role='school_staff',
            employee_id=factory.LazyFunction(lambda: f"EMP{fake.random_int(min=1000, max=9999)}"),
            department=factory.Faker('random_element', elements=['Mathematics', 'Science', 'English', 'Hindi', 'Social Studies']),
            designation='Teacher'
        )
        parent = factory.Trait(
            role='parent'
        )
        student = factory.Trait(
            role='student',
            admission_no=factory.LazyFunction(lambda: f"SVP{fake.random_int(min=10000, max=99999)}"),
            roll_no=factory.LazyFunction(lambda: str(fake.random_int(min=1, max=60)))
        )
