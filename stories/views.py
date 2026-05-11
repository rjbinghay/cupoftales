from urllib import request

from django.shortcuts import render, get_object_or_404, redirect
from .models import Story, Category, Tag
# Create your views here.
from django.http import HttpResponse


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StoryForm
from django.core.paginator import Paginator  # NEW!
from django.db.models import Q, Count, Max  # NEW! For complex queries
from urllib.parse import urlencode  # NEW! For building query strings


def home(request):
    """Homepage - list all published stories with filter toolbar."""

    # Read filter params (all optional)
    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    max_read = request.GET.get('max_read', '')
    ai_label = request.GET.get('ai_label', '')
    sort = request.GET.get('sort', 'newest')

    # Data for the dropdowns
    categories = Category.objects.all()
    read_time_thresholds = Story.objects.read_time_thresholds()

    # Filtered queryset
    stories_list = Story.objects.for_listing(
        max_read=max_read or None,
        category_slug=category_slug or None,
        q=q or None,
        ai_label=ai_label or None,
        sort=sort,
    )

    # Pagination
    paginator = Paginator(stories_list, 10)
    page_number = request.GET.get('page')
    stories = paginator.get_page(page_number)

    # Preserve filters across pagination
    query_params = {}
    if q:
        query_params['q'] = q
    if category_slug:
        query_params['category'] = category_slug
    if max_read:
        query_params['max_read'] = max_read
    if ai_label:
        query_params['ai_label'] = ai_label
    if sort and sort != 'newest':
        query_params['sort'] = sort

    # Per-strip helpers: each strip's chip needs to swap its OWN value while
    # preserving every other filter. So we build a querystring without that
    # strip's own param.
    qp_no_max = {k: v for k, v in query_params.items() if k != 'max_read'}
    qp_no_ai = {k: v for k, v in query_params.items() if k != 'ai_label'}

    context = {
        'stories': stories,
        'page_title': 'Latest stories',
        'querystring': urlencode(query_params),
        'querystring_no_max_read': urlencode(qp_no_max),
        'querystring_no_ai':       urlencode(qp_no_ai),
        # Selected values (so the form remembers state)
        'q': q,
        'category_slug': category_slug,
        'max_read': max_read,
        'ai_label': ai_label,
        'sort': sort,
        # Dropdown options
        'categories': categories,
        'read_time_thresholds': read_time_thresholds,
    }
    return render(request, 'stories/home.html', context)


def about(request):
    """About page"""
    return render(request, 'stories/about.html')


def story_detail(request, id):
    """Individual story page"""
    # Get story by ID, or show 404 if not found
    story = get_object_or_404(Story, id=id)

    context = {
        'story': story,
        'page_title': story.title
    }

    return render(request, 'stories/story_detail.html', context)


def category_filter(request, slug):
    """Filter stories by category"""
    # Get category or 404
    category = get_object_or_404(Category, slug=slug)

    stories = Story.objects.for_listing(category_slug=slug)

    context = {
        'stories': stories,
        'category': category,
        'page_title': f'{category.name} Stories'
    }

    return render(request, 'stories/category.html', context)


@login_required
def story_create(request):
    """Create a new story"""
    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)  # Don't save yet
            story.author = request.user  # Set the author
            story.save()  # Now save
            form.save_m2m()  # Save tags (many-to-many)
            if story.is_published:
                messages.success(
                    request, f'Story "{story.title}" published successfully!')
            else:
                messages.success(
                    request, f'Story "{story.title}" saved as draft.')

            return redirect('dashboard')
    else:
        form = StoryForm()

    return render(request, 'stories/story_form.html', {
        'form': form,
        'action': 'Create',
        'all_tags': Tag.objects.all(),
    })


@login_required
def story_edit(request, id):
    """Edit an existing story"""
    story = get_object_or_404(Story, id=id)

    # Only allow editing your own stories
    if story.author != request.user:
        messages.error(request, "You can only edit your own stories!")
        return redirect('dashboard')

    if request.method == 'POST':
        form = StoryForm(request.POST, instance=story)
        if form.is_valid():
            form.save()

            if story.is_published:
                messages.success(
                    request, f'Story "{story.title}" updated and published!')
            else:
                messages.success(
                    request, f'Story "{story.title}" updated as draft.')

            return redirect('dashboard')
    else:
        form = StoryForm(instance=story)

    return render(request, 'stories/story_form.html', {
        'form': form,
        'story': story,
        'action': 'Edit',
        'all_tags': Tag.objects.all(),
    })


@login_required
def story_delete(request, id):
    """Delete a story"""
    story = get_object_or_404(Story, id=id)

    # Only allow deleting your own stories
    if story.author != request.user:
        messages.error(request, "You can only delete your own stories!")
        return redirect('dashboard')

    if request.method == 'POST':
        title = story.title
        story.delete()
        messages.success(request, f'Story "{title}" deleted successfully.')
        return redirect('dashboard')

    return render(request, 'stories/story_confirm_delete.html', {'story': story})


def search_stories(request):
    """Search stories by title and content"""

    # Get search query from URL (?q=search+term)
    query = request.GET.get('q', '')

    if query:
        # Search in title OR content (case-insensitive)
        stories_list = Story.objects.published().filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).order_by('-created_at')
    else:
        # No query - show all published stories
        stories_list = Story.objects.for_listing()

    # Paginate results - 10 per page
    paginator = Paginator(stories_list, 10)
    page_number = request.GET.get('page')
    stories = paginator.get_page(page_number)

    context = {
        'stories': stories,
        'query': query,
        'result_count': stories_list.count(),
    }

    return render(request, 'stories/search_results.html', context)


def category_list(request):
    """List all categories"""
    categories = Category.objects.annotate(
        story_count=Count('story', filter=Q(story__is_published=True))
    ).order_by('display_order', 'name')

    context = {
        'categories': categories,
        'page_title': 'Browse by Categories'
    }

    return render(request, 'stories/category_list.html', context)


def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    stories = Story.objects.for_listing(tag_slug=slug)
    context = {
        'tag': tag,
        'stories': stories,
        'page_title': f'#{tag.name}',
    }
    return render(request, 'stories/tag_detail.html', context)
