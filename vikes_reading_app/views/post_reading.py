from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from vikes_reading_app.models import Story, PostReadingQuestion, Progress
from vikes_reading_app.forms import PostReadingQuestionForm
from django.contrib import messages
from vikes_reading_app.decorators import teacher_required, teacher_is_author, student_can_view_story

def get_post_reading_questions(story):
    return list(PostReadingQuestion.objects.filter(story=story).order_by('id'))

@teacher_required
def post_reading_create(request, story_id):
    """
    Allows the story author to add a new post-reading question to a story.
    """
    story = get_object_or_404(Story, id=story_id)
    if request.method == "POST":
        form = PostReadingQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.story = story
            question.save()
            return redirect('manage_questions', story_id=story.id)
    else:
        form = PostReadingQuestionForm()
    return render(request, 'vikes_reading_app/post_reading_create.html', {'form': form, 'story': story})

@teacher_is_author
def post_reading_edit(request, story, question_id):
    """
    Allows the story author to edit an existing post-reading question.
    """
    question = get_object_or_404(PostReadingQuestion, id=question_id, story=story)
    if request.method == "POST":
        form = PostReadingQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
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
    question = get_object_or_404(PostReadingQuestion, id=question_id, story_id=story.id)
    story = question.story
    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted successfully!")
        return redirect('manage_questions', story_id=story.id)
    return render(request, 'vikes_reading_app/post_reading_delete.html', {'question': question, 'story': story})

@student_can_view_story
def post_reading_read(request, story, question_index=0):
    """
    Handles displaying post-reading questions one by one to the student.
    Tracks lookup count in session and determines lookup wait time.
    Redirects to summary page when all questions are answered.
    """
    questions = get_post_reading_questions(story)
    if question_index >= len(questions):
        return redirect('post_reading_summary', story_id=story.id)  # All questions finished
    question = questions[question_index]
    # Track how many times the student has looked up the story for this question (session)
    lookup_key = f'lookup_story_{story.id}_q{question.id}'
    lookup_count = request.session.get(lookup_key, 0)
    # Set time allowed for lookup depending on count
    if lookup_count == 0:
        next_lookup_time = 30
    elif lookup_count == 1:
        next_lookup_time = 45
    elif lookup_count == 2:
        next_lookup_time = 60
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
    question = get_object_or_404(PostReadingQuestion, id=question_id, story=story)
    if request.method == "POST":
        try:
            selected_answer_id = str(int(request.POST.get("answer")))
        except (TypeError, ValueError):
            messages.error(request, "Invalid answer.")
            return redirect("post_reading_read", story_id=story.id, question_index=question_id)
        # Determine if the selected answer is correct
        is_correct = str(question.correct_option) == selected_answer_id
        # Retrieve or create progress for this user/story
        progress, _ = Progress.objects.get_or_create(
            student=request.user,
            read_story=story,
        )
        # Store the correctness for this question in answers_given dict
        answers = progress.answers_given or {}
        answers[str(question.id)] = is_correct
        progress.answers_given = answers
        progress.save()
        # Find the index of the next question (if any)
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
    questions = get_post_reading_questions(story)
    # Retrieve student's progress and answers
    progress = Progress.objects.filter(student=request.user, read_story=story).first()
    student_answers = progress.answers_given if progress and progress.answers_given else {}
    correct_count = 0
    for question in questions:
        is_correct = student_answers.get(str(question.id), False)
        if is_correct:
            correct_count += 1
    total_questions = len(questions)
    context = {
        'story': story,
        'questions': questions,
        'correct_answers': correct_count,
        'total_questions': total_questions,
        'post_reading_time': progress.post_reading_time if progress else 0,
    }
    return render(request, 'vikes_reading_app/post_reading_summary.html', context)