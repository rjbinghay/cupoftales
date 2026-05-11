# stories/management/commands/clear_fake_stories.py
from django.core.management.base import BaseCommand
from stories.models import Story
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Delete all fake stories and users (keeps your original data)'

    def handle(self, *args, **options):
        # List of usernames to keep (your real accounts)
        keep_users = ['admin', 'your_real_username', 'emma@example.com']

        # Delete stories by fake users
        fake_users = User.objects.exclude(username__in=keep_users)
        story_count = Story.objects.filter(author__in=fake_users).count()
        Story.objects.filter(author__in=fake_users).delete()

        # Delete fake users
        user_count = fake_users.count()
        fake_users.delete()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Deleted {story_count} fake stories'))
        self.stdout.write(self.style.SUCCESS(
            f'✅ Deleted {user_count} fake users'))
