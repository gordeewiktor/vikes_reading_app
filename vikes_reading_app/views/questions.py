# --- Django Imports ---
from django.shortcuts import render

# --- App Imports ---
from vikes_reading_app.decorators import teacher_is_author
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository


# --- Views for Managing Questions ---

@teacher_is_author
def manage_questions(request, story):
    """
    Allows the story author to view and manage (add/edit/delete) 
    pre-reading and post-reading questions for a story.

    - Retrieves and displays all pre-reading exercises and post-reading questions.
    - Only the author (teacher) of the story can access this view.
    """
    repo = ORMStoryRepository()
    pre_reading_exercises = repo.list_pre_reading_exercises(story)
    post_reading_questions = repo.list_post_reading_questions(story)

    # Render the management page with fetched data
    return render(request, 'vikes_reading_app/manage_questions.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })
