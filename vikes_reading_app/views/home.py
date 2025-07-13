
# --- Imports ---
from django.shortcuts import render
from django.urls import reverse
from vikes_reading_app.models import Story

# --- Home Page View ---

def home(request):
    """
    Renders the home page with links to stories based on user role:
    - Students and unauthenticated users see only published stories.
    - Teachers see all stories, including drafts.
    Each story gets a role-specific link.
    """
    user = request.user

    # Determine which stories to show based on role
    if not user.is_authenticated or user.role == 'student':
        # Only show published stories to students or unauthenticated users
        stories = Story.objects.filter(status='published')
    elif user.role == 'teacher':
        # Teachers see all stories, including drafts
        stories = Story.objects.all()
    else:
        # Other roles see no stories
        stories = Story.objects.none()

    # Generate appropriate story URLs per user role
    def get_story_url(story):
        if not user.is_authenticated:
            # Unauthenticated users are directed to login
            return reverse('login')
        if user.role == 'student':
            # Students go to the student entry point
            return reverse('story_entry_point', args=[story.id])
        if user.role == 'teacher':
            # Teachers go to the teacher reading view
            return reverse('story_read_teacher', args=[story.id])
        # Fallback for other roles
        return "#"

    # Pair each story with its link
    story_links = [(story, get_story_url(story)) for story in stories]

    return render(request, 'vikes_reading_app/home.html', {'story_links': story_links})