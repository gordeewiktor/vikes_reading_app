from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from vikes_reading_app.models import PreReadingExercise, PostReadingQuestion, Story, Progress
from vikes_reading_app.decorators import teacher_is_author, student_can_view_story
from vikes_reading_app.helpers import (
    get_session_progress,
    should_redirect_student,
    get_pre_reading_score,
    get_post_reading_score,
)


@teacher_is_author
def story_read_teacher(request, story):
    """
    Teacher view for a story. Shows the story text and associated pre-reading and post-reading questions.
    Only the author can access it.
    """
    pre_reading_exercises = PreReadingExercise.objects.filter(story=story).order_by('id')
    post_reading_questions = PostReadingQuestion.objects.filter(story=story).order_by('id')
    return render(request, 'vikes_reading_app/story_read_teacher.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })

@student_can_view_story
def story_read_student(request, story):
    """
    Displays the story text only (no exercises/questions) for students.
    """
    return render(request, 'vikes_reading_app/story_read_student.html', {'story': story})

@student_can_view_story
def story_entry_point(request, story):
    """
    Entry point for students to start or resume reading a story.
    """
    progress = Progress.objects.filter(student=request.user, read_story=story).first()
    session_progress = get_session_progress(request, story.id)

    redirect_target = should_redirect_student(progress, session_progress, story)
    if redirect_target:
        return redirect(redirect_target, story_id=story.id)

    pre_correct, pre_total = get_pre_reading_score(request, story)
    post_correct, post_total = get_post_reading_score(progress)

    context = {
        'story': story,
        'pre_correct_answers': pre_correct,
        'pre_total_questions': pre_total,
        'post_correct_answers': post_correct,
        'post_total_questions': post_total,
    }
    return render(request, 'vikes_reading_app/story_entry_point.html', context)