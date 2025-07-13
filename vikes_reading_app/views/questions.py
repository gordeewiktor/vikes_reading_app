# --- Django Imports ---
from django.shortcuts import render

# --- App Imports ---
from vikes_reading_app.models import PreReadingExercise, PostReadingQuestion
from vikes_reading_app.decorators import teacher_is_author


# --- Views for Managing Questions ---

@teacher_is_author
def manage_questions(request, story):
    """
    Allows the story author to view and manage (add/edit/delete) 
    pre-reading and post-reading questions for a story.

    - Retrieves and displays all pre-reading exercises and post-reading questions.
    - Only the author (teacher) of the story can access this view.
    """
    # Fetch pre-reading exercises linked to this story
    pre_reading_exercises = PreReadingExercise.objects.filter(story=story).order_by('id')

    # Fetch post-reading questions linked to this story
    post_reading_questions = PostReadingQuestion.objects.filter(story=story).order_by('id')

    # Render the management page with fetched data
    return render(request, 'vikes_reading_app/manage_questions.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })