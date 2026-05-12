import os
import anthropic
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from stories.models import Story, Category, Tag
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Generate AI-written stories using Claude API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--style',
            type=str,
            default='a classic fairy tale',
            help='Story title, theme, or inspiration (e.g. "the match girl", "a dragon afraid of fire")',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of stories to generate (default: 1)',
        )
        parser.add_argument(
            '--author',
            type=str,
            default=None,
            help='Username to assign stories to (default: first superuser)',
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            default=False,
            help='Publish stories immediately (default: save as draft)',
        )
        parser.add_argument(
            '--category',
            type=str,
            default=None,
            help='Category slug to assign (default: first available category)',
        )
        parser.add_argument(
            '--tags',
            type=str,
            default=None,
            help='Set Tags (set --tags Random to let AI generate)',
        )

    def handle(self, *args, **options):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise CommandError(
                'ANTHROPIC_API_KEY is not set in your .env file.')

        # Resolve author
        if options['author']:
            try:
                author = User.objects.get(username=options['author'])
            except User.DoesNotExist:
                raise CommandError(f"User '{options['author']}' not found.")
        else:
            author = User.objects.filter(is_superuser=True).first()
            if not author:
                raise CommandError(
                    'No superuser found. Create one first or pass --author.')

        # Resolve category
        if options['category']:
            try:
                category = Category.objects.get(slug=options['category'])
            except Category.DoesNotExist:
                raise CommandError(
                    f"Category '{options['category']}' not found.")
        else:
            category = Category.objects.first()
            if not category:
                raise CommandError(
                    'No categories found. Create one first or pass --category.')

        client = anthropic.Anthropic(api_key=api_key)
        style = options['style']
        count = options['count']

        self.stdout.write(self.style.WARNING(
            f'Generating {count} story/stories inspired by "{style}"...'
        ))

        for i in range(count):
            self.stdout.write(f'  [{i + 1}/{count}] Calling Claude API...')

            message = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                messages=[
                    {
                        'role': 'user',
                        'content': (
                                f'Write an original short story inspired by or in the style of "{style}". '
                                'Keep it between 2 to 10 minutes reading time. '
                                'Give it a fitting title. '
                                'If the story is based on an existing tale, mark it as retelling or adaptation and credit the source.\n\n'
                                'Return your response in this exact format with no extra text before or after:\n\n'
                                'TITLE: <title here>\n'
                                'TAGS: <3 to 5 comma-separated tags relevant to the story>\n'
                                'STORY_TYPE: <one of: original, retelling, adaptation>\n'
                                'SOURCE: <credit the original source with links if applicable, or leave blank>\n'
                                'STORY: <full story text here — this must be the last field>'
                        ),
                    }
                ],
            )

            raw = message.content[0].text.strip()

            # Parse title and story body
            title, content, storytags, story_type, source = self._parse_response(
                raw)

            self.stdout.write(self.style.WARNING(raw))

            if not title or not content:
                self.stdout.write(self.style.ERROR(
                    f'  [{i + 1}/{count}] Could not parse response. Skipping.'
                ))
                continue

            story = Story.objects.create(
                title=title,
                content=content,
                author=author,
                category=category,
                ai_label=Story.AI_GENERATED,
                is_published=options['publish'],
                story_type=story_type,
                source=source

            )
            story.cover_image = f'https://picsum.photos/seed/{story.id}/1200/500'
            story.save()

            if options['tags']:
                tag_names = [t.strip() for t in options['tags'].split(',')]
            else:
                tag_names = [t.strip() for t in storytags.split(',')]

            tags = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(
                    slug=slugify(name),
                    defaults={'name': name}
                )
                tags.append(tag)
            story.tag.set(tags)

            status = 'published' if options['publish'] else 'draft'
            self.stdout.write(self.style.SUCCESS(
                f'  [{i + 1}/{count}] Created "{story.title}" ({status})'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done. {count} story/stories generated and assigned to @{author.username}.'
        ))

    def _parse_response(self, raw):
        title = ''
        content = ''
        tags = ''
        story_type = 'original'
        source = ''
        for line in raw.splitlines():
            if line.startswith('TITLE:'):
                title = line.removeprefix('TITLE:').strip()
            elif line.startswith('TAGS:'):
                tags = line.removeprefix('TAGS:').strip()
            elif line.startswith('STORY_TYPE:'):
                story_type = line.removeprefix('STORY_TYPE:').strip().lower()
            elif line.startswith('SOURCE:'):
                source = line.removeprefix('SOURCE:').strip()
            elif line.startswith('STORY:'):
                content = line.removeprefix('STORY:').strip()
            elif content:
                content += '\n' + line
        return title, content, tags, story_type, source
