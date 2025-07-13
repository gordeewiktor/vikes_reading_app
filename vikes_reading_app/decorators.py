
from django.shortcuts import redirect, get_object_or_404
from functools import wraps
from django.http import HttpResponseForbidden
from vikes_reading_app.models import Story


# --- Teacher Role Required Decorator ---

def teacher_required(view_func):
    """
    Allows access only to authenticated teachers.
    Redirects unauthenticated users to login, and non-teachers to profile.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'teacher':
            return redirect('profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# --- Teacher Must Be Author Decorator ---

def teacher_is_author(view_func):
    """
    Allows access only to the author teacher of a specific story.
    Redirects unauthenticated or non-teachers to login.
    Forbids access if the teacher is not the author of the story.
    """
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


# --- Student Role and Story Access Decorator ---

def student_can_view_story(view_func):
    """
    Allows access only to authenticated students for a specific story.
    Redirects unauthenticated users to login.
    Forbids access if the user is not a student.
    """
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
