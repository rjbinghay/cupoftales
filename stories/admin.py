# stories/admin.py
from django.contrib import admin
from .models import Category, Story, WriterProfile, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_filter = ['category', 'ai_label', 'is_published']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'

    list_display = ['title', 'author', 'category',
                    'read_time_minutes', 'ai_label', 'is_published']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WriterProfile)
class WriterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'paypal_link', 'kofi_link']
    list_filter = ['is_verified']
