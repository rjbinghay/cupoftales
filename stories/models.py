# stories/models.py
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class StoryManager(models.Manager):
    def published(self):
        """Return only published stories"""
        return self.filter(is_published=True)

    def read_time_thresholds(self, candidates=(1, 3, 5, 10)):
        """Return distinct read time thresholds for filtering"""
        max_in_data = self.published().aggregate(
            m=models.Max('read_time_minutes')
        )['m'] or 0
        thresholds = [t for t in candidates if t < max_in_data]
        thresholds.append(max_in_data)
        return thresholds

    def for_listing(self, max_read=None, category_slug=None, q=None,
                    ai_label=None, sort='newest', tag_slug=None):
        """
        Build the queryset for any 'list of stories' page (home, future
        /tag/<slug>/, etc.). Each filter is opt-in: pass None or '' to skip.

        sort options (chronological only — length sorting was deliberately
        removed because it overlapped with the length-chip filter):
          'newest' — default, newest first
          'oldest' — oldest first

        ai_label: 'human' | 'assisted' | 'ai' (matches Story.AI_CHOICES)
        """
        qs = self.published().select_related('author', 'category').prefetch_related('tag')

        if max_read:
            qs = qs.filter(read_time_minutes__lte=int(max_read))
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        if ai_label:
            qs = qs.filter(ai_label=ai_label)
        if tag_slug:
            qs = qs.filter(tag__slug=tag_slug)

        if sort == 'oldest':
            return qs.order_by('created_at', '-read_time_minutes')
        return qs.order_by('-created_at', '-read_time_minutes')  # newest


class Category(models.Model):
    """Story categories: funny, sad, interesting"""
    name = models.CharField(max_length=50)  # VARCHAR(50)
    slug = models.SlugField(unique=True)    # URL-friendly version
    display_order = models.PositiveIntegerField(
        default=0)  # For custom ordering

    class Meta:
        verbose_name_plural = "Categories"  # Fix "Categorys" in admin
        # Order by display_order, then name
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name  # Like ToString() in C#


class Story(models.Model):
    """Main story model"""
    # Fields

    objects = StoryManager()

    title = models.CharField(max_length=200)
    content = models.TextField()  # TEXT field (unlimited length)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,  # If category deleted, set NULL
        null=True,
        blank=True

    )
    tag = models.ManyToManyField(
        'Tag', blank=True, related_name='stories')

    author = models.ForeignKey(
        User,  # Built-in Django user
        on_delete=models.CASCADE  # If user deleted, delete stories
    )

    # Estimated read time (from our stories!)
    read_time_minutes = models.PositiveIntegerField(default=1)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)  # Set on creation
    updated_at = models.DateTimeField(auto_now=True)      # Updated on save
    is_published = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    cover_image = models.URLField(blank=True)  # URL for image
    source = models.TextField(blank=True)  # TEXT field (unlimited length)

    # AI labeling (from our documentation!)
    AI_HUMAN = 'human'
    AI_ASSISTED = 'assisted'
    AI_GENERATED = 'ai'
    AI_CHOICES = [
        (AI_HUMAN, '100% Human Written'),
        (AI_ASSISTED, 'AI-Assisted'),
        (AI_GENERATED, 'AI-Generated'),
    ]
    ai_label = models.CharField(
        max_length=10,
        choices=AI_CHOICES,
        default=AI_HUMAN
    )

    story_type_original = 'original'
    story_type_retelling = 'retelling'
    story_type_adaptation = 'adaptation'
    story_type_choices = [
        (story_type_original, 'Original'),
        (story_type_retelling, 'Retelling'),
        (story_type_adaptation, 'Adaptation'),
    ]

    story_type = models.CharField(
        max_length=10,
        choices=story_type_choices,
        default=story_type_original
    )

    class Meta:
        ordering = ['-created_at']  # Newest first
        verbose_name_plural = "Stories"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        word_count = len(self.content.split())
        self.read_time_minutes = max(1, round(word_count / 200))
        super().save(*args, **kwargs)


class WriterProfile(models.Model):
    """Extended user profile for donation links and public-facing identity."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)

    # Public pen name. Optional. If set, shown on bylines instead of real name.
    # null=True so unique=True doesn't choke on multiple empty strings.
    display_name = models.CharField(
        max_length=60, blank=True, null=True, unique=True,
        help_text="Optional pen name. Shown on your stories instead of your real name."
    )

    # Donation links
    paypal_link = models.URLField(blank=True)
    kofi_link = models.URLField(blank=True)
    other_donation_link = models.URLField(blank=True)

    # Verification (from authenticity strategy!)
    is_verified = models.BooleanField(default=False)

    @property
    def public_name(self):
        """
        What to show on bylines. Order: pen name → real full name → @username.
        Drives stories/_author_name.html — keep that template thin.
        """
        if self.display_name:
            return self.display_name
        full = self.user.get_full_name()
        if full:
            return full
        return f"@{self.user.username}"

    def __str__(self):
        return f"{self.user.username}'s Profile"
