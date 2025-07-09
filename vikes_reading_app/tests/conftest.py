import pytest
from django.contrib.auth import get_user_model

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