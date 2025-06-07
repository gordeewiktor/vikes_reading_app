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

@pytest.mark.django_db
def test_teacher_can_edit_own_story(client):
    # 1. Create a teacher user and log in
    teacher = User.objects.create_user(username='teachera', password='pass123', role='teacher')
    client.login(username='teachera', password='pass123')

    # 2. Create a story authored by this teacher
    story = Story.objects.create(
        title='Original Title',
        description='Original description',
        content='Original content',
        author=teacher,
        status='published'
    )

    # 3. Prepare updated story data
    updated_data = {
        'title': 'Updated Title',
        'description': 'Updated description',
        'content': 'Updated content',
    }

    # 4. Send POST request to the story edit view
    url = reverse('story_edit', args=[story.id])
    response = client.post(url, updated_data)

    # 5. Confirm the response is a redirect (successful update)
    assert response.status_code == 302

    # 6. Refresh the story from the DB and check that fields were updated
    story.refresh_from_db()
    assert story.title == 'Updated Title'
    assert story.description == 'Updated description'
    assert story.content == 'Updated content'


# New test: another teacher cannot edit someone else's story
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_other_teacher_cannot_edit_story(client):
    # 1. Create two teachers
    author = User.objects.create_user(username='author', password='pass123', role='teacher')
    intruder = User.objects.create_user(username='intruder', password='pass123', role='teacher')

    # 2. Author creates a story
    story = Story.objects.create(
        title='Original Title',
        description='Original description',
        content='Original content',
        author=author,
        status='published'
    )

    # 3. Log in as the second teacher (intruder)
    client.login(username='intruder', password='pass123')

    # 4. Try to edit the author's story
    updated_data = {
        'title': 'Hacked Title',
        'description': 'Hacked description',
        'content': 'Hacked content',
    }
    url = reverse('story_edit', args=[story.id])
    response = client.post(url, updated_data)

    # 5. Expect forbidden or redirect
    assert response.status_code in [302, 403]

    # 6. Ensure story content did not change
    story.refresh_from_db()
    assert story.title == 'Original Title'
    assert story.description == 'Original description'
    assert story.content == 'Original content'

@pytest.mark.django_db
def test_teacher_can_delete_own_story(client):
    # 1. Create a teacher user and log in
    teacher = User.objects.create_user(username='teacherdelete', password='pass1234', role='teacher')
    client.login(username='teacherdelete', password='pass1234')

    # 2. Create a story by this teacher
    story = Story.objects.create(
        title='Delete Me',
        description='This will be deleted.',
        content='Temporary content.',
        author=teacher
    )

    # 3. Send POST request to delete the story
    url = reverse('story_delete', args=[story.id])
    response = client.post(url)

    # 4. Check redirect (or success)
    assert response.status_code in [302, 200]

    # 5. Ensure the story is deleted from DB
    assert not Story.objects.filter(id=story.id).exists()

@pytest.mark.django_db
def test_other_teacher_cannot_delete_story(client):
    # 1. Create two teachers
    author = User.objects.create_user(username='authordelete', password='pass123', role='teacher')
    intruder = User.objects.create_user(username='badteacher', password='pass123', role='teacher')

    # 2. Author creates a story
    story = Story.objects.create(
        title='Protected Story',
        description='Should not be deleted.',
        content='Don’t touch me.',
        author=author
    )

    # 3. Log in as the second teacher
    client.login(username='badteacher', password='pass123')

    # 4. Attempt to delete the story
    url = reverse('story_delete', args=[story.id])
    response = client.post(url)

    # 5. Expect forbidden or redirect
    assert response.status_code in [302, 403]

    # 6. Ensure story still exists
    assert Story.objects.filter(id=story.id).exists()

@pytest.mark.django_db
def test_student_cannot_delete_story(client):
    # 1. Create a teacher and a student
    author = User.objects.create_user(username='teacherauth', password='pass123', role='teacher')
    student = User.objects.create_user(username='studentdelete', password='pass123', role='student')

    # 2. Author creates a story
    story = Story.objects.create(
        title='No Touchy',
        description='Protected from students.',
        content='Leave me be.',
        author=author
    )

    # 3. Log in as student
    client.login(username='studentdelete', password='pass123')

    # 4. Attempt to delete the story
    url = reverse('story_delete', args=[story.id])
    response = client.post(url)

    # 5. Expect forbidden or redirect
    assert response.status_code in [302, 403]

    # 6. Ensure story still exists
    assert Story.objects.filter(id=story.id).exists()


# Test: teacher cannot create story with missing fields
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_teacher_cannot_create_story_with_missing_fields(client):
    # 1. Create and log in a teacher
    teacher = User.objects.create_user(username='teacher_incomplete', password='pass123', role='teacher')
    client.login(username='teacher_incomplete', password='pass123')

    # 2. Prepare invalid data (missing title and content)
    invalid_data = {
        'title': '',
        'description': 'Oops, I forgot something.',
        'content': '',
    }

    # 3. Send POST request to create story
    url = reverse('story_create')
    response = client.post(url, invalid_data)

    # 4. Check that the form is invalid and page is re-rendered (not redirected)
    assert response.status_code == 200  # Stay on the same page due to form errors
    assert 'This field is required' in response.content.decode()

    # 5. Ensure no story was created
    assert not Story.objects.filter(description='Oops, I forgot something.').exists()
@pytest.mark.django_db
def test_anonymous_user_cannot_create_story(client):
    # Not logged in!

    form_data = {
        'title': 'Anonymous Attack',
        'description': 'Should not be allowed.',
        'content': 'No auth, no access.',
    }

    url = reverse('story_create')
    response = client.post(url, form_data)

    # Expect redirect to login page (usually 302)
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url

    # Ensure story was NOT created
    from vikes_reading_app.models import Story
    assert not Story.objects.filter(title='Anonymous Attack').exists()

@pytest.mark.django_db
def test_anonymous_user_cannot_access_story_views(client):
    from django.urls import reverse

    story_id = 999  # Dummy ID – doesn't matter since we expect redirect before lookup

    protected_urls = [
        reverse('story_read_teacher', args=[story_id]),
        reverse('story_read_student', args=[story_id]),
        reverse('story_entry_point', args=[story_id]),
        reverse('story_edit', args=[story_id]),
        reverse('story_delete', args=[story_id]),
        reverse('story_create'),
        reverse('my_stories'),
        reverse('profile'),
    ]

    for url in protected_urls:
        response = client.get(url)
        # Anonymous users should get redirected to login
        assert response.status_code == 302
        assert '/login' in response.url or 'accounts/login' in response.url

@pytest.mark.django_db
def test_student_cannot_access_teacher_views(client):
    from django.urls import reverse
    from django.contrib.auth import get_user_model
    from vikes_reading_app.models import Story

    User = get_user_model()

    # Create a teacher and a student
    teacher = User.objects.create_user(username='teacher', password='pass', role='teacher')
    student = User.objects.create_user(username='student', password='pass', role='student')

    # Create a real story authored by the teacher
    story = Story.objects.create(
        title='Protected',
        description='Teacher only',
        content='Secret stuff',
        author=teacher,
        status='published'
    )

    # Login as student
    client.login(username='student', password='pass')

    # URLs the student shouldn't access
    urls = [
        reverse('story_create'),
        reverse('story_edit', args=[story.id]),
        reverse('story_delete', args=[story.id]),
        reverse('story_read_teacher', args=[story.id]),
        reverse('manage_questions', args=[story.id]),
    ]

    for url in urls:
        response = client.get(url)
        assert response.status_code in [403, 302]