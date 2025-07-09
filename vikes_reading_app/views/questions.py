from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from vikes_reading_app.models import Story, PreReadingExercise, PostReadingQuestion

@login_required
def manage_questions(request, story_id):
    """
    Allows the story author to view and manage (add/edit/delete) pre-reading and post-reading questions for a story.
    """
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
    story = get_object_or_404(Story, id=story_id)
    pre_reading_exercises = PreReadingExercise.objects.filter(story=story).order_by('id')
    post_reading_questions = PostReadingQuestion.objects.filter(story=story).order_by('id')
    return render(request, 'vikes_reading_app/manage_questions.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })