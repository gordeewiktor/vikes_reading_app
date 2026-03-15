
# --- Imports ---
from django.shortcuts import render
from django.urls import reverse
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository

# --- Home Page View ---

def home(request):
    """
    Renders the home page with links to stories based on user role:
    - Students and unauthenticated users see only published stories.
    - Teachers see all stories, including drafts.
    Each story gets a role-specific link.
    """
    repo = ORMStoryRepository()
    user = request.user
    stories = repo.list_home_stories(user)

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
