from .models import PreReadingExercise, PostReadingQuestion

# Function to check if the user is a teacher
# This will be used as a decorator to restrict access to views
# Only authenticated users with the role 'teacher' will pass this test
def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

def get_session_progress(request, story_id):
    return request.session.get(f'pre_reading_progress_{story_id}', [])

def should_redirect_student(progress, session_progress, story):
    if not progress and not session_progress:
        return 'pre_reading_read'

    post_total = PostReadingQuestion.objects.filter(story=story).count()
    answers = progress.answers_given if progress and progress.answers_given else {}
    if post_total > 0 and len(answers) == post_total:
        return 'post_reading_summary'

    return None  # Continue to render the entry point

def get_pre_reading_score(request, story):
    exercises = PreReadingExercise.objects.filter(story=story)
    total = exercises.count()
    correct = 0

    for exercise in exercises:
        selected = request.session.get(f'answer_{exercise.id}')
        if selected:
            correct_answer = exercise.option_1 if exercise.is_option_1_correct else exercise.option_2
            if selected == correct_answer:
                correct += 1

    return correct, total

def get_post_reading_score(progress):
    if not progress or not progress.answers_given:
        return 0, 0
    total = len(progress.answers_given)
    correct = sum(1 for value in progress.answers_given.values() if value)
    return correct, total