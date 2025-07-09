from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from vikes_reading_app.models import PreReadingExercise, PostReadingQuestion, Story, Progress
from vikes_reading_app.decorators import teacher_is_author

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

@login_required
def story_read_student(request, story_id):
    """
    Displays the story text only (no exercises/questions) for students.
    """
    if not request.user.is_authenticated or request.user.role != 'student':
        return HttpResponseForbidden("Access denied: Only students can view this page.")
    
    story = get_object_or_404(Story, id=story_id)
    return render(request, 'vikes_reading_app/story_read_student.html', {'story': story})

@login_required
def story_entry_point(request, story_id):
    """
    Entry point for students to start or resume reading a story.
    - If no progress, redirects to pre-reading.
    - Calculates and displays pre/post-reading scores for the story.
    """
    story = get_object_or_404(Story, id=story_id)
    progress = Progress.objects.filter(student=request.user, read_story=story).first()
    # Check for session pre-reading progress
    session_key = f'pre_reading_progress_{story_id}'
    session_progress = request.session.get(session_key, [])
    # If no progress in DB and no session progress, go to pre-reading
    if not progress and not session_progress:
        return redirect('pre_reading_read', story_id=story.id)

    # Check if post-reading is already completed by comparing progress.answers_given
    post_total_questions = PostReadingQuestion.objects.filter(story=story).count()
    post_answers = progress.answers_given if progress and progress.answers_given else {}
    if post_total_questions > 0 and len(post_answers) == post_total_questions:
        return redirect('post_reading_summary', story_id=story.id)

    # Calculate pre-reading score from session answers
    pre_reading_exercises = PreReadingExercise.objects.filter(story=story)
    pre_total_questions = pre_reading_exercises.count()
    pre_correct_answers = 0
    for exercise in pre_reading_exercises:
        selected_answer = request.session.get(f'answer_{exercise.id}')
        if selected_answer:
            correct_answer = exercise.option_1 if exercise.is_option_1_correct else exercise.option_2
            if selected_answer == correct_answer:
                pre_correct_answers += 1

    # Post-reading progress calculation (after redirect check)
    post_correct_answers = sum(1 for value in post_answers.values() if value)

    context = {
        'story': story,
        'pre_correct_answers': pre_correct_answers,
        'pre_total_questions': pre_total_questions,
        'post_correct_answers': post_correct_answers,
        'post_total_questions': post_total_questions,
    }
    return render(request, 'vikes_reading_app/story_entry_point.html', context)