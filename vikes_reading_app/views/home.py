from vikes_reading_app.models import Story
from django.urls import reverse
from django.shortcuts import render

def home(request):
    """
    Home page view. Lists all stories and generates appropriate links for each story
    depending on user authentication and role:
      - Students: link to entry point (pre-reading, reading, etc.)
      - Teachers: link to teacher view of the story
      - Unauthenticated: link to login page
    """
    
    user = request.user

    # Filter stories based on user role:
    # - Students and unauthenticated users see only 'published' stories.
    # - Teachers can see all stories, including drafts.
    # - Unknown roles get no stories (just in case). 
    if user.is_authenticated:
        if user.role == 'student':
            stories = Story.objects.filter(status='published')
        elif user.role == 'teacher':
            stories = Story.objects.all()
        else:
            stories = Story.objects.none()
    else:
        stories = Story.objects.filter(status='published')

    story_links = []

    for story in stories:
        if user.is_authenticated:
            if user.role == 'student':
                story_url = reverse('story_entry_point', args=[story.id])
            elif user.role == 'teacher':
                story_url = reverse('story_read_teacher', args=[story.id])
            else:
                story_url = "#"  # fallback for unknown roles
        else:
            story_url = reverse('login')  # force login for unauthenticated users

        story_links.append((story, story_url))

    return render(request, 'vikes_reading_app/home.html', {'story_links': story_links})