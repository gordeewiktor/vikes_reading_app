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

@pytest.fixture
def create_user(db):
    def _create_user(username="user", password="pass123", role="student"):
        return CustomUser.objects.create_user(username=username, password=password, role=role)
    return _create_user
pytestmark = pytest.mark.django_db

@pytest.fixture
def create_story(create_user):
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
    return SimpleUploadedFile(
        name="test_audio.mp3",
        content=b"fake audio content",
        content_type="audio/mpeg",
    )

# === CustomUser ===
@pytest.mark.parametrize('username, role', [
    ('john', 'teacher'),
    ('jane', 'student'),
    ('admin', 'teacher'),
])
def test_create_custom_user(create_user, username, role):
    user = create_user(username=username, role=role)
    assert user.username == username
    assert user.role == role

@pytest.mark.parametrize('username, role, expected_str', [
    ('tester', 'student', 'tester (Student)'),
    ('mr_smith', 'teacher', 'mr_smith (Teacher)'),
])
def test_custom_user_str(create_user, username, role, expected_str):
    user = create_user(username=username, role=role)
    assert str(user) == expected_str


# === Story ===
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

def test_story_default_status(create_story):
    story = create_story(
        title="Silent Hill",
        description="Mysterious",
        content="..."
    )
    assert story.status == "draft"

def test_story_str(create_story):
    story = create_story(
        title="My Title",
        description="Desc",
        content="Text"
    )
    assert str(story) == "My Title"


# === Progress ===
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

def test_progress_score_validation(create_user, create_story):
    student = create_user(username="s2", role="student")
    story = create_story(title="Weird", author=student)

    with pytest.raises(ValidationError):
        progress = Progress(
            student=student,
            read_story=story,
            score=150.0,  # 🚫 Invalid score (above 100)
        )
        progress.full_clean()

def test_progress_str(create_user, create_story):
    student = create_user(username="Anna", role="student")
    story = create_story(title="Clouds", author=student)
    progress = Progress.objects.create(
        student=student,
        read_story=story,
        score=50,
    )
    assert str(progress) == "Anna - Clouds - pre_reading"


# === PreReadingExercise ===
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


# === PostReadingQuestion ===
def test_create_post_reading_question(create_user, create_story):
    story = create_story(
        title="Moonlight",
        description="Night story",
        author=create_user(username="x", role="teacher")
    )
    question = PostReadingQuestion.objects.create(
        story=story,
        question_text="What happened at night?",
        option_1="They slept",
        option_2="They danced",
        option_3="They flew",
        option_4="They ate",
        correct_option=2,
        explanation="They danced because the moon was bright."
    )
    assert question.correct_option == 2


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