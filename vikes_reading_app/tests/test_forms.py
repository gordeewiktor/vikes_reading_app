import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from vikes_reading_app.forms import (
    CustomUserCreationForm,
    StoryForm,
    PreReadingExerciseForm,
    PostReadingQuestionForm,
)
from vikes_reading_app.models import CustomUser

# --- Fixtures for Valid Form Data ---

@pytest.fixture
def valid_user_data():
    return {
        "username": "formuser",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123",
    }

@pytest.fixture
def valid_story_data():
    return {
        "title": "Moonlight",
        "description": "A peaceful night tale",
        "content": "Once upon a time, there was silence.",
    }

@pytest.fixture
def valid_pre_reading_data():
    return {
        "question_text": "What do you see in the sky?",
        "option_1": "Stars",
        "option_2": "Fish",
        "is_option_1_correct": True,
        "is_option_2_correct": False,
    }

@pytest.fixture
def valid_post_reading_data():
    return {
        "question_text": "Why did they dance?",
        "option_1": "Because it rained",
        "option_2": "Because it snowed",
        "option_3": "Because of the music",
        "option_4": "Because of the moonlight",
        "correct_option": 4,
        "explanation": "They danced because of the moonlight.",
    }

# ============================
# 🧪 User Registration Form
# ============================

# ✅ Accepts valid registration input
@pytest.mark.django_db
def test_user_registration_form_valid(valid_user_data):
    form = CustomUserCreationForm(data=valid_user_data)
    assert form.is_valid()

# ❌ Rejects mismatched passwords
@pytest.mark.django_db
def test_user_registration_passwords_mismatch(valid_user_data):
    data = valid_user_data.copy()
    data["password2"] = "DifferentPassword123"
    form = CustomUserCreationForm(data=data)
    assert not form.is_valid()
    assert "password2" in form.errors

# ❌ Rejects weak passwords (too simple)
@pytest.mark.django_db
def test_user_registration_weak_password(valid_user_data):
    data = valid_user_data.copy()
    data["password1"] = data["password2"] = "123"
    form = CustomUserCreationForm(data=data)
    assert not form.is_valid()
    assert "password2" in form.errors or "password1" in form.errors


# ========================
# 📝 Story Form
# ========================

# ✅ Valid story form submission
def test_story_form_valid(valid_story_data):
    form = StoryForm(data=valid_story_data)
    assert form.is_valid()


# ✅ Content is optional
def test_story_form_content_optional(valid_story_data):
    data = valid_story_data.copy()
    data["content"] = ""
    form = StoryForm(data=data)
    assert form.is_valid()


# ❌ Missing title or description
@pytest.mark.parametrize("missing_field", ["title", "description"])
def test_story_form_missing_required_fields(valid_story_data, missing_field):
    data = valid_story_data.copy()
    data[missing_field] = ""
    form = StoryForm(data=data)
    assert not form.is_valid()
    assert missing_field in form.errors


# ========================
# 📚 Pre-Reading Exercise Form
# ========================

# ✅ Only one correct option is marked
def test_pre_reading_form_valid_one_correct(valid_pre_reading_data):
    form = PreReadingExerciseForm(data=valid_pre_reading_data)
    assert form.is_valid()


@pytest.mark.parametrize("form_data", [
    {
        "question_text": "Ambiguous",
        "option_1": "Yes",
        "option_2": "Also yes",
        "is_option_1_correct": True,
        "is_option_2_correct": True,
    },
    {
        "question_text": "Forgot something?",
        "option_1": "Left",
        "option_2": "Right",
        "is_option_1_correct": False,
        "is_option_2_correct": False,
    },
])
def test_pre_reading_form_invalid_correct_options(form_data):
    form = PreReadingExerciseForm(data=form_data)
    assert not form.is_valid()
    assert "__all__" in form.errors


# ✅ Audio file is optional
def test_pre_reading_form_with_audio(valid_pre_reading_data):
    audio = SimpleUploadedFile("sound.mp3", b"fake-audio-content", content_type="audio/mpeg")
    form = PreReadingExerciseForm(data=valid_pre_reading_data, files={"audio_file": audio})
    assert form.is_valid()


# ========================
# 📖 Post-Reading Question Form
# ========================

# ✅ Valid post-reading form submission
def test_post_reading_form_valid(valid_post_reading_data):
    form = PostReadingQuestionForm(data=valid_post_reading_data)
    assert form.is_valid()


# ❌ Missing required fields
@pytest.mark.parametrize("missing_field", [
    "question_text", "option_1", "option_2", "option_3", "option_4", "correct_option"
])
def test_post_reading_form_missing_fields(valid_post_reading_data, missing_field):
    data = valid_post_reading_data.copy()
    data[missing_field] = "" if missing_field != "correct_option" else None
    form = PostReadingQuestionForm(data=data)
    assert not form.is_valid()
    assert missing_field in form.errors