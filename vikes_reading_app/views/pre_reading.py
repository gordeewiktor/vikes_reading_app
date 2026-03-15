# --- Django Imports ---
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.urls import reverse

# --- App Imports ---
from vikes_reading_app.forms import PreReadingExerciseForm
from vikes_reading_app.decorators import teacher_is_author, student_can_view_story
from vikes_reading_app.repositories.progress_repository_impl import ORMProgressRepository
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository
from vikes_reading_app.services.reading_flow import ReadingFlowService


# ========================
# 📘 Pre-Reading: Teacher Views
# ========================

@teacher_is_author
def pre_reading_create(request, story):
    """
    Allows the story author to add a new pre-reading exercise to a story.
    """
    repo = ORMStoryRepository()
    if request.method == "POST":
        form = PreReadingExerciseForm(request.POST, request.FILES)
        if form.is_valid():
            repo.create_pre_reading_exercise(story, form.cleaned_data)
            return redirect('manage_questions', story_id=story.id)
    else:
        form = PreReadingExerciseForm()
    return render(request, 'vikes_reading_app/pre_reading_create.html', {'form': form, 'story': story})


@teacher_is_author
def pre_reading_edit(request, exercise_id, story):
    """
    Allows the story author to edit an existing pre-reading exercise.
    """
    repo = ORMStoryRepository()
    exercise = repo.get_pre_reading_exercise(exercise_id)
    if request.method == "POST":
        form = PreReadingExerciseForm(request.POST, request.FILES, instance=exercise)
        if form.is_valid():
            repo.update_pre_reading_exercise(exercise, form.cleaned_data)
            return redirect('manage_questions', story_id=exercise.story.id)
    else:
        form = PreReadingExerciseForm(instance=exercise)
    return render(request, 'vikes_reading_app/pre_reading_edit.html', {
        'form': form,
        'exercise': exercise,
        'story': story,
    })


@teacher_is_author
def pre_reading_delete(request, exercise_id):
    """
    Allows the story author to delete a pre-reading exercise.
    """
    repo = ORMStoryRepository()
    exercise = repo.get_pre_reading_exercise(exercise_id)
    if request.method == "POST":
        repo.delete_pre_reading_exercise(exercise)
        messages.success(request, "Exercise deleted successfully!")
        return redirect('manage_questions', story_id=exercise.story.id)
    return render(request, 'vikes_reading_app/pre_reading_delete.html', {'exercise': exercise})


# ========================
# 📗 Pre-Reading: Student Views
# ========================

@student_can_view_story
def pre_reading_summary(request, story):
    """
    Shows a summary of pre-reading exercise results for the student.
    Calculates the number of correct answers using Progress data.
    """
    story_repo = ORMStoryRepository()
    progress_repo = ORMProgressRepository()
    exercises = story_repo.list_pre_reading_exercises(story)
    progress = progress_repo.get_progress_model(request.user, story)
    answers = ReadingFlowService.get_pre_reading_answers(progress)
    completed_ids = {int(exercise_id) for exercise_id in answers.keys()}

    if len(completed_ids) < len(exercises):
        return redirect('pre_reading_read', story_id=story.id)

    correct_count = 0
    question_data = []
    for exercise in exercises:
        correct_option = exercise.option_1 if exercise.is_option_1_correct else exercise.option_2
        question_data.append({
            'text': exercise.question_text,
            'correct_answer': correct_option,
        })
        if exercise.id in completed_ids:
            selected = answers.get(str(exercise.id))
            if selected == correct_option:
                correct_count += 1

    context = {
        'story': story,
        'questions': question_data,
        'correct_answers': correct_count,
        'total_questions': len(exercises),
    }
    return render(request, 'vikes_reading_app/pre_reading_summary.html', context)


@student_can_view_story
def pre_reading_read(request, story):
    """
    Displays pre-reading exercises to students, one at a time.
    Tracks which questions have been completed using Progress.
    Redirects to summary when all are completed.
    """
    story_repo = ORMStoryRepository()
    progress_repo = ORMProgressRepository()
    pre_reading_exercises = story_repo.list_pre_reading_exercises(story)
    if not pre_reading_exercises:
        messages.info(request, "No pre-reading exercises available for this story.")
        return redirect('read_story', story_id=story.id)

    progress = progress_repo.get_progress_model(request.user, story)
    answers = ReadingFlowService.get_pre_reading_answers(progress)
    completed_questions = {int(exercise_id) for exercise_id in answers.keys()}

    next_question = next(
        (q for q in pre_reading_exercises if q.id not in completed_questions),
        None
    )

    if not next_question:
        return redirect('pre_reading_summary', story_id=story.id)

    context = {
        'story': story,
        'exercise': next_question,
    }
    return render(request, 'vikes_reading_app/pre_reading_read.html', context)


@student_can_view_story
def pre_reading_submit(request, story):
    """
    Handles student submission of a pre-reading answer.
    Saves progress in the Progress model, returns JSON with result and next URL.
    """
    story_repo = ORMStoryRepository()
    progress_repo = ORMProgressRepository()
    pre_reading_exercises = story_repo.list_pre_reading_exercises(story)

    if request.method == "POST":
        try:
            exercise_id = int(request.POST.get("exercise_id"))
        except (TypeError, ValueError):
            return HttpResponseForbidden("Invalid exercise ID.")

        selected_answer = request.POST.get("selected_answer")
        exercise = story_repo.get_pre_reading_exercise(exercise_id)

        if exercise.story != story:
            return HttpResponseForbidden("Exercise does not belong to this story.")

        is_correct = (
            (selected_answer == exercise.option_1 and exercise.is_option_1_correct) or
            (selected_answer == exercise.option_2 and exercise.is_option_2_correct)
        )

        progress, _ = progress_repo.get_or_create_progress(request.user, story)
        ReadingFlowService.set_pre_reading_answer(progress, exercise.id, selected_answer)
        progress_repo.save_progress(progress)

        completed_questions = {
            int(exercise_id) for exercise_id in
            ReadingFlowService.get_pre_reading_answers(progress).keys()
        }

        next_question = next(
            (q for q in pre_reading_exercises if q.id not in completed_questions),
            None
        )
        next_url = (
            reverse('pre_reading_read', args=[story.id])
            if next_question else reverse('pre_reading_summary', args=[story.id])
        )

        return JsonResponse({
            "correct": is_correct,
            "next_url": next_url
        })

    return redirect('pre_reading_read', story_id=story.id)
