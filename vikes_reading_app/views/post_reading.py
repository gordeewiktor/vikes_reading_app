# --- Django & Project Imports ---

from django.contrib import messages
from django.shortcuts import redirect, render

from vikes_reading_app.decorators import student_can_view_story, teacher_is_author
from vikes_reading_app.forms import PostReadingQuestionForm
from vikes_reading_app.repositories.progress_repository_impl import ORMProgressRepository
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository
from vikes_reading_app.services.reading_flow import ReadingFlowService


# --- Utility Function ---

def get_post_reading_questions(story):
    """
    Retrieve all post-reading questions for a given story, ordered by ID.
    """
    # Query and order all post-reading questions for this story
    repo = ORMStoryRepository()
    return repo.list_post_reading_questions(story)


def get_option_text(question, option_number):
    return {
        '1': question.option_1,
        '2': question.option_2,
        '3': question.option_3,
        '4': question.option_4,
    }.get(str(option_number))


# --- Teacher CRUD Views ---


@teacher_is_author
def post_reading_create(request, story):
    """
    Allows the story author to add a new post-reading question to a story.
    """
    repo = ORMStoryRepository()
    if request.method == "POST":
        form = PostReadingQuestionForm(request.POST)
        if form.is_valid():
            repo.create_post_reading_question(story, form.cleaned_data)
            return redirect('manage_questions', story_id=story.id)

    else:
        form = PostReadingQuestionForm()

    return render(request, 'vikes_reading_app/post_reading_create.html', {'form': form, 'story': story})


@teacher_is_author
def post_reading_edit(request, story, question_id):
    """
    Allows the story author to edit an existing post-reading question.
    """
    repo = ORMStoryRepository()
    question = repo.get_post_reading_question(question_id, story=story)

    if request.method == "POST":
        form = PostReadingQuestionForm(request.POST, instance=question)
        if form.is_valid():
            repo.update_post_reading_question(question, form.cleaned_data)
            messages.success(request, "Question updated successfully!")

            return redirect('manage_questions', story_id=story.id)

    else:
        form = PostReadingQuestionForm(instance=question)

    return render(request, 'vikes_reading_app/post_reading_edit.html', {
        'form': form,
        'story': story,
        'question': question,
    })


@teacher_is_author
def post_reading_delete(request, story, question_id):
    """
    Allows the story author to delete a post-reading question.
    """
    repo = ORMStoryRepository()
    question = repo.get_post_reading_question(question_id, story=story)
    story = question.story

    if request.method == "POST":
        repo.delete_post_reading_question(question)
        messages.success(request, "Question deleted successfully!")

        return redirect('manage_questions', story_id=story.id)

    return render(request, 'vikes_reading_app/post_reading_delete.html', {'question': question, 'story': story})


# --- Student Reading Flow Views ---


@student_can_view_story
def post_reading_read(request, story, question_index=0):
    """
    Handles displaying post-reading questions one by one to the student.
    Tracks lookup count in session and determines lookup wait time.
    Redirects to summary page when all questions are answered.
    """
    # Get all post-reading questions for this story
    questions = get_post_reading_questions(story)

    if question_index >= len(questions):
        return redirect('post_reading_summary', story_id=story.id)  # All questions finished

    question = questions[question_index]

    # Track how many times the student has looked up the story for this question (session)
    lookup_key = f'lookup_story_{story.id}_q{question.id}'
    lookup_count = request.session.get(lookup_key, 0)

    # Set time allowed for lookup depending on count
    if lookup_count == 0:
        next_lookup_time = 30  # First lookup allowed for 30 seconds
    elif lookup_count == 1:
        next_lookup_time = 45  # Second lookup allowed for 45 seconds
    elif lookup_count == 2:
        next_lookup_time = 60  # Third lookup allowed for 60 seconds
    else:
        next_lookup_time = None  # No more lookups allowed

    return render(request, 'vikes_reading_app/post_reading_read.html', {
        'story': story,
        'question': question,
        'question_index': question_index,
        'total_questions': len(questions),
        'lookup_count': lookup_count,
        'next_lookup_time': next_lookup_time,
    })


@student_can_view_story
def post_reading_submit(request, story, question_id):
    """
    Handles submission of a post-reading question answer.
    Saves answer correctness in Progress for this user and story.
    Redirects to next question or summary.
    """
    # Get the specific question being answered
    story_repo = ORMStoryRepository()
    progress_repo = ORMProgressRepository()
    question = story_repo.get_post_reading_question(question_id, story=story)

    if request.method == "POST":
        try:
            selected_answer_id = str(int(request.POST.get("answer")))
        except (TypeError, ValueError):
            messages.error(request, "Invalid answer.")
            return redirect("post_reading_read", story_id=story.id, question_index=question_id)

        # Check if selected answer matches the correct one
        is_correct = str(question.correct_option) == selected_answer_id

        # Get or create progress record for this student and story
        progress, _ = progress_repo.get_or_create_progress(request.user, story)

        # Save the result of the current question
        ReadingFlowService.set_post_reading_answer(
            progress,
            question.id,
            selected_answer_id,
            is_correct,
        )
        progress_repo.save_progress(progress)

        # Get all questions again to determine the next one
        questions = get_post_reading_questions(story)
        next_index = None
        for idx, q in enumerate(questions):
            if q.id == question.id and idx + 1 < len(questions):
                next_index = idx + 1
                break

        if next_index is not None:
            return redirect("post_reading_read", story_id=story.id, question_index=next_index)
        else:
            return redirect("post_reading_summary", story_id=story.id)

    return redirect("post_reading_read", story_id=story.id, question_index=question_id)


@student_can_view_story
def post_reading_summary(request, story):
    """
    Shows a summary of post-reading results for the student.
    Displays number of correct answers and time spent.
    """
    # Get all questions for this story
    questions = get_post_reading_questions(story)

    # Get the student's progress (answers and time)
    progress_repo = ORMProgressRepository()
    progress = progress_repo.get_progress_model(request.user, story)
    student_answers = ReadingFlowService.get_post_reading_answers(progress)

    correct_count = 0
    question_summaries = []
    for question in questions:
        answer_data = student_answers.get(str(question.id))
        if isinstance(answer_data, dict):
            selected_option = answer_data.get('selected_option')
            is_correct = answer_data.get('is_correct', False)
        else:
            selected_option = None
            is_correct = bool(answer_data)

        if is_correct:
            correct_count += 1

        correct_answer = get_option_text(question, question.correct_option)
        your_answer = get_option_text(question, selected_option) if selected_option else None
        question_summaries.append({
            'question_text': question.question_text,
            'correct_answer': correct_answer,
            'your_answer': your_answer or "(No answer)",
            'is_correct': is_correct,
            'explanation': question.explanation,
        })

    total_questions = len(questions)

    context = {
        'story': story,
        'question_summaries': question_summaries,
        'correct_answers': correct_count,
        'total_questions': total_questions,
        'post_reading_time': progress.post_reading_time if progress else 0,
    }

    return render(request, 'vikes_reading_app/post_reading_summary.html', context)
