import pytest
from django.contrib.auth import get_user_model
from vikes_reading_app.models import Story, PostReadingQuestion, PreReadingExercise

User = get_user_model()

# --- User Fixtures ---

@pytest.fixture
def teacher_user(db):
    """Creates a teacher user."""
    return User.objects.create_user(username='teacher', password='pass', role='teacher')

@pytest.fixture
def student_user(db):
    """Creates a student user."""
    return User.objects.create_user(username='student', password='pass', role='student')

@pytest.fixture
def published_story(teacher_user) -> Story:
    """Creates a published story visible to students."""
    return Story.objects.create(
        title="Published Story",
        description="Visible to students",
        content="Once upon a published time...",
        author=teacher_user,
        status="published"
    )

@pytest.fixture
def post_reading_question(published_story):
    """Creates one post-reading question for a story."""
    return PostReadingQuestion.objects.create(
        story=published_story,
        question_text='What happened at the end?',
        option_1='They fought a dragon.',
        option_2='They lived happily ever after.',
        option_3='They moved to Mars.',
        option_4='They went to bed.',
        correct_option=2,
        explanation='Classic fairy tale ending.'
    )

@pytest.fixture
def two_pre_reading_exercises(published_story):
    """Creates two pre-reading exercises for a story."""
    ex1 = PreReadingExercise.objects.create(
        story=published_story,
        question_text="Q1?",
        option_1="A",
        option_2="B",
        is_option_1_correct=True
    )
    ex2 = PreReadingExercise.objects.create(
        story=published_story,
        question_text="Q2?",
        option_1="C",
        option_2="D",
        is_option_2_correct=True
    )
    return ex1, ex2