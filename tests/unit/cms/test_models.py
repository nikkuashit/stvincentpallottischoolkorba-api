"""
Unit tests for CMS models.
"""

import pytest

from cms.models import NavigationMenu, Page, Section as CMSSection
from tests.factories import (
    NavigationMenuFactory,
    PageFactory,
    SectionModelFactory,
    GalleryFactory,
    SliderFactory,
    MarqueeFactory
)


@pytest.mark.django_db
class TestNavigationMenu:
    """Test cases for NavigationMenu model."""

    def test_create_navigation_menu(self):
        """Test creating a navigation menu."""
        menu = NavigationMenuFactory()

        assert menu.id is not None
        assert menu.title is not None
        assert menu.slug is not None
        assert menu.is_active is True

    def test_navigation_menu_str(self):
        """Test __str__ method returns title."""
        menu = NavigationMenuFactory(title='About Us')

        assert str(menu) == 'About Us'

    def test_menu_type_choices(self):
        """Test all valid menu_type choices."""
        for menu_type in ['page', 'section', 'dropdown', 'external']:
            menu = NavigationMenuFactory(menu_type=menu_type)
            assert menu.menu_type == menu_type

    def test_dropdown_trait(self):
        """Test dropdown trait creates dropdown menu without href."""
        menu = NavigationMenuFactory(dropdown=True)

        assert menu.menu_type == 'dropdown'
        assert menu.href == ''

    def test_external_trait(self):
        """Test external trait creates external link menu."""
        menu = NavigationMenuFactory(external=True)

        assert menu.menu_type == 'external'
        assert menu.is_external is True
        assert menu.external_url is not None
        assert menu.open_in_new_tab is True

    def test_footer_trait(self):
        """Test footer trait shows in footer only."""
        menu = NavigationMenuFactory(footer=True)

        assert menu.show_in_navigation is False
        assert menu.show_in_footer is True

    def test_landing_trait(self):
        """Test landing trait shows in landing page."""
        menu = NavigationMenuFactory(landing=True)

        assert menu.show_in_landing_page is True

    def test_parent_child_relationship(self):
        """Test parent-child relationship for menus."""
        parent = NavigationMenuFactory(menu_type='dropdown')
        child1 = NavigationMenuFactory(parent=parent, title='Child 1')
        child2 = NavigationMenuFactory(parent=parent, title='Child 2')

        assert child1.parent == parent
        assert child2.parent == parent
        assert parent.children.count() == 2

    def test_display_order_sequence(self):
        """Test that display_order is sequential."""
        menu1 = NavigationMenuFactory()
        menu2 = NavigationMenuFactory()
        menu3 = NavigationMenuFactory()

        # Each should have different display_order
        orders = [menu1.display_order, menu2.display_order, menu3.display_order]
        assert len(set(orders)) == 3


@pytest.mark.django_db
class TestPage:
    """Test cases for Page model."""

    def test_create_page(self):
        """Test creating a page."""
        page = PageFactory()

        assert page.id is not None
        assert page.title is not None
        assert page.slug is not None

    def test_page_str(self):
        """Test __str__ method returns title."""
        page = PageFactory(title='Welcome to Our School')

        assert str(page) == 'Welcome to Our School'

    def test_published_page(self):
        """Test creating a published page."""
        page = PageFactory(is_published=True)

        assert page.is_published is True
        assert page.published_at is not None

    def test_draft_trait(self):
        """Test draft trait creates unpublished page."""
        page = PageFactory(draft=True)

        assert page.is_published is False
        assert page.published_at is None

    def test_seo_fields(self):
        """Test SEO fields are set correctly."""
        page = PageFactory()

        assert page.meta_title is not None
        assert page.meta_description is not None


@pytest.mark.django_db
class TestCMSSection:
    """Test cases for CMS Section model."""

    def test_create_section(self):
        """Test creating a CMS section."""
        section = SectionModelFactory()

        assert section.id is not None
        assert section.title is not None
        assert section.slug is not None

    def test_section_str(self):
        """Test __str__ method returns title."""
        section = SectionModelFactory(title='Our Mission')

        assert str(section) == 'Our Mission'

    def test_section_type_choices(self):
        """Test all valid section_type choices."""
        valid_types = ['hero', 'about', 'features', 'gallery', 'news',
                       'events', 'contact', 'principal', 'courses', 'custom']

        for section_type in valid_types:
            section = SectionModelFactory(section_type=section_type)
            assert section.section_type == section_type

    def test_hero_trait(self):
        """Test hero trait creates hero section with CTA."""
        section = SectionModelFactory(hero=True)

        assert section.section_type == 'hero'
        assert 'cta_text' in section.content
        assert 'cta_link' in section.content

    def test_about_trait(self):
        """Test about trait creates about section."""
        section = SectionModelFactory(about=True)

        assert section.section_type == 'about'
        assert 'mission' in section.content
        assert 'vision' in section.content

    def test_landing_trait(self):
        """Test landing trait shows in landing page."""
        section = SectionModelFactory(landing=True)

        assert section.show_in_landing_page is True

    def test_section_page_relationship(self):
        """Test section belongs to a page."""
        page = PageFactory()
        section1 = SectionModelFactory(page=page)
        section2 = SectionModelFactory(page=page)

        assert section1.page == page
        assert section2.page == page
        assert page.sections.count() == 2

    def test_content_json_field(self):
        """Test content is stored as JSON."""
        content = {
            'heading': 'Test Heading',
            'body': 'Test body content',
            'items': ['item1', 'item2']
        }
        section = SectionModelFactory(content=content)

        assert section.content['heading'] == 'Test Heading'
        assert len(section.content['items']) == 2

    def test_landing_page_width_choices(self):
        """Test landing_page_width choices."""
        valid_widths = ['full', 'three-quarters', 'two-thirds', 'half', 'third', 'quarter']

        for width in valid_widths:
            section = SectionModelFactory(landing_page_width=width)
            assert section.landing_page_width == width


@pytest.mark.django_db
class TestGallery:
    """Test cases for Gallery model."""

    def test_create_gallery(self):
        """Test creating a gallery."""
        gallery = GalleryFactory()

        assert gallery.id is not None
        assert gallery.title is not None
        assert gallery.slug is not None

    def test_gallery_str(self):
        """Test __str__ method returns title."""
        gallery = GalleryFactory(title='School Events 2025')

        assert str(gallery) == 'School Events 2025'

    def test_draft_trait(self):
        """Test draft trait creates unpublished gallery."""
        gallery = GalleryFactory(draft=True)

        assert gallery.is_published is False
        assert gallery.published_date is None


@pytest.mark.django_db
class TestSlider:
    """Test cases for Slider model."""

    def test_create_slider(self):
        """Test creating a slider."""
        slider = SliderFactory()

        assert slider.id is not None
        assert slider.title is not None
        assert slider.is_active is True

    def test_slider_str(self):
        """Test __str__ method returns title."""
        slider = SliderFactory(title='Welcome Banner')

        assert str(slider) == 'Welcome Banner'

    def test_cta_fields(self):
        """Test CTA fields are set."""
        slider = SliderFactory()

        assert slider.cta_text is not None
        assert slider.cta_link is not None


@pytest.mark.django_db
class TestMarquee:
    """Test cases for Marquee model."""

    def test_create_marquee(self):
        """Test creating a marquee."""
        marquee = MarqueeFactory()

        assert marquee.id is not None
        assert marquee.text is not None
        assert marquee.is_active is True

    def test_marquee_str(self):
        """Test __str__ method truncates long text."""
        long_text = 'This is a very long marquee text that should be truncated'
        marquee = MarqueeFactory(text=long_text)

        assert str(marquee).endswith('...')
        assert len(str(marquee)) <= 53  # 50 chars + '...'
