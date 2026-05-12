# stories/forms.py
from django import forms
from django.utils.text import slugify
from .models import Story, Tag


class StoryForm(forms.ModelForm):
    """Form for creating/editing stories"""

    MAX_TAGS = 5

    tag_input = forms.CharField(
        required=False,
        label='Tags',
        widget=forms.TextInput(attrs={
            'placeholder': 'horror, twist-ending, short',
            'list': 'tag-options',
            'class': 'form-control',
            'autocomplete': 'off',
        }),
        help_text=f'Up to {MAX_TAGS} tags, comma-separated. Pick existing or create new.'
    )

    class Meta:
        model = Story
        # tag is handled manually via tag_input — not in fields
        fields = ['title', 'content', 'category',
                  'ai_label', 'is_published', 'cover_image', 'story_type', 'source']

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter your story title...',
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Write your story here...',
                'rows': 15,
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'ai_label': forms.Select(attrs={'class': 'form-control'}),

            'cover_image': forms.TextInput(attrs={
                'placeholder': 'https://picsum.photos/800/400',
                'class': 'form-control'
            }),
            'story_type': forms.Select(attrs={'class': 'form-control'}),
            'source': forms.Textarea(attrs={
                'placeholder': ('This story was adapted from [Aesop\'s Fables](https://gutenberg.org/ebooks/11).\n'
                                'Original tales can also be found at [Wikisource](https://en.wikisource.org).\n'
                                'Supports markdown — wrap links like [text](url).'),
                'rows': 5,
                'class': 'form-control'
            }),
        }

        labels = {
            'title': 'Story Title',
            'content': 'Your Story',
            'category': 'Category',
            'ai_label': 'AI Involvement',
            'is_published': 'Publish immediately?',
            'cover_image': 'Cover Image URL',
            'story_type': 'Story Type',
            'source': 'Source',
        }

        help_texts = {
            'title': 'Make it catchy!',
            'content': 'Pour your heart out.',
            'ai_label': 'Be honest about AI usage.',
            'is_published': 'Uncheck to save as draft.',
            'cover_image': 'Enter your Cover Image URL if any.',
            'source': 'Optional. Credit your sources and link to originals. Supports markdown.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On edit: pre-fill tag_input with the story's current tags
        if self.instance and self.instance.pk:
            existing = self.instance.tag.values_list('name', flat=True)
            self.fields['tag_input'].initial = ', '.join(existing)

    def clean_tag_input(self):
        raw = self.cleaned_data.get('tag_input', '').strip()
        if not raw:
            return []

        # Split, lowercase-normalize, dedupe (preserve order)
        names = []
        seen = set()
        for piece in raw.split(','):
            name = piece.strip().lower()
            if name and name not in seen:
                seen.add(name)
                names.append(name)

        if len(names) > self.MAX_TAGS:
            raise forms.ValidationError(
                f'Maximum {self.MAX_TAGS} tags allowed (you entered {len(names)}).'
            )
        return names

    def _save_m2m(self):
        super()._save_m2m()
        names = self.cleaned_data.get('tag_input', [])
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name},
            )
            tags.append(tag)
        self.instance.tag.set(tags)
