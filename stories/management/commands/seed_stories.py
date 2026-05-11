# stories/management/commands/seed_stories.py
from email import parser

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stories.models import Story, Category, WriterProfile
from faker import Faker
import random


class Command(BaseCommand):
    help = 'Generate fake stories for testing pagination'

    def add_arguments(self, parser):
        print("🔧 Django is calling add_arguments()")
        parser.add_argument(
            'count',
            type=int,
            default=1000,
            nargs='?',
            help='Number of stories to create (default: 1000)',
        )

        parser.add_argument(
            'writers',
            type=int,
            default=15,
            nargs='?',
            help='Number of fake authors to create (default: 15)',
        )

    def handle(self, *args, **options):
        print("🚀 Django is calling handle()")
        print(f"📦 Arguments received: {options}")
        count = options['count']
        writers = options['writers']
        print(f"📊 Will create {count} stories")
        print(f"📊 Will create {writers} fake authors")
        fake = Faker()

        self.stdout.write(self.style.WARNING(
            f'Starting to generate {count} fake stories...'))

        # Get or create test users
        users = []
        for i in range(writers):  # Create specified number of fake authors
            username = fake.user_name()
            email = fake.email()
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                }
            )

            ai_labels = ['human', 'assisted', 'ai']

            WriterProfile.objects.get_or_create(
                user=user,
                defaults={
                    'bio': fake.paragraph(nb_sentences=random.randint(1, 3)),
                    'paypal_link': random.choice([f'https://paypal.me/{username}', '', '']),
                    'kofi_link': random.choice([f'https://ko-fi.com/{username}', '', '', '']),
                    'other_donation_link': random.choice([f'https://otherdonations.com/{username}', '']),
                    'is_verified': random.choice([True, False, True, True]),
                }
            )

            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username}')
            users.append(user)

        # Get all categories
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR(
                'No categories found! Please create categories first.'))
            return

        # AI labels
        ai_labels = ['human', 'assisted', 'ai']

        # Generate stories
        stories_created = 0
        for i in range(count):
            # Generate random story content
            title = fake.sentence(nb_words=random.randint(3, 8)).rstrip('.')

            # Generate realistic story content (3-25 paragraphs)
            paragraphs = [fake.paragraph(nb_sentences=random.randint(3, 25))
                          for _ in range(random.randint(3, 25))]
            content = '\n\n'.join(paragraphs)

            # Random author, category, AI label
            author = random.choice(users)
            category = random.choice(categories)
            ai_label = random.choice(ai_labels)
            is_published = random.choice(
                [True, True, True, False])  # 75% published

            # Create story
            story = Story.objects.create(
                title=title,
                content=content,
                author=author,
                category=category,
                ai_label=ai_label,
                is_published=is_published,
                view_count=random.randint(0, 5000)
            )

            stories_created += 1

            # Progress indicator
            if (i + 1) % 100 == 0:
                self.stdout.write(f'Created {i + 1}/{count} stories...')

        self.stdout.write(self.style.SUCCESS(
            f'✅ Successfully created {stories_created} fake stories!'))
        self.stdout.write(self.style.SUCCESS(
            f'✅ Created {len(users)} fake authors'))
