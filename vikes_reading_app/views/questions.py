from django.shortcuts import get_object_or_404, render
from vikes_reading_app.models import Story, PreReadingExercise, PostReadingQuestion
from vikes_reading_app.decorators import teacher_is_author

@teacher_is_author
def manage_questions(request, story):
    """
    Allows the story author to view and manage (add/edit/delete) pre-reading and post-reading questions for a story.
    """
    pre_reading_exercises = PreReadingExercise.objects.filter(story=story).order_by('id')
    post_reading_questions = PostReadingQuestion.objects.filter(story=story).order_by('id')
    return render(request, 'vikes_reading_app/manage_questions.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })