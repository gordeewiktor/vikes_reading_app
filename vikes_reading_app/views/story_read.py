from django.shortcuts import render, redirect
from vikes_reading_app.decorators import student_can_view_story, teacher_is_author
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository
from vikes_reading_app.repositories.progress_repository_impl import ORMProgressRepository
from vikes_reading_app.services.reading_flow import ReadingFlowService



# --- Teacher Views ---

@teacher_is_author
def story_read_teacher(request, story):
    """
    Teacher view for a story.
    Displays the story text along with all related pre-reading and post-reading questions.
    Only the author of the story (teacher) can access this view.
    """
    repo = ORMStoryRepository()
    pre_reading_exercises = repo.list_pre_reading_exercises(story)
    post_reading_questions = repo.list_post_reading_questions(story)
    return render(request, 'vikes_reading_app/story_read_teacher.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })


# --- Student Views ---

@student_can_view_story
def story_read_student(request, story):
    """
    Student view for a story.
    Displays the story text only, without any exercises or questions.
    Only accessible to students.
    """
    return render(request, 'vikes_reading_app/story_read_student.html', {'story': story})


@student_can_view_story
def story_entry_point(request, story):
    """
    Entry point for students to start or continue their reading journey.
    This view checks the student's current progress and redirects them appropriately
    to the next section (pre-reading, reading, or post-reading). If no redirection is needed,
    it shows a summary of their progress on this story.
    """
    repo = ORMProgressRepository()
    # Retrieve the student's progress from the database
    progress = repo.get_progress(student_id=request.user.id, story_id=story.id)

    # Determine if the student should be redirected to another part of the app
    redirect_target = ReadingFlowService.get_resume_target(progress, story)
    if redirect_target:
        return redirect(redirect_target, story_id=story.id)

    # Calculate pre-reading and post-reading scores
    pre_correct, pre_total = ReadingFlowService.get_pre_reading_score(progress, story)
    post_correct, post_total = ReadingFlowService.get_post_reading_score(progress)

    # Render the entry point template with progress summary
    context = {
        'story': story,
        'pre_correct_answers': pre_correct,
        'pre_total_questions': pre_total,
        'post_correct_answers': post_correct,
        'post_total_questions': post_total,
    }
    return render(request, 'vikes_reading_app/story_entry_point.html', context)
