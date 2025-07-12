from django.shortcuts import redirect
from functools import wraps
from django.shortcuts import get_object_or_404
from vikes_reading_app.models import Story
from django.http import HttpResponseForbidden

def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role != 'teacher':
            return redirect('profile')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def teacher_is_author(view_func):
    @wraps(view_func)
    def _wrapped_view(request, story_id, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.role != 'teacher':
            return redirect('login')
        
        story = get_object_or_404(Story, id=story_id)
        if story.author != user:
            return HttpResponseForbidden("You are not allowed to view this story.")

        return view_func(request, story=story, *args, **kwargs)
    return _wrapped_view

def student_can_view_story(view_func):
    @wraps(view_func)
    def _wrapped_view(request, story_id, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('login')
        if user.role != 'student':
            return HttpResponseForbidden("Access denied: Only students can view this page.")

        story = get_object_or_404(Story, id=story_id)
        return view_func(request, story=story, *args, **kwargs)
    return _wrapped_view