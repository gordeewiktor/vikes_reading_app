# --- Imports and Model Setup ---

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from vikes_reading_app.models import (
    CustomUser,
    Story,
    Progress,
    PreReadingExercise,
    PostReadingQuestion
)

# --- Fixtures ---

@pytest.fixture
def create_user(db):
    """Creates a user with given username, password, and role."""
    def _create_user(username="user", password="pass123", role="student"):
        return CustomUser.objects.create_user(username=username, password=password, role=role)
    return _create_user

@pytest.fixture
def create_story(create_user):
    """Creates a story with optional attributes."""
    def _create_story(**kwargs):
        return Story.objects.create(
            title=kwargs.get("title", "Default Title"),
            description=kwargs.get("description", "Default description."),
            content=kwargs.get("content", "Default content."),
            author=kwargs.get("author", create_user(role='teacher')),
            status=kwargs.get("status", "draft"),
            narration_audio=kwargs.get("narration_audio"),
        )
    return _create_story

@pytest.fixture
def audio_file():
    """Creates a dummy uploaded audio file."""
    return SimpleUploadedFile(
        name="test_audio.mp3",
        content=b"fake audio content",
        content_type="audio/mpeg",
    )

pytestmark = pytest.mark.django_db

# ========================
# 👤 CustomUser Model Tests
# ========================

# ✅ Create user with different roles
@pytest.mark.parametrize('username, role', [
    ('john', 'teacher'),
    ('jane', 'student'),
    ('admin', 'teacher'),
])
def test_create_custom_user(create_user, username, role):
    user = create_user(username=username, role=role)
    assert user.username == username
    assert user.role == role

# ✅ __str__ method of CustomUser
@pytest.mark.parametrize('username, role, expected_str', [
    ('tester', 'student', 'tester (Student)'),
    ('mr_smith', 'teacher', 'mr_smith (Teacher)'),
])
def test_custom_user_str(create_user, username, role, expected_str):
    user = create_user(username=username, role=role)
    assert str(user) == expected_str

# ========================
# 📘 Story Model Tests
# ========================

# ✅ Create story with audio

def test_create_story_with_audio(create_story, audio_file):
    story = create_story(
        title="Magic Tale",
        description="Exciting adventure",
        content="Once upon a time...",
        status="published",
        narration_audio = audio_file,
    )
    assert story.title == "Magic Tale"
    assert story.status == "published"
    assert story.narration_audio.name.startswith('story_audio/test_audio')
    assert story.narration_audio.name.endswith('.mp3')

# ✅ Default status is draft

def test_story_default_status(create_story):
    story = create_story(
        title="Silent Hill",
        description="Mysterious",
        content="..."
    )
    assert story.status == "draft"

# ✅ __str__ method of Story

def test_story_str(create_story):
    story = create_story(
        title="My Title",
        description="Desc",
        content="Text"
    )
    assert str(story) == "My Title"

# 🧪 Story title validation

@pytest.mark.parametrize("title, is_valid", [
    ("", False),
    ("A brave tale", True),
    ("A" * 201, False),
])
def test_story_title_edge_cases(create_user, title, is_valid):
    story = Story(
        title=title,
        description="Desc",
        content="Content",
        author=create_user(username="maxy", role="teacher"),
    )
    if is_valid:
        story.full_clean()
    else:
        with pytest.raises(ValidationError):
            story.full_clean()

# ========================
# 📊 Progress Model Tests
# ========================

# ✅ Create progress entry with valid score

def test_create_progress_entry(create_user, create_story):
    student = create_user(username="student1", role="student")
    story = create_story(title="The End", author=create_user(username="teachy", role="teacher"))
    progress = Progress.objects.create(
        student=student,
        read_story=story,
        score=85.5,
        current_stage='reading',
        answers_given={"q1": "a"},
        post_reading_lookups={},
    )
    assert progress.score == 85.5
    assert progress.current_stage == "reading"

# ❌ Invalid score above 100

def test_progress_score_validation(create_user, create_story):
    student = create_user(username="s2", role="student")
    story = create_story(title="Weird", author=student)
    with pytest.raises(ValidationError):
        progress = Progress(
            student=student,
            read_story=story,
            score=150.0,
        )
        progress.full_clean()

# ✅ __str__ method of Progress

@pytest.mark.parametrize("username, story_title, expected_str", [
    ("Anna", "Clouds", "Anna - Clouds - pre_reading"),
    ("Leo", "Jungle Book", "Leo - Jungle Book - pre_reading"),
    ("Mira", "Ocean Deep", "Mira - Ocean Deep - pre_reading"),
])
def test_progress_str(create_user, create_story, username, story_title, expected_str):
    student = create_user(username=username, role="student")
    story = create_story(title=story_title, author=student)
    progress = Progress.objects.create(
        student=student,
        read_story=story,
        score=50,
    )
    assert str(progress) == expected_str

# ================================
# 🎧 PreReadingExercise Model Tests
# ================================

# ✅ Create pre-reading exercise with audio

def test_create_pre_reading_exercise_with_audio(create_user, create_story, audio_file):
    story = create_story(author=create_user(username="t", role="teacher"))
    question = PreReadingExercise.objects.create(
        story=story,
        question_text="What is the sea?",
        option_1="Water",
        option_2="Sky",
        is_option_1_correct=True,
        audio_file=audio_file
    )
    assert question.story == story
    assert question.is_option_1_correct is True
    assert question.audio_file.name.startswith('pre_reading_audio/test_audio')
    assert question.audio_file.name.endswith('.mp3')

# ✅ Create pre-reading without audio

def test_create_pre_reading_exercise_without_audio(create_user, create_story):
    story = create_story(author=create_user(username="alice", role="teacher"))
    question = PreReadingExercise.objects.create(
        story=story,
        question_text="What color is the sky?",
        option_1="Blue",
        option_2="Green",
        is_option_1_correct=True,
        audio_file=None
    )
    assert question.story == story
    assert question.audio_file.name is None
    assert question.is_option_1_correct is True

# ✅ __str__ method of PreReadingExercise

def test_pre_reading_exercise_str(create_user, create_story):
    story = create_story(author=create_user(username="testy", role="teacher"))
    question = PreReadingExercise.objects.create(
        story=story,
        question_text="What is the sea?",
        option_1="Water",
        option_2="Sky",
        is_option_1_correct=True
    )
    assert str(question) == "Default Title - What is the sea?"

# 🧪 Validate question text limits

@pytest.mark.parametrize("question_text, is_valid", [
    ("", False),
    ("What is the sky made of?", True),
    ("A" * 501, False),
])
def test_pre_reading_question_text_validation(create_story, create_user, question_text, is_valid):
    story = create_story(author=create_user(username="edgy", role="teacher"))
    question = PreReadingExercise(
        story=story,
        question_text=question_text,
        option_1="Clouds",
        option_2="Stars",
        is_option_1_correct=True
    )
    if is_valid:
        question.full_clean()
    else:
        with pytest.raises(ValidationError):
            question.full_clean()

# ================================
# ✅ PostReadingQuestion Model Tests
# ================================

# ✅ Create post-reading question

@pytest.mark.parametrize("title, username, question_text, correct_option, explanation", [
    ("Moonlight", "x", "What happened at night?", 2, "They danced because the moon was bright."),
    ("Morning Breeze", "sunny", "What did they do at sunrise?", 1, "They watched the sunrise."),
    ("Stormy Night", "storm_rider", "What caused the noise?", 4, "It was thunder."),
])
def test_create_post_reading_question(create_user, create_story, title, username, question_text, correct_option, explanation):
    story = create_story(
        title=title,
        description="Just a test story",
        author=create_user(username=username, role="teacher")
    )
    question = PostReadingQuestion.objects.create(
        story=story,
        question_text=question_text,
        option_1="They slept",
        option_2="They danced",
        option_3="They flew",
        option_4="They ate",
        correct_option=correct_option,
        explanation=explanation
    )
    assert question.correct_option == correct_option
    assert question.explanation == explanation

# ✅ __str__ method of PostReadingQuestion

def test_post_reading_question_str(create_user, create_story):
    story = create_story(
        title="Starlight",
        description="Peaceful",
        author=create_user(username="maria", role="teacher")
    )
    question = PostReadingQuestion.objects.create(
        story=story,
        question_text="What did they see?",
        option_1="Stars",
        option_2="Clouds",
        option_3="Bats",
        option_4="Nothing",
        correct_option=1
    )
    assert str(question) == "Starlight - What did they see?"

# 🧪 Validate correct_option field

@pytest.mark.parametrize("correct_option, is_valid", [
    (1, True),
    (4, True),
    (5, False),
    (0, False),
])
def test_post_question_correct_option_validation(create_story, create_user, correct_option, is_valid):
    story = create_story(title="Limits", author=create_user(username="bouncer", role="teacher"))
    question = PostReadingQuestion(
        story=story,
        question_text="Pick the truth",
        option_1="This one",
        option_2="That one",
        option_3="Maybe",
        option_4="Nope",
        correct_option=correct_option,
        explanation="Only 1–4 allowed"
    )
    if is_valid:
        question.full_clean()
    else:
        with pytest.raises(ValidationError):
            question.full_clean()