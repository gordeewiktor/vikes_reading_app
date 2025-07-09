from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from vikes_reading_app.forms import PreReadingExerciseForm
from vikes_reading_app.models import Story, PreReadingExercise
from django.contrib import messages
from django.urls import reverse

@login_required
def pre_reading_create(request, story_id):
    """
    Allows the story author to add a new pre-reading exercise to a story.
    """
    story = get_object_or_404(Story, id=story_id)
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
    if request.method == "POST":
        form = PreReadingExerciseForm(request.POST, request.FILES)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.story = story
            exercise.save()
            return redirect('manage_questions', story_id=story.id)
    else:
        form = PreReadingExerciseForm()
    return render(request, 'vikes_reading_app/pre_reading_create.html', {'form':  form, 'story': story})

@login_required
def pre_reading_edit(request, exercise_id):
    """
    Allows the story author to edit an existing pre-reading exercise.
    """
    exercise = get_object_or_404(PreReadingExercise, id=exercise_id)
    story = exercise.story
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
    if request.method == "POST":
        form = PreReadingExerciseForm(request.POST, request.FILES, instance=exercise)
        if form.is_valid():
            form.save()
            return redirect('manage_questions', story_id=exercise.story.id)
    else:
        form = PreReadingExerciseForm(instance=exercise)
    return render(request, 'vikes_reading_app/pre_reading_edit.html', {
        'form': form,
        'exercise': exercise,
        'story': story,
        })

@login_required
def pre_reading_delete(request, exercise_id):
    """
    Allows the story author to delete a pre-reading exercise.
    """
    exercise = get_object_or_404(PreReadingExercise, id=exercise_id)
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
    if request.method == "POST":
        exercise.delete()
        messages.success(request, "Exercise deleted successfully!")
        return redirect('manage_questions', story_id=exercise.story.id)
    return render(request, 'vikes_reading_app/pre_reading_delete.html', {'exercise': exercise})

@login_required
def pre_reading_summary(request, story_id):
    """
    Shows a summary of pre-reading exercise results for the student.
    Calculates the number of correct answers using session data.
    """
    story = get_object_or_404(Story, id=story_id)
    exercises = PreReadingExercise.objects.filter(story=story)
    # Retrieve completed question IDs from session
    session_key = f'pre_reading_progress_{story_id}'
    completed_ids = request.session.get(session_key, [])

    #check whether all questions were completed
    if len(completed_ids) < exercises.count():
        return redirect('pre_reading_read', story_id=story_id)
    
    correct_count = 0
    question_data = []
    for exercise in exercises:
        correct_option = exercise.option_1 if exercise.is_option_1_correct else exercise.option_2
        question_data.append({
            'text': exercise.question_text,
            'correct_answer': correct_option,
        })
        if exercise.id in completed_ids:
            selected = request.session.get(f'answer_{exercise.id}')
            if selected == correct_option:
                correct_count += 1
    context = {
        'story': story,
        'questions': question_data,
        'correct_answers': correct_count,
        'total_questions': exercises.count(),
    }
    return render(request, 'vikes_reading_app/pre_reading_summary.html', context)

@login_required
def pre_reading_read(request, story_id):
    """
    Display pre-reading exercises to students, one at a time.
    Uses session to track which questions have been completed.
    Redirects to summary when all are done.
    """
    story = get_object_or_404(Story, id=story_id)
    pre_reading_exercises = list(PreReadingExercise.objects.filter(story=story))
    if not pre_reading_exercises:
        messages.info(request, "No pre-reading exercises available for this story.")
        return redirect('read_story', story_id=story.id)
    # Get current progress from session
    session_key = f'pre_reading_progress_{story_id}'
    completed_questions = request.session.get(session_key, [])
    # Find the next unanswered question
    next_question = next(
        (q for q in pre_reading_exercises if q.id not in completed_questions), 
        None
    )
    if not next_question:
        # All questions are done, redirect to summary
        return redirect('pre_reading_summary', story_id=story.id)
    context = {
        'story': story,
        'exercise': next_question,
    }
    return render(request, 'vikes_reading_app/pre_reading_read.html', context)

from django.http import JsonResponse

@login_required
def pre_reading_submit(request, story_id):
    """
    Handles student submission of a pre-reading answer.
    Saves answer and progress in session, then returns JSON with correctness and next URL.
    """
    story = get_object_or_404(Story, id=story_id)
    pre_reading_exercises = list(PreReadingExercise.objects.filter(story=story))
    if request.method == "POST":
        exercise_id = int(request.POST.get("exercise_id"))
        selected_answer = request.POST.get("selected_answer")
        exercise = get_object_or_404(PreReadingExercise, id=exercise_id)
        # Determine correctness
        is_correct = (
            (selected_answer == exercise.option_1 and exercise.is_option_1_correct) or
            (selected_answer == exercise.option_2 and exercise.is_option_2_correct)
        )
        # Save progress in session (list of completed question IDs and answer per question)
        session_key = f'pre_reading_progress_{story_id}'
        completed_questions = request.session.get(session_key, [])
        completed_questions.append(exercise.id)
        request.session[session_key] = completed_questions
        request.session[f'answer_{exercise.id}'] = selected_answer
        # Find next question
        next_question = next(
            (q for q in pre_reading_exercises if q.id not in completed_questions), 
            None
        )
        next_url = (
            reverse('pre_reading_read', args=[story_id])
            if next_question else reverse('pre_reading_summary', args=[story_id])
        )
        return JsonResponse({
            "correct": is_correct,
            "next_url": next_url
        })
    return redirect('pre_reading_read', story_id=story_id)