from vikes_reading_app.models import Story
from django.urls import reverse
from django.shortcuts import render

from django.shortcuts import render
from django.urls import reverse
from vikes_reading_app.models import Story

def home(request):
    """
    Home page view. Lists all stories and generates appropriate links 
    depending on user role or authentication status.
    """
    user = request.user

    if not user.is_authenticated or user.role == 'student':
        stories = Story.objects.filter(status='published')
    elif user.role == 'teacher':
        stories = Story.objects.all()
    else:
        stories = Story.objects.none()

    def get_story_url(story):
        if not user.is_authenticated:
            return reverse('login')
        if user.role == 'student':
            return reverse('story_entry_point', args=[story.id])
        if user.role == 'teacher':
            return reverse('story_read_teacher', args=[story.id])
        return "#"

    story_links = [(story, get_story_url(story)) for story in stories]

    return render(request, 'vikes_reading_app/home.html', {'story_links': story_links})