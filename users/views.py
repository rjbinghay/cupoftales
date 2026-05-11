# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from stories.models import WriterProfile
from .forms import CustomUserCreationForm  # ← ADD THIS LINE
from django.contrib.auth.models import User


def signup_view(request):
    """User signup page"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # ← CHANGED
        if form.is_valid():
            user = form.save()

            # Create WriterProfile for new user
            WriterProfile.objects.create(user=user)

            # Log the user in
            login(request, user)

            messages.success(
                request, f'Welcome {user.username}! Your account has been created.')
            return redirect('home')
    else:
        form = CustomUserCreationForm()  # ← CHANGED

    return render(request, 'users/signup.html', {'form': form})


def login_view(request):
    """User login page"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')

                # Redirect to 'next' parameter or home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# @login_required #
def profile_view(request, username):
    """Public writer profile page"""

    writer = get_object_or_404(User, username=username)

    # Get writer's published stories
    stories = writer.story_set.filter(is_published=True)

    context = {
        'writer': writer,
        'stories': stories,
    }

    return render(request, 'users/profile.html', context)


@login_required
def dashboard_view(request):
    """Writer's personal dashboard"""
    # Get all stories by current user (published and unpublished)
    my_stories = request.user.story_set.all()

    context = {
        'my_stories': my_stories,
    }

    return render(request, 'users/dashboard.html', context)


@login_required
def edit_profile_view(request):
    """Edit writer profile (donation links, bio)"""
    profile = request.user.writerprofile

    if request.method == 'POST':
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        profile.paypal_link = request.POST.get('paypal_link', '')
        profile.kofi_link = request.POST.get('kofi_link', '')
        profile.other_donation_link = request.POST.get(
            'other_donation_link', '')
        # Pen name — empty string means "no pen name", store as NULL so the
        # unique constraint doesn't reject multiple writers without one.
        profile.display_name = request.POST.get('display_name', '').strip() or None
        profile.user.first_name = request.POST.get('first_name', '')
        profile.user.last_name = request.POST.get('last_name', '')
        profile.user.save()  # Save User model changes
        profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard')

    return render(request, 'users/edit_profile.html', {'profile': profile})


def profile_view(request, username):
    """Public writer profile page"""
    writer = get_object_or_404(User, username=username)
    stories = (
        writer.story_set
        .filter(is_published=True)
        .select_related('category')
        .order_by('-created_at')
    )

    context = {
        'writer': writer,
        'stories': stories,
    }
    return render(request, 'users/profile.html', context)
