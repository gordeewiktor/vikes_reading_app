import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from vikes_reading_app.models import Story, PreReadingExercise, PostReadingQuestion

User = get_user_model()

@pytest.fixture
def teacher_user(db):
    return User.objects.create_user(username='teacher', password='pass', role='teacher')

@pytest.fixture
def student_user(db):
    return User.objects.create_user(username='student', password='pass', role='student')

@pytest.fixture
def logged_in_client_teacher(client, teacher_user):
    client.login(username='teacher', password='pass')
    return client, teacher_user

@pytest.fixture
def logged_in_client_student(client, student_user):
    client.login(username='student', password='pass')
    return client

@pytest.mark.django_db
def test_teacher_can_create_story(logged_in_client_teacher):
    client, teacher = logged_in_client_teacher
    form_data = {
        'title': 'Test Story Title',
        'description': 'A quick story description.',
        'content': 'Once upon a time...',
    }

    url = reverse('story_create')
    response = client.post(url, form_data)

    assert response.status_code == 302
    stories = Story.objects.filter(title='Test Story Title')
    assert stories.exists()
    assert stories.first().author == teacher

@pytest.mark.django_db
def test_student_cannot_create_story(logged_in_client_student):
    client = logged_in_client_student
    form_data = {
        'title': 'Student Story',
        'description': 'Student should not do this.',
        'content': 'Forbidden content!',
    }

    url = reverse('story_create')
    response = client.post(url, form_data)

    # 2. Expect forbidden or redirect
    assert response.status_code in [302, 403]
    assert not Story.objects.filter(title='Student Story').exists()

@pytest.mark.django_db
def test_teacher_can_edit_own_story(logged_in_client_teacher):
    client, teacher = logged_in_client_teacher
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


@pytest.mark.django_db
def test_other_teacher_cannot_edit_story(client, teacher_user):
    # 1. Create two teachers
    author = teacher_user

    # 2. Author creates a story
    story = Story.objects.create(
        title='Original Title',
        description='Original description',
        content='Original content',
        author=author,
        status='published'
    )

    # 3. Log in as the second teacher (intruder)
    intruder = User.objects.create_user(username='intruder', password='pass123', role='teacher')
    client.login(username=intruder.username, password='pass123')

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
def test_teacher_can_delete_own_story(logged_in_client_teacher):
    # 1. Create a teacher user and log in
    client, teacher = logged_in_client_teacher

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
def test_student_cannot_delete_story(client, student_user):
    # 1. Create a teacher and a student
    author = User.objects.create_user(username='teacherauth', password='pass123', role='teacher')
    student = student_user

    # 2. Author creates a story
    story = Story.objects.create(
        title='No Touchy',
        description='Protected from students.',
        content='Leave me be.',
        author=author
    )

    # 3. Log in as student
    client.login(username=student.username, password='pass')

    # 4. Attempt to delete the story
    url = reverse('story_delete', args=[story.id])
    response = client.post(url)

    # 5. Expect forbidden or redirect
    assert response.status_code in [302, 403]

    # 6. Ensure story still exists
    assert Story.objects.filter(id=story.id).exists()

@pytest.mark.django_db
def test_teacher_cannot_create_story_with_missing_fields(logged_in_client_teacher):
    # 1. Use logged-in teacher fixture
    client, _ = logged_in_client_teacher

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
def test_student_cannot_access_teacher_views(client, teacher_user, student_user):
    story = Story.objects.create(
        title='Protected',
        description='Teacher only',
        content='Secret stuff',
        author=teacher_user,
        status='published'
    )

    client.login(username=student_user.username, password='pass')

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

@pytest.mark.django_db
def test_student_can_view_story_read_student(client, teacher_user, student_user):
    story = Story.objects.create(
        title='Public Story',
        description='Readable by students',
        content='This story is safe for students to view.',
        author=teacher_user,
        status='published'
    )

    client.login(username=student_user.username, password='pass')

    url = reverse('story_read_student', args=[story.id])
    response = client.get(url)

    assert response.status_code == 200
    assert b'This story is safe for students to view.' in response.content

@pytest.mark.django_db
def test_student_redirected_to_pre_reading_if_no_progress(client, teacher_user, student_user):
    story = Story.objects.create(
        title='Fresh Start',
        description='No progress yet',
        content='Story content.',
        author=teacher_user,
        status='published'
    )

    client.login(username=student_user.username, password='pass')

    url = reverse('story_entry_point', args=[story.id])
    response = client.get(url)

    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_redirected_to_summary_after_finishing_pre_reading(client, teacher_user, student_user):

    # Create a story
    story = Story.objects.create(
        title='Summary Redirect Test',
        description='Test redirection to pre-reading summary',
        content='Some content',
        author=teacher_user,
        status='published'
    )

    # Create two pre-reading exercises
    exercise1 = PreReadingExercise.objects.create(
        story=story,
        question_text='What is 1+1?',
        option_1='2',
        option_2='3',
        is_option_1_correct=True
    )
    exercise2 = PreReadingExercise.objects.create(
        story=story,
        question_text='What is 2+2?',
        option_1='3',
        option_2='4',
        is_option_2_correct=True
    )

    # Log in as student
    client.login(username=student_user.username, password='pass')

    # Simulate session with all pre-reading questions answered
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [exercise1.id, exercise2.id]
    session.save()

    # Access pre-reading read view
    url = reverse('pre_reading_read', args=[story.id])
    response = client.get(url)

    # Should redirect to summary
    assert response.status_code == 302
    assert reverse('pre_reading_summary', args=[story.id]) in response.url

@pytest.mark.django_db
def test_teacher_can_view_only_their_own_stories(client):
    # 1. Create two teachers
    teacher1 = User.objects.create_user(username='t1', password='pass123', role='teacher')
    teacher2 = User.objects.create_user(username='t2', password='pass123', role='teacher')

    # 2. Each teacher creates a story
    story1 = Story.objects.create(title='T1 Story', description='desc', content='...', author=teacher1)
    story2 = Story.objects.create(title='T2 Story', description='desc', content='...', author=teacher2)

    # 3. Log in as teacher1
    client.login(username='t1', password='pass123')

    # 4. Access "My Stories" page
    url = reverse('my_stories')
    response = client.get(url)

    # 5. Make sure teacher1's story is present
    assert response.status_code == 200
    content = response.content.decode()
    assert 'T1 Story' in content

    # 6. Make sure teacher2's story is NOT present
    assert 'T2 Story' not in content

@pytest.mark.django_db
def test_student_cannot_access_my_stories(client, student_user):
    # Log in as student
    client.login(username=student_user.username, password='pass')

    # Attempt to access the teacher-only 'my_stories' page
    url = reverse('my_stories')
    response = client.get(url)

    # Expect redirect to login or 403 Forbidden
    assert response.status_code in [302, 403]

@pytest.mark.django_db
def test_teacher_can_access_story_read_teacher_view(client, teacher_user):
    # 1. Teacher creates a story
    story = Story.objects.create(
        title='Secret Teacher View',
        description='For teacher eyes only',
        content='Top secret stuff here.',
        author=teacher_user,
        status='published'
    )

    # 2. Log in as that teacher
    client.login(username=teacher_user.username, password='pass')

    # 3. Access the teacher view for this story
    url = reverse('story_read_teacher', args=[story.id])
    response = client.get(url)

    # 4. Confirm successful access and correct content
    assert response.status_code == 200
    assert b'Top secret stuff here.' in response.content

@pytest.mark.django_db
def test_other_teacher_cannot_access_teacher_read_view(client):
    # 1. Create two teachers
    author = User.objects.create_user(username='authorteacher', password='pass123', role='teacher')
    intruder = User.objects.create_user(username='intruderteacher', password='pass123', role='teacher')

    # 2. Author creates a story
    story = Story.objects.create(
        title='Top Secret',
        description='For author only',
        content='Confidential teacher stuff',
        author=author,
        status='published'
    )

    # 3. Log in as intruder
    client.login(username=intruder.username, password='pass123')

    # 4. Try to access the teacher-only read view
    url = reverse('story_read_teacher', args=[story.id])
    response = client.get(url)

    # 5. Should be forbidden or redirected
    assert response.status_code in [302, 403]

@pytest.mark.django_db
def test_student_cannot_access_teacher_read_view(client, teacher_user, student_user):
    # 1. Author teacher creates a story
    story = Story.objects.create(
        title='Secret Stuff',
        description='Only for teachers',
        content='Do not show students!',
        author=teacher_user,
        status='published'
    )

    # 2. Student logs in
    client.login(username=student_user.username, password='pass')

    # 3. Student tries to access the teacher-only view
    url = reverse('story_read_teacher', args=[story.id])
    response = client.get(url)

    # 4. Should be forbidden or redirect
    assert response.status_code in [302, 403]

@pytest.mark.django_db
def test_teacher_can_see_pre_and_post_reading_items_in_teacher_read_view(client):
    # 1. Create teacher and log in
    teacher = User.objects.create_user(username='teachertest', password='pass123', role='teacher')
    client.login(username='teachertest', password='pass123')

    # 2. Create story authored by teacher
    story = Story.objects.create(
        title='Story with Content',
        description='Something to test',
        content='Story goes here',
        author=teacher,
        status='published'
    )

    # 3. Create pre- and post-reading items
    pre = PreReadingExercise.objects.create(
        story=story,
        question_text='What’s the main idea?',
        option_1='Option A',
        option_2='Option B',
        is_option_1_correct=True
    )

    post = PostReadingQuestion.objects.create(
        story=story,
        question_text='What happened at the end?',
        option_1='They fought a dragon.',
        option_2='They lived happily ever after.',
        option_3='They moved to Mars.',
        option_4='They went to bed.',
        correct_option=2,  # Option 2 is correct
        explanation='Classic fairy tale ending.'
    )

    # 4. Access the teacher read view
    url = reverse('story_read_teacher', args=[story.id])
    response = client.get(url)

    # 5. Confirm everything is there
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Story with Content' in content
    assert 'What’s the main idea?' in content
    assert 'What happened at the end?' in content

@pytest.mark.django_db
def test_student_redirected_to_summary_if_all_pre_reading_done(client, teacher_user, student_user):
    # 1. Create a story
    story = Story.objects.create(
        title='Finished Story',
        description='Already done by student',
        content='Some content',
        author=teacher_user,
        status='published'
    )

    # 2. Create 2 pre-reading exercises
    ex1 = PreReadingExercise.objects.create(
        story=story,
        question_text='What’s the main idea?',
        option_1='Option A',
        option_2='Option B',
        is_option_1_correct=True
    )
    ex2 = PreReadingExercise.objects.create(
        story=story,
        question_text='What’s the conclusion?',
        option_1='Option C',
        option_2='Option D',
        is_option_2_correct=True
    )

    # 3. Log in as student
    client.login(username=student_user.username, password='pass')

    # 4. Simulate session where both exercises are already answered
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [ex1.id, ex2.id]
    session.save()

    # 5. Access the pre-reading view
    url = reverse('pre_reading_read', args=[story.id])
    response = client.get(url)

    # 6. Check redirection to summary
    assert response.status_code == 302
    assert reverse('pre_reading_summary', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_sees_next_pre_reading_question_if_not_all_done(client, teacher_user, student_user):
    # 1. Create a story
    story = Story.objects.create(
        title='Halfway There',
        description='One question done',
        content='...',
        author=teacher_user,
        status='published'
    )

    # 2. Create 2 exercises
    ex1 = PreReadingExercise.objects.create(
        story=story,
        question_text='Q1?',
        option_1='Yes',
        option_2='No',
        is_option_1_correct=True
    )
    ex2 = PreReadingExercise.objects.create(
        story=story,
        question_text='Q2?',
        option_1='Maybe',
        option_2='Never',
        is_option_2_correct=True
    )

    # 3. Login as student
    client.login(username=student_user.username, password='pass')

    # 4. Simulate session with only first question done
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [ex1.id]
    session.save()

    # 5. Hit the pre-reading route
    url = reverse('pre_reading_read', args=[story.id])
    response = client.get(url)

    # 6. Should NOT redirect to summary
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Q2?' in content

@pytest.mark.django_db
def test_student_redirected_to_summary_if_all_pre_reading_done(client, teacher_user, student_user):
    # 1. Create a story
    story = Story.objects.create(
        title='Complete Story',
        description='All exercises done',
        content='Full story content',
        author=teacher_user,
        status='published'
    )

    # 2. Create two pre-reading questions
    ex1 = PreReadingExercise.objects.create(
        story=story,
        question_text='First Q?',
        option_1='One',
        option_2='Two',
        is_option_1_correct=True
    )
    ex2 = PreReadingExercise.objects.create(
        story=story,
        question_text='Second Q?',
        option_1='Three',
        option_2='Four',
        is_option_2_correct=True
    )

    # 3. Log in as student
    client.login(username=student_user.username, password='pass')

    # 4. Simulate session where both are answered
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [ex1.id, ex2.id]
    session.save()

    # 5. Access the pre-reading view
    url = reverse('pre_reading_read', args=[story.id])
    response = client.get(url)

    # 6. Should redirect to summary page
    assert response.status_code == 302
    assert reverse('pre_reading_summary', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_redirected_to_pre_reading_if_no_progress(client, teacher_user, student_user):
    story = Story.objects.create(
        title='Fresh Start',
        description='No progress yet',
        content='Story content.',
        author=teacher_user,
        status='published'
    )

    client.login(username=student_user.username, password='pass')

    url = reverse('story_entry_point', args=[story.id])
    response = client.get(url)

    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_redirected_to_summary_after_finishing_pre_reading(client, teacher_user, student_user):
    story = Story.objects.create(
        title='Summary Redirect Test',
        description='Test redirection to pre-reading summary',
        content='Some content',
        author=teacher_user,
        status='published'
    )

    # Create two pre-reading exercises
    exercise1 = PreReadingExercise.objects.create(
        story=story,
        question_text='What is 1+1?',
        option_1='2',
        option_2='3',
        is_option_1_correct=True
    )
    exercise2 = PreReadingExercise.objects.create(
        story=story,
        question_text='What is 2+2?',
        option_1='3',
        option_2='4',
        is_option_2_correct=True
    )

    # Log in as student
    client.login(username=student_user.username, password='pass')

    # Simulate session with all pre-reading questions answered
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [exercise1.id, exercise2.id]
    session.save()

    # Access pre-reading read view
    url = reverse('pre_reading_read', args=[story.id])
    response = client.get(url)

    # Should redirect to summary
    assert response.status_code == 302
    assert reverse('pre_reading_summary', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_cannot_access_summary_without_completing_all_questions(client, teacher_user, student_user):
    # 1. Create story
    story = Story.objects.create(
        title='Half Done',
        description='Incomplete attempt',
        content='Finish what you start!',
        author=teacher_user,
        status='published'
    )

    # 2. Create two pre-reading exercises
    exercise1 = PreReadingExercise.objects.create(
        story=story,
        question_text='Easy Q1',
        option_1='Yes',
        option_2='No',
        is_option_1_correct=True
    )
    exercise2 = PreReadingExercise.objects.create(
        story=story,
        question_text='Easy Q2',
        option_1='Maybe',
        option_2='Never',
        is_option_2_correct=True
    )

    # 3. Log in as student
    client.login(username=student_user.username, password='pass')

    # 4. Simulate student only answered ONE question
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [exercise1.id]  # not all answered!
    session.save()

    # 5. Try to access the summary
    url = reverse('pre_reading_summary', args=[story.id])
    response = client.get(url)

    # 6. Should redirect to continue answering
    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_cannot_see_draft_story_on_homepage(client, student_user, teacher_user):
    client.force_login(student_user)

    # Create one published and one draft story manually
    Story.objects.create(
        title="Published Story",
        description="Visible to students",
        content="Content here",
        author=teacher_user,
        status="published"
    )
    Story.objects.create(
        title="Draft Story",
        description="Hidden from students",
        content="Secret content",
        author=teacher_user,
        status="draft"
    )

    response = client.get(reverse("home"))
    content = response.content.decode()

    assert "Published Story" in content
    assert "Draft Story" not in content

@pytest.mark.django_db
def test_student_sees_published_story_title_and_description_on_homepage(client, teacher_user, student_user):
    # Log in as student
    client.force_login(student_user)

    # Create a published story
    Story.objects.create(
        title='Visible Story',
        description='Should appear on homepage',
        content='Some cool stuff here.',
        author=teacher_user,
        status='published'
    )

    # Go to home page
    response = client.get(reverse('home'))
    content = response.content.decode()

    # Check that title and description appear
    assert 'Visible Story' in content
    assert 'Should appear on homepage' in content

@pytest.mark.django_db
def test_student_cannot_access_teacher_view_directly(client, teacher_user, student_user):
    # Create a published story
    story = Story.objects.create(
        title='Forbidden Access',
        description='This is for teachers only',
        content='Don’t look here, student!',
        author=teacher_user,
        status='published'
    )

    # Log in as student
    client.login(username=student_user.username, password='pass')

    # Try to access the teacher view URL
    url = reverse('story_read_teacher', args=[story.id])
    response = client.get(url)

    # Expect forbidden or redirect (depends on your view logic)
    assert response.status_code in [302, 403]

# 1. Anonymous user cannot access student view
@pytest.mark.django_db
def test_anonymous_cannot_access_student_view(client, teacher_user):
    story = Story.objects.create(
        title='Private View',
        description='Student-only',
        content='Read with login',
        author=teacher_user,
        status='published'
    )
    url = reverse('story_read_student', args=[story.id])
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url


# 2. Student cannot access another student’s profile
@pytest.mark.django_db
def test_student_cannot_access_others_profile(client, student_user):
    other_student = User.objects.create_user(username='student2', password='pass', role='student')
    client.login(username=student_user.username, password='pass')
    url = reverse('profile_detail', args=[other_student.id])
    response = client.get(url)
    assert response.status_code in [403, 302]  # depends on your implementation


# 3. Teacher can access another student’s profile
@pytest.mark.django_db
def test_teacher_can_access_student_profile(client, teacher_user):
    student = User.objects.create_user(username='student3', password='pass', role='student')
    client.login(username=teacher_user.username, password='pass')
    url = reverse('profile_detail', args=[student.id])
    response = client.get(url)
    assert response.status_code == 200
    assert student.username in response.content.decode()


# 4. Student sees only published stories
@pytest.mark.django_db
def test_student_sees_only_published_stories_on_home(client, student_user, teacher_user):
    Story.objects.create(title="Pub", description="Visible", content="...", author=teacher_user, status="published")
    Story.objects.create(title="Draft", description="Hidden", content="...", author=teacher_user, status="draft")
    client.login(username=student_user.username, password='pass')
    response = client.get(reverse("home"))
    content = response.content.decode()
    assert "Pub" in content
    assert "Draft" not in content


# 5. Teacher sees both draft and published stories on home
@pytest.mark.django_db
def test_teacher_sees_all_stories_on_home(client, teacher_user):
    Story.objects.create(title="Pub", description="Visible", content="...", author=teacher_user, status="published")
    Story.objects.create(title="Draft", description="Hidden", content="...", author=teacher_user, status="draft")
    client.login(username=teacher_user.username, password='pass')
    response = client.get(reverse("home"))
    content = response.content.decode()
    assert "Pub" in content
    assert "Draft" in content


# 6. Teacher cannot access student-only read view
@pytest.mark.django_db
def test_teacher_cannot_access_student_read_view(client, teacher_user):
    story = Story.objects.create(title='Student View', description='Not for teachers', content='...', author=teacher_user, status='published')
    client.login(username=teacher_user.username, password='pass')
    url = reverse('story_read_student', args=[story.id])
    response = client.get(url)
    assert response.status_code in [403, 302]


# 7. Unauthenticated user cannot access profile page
@pytest.mark.django_db
def test_anonymous_cannot_access_profile_page(client):
    response = client.get(reverse('profile'))
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url


# 8. Student cannot access teacher-only 'manage_questions'
@pytest.mark.django_db
def test_student_cannot_access_manage_questions(client, teacher_user, student_user):
    story = Story.objects.create(title="Story", description="...", content="...", author=teacher_user, status="published")
    client.login(username=student_user.username, password='pass')
    url = reverse('manage_questions', args=[story.id])
    response = client.get(url)
    assert response.status_code in [403, 302]


# 9. Anonymous user cannot access 'my_stories'
@pytest.mark.django_db
def test_anonymous_cannot_access_my_stories(client):
    url = reverse("my_stories")
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url