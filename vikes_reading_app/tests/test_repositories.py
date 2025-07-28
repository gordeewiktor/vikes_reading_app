import pytest
from django.contrib.auth import get_user_model
from vikes_reading_app.models import Story, PreReadingExercise, PostReadingQuestion
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository

User = get_user_model()

@pytest.mark.django_db
def test_delete_story_with_related(published_story: Story, post_reading_question: PostReadingQuestion, two_pre_reading_exercises) -> None:
    # --- Setup: create teacher user and story ---
   
    story = published_story

    # --- Ensure they exist ---
    assert Story.objects.filter(id=story.id).exists()
    assert PreReadingExercise.objects.filter(story=story).exists()
    assert PostReadingQuestion.objects.filter(story=story).exists()
    assert Story.objects.count() == 1

    # --- Call repository logic ---
    repo = ORMStoryRepository()
    repo.delete_story_with_related(story.id)

    # --- Verify story and related objects are deleted ---
    assert not Story.objects.filter(id=story.id).exists()
    assert not PreReadingExercise.objects.filter(story=story).exists()
    assert not PostReadingQuestion.objects.filter(story=story).exists()


@pytest.mark.django_db
def test_create_story(teacher_user):
    # --- Prepare data for story creation ---
    data = {
        "title": "New Story",
        "description": "A description of the new story",
        "content": "Once upon a time...",
        "status": "published"
    }

    # --- Call repository logic ---
    repo = ORMStoryRepository()
    story = repo.create_story(teacher_user.id, data)

    # --- Verify story is created with correct data ---
    assert story.id is not None
    assert story.title == data["title"]
    assert story.description == data["description"]
    assert story.content == data["content"]
    assert story.status == data["status"]
    assert story.author == teacher_user

    # --- Ensure it's in the database ---
    db_story = Story.objects.get(id=story.id)
    assert db_story.title == "New Story"


@pytest.mark.django_db
def test_edit_story(teacher_user):
    # --- Create initial story ---
    story = Story.objects.create(
        title="Old Title",
        description="Old description",
        content="Old content",
        author=teacher_user,
        status="draft"
    )

    # --- Data for update ---
    update_data = {
        "title": "Updated Title",
        "description": "Updated description",
        "content": "Updated content",
        "status": "published"
    }

    # --- Call repository logic ---
    repo = ORMStoryRepository()
    updated_story = repo.edit_story(story.id, update_data)

    # --- Verify changes ---
    assert updated_story.title == update_data["title"]
    assert updated_story.description == update_data["description"]
    assert updated_story.content == update_data["content"]
    assert updated_story.status == update_data["status"]

    # --- Ensure changes are persisted in the database ---
    db_story = Story.objects.get(id=story.id)
    assert db_story.title == "Updated Title"
    assert db_story.description == "Updated description"
    assert db_story.content == "Updated content"
    assert db_story.status == "published"