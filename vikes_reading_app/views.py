from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from .forms import CustomUserCreationForm, StoryForm, PreReadingExerciseForm, PostReadingQuestionForm
from .models import Story, Progress, PreReadingExercise, PostReadingQuestion
from django.views.decorators.csrf import csrf_exempt
import json

def home(request):
    """
    Home page view. Lists all stories and generates appropriate links for each story
    depending on user authentication and role:
      - Students: link to entry point (pre-reading, reading, etc.)
      - Teachers: link to teacher view of the story
      - Unauthenticated: link to login page
    """
    stories = Story.objects.all()
    user = request.user
    story_links = []

    for story in stories:
        if user.is_authenticated:
            if user.role == 'student':
                story_url = reverse('story_entry_point', args=[story.id])
            elif user.role == 'teacher':
                story_url = reverse('story_read_teacher', args=[story.id])
            else:
                story_url = "#"  # fallback for unknown roles
        else:
            story_url = reverse('login')  # force login for unauthenticated users

        story_links.append((story, story_url))

    return render(request, 'vikes_reading_app/home.html', {'story_links': story_links})

def register_view(request):
    """
    Handles user registration. On GET, shows registration form.
    On POST, creates a new user (default role: student), logs them in, and redirects home.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'  # Default role for new registrations
            user.save()

            login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'vikes_reading_app/auth/register.html', {'form': form})

def logout_confirm(request):
    """
    Presents a confirmation page before logging out the user.
    """
    return render(request, 'vikes_reading_app/auth/logout_confirm.html')

@login_required
def my_stories(request):
    """
    Shows a list of stories authored by the currently logged-in user.
    """
    stories = Story.objects.filter(author=request.user)
    return render(request, 'vikes_reading_app/my_stories.html', {'stories': stories})

@login_required
def profile(request):
    """
    Allow users to view and edit their own profile.
    - If POST: Update profile details (currently only bio).
    - If teacher: Show progress of all students.
    - If student: Show own profile.
    """
    if request.method == 'POST':
        bio = request.POST.get('bio', '')
        user = request.user  # The logged-in user
        user.bio = bio
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    # If teacher, aggregate all students' progress for display
    if request.user.role == 'teacher':
        progress_list = Progress.objects.select_related('student', 'read_story')
        students_progress = {}
        for progress in progress_list:
            student = progress.student
            story = progress.read_story
            if student not in students_progress:
                students_progress[student] = []
            students_progress[student].append({
                "story": story,
                "pre_reading_time": progress.pre_reading_time,
                # Pre-reading score logic: count of pre-reading answers (if present)
                "pre_reading_score": len(progress.answers_given.get("pre_reading", {})) if progress.answers_given else 0,
                "reading_time": progress.reading_time,
                # Post-reading score: count of correct answers (True)
                "post_reading_score": sum(1 for value in progress.answers_given.values() if value) if progress.answers_given else 0,
                "post_reading_time": progress.post_reading_time
            })
        return render(request, 'vikes_reading_app/profile.html', {
            'user': request.user,
            'students_progress': students_progress
        })

    # Default for student users: show only their own profile
    return render(request, 'vikes_reading_app/profile.html', {'user': request.user})

@login_required
def story_create(request):
    """
    Allows teachers to create a new story.
    On POST, saves the story as 'published' and redirects to 'my_stories'.
    """
    if request.user.role != 'teacher':
        return HttpResponseForbidden("You are not allowed to create stories.")
    
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.author = request.user
            story.status = 'published'
            messages.success(request, "Your story has been published!")
            story.save()
            return redirect('my_stories')
    else:
        form = StoryForm()
    return render(request, 'vikes_reading_app/story_create.html', {'form': form})

@login_required
def story_edit(request, story_id):
    """
    Allows authors to edit their own stories.
    On POST, updates the story and redirects to 'my_stories'.
    """
    story = get_object_or_404(Story, id=story_id)
    if request.user != story.author:
        return HttpResponseForbidden("You are not allowed to edit this story.")
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES, instance=story)
        if form.is_valid():
            story = form.save(commit=False)
            story.status = 'published'
            story.save()
            messages.success(request, "Your story has been updated!")
            return redirect('my_stories')
    else:
        form = StoryForm(instance=story)
    return render(request, 'vikes_reading_app/story_edit.html', {
        'form': form,
        'story': story
    })

@login_required
def story_read_teacher(request, story_id):
    """
    Teacher view for a story. Shows the story text and associated pre-reading and post-reading questions.
    """
    story = get_object_or_404(Story, id=story_id)
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
    pre_reading_exercises = PreReadingExercise.objects.filter(story=story).order_by('id')
    post_reading_questions = PostReadingQuestion.objects.filter(story=story).order_by('id')
    return render(request, 'vikes_reading_app/story_read_teacher.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })



@login_required
def story_delete(request, story_id):
    """
    Allows authors to delete their own stories.
    On POST, deletes the story and all related exercises/questions.
    """
    story = get_object_or_404(Story, id=story_id)
    if request.user.role != 'teacher' or story.author != request.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        PreReadingExercise.objects.filter(story=story).delete()
        PostReadingQuestion.objects.filter(story=story).delete()
        story.delete()
        messages.success(request, "Your story and related content have been deleted successfully!")
        return redirect('my_stories')
    return render(request, 'vikes_reading_app/story_delete.html', {'story': story})

@login_required
def manage_questions(request, story_id):
    """
    Allows the story author to view and manage (add/edit/delete) pre-reading and post-reading questions for a story.
    """
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
    story = get_object_or_404(Story, id=story_id)
    pre_reading_exercises = PreReadingExercise.objects.filter(story=story).order_by('id')
    post_reading_questions = PostReadingQuestion.objects.filter(story=story).order_by('id')
    return render(request, 'vikes_reading_app/manage_questions.html', {
        'story': story,
        'pre_reading_exercises': pre_reading_exercises,
        'post_reading_questions': post_reading_questions,
    })

@login_required
def post_reading_create(request, story_id):
    """
    Allows the story author to add a new post-reading question to a story.
    """
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
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

@login_required
def post_reading_edit(request, story_id, question_id):
    """
    Allows the story author to edit an existing post-reading question.
    """
    if request.user.role != 'teacher':
        return HttpResponseForbidden("Students cannot view this page.")
    story = get_object_or_404(Story, id=story_id, author=request.user)
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

@login_required
def post_reading_delete(request, story_id, question_id):
    """
    Allows the story author to delete a post-reading question.
    """
    question = get_object_or_404(PostReadingQuestion, id=question_id, story__id=story_id)
    story = question.story
    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted successfully!")
        return redirect('manage_questions', story_id=story.id)
    return render(request, 'vikes_reading_app/post_reading_delete.html', {'question': question, 'story': story})

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

@login_required
def story_read_student(request, story_id):
    """
    Displays the story text only (no exercises/questions) for students.
    """
    story = get_object_or_404(Story, id=story_id)
    return render(request, 'vikes_reading_app/story_read_student.html', {'story': story})

@login_required
def post_reading_read(request, story_id, question_index=0):
    """
    Handles displaying post-reading questions one by one to the student.
    Tracks lookup count in session and determines lookup wait time.
    Redirects to summary page when all questions are answered.
    """
    story = get_object_or_404(Story, id=story_id)
    questions = list(PostReadingQuestion.objects.filter(story=story).order_by('id'))
    if question_index >= len(questions):
        return redirect('post_reading_summary', story_id=story.id)  # All questions finished
    question = questions[question_index]
    # Track how many times the student has looked up the story for this question (session)
    lookup_key = f'lookup_story_{story_id}_q{question.id}'
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

@login_required
def story_lookup(request, story_id):
    """
    Temporarily displays the story text for a post-reading question lookup.
    Tracks and limits lookup count per question in session.
    After max lookups, redirects back to the question.
    """
    story = get_object_or_404(Story, id=story_id)
    question_id = int(request.GET.get('question_id'))
    # Track lookup count in session
    lookup_key = f'lookup_story_{story_id}_q{question_id}'
    lookup_count = request.session.get(lookup_key, 0)
    # Find the index for this question (for returning)
    questions = list(PostReadingQuestion.objects.filter(story=story).order_by('id'))
    question_index = next((index for index, q in enumerate(questions) if q.id == question_id), 0)
    if lookup_count >= 3:
        # No more lookups allowed; return to question
        return redirect('post_reading_read', story_id=story.id, question_index=question_index)
    lookup_count += 1
    request.session[lookup_key] = lookup_count
    # Set time limit for this lookup (in seconds)
    times = {1: 30, 2: 45, 3: 60}
    time_limit = times.get(lookup_count, 60)
    return render(request, 'vikes_reading_app/story_lookup.html', {
        'story': story,
        'time_limit': time_limit,
        'story_id': story_id,
        'question_id': question_id,
        'question_index': question_index,
    })

from django.shortcuts import redirect


@login_required
def post_reading_submit(request, story_id, question_id):
    """
    Handles submission of a post-reading question answer.
    Saves answer correctness in Progress for this user and story.
    Redirects to next question or summary.
    """
    story = get_object_or_404(Story, id=story_id)
    question = get_object_or_404(PostReadingQuestion, id=question_id, story=story)
    if request.method == "POST":
        selected_answer_id = request.POST.get("answer")
        # If no answer selected, show error and reload question
        if not selected_answer_id:
            messages.error(request, "Please select an answer before submitting.")
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
        questions = list(PostReadingQuestion.objects.filter(story=story).order_by('id'))
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

@login_required
def post_reading_summary(request, story_id):
    """
    Shows a summary of post-reading results for the student.
    Displays number of correct answers and time spent.
    """
    story = get_object_or_404(Story, id=story_id)
    questions = PostReadingQuestion.objects.filter(story=story).order_by('id')
    # Retrieve student's progress and answers
    progress = Progress.objects.filter(student=request.user, read_story=story).first()
    student_answers = progress.answers_given if progress and progress.answers_given else {}
    correct_count = 0
    for question in questions:
        is_correct = student_answers.get(str(question.id), False)
        if is_correct:
            correct_count += 1
    total_questions = questions.count()
    context = {
        'story': story,
        'questions': questions,
        'correct_answers': correct_count,
        'total_questions': total_questions,
        'post_reading_time': progress.post_reading_time if progress else 0,
    }
    return render(request, 'vikes_reading_app/post_reading_summary.html', context)

@csrf_exempt
@login_required
def save_reading_time(request, story_id):
    """
    API endpoint to save the time spent reading a story.
    Updates or creates Progress record for the user/story.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            time_spent = data.get("time_spent", 0)
            # Save or update the progress
            story = get_object_or_404(Story, id=story_id)
            progress, _ = Progress.objects.update_or_create(
                student=request.user,
                read_story=story,
                defaults={
                    'reading_time': time_spent,
                    'score': 0.0,
                    'current_stage': 'reading'
                }
            )
            return JsonResponse({"status": "success", "time_spent": time_spent})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
@login_required
def save_pre_reading_time(request, story_id):
    """
    API endpoint to save time spent in pre-reading exercises.
    Updates or creates Progress record for the user/story.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            time_spent = data.get("time_spent", 0)
            # Save or update the progress
            story = get_object_or_404(Story, id=story_id)
            progress, _ = Progress.objects.update_or_create(
                student=request.user,
                read_story=story,
                defaults={
                    'pre_reading_time': time_spent,
                    'current_stage': 'reading'
                }
            )
            print(f"Pre-reading time saved: {time_spent} seconds")
            return JsonResponse({"status": "success", "time_spent": time_spent})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
@login_required
def save_post_reading_time(request, story_id):
    """
    API endpoint to save time spent in post-reading questions.
    Updates or creates Progress record for the user/story.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            time_spent = data.get("time_spent", 0)
            # Save or update the progress
            story = get_object_or_404(Story, id=story_id)
            progress, _ = Progress.objects.update_or_create(
                student=request.user,
                read_story=story,
                defaults={
                    'post_reading_time': time_spent,
                    'current_stage': 'completed'
                }
            )
            print(f"Post-reading time saved: {time_spent} seconds")
            return JsonResponse({"status": "success", "time_spent": time_spent})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@login_required
def reset_progress(request, story_id):
    """
    Resets all progress for the current user and story:
      - Removes session-based pre/post-reading answers and lookups
      - Deletes Progress record from DB
      - Redirects to start pre-reading again
    """
    story = get_object_or_404(Story, id=story_id)
    # Remove session-based pre-reading answers
    session_key = f'pre_reading_progress_{story_id}'
    completed = request.session.get(session_key, [])
    for qid in completed:
        request.session.pop(f'answer_{qid}', None)
    request.session.pop(session_key, None)
    # Remove session-based post-reading answers
    post_reading_key = f'post_reading_progress_{story_id}'
    post_completed = request.session.get(post_reading_key, [])
    for qid in post_completed:
        request.session.pop(f'answer_{qid}', None)
    request.session.pop(post_reading_key, None)
    # Remove lookup-related session data for this story
    keys_to_delete = [key for key in request.session.keys() if key.startswith(f'lookup_story_{story_id}_')]
    for key in keys_to_delete:
        del request.session[key]
    # Remove DB-based progress for this user/story
    Progress.objects.filter(student=request.user, read_story=story).delete()
    # Redirect to start pre-reading again
    return redirect('pre_reading_read', story_id=story_id)

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
    # Calculate post-reading score from Progress
    post_total_questions = PostReadingQuestion.objects.filter(story=story).count()
    post_correct_answers = 0
    if progress and progress.answers_given:
        post_correct_answers = sum(1 for value in progress.answers_given.values() if value)
    context = {
        'story': story,
        'pre_correct_answers': pre_correct_answers,
        'pre_total_questions': pre_total_questions,
        'post_correct_answers': post_correct_answers,
        'post_total_questions': post_total_questions,
    }
    return render(request, 'vikes_reading_app/story_entry_point.html', context)


@require_POST
@login_required
def start_lookup(request, story_id, question_id):
    """
    Handles tracking of post-reading lookups at the DB level (if used).
    Increments lookup count for a specific question and user.
    Redirects to the story lookup page with appropriate time limit.
    """
    story = get_object_or_404(Story, id=story_id)
    question = get_object_or_404(PostReadingQuestion, id=question_id, story=story)
    progress, _ = Progress.objects.get_or_create(student=request.user, read_story=story)
    lookups = progress.post_reading_lookups or {}
    current_count = lookups.get(str(question_id), 0)
    if current_count >= 3:
        messages.error(request, "No more lookups left for this question.")
        return redirect("post_reading_read", story_id=story.id, question_index=0)
    current_count += 1
    lookups[str(question_id)] = current_count
    progress.post_reading_lookups = lookups
    progress.save()
    time_limit = {1: 30, 2: 45, 3: 60}.get(current_count, 60)
    return redirect(f"/story-lookup/{story_id}/?question_id={question_id}&time_limit={time_limit}")

@require_POST
@login_required
def return_to_question(request, story_id, question_index):
    """
    Redirects user back to the post-reading question after a lookup.
    """
    return redirect("post_reading_read", story_id=story_id, question_index=question_index)

