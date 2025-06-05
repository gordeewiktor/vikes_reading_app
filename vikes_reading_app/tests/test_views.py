import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from vikes_reading_app.models import Story

User = get_user_model()

@pytest.mark.django_db
def test_teacher_can_create_story(client):
    # 1. Create and log in a teacher user
    teacher = User.objects.create_user(username='teachertest', password='password123', role='teacher')
    client.login(username='teachertest', password='password123')

    # 2. Prepare story data
    form_data = {
        'title': 'Test Story Title',
        'description': 'A quick story description.',
        'content': 'Once upon a time...',
    }

    # 3. Send POST request to create story
    url = reverse('story_create')
    response = client.post(url, form_data)

    # 4. Check the redirect status (302)
    assert response.status_code == 302

    # 5. Check that the story was actually created in DB
    stories = Story.objects.filter(title='Test Story Title')
    assert stories.exists()
    assert stories.first().author == teacher

@pytest.mark.django_db
def test_student_cannot_create_story(client):
    # 1. Create and log in a student user
    student = User.objects.create_user(username='studenttest', password='password123', role='student')
    client.login(username='studenttest', password='password123')

    # 2. Attempt to create a story
    form_data = {
        'title': 'Student Story',
        'description': 'Student should not do this.',
        'content': 'Forbidden content!',
    }

    url = reverse('story_create')
    response = client.post(url, form_data)

    # 3. Expect forbidden or redirect
    assert response.status_code in [302, 403]
    assert not Story.objects.filter(title='Student Story').exists()