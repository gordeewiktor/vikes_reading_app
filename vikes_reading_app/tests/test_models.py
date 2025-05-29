import pytest
from vikes_reading_app.models import Story
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_create_story():
    author = User.objects.create_user(username="user", password="pass")
    story = Story.objects.create(
        title="Test story",
        description="A quick test",
        author=author,
        content="Once uppon a time...",
    )
    assert story.title == "Test story"