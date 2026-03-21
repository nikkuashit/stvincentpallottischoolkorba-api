"""
CMS factories for testing (NavigationMenu, Page, Section).
"""

import factory
from faker import Faker

from cms.models import NavigationMenu, Page, Section as CMSSection, Gallery, Document, Slider, Marquee

fake = Faker()


class NavigationMenuFactory(factory.django.DjangoModelFactory):
    """Factory for creating NavigationMenu instances."""

    class Meta:
        model = NavigationMenu
        django_get_or_create = ('slug',)

    title = factory.Faker('sentence', nb_words=3)
    slug = factory.LazyAttribute(lambda obj: fake.slug() + '-' + str(fake.random_int(min=1, max=9999)))
    href = factory.LazyAttribute(lambda obj: f"/{obj.slug}")
    icon = factory.Faker('random_element', elements=['home', 'info', 'school', 'contact', 'calendar', 'book'])
    description = factory.Faker('sentence')
    menu_type = 'page'
    is_external = False
    external_url = ''
    open_in_new_tab = False
    show_in_navigation = True
    show_in_footer = False
    show_in_landing_page = False
    display_order = factory.Sequence(lambda n: n)
    is_active = True
    parent = None

    class Params:
        """Traits for different menu types."""
        dropdown = factory.Trait(
            menu_type='dropdown',
            href=''
        )
        external = factory.Trait(
            menu_type='external',
            is_external=True,
            external_url=factory.Faker('url'),
            open_in_new_tab=True
        )
        footer = factory.Trait(
            show_in_navigation=False,
            show_in_footer=True
        )
        landing = factory.Trait(
            show_in_landing_page=True
        )


class PageFactory(factory.django.DjangoModelFactory):
    """Factory for creating Page instances."""

    class Meta:
        model = Page
        django_get_or_create = ('slug',)

    title = factory.Faker('sentence', nb_words=4)
    slug = factory.LazyAttribute(lambda obj: fake.slug() + '-page-' + str(fake.random_int(min=1, max=9999)))
    description = factory.Faker('paragraph')
    meta_title = factory.LazyAttribute(lambda obj: obj.title)
    meta_description = factory.LazyAttribute(lambda obj: obj.description[:160] if obj.description else '')
    meta_keywords = factory.Faker('words', nb=5)
    is_published = True
    published_at = factory.Faker('date_time_this_year')

    class Params:
        """Traits for different page states."""
        draft = factory.Trait(
            is_published=False,
            published_at=None
        )


class SectionModelFactory(factory.django.DjangoModelFactory):
    """Factory for creating CMS Section instances (renamed to avoid conflict with academics.Section)."""

    class Meta:
        model = CMSSection

    page = factory.SubFactory(PageFactory)
    title = factory.Faker('sentence', nb_words=3)
    slug = factory.LazyAttribute(lambda obj: fake.slug() + '-section-' + str(fake.random_int(min=1, max=9999)))
    section_type = factory.Faker('random_element', elements=[
        'hero', 'about', 'features', 'gallery', 'news', 'events', 'contact', 'principal', 'courses', 'custom'
    ])
    content = factory.LazyFunction(lambda: {
        'heading': fake.sentence(),
        'body': fake.paragraph(),
        'items': []
    })
    display_order = factory.Sequence(lambda n: n)
    is_visible = True
    background_color = factory.Faker('hex_color')
    show_in_landing_page = False
    landing_page_order = 0
    landing_page_width = 'full'

    class Params:
        """Traits for different section types."""
        hero = factory.Trait(
            section_type='hero',
            content=factory.LazyFunction(lambda: {
                'heading': fake.sentence(),
                'subheading': fake.sentence(),
                'cta_text': 'Learn More',
                'cta_link': '/about'
            })
        )
        about = factory.Trait(
            section_type='about',
            content=factory.LazyFunction(lambda: {
                'heading': 'About Us',
                'body': fake.paragraphs(3),
                'mission': fake.sentence(),
                'vision': fake.sentence()
            })
        )
        landing = factory.Trait(
            show_in_landing_page=True,
            landing_page_order=factory.Sequence(lambda n: n)
        )


class GalleryFactory(factory.django.DjangoModelFactory):
    """Factory for creating Gallery instances."""

    class Meta:
        model = Gallery
        django_get_or_create = ('slug',)

    title = factory.Faker('sentence', nb_words=3)
    slug = factory.LazyAttribute(lambda obj: fake.slug() + '-gallery-' + str(fake.random_int(min=1, max=9999)))
    description = factory.Faker('paragraph')
    is_published = True
    published_date = factory.Faker('date_time_this_year')

    class Params:
        """Traits for different gallery states."""
        draft = factory.Trait(
            is_published=False,
            published_date=None
        )


class SliderFactory(factory.django.DjangoModelFactory):
    """Factory for creating Slider instances."""

    class Meta:
        model = Slider

    title = factory.Faker('sentence', nb_words=4)
    subtitle = factory.Faker('sentence', nb_words=8)
    description = factory.Faker('paragraph')
    cta_text = factory.Faker('random_element', elements=['Learn More', 'Apply Now', 'Contact Us', 'Explore'])
    cta_link = factory.Faker('uri_path')
    display_order = factory.Sequence(lambda n: n)
    is_active = True


class MarqueeFactory(factory.django.DjangoModelFactory):
    """Factory for creating Marquee instances."""

    class Meta:
        model = Marquee

    text = factory.Faker('sentence', nb_words=10)
    link = factory.Faker('uri_path')
    display_order = factory.Sequence(lambda n: n)
    is_active = True
    start_date = None
    end_date = None
