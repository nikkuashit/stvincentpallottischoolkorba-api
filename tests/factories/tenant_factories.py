"""
Tenant factories for testing (Organization, School).
"""

import factory
from faker import Faker

from tenants.models import Organization, School, SubscriptionPlan, Subscription

fake = Faker()


class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory for creating Organization instances."""

    class Meta:
        model = Organization
        django_get_or_create = ('slug',)

    name = factory.Faker('company')
    slug = factory.LazyAttribute(lambda obj: fake.slug() + str(fake.random_int(min=1, max=9999)))
    email = factory.Faker('company_email')
    phone = factory.Faker('phone_number')
    address = factory.Faker('street_address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    country = 'India'
    postal_code = factory.Faker('postcode')
    is_active = True
    is_verified = True
    settings = factory.LazyFunction(dict)


class SubscriptionPlanFactory(factory.django.DjangoModelFactory):
    """Factory for creating SubscriptionPlan instances."""

    class Meta:
        model = SubscriptionPlan
        django_get_or_create = ('slug',)

    name = factory.Faker('random_element', elements=['Basic', 'Standard', 'Premium', 'Enterprise'])
    slug = factory.LazyAttribute(lambda obj: obj.name.lower() + '-' + str(fake.random_int(min=1, max=999)))
    description = factory.Faker('paragraph')
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    billing_period = 'monthly'
    max_students = 500
    max_staff = 50
    max_storage_gb = 10
    features = factory.LazyFunction(lambda: {'feature1': True, 'feature2': True})
    is_active = True
    display_order = factory.Sequence(lambda n: n)


class SubscriptionFactory(factory.django.DjangoModelFactory):
    """Factory for creating Subscription instances."""

    class Meta:
        model = Subscription

    organization = factory.SubFactory(OrganizationFactory)
    plan = factory.SubFactory(SubscriptionPlanFactory)
    status = 'active'
    start_date = factory.Faker('date_this_year')
    end_date = factory.Faker('date_between', start_date='+1y', end_date='+2y')
    auto_renew = True
    current_students = 0
    current_staff = 0
    current_storage_gb = 0


class SchoolFactory(factory.django.DjangoModelFactory):
    """Factory for creating School instances."""

    class Meta:
        model = School
        django_get_or_create = ('slug',)

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.LazyAttribute(lambda obj: obj.organization.name + ' School')
    slug = factory.LazyAttribute(lambda obj: fake.slug() + '-school-' + str(fake.random_int(min=1, max=9999)))
    short_name = factory.LazyFunction(lambda: ''.join([w[0].upper() for w in fake.words(3)]))
    tagline = factory.Faker('catch_phrase')
    description = factory.Faker('paragraph')
    established_year = factory.Faker('random_int', min=1950, max=2020)
    email = factory.Faker('company_email')
    phone = factory.Faker('phone_number')
    website = factory.Faker('url')
    address_line1 = factory.Faker('street_address')
    address_line2 = factory.Faker('secondary_address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    country = 'India'
    postal_code = factory.Faker('postcode')
    timezone = 'Asia/Kolkata'
    language = 'en'
    currency = 'INR'
    config = factory.LazyFunction(dict)
    is_active = True
