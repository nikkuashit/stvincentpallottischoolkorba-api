"""
Management command to migrate static page content from frontend to database.

This command creates Page objects in the cms app for all pages defined in the
frontend's pageContent.tsx file.

Usage:
    python manage.py migrate_static_pages [--school-slug SLUG]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from tenants.models import School
from cms.models import Page


# Complete page content data from pageContent.tsx
PAGE_CONTENT_DATA = {
    # Main navigation pages
    "about": {
        "title": "About Us",
        "description": "St. Vincent Pallotti School Korba stands as a beacon of educational excellence, fostering holistic development in every student..."
    },
    "academics": {
        "title": "Academics",
        "description": "Our comprehensive academic program is designed to challenge and inspire students at every level..."
    },
    "admissions": {
        "title": "Admissions",
        "description": "Welcome to the beginning of an exceptional educational journey..."
    },
    "activities": {
        "title": "Activities",
        "description": "Beyond the classroom, we offer a rich tapestry of extracurricular activities..."
    },
    "gallery": {
        "title": "Gallery",
        "description": "Take a visual journey through the vibrant life at St. Vincent Pallotti School Korba..."
    },
    "contact": {
        "title": "Contact Us",
        "description": "We welcome the opportunity to connect with prospective families..."
    },

    # About section nested paths
    "about/about-us": {
        "title": "About Us",
        "description": "St. Vincent Pallotti School Korba stands as a beacon of educational excellence..."
    },
    "about/goal": {
        "title": "Our Goal",
        "description": "GO FORTH TO SERVE - Our School Motto. We form the children into responsible and caring persons..."
    },
    "about/mission": {
        "title": "Our Mission",
        "description": "Our mission is to encourage and nurture the overall development of a child..."
    },
    "about/aim": {
        "title": "Aims & Objectives",
        "description": "St. Vincent Pallotti School aims to impart good education and discipline..."
    },
    "about/aims-objectives": {
        "title": "Aims & Objectives",
        "description": "St. Vincent Pallotti School aims to impart good education and discipline..."
    },
    "about/message": {
        "title": "Principal's Message",
        "description": "It is my pleasure and privilege to serve as the Principal..."
    },
    "about/message-principal": {
        "title": "Principal's Message",
        "description": "It is my pleasure and privilege to serve as the Principal..."
    },
    "about/principal-message": {
        "title": "Principal's Message",
        "description": "It is my pleasure and privilege to serve as the Principal..."
    },
    "about/mandatory-disclosure": {
        "title": "Mandatory Disclosure",
        "description": "In compliance with CBSE guidelines, we provide complete transparency..."
    },
    "about/pallotti-group": {
        "title": "Pallotti Group",
        "description": "The Pallotti Group represents a network of educational institutions..."
    },

    # Facilities section
    "facilities/infrastructure": {
        "title": "Infrastructure",
        "description": "The Concept of the school building is unique. There are two different blocks..."
    },
    "facilities/library": {
        "title": "Library",
        "description": "We include a library period for 3rd and above classes..."
    },
    "facilities/laboratory": {
        "title": "Science Laboratory",
        "description": "Our school is equipped with well-maintained science laboratories..."
    },
    "facilities/computer-lab": {
        "title": "Computer Laboratory",
        "description": "The computer laboratory is equipped with modern computers..."
    },
    "facilities/staff": {
        "title": "Our Staff",
        "description": "Our dedicated team of qualified and experienced teachers..."
    },
    "facilities/bio-lab": {
        "title": "Biology Laboratory",
        "description": "Our biology laboratory is fully equipped with modern instruments..."
    },
    "facilities/physics-lab": {
        "title": "Physics Laboratory",
        "description": "The physics laboratory features state-of-the-art equipment..."
    },
    "facilities/chemistry-lab": {
        "title": "Chemistry Laboratory",
        "description": "Our chemistry laboratory provides a safe and well-ventilated environment..."
    },
    "facilities/smart-class": {
        "title": "Smart Class",
        "description": "Our smart classrooms are equipped with interactive whiteboards..."
    },
    "facilities/playground": {
        "title": "Playground & Sports Facilities",
        "description": "Our spacious playground and sports facilities spread over 5 acres..."
    },
    "facilities/auditorium": {
        "title": "Auditorium",
        "description": "Our modern auditorium hosts cultural events, educational seminars..."
    },
    "facilities/cafeteria": {
        "title": "Cafeteria",
        "description": "Our hygienic cafeteria serves nutritious and delicious meals..."
    },
    "facilities/transport": {
        "title": "Transport Facility",
        "description": "We provide safe and reliable transport services..."
    },

    # Flat paths (for backward compatibility)
    "about-us": {
        "title": "About Us",
        "description": "St. Vincent Pallotti School Korba stands as a beacon of educational excellence..."
    },
    "goal": {
        "title": "Our Goal",
        "description": "GO FORTH TO SERVE - Our School Motto..."
    },
    "mission": {
        "title": "Our Mission",
        "description": "Our mission is to encourage and nurture the overall development..."
    },
    "aim": {
        "title": "Aims & Objectives",
        "description": "St. Vincent Pallotti School aims to impart good education..."
    },
    "aims-objectives": {
        "title": "Aims & Objectives",
        "description": "St. Vincent Pallotti School aims to impart good education..."
    },
    "message": {
        "title": "Principal's Message",
        "description": "It is my pleasure and privilege to serve as the Principal..."
    },
    "message-principal": {
        "title": "Principal's Message",
        "description": "It is my pleasure and privilege to serve as the Principal..."
    },
    "principal-message": {
        "title": "Principal's Message",
        "description": "It is my pleasure and privilege to serve as the Principal..."
    },
    "mandatory-disclosure": {
        "title": "Mandatory Disclosure",
        "description": "In compliance with CBSE guidelines..."
    },
    "pallotti-group": {
        "title": "Pallotti Group",
        "description": "The Pallotti Group represents a network of educational institutions..."
    },
    "infrastructure": {
        "title": "Infrastructure",
        "description": "The Concept of the school building is unique..."
    },
    "library": {
        "title": "Library",
        "description": "We include a library period for 3rd and above classes..."
    },
    "laboratory": {
        "title": "Science Laboratory",
        "description": "Our school is equipped with well-maintained science laboratories..."
    },
    "computer-lab": {
        "title": "Computer Laboratory",
        "description": "The computer laboratory is equipped with modern computers..."
    },
    "staff": {
        "title": "Our Staff",
        "description": "Our dedicated team of qualified and experienced teachers..."
    },
    "bio-lab": {
        "title": "Biology Laboratory",
        "description": "Our biology laboratory is fully equipped..."
    },
    "physics-lab": {
        "title": "Physics Laboratory",
        "description": "The physics laboratory features state-of-the-art equipment..."
    },
    "chemistry-lab": {
        "title": "Chemistry Laboratory",
        "description": "Our chemistry laboratory provides a safe environment..."
    },
    "smart-class": {
        "title": "Smart Class",
        "description": "Our smart classrooms are equipped with interactive whiteboards..."
    },
    "playground": {
        "title": "Playground & Sports Facilities",
        "description": "Our spacious playground and sports facilities..."
    },
    "auditorium": {
        "title": "Auditorium",
        "description": "Our modern auditorium hosts cultural events..."
    },
    "cafeteria": {
        "title": "Cafeteria",
        "description": "Our hygienic cafeteria serves nutritious meals..."
    },
    "transport": {
        "title": "Transport Facility",
        "description": "We provide safe and reliable transport services..."
    },
}


class Command(BaseCommand):
    help = 'Migrate static page content from frontend to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-slug',
            type=str,
            default='stvincentpallottikorba',
            help='Slug of the school to migrate content for'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing pages'
        )

    def handle(self, *args, **options):
        school_slug = options['school_slug']
        overwrite = options['overwrite']

        try:
            school = School.objects.get(slug=school_slug)
            organization = school.organization
        except School.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'School with slug "{school_slug}" not found.'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Migrating pages for: {school.name}'
        ))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for slug, content in PAGE_CONTENT_DATA.items():
            # Check if page already exists
            existing_page = Page.objects.filter(
                organization=organization,
                school=school,
                slug=slug
            ).first()

            if existing_page and not overwrite:
                self.stdout.write(self.style.WARNING(
                    f'Skipping "{slug}" - already exists'
                ))
                skipped_count += 1
                continue

            if existing_page:
                # Update existing page
                existing_page.title = content['title']
                existing_page.description = content['description']
                existing_page.meta_title = content['title']
                existing_page.meta_description = content['description'][:160]
                existing_page.is_published = True
                existing_page.published_at = timezone.now()
                existing_page.save()

                self.stdout.write(self.style.SUCCESS(
                    f'Updated: {slug} - {content["title"]}'
                ))
                updated_count += 1
            else:
                # Create new page
                page = Page.objects.create(
                    organization=organization,
                    school=school,
                    title=content['title'],
                    slug=slug,
                    description=content['description'],
                    meta_title=content['title'],
                    meta_description=content['description'][:160],
                    is_published=True,
                    published_at=timezone.now()
                )

                self.stdout.write(self.style.SUCCESS(
                    f'Created: {slug} - {content["title"]}'
                ))
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nMigration complete!\n'
            f'Created: {created_count}\n'
            f'Updated: {updated_count}\n'
            f'Skipped: {skipped_count}'
        ))
