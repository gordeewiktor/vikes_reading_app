import pytest, copy
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
    client.login(username=teacher_user.username, password='pass')
    return client

@pytest.fixture
def logged_in_client_student(client, student_user):
    client.login(username=student_user.username, password='pass')
    return client

@pytest.fixture
def base_story_data():
    return {
        'title': 'Valid Title',
        'description': 'A story that makes sense.',
        'content': 'This is actual content.',
    }

@pytest.fixture
def logged_in_client_intruder(client):
    intruder = User.objects.create_user(username='intruder', password='pass123', role='teacher')
    client.login(username=intruder.username, password='pass123')
    return client

@pytest.fixture
def published_story(teacher_user):
    return Story.objects.create(
        title="Published Story",
        description="Visible to students",
        content="Once upon a published time...",
        author=teacher_user,
        status="published"
    )

@pytest.fixture
def draft_story(teacher_user):
    return Story.objects.create(
        title="Draft Story",
        description="Hidden from students",
        content="Once upon a draft time...",
        author=teacher_user,
        status="draft"
    )

@pytest.mark.django_db
def test_teacher_can_create_story(logged_in_client_teacher, teacher_user, base_story_data):
    client = logged_in_client_teacher

    url = reverse('story_create')
    response = client.post(url, base_story_data)

    assert response.status_code == 302
    stories = Story.objects.filter(title=base_story_data['title']).first()
    assert stories is not None
    assert stories.author == teacher_user

@pytest.mark.django_db
def test_student_cannot_create_story(logged_in_client_student, base_story_data):
    client = logged_in_client_student

    url = reverse('story_create')
    response = client.post(url, base_story_data)

    # Expect forbidden or redirect
    assert response.status_code in [302, 403]
    assert not Story.objects.filter(title=base_story_data['title']).exists()

@pytest.mark.django_db
def test_teacher_can_edit_own_story(logged_in_client_teacher, published_story, base_story_data):
    
    client = logged_in_client_teacher

    # Create a story authored by this teacher
    story = published_story

    # Prepare updated story data
    updated_data = base_story_data

    # Send POST request to the story edit view
    url = reverse('story_edit', args=[story.id])
    response = client.post(url, updated_data)

    # Confirm the response is a redirect (successful update)
    assert response.status_code == 302

    # Refresh the story from the DB and check that fields were updated
    story.refresh_from_db()
    assert story.title == 'Valid Title'
    assert story.description == 'A story that makes sense.'
    assert story.content == 'This is actual content.'

@pytest.mark.django_db
def test_other_teacher_cannot_edit_story(logged_in_client_intruder, published_story, base_story_data):

    story = published_story

    # Try to edit the author's story
    updated_data = base_story_data
    url = reverse('story_edit', args=[story.id])
    response = logged_in_client_intruder.post(url, updated_data)

    # Expect forbidden or redirect
    assert response.status_code in [302, 403]

    # Ensure story content did not change
    story.refresh_from_db()
    assert story.title == 'Published Story'
    assert story.description == 'Visible to students'
    assert story.content == 'Once upon a published time...'

@pytest.mark.django_db
def test_teacher_can_delete_own_story(logged_in_client_teacher, published_story):
    
    client = logged_in_client_teacher

    # Send POST request to delete the story
    url = reverse('story_delete', args=[published_story.id])
    response = client.post(url)

    # Check redirect (or success)
    assert response.status_code in [302, 200]

    # Ensure the story is deleted from DB
    assert not Story.objects.filter(id=published_story.id).exists()

@pytest.mark.django_db
def test_other_teacher_cannot_delete_story(logged_in_client_intruder, published_story):

    client = logged_in_client_intruder

    # Attempt to delete the story
    url = reverse('story_delete', args=[published_story.id])
    response = client.post(url)

    # Expect forbidden or redirect
    assert response.status_code in [302, 403]

    # Ensure story still exists
    assert Story.objects.filter(id=published_story.id).exists()

@pytest.mark.django_db
def test_student_cannot_delete_story(logged_in_client_student, published_story):
    client = logged_in_client_student

    # Attempt to delete the story
    url = reverse('story_delete', args=[published_story.id])
    response = client.post(url)

    # Expect forbidden or redirect
    assert response.status_code in [302, 403]

    # Ensure story still exists
    assert Story.objects.filter(id=published_story.id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("missing_fields, expected_status, should_exist", [
    (['title'], 200, False),                 # title is required
    (['description'], 200, False),           # description is required
    (['content'], 302, True),                # content is optional
    (['title', 'description'], 200, False),  # both required fields missing
])
def test_teacher_story_creation_variants(logged_in_client_teacher, base_story_data, missing_fields, expected_status, should_exist):
    client = logged_in_client_teacher

    # Make a deep copy so we don’t mess up the base fixture
    invalid_data = copy.deepcopy(base_story_data)

    # Blank out the specified fields
    for field in missing_fields:
        invalid_data[field] = ''

    url = reverse('story_create')
    response = client.post(url, invalid_data)

    # Check response status
    assert response.status_code == expected_status

    # Check if the story was saved (based on the unique description)
    exists = Story.objects.filter(description=base_story_data['description']).exists()
    assert exists is should_exist

@pytest.mark.django_db
def test_anonymous_user_cannot_create_story(client, base_story_data):

    url = reverse('story_create')
    response = client.post(url, base_story_data)

    # Expect redirect to login page (usually 302)
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url

    # Ensure story was NOT created
    assert not Story.objects.filter(title=base_story_data['title']).exists()

@pytest.mark.django_db
def test_anonymous_user_cannot_access_story_views(client):

    story_id = 999  # Dummy ID – doesn't matter since we expect redirect before lookup

    protected_urls = [
        reverse('story_read_teacher', args=[story_id]),
        reverse('story_read_student', args=[story_id]),
        reverse('story_entry_point', args=[story_id]),
        reverse('story_edit', args=[story_id]),
        reverse('story_delete', args=[story_id]),
        reverse('story_create'),
        reverse('my_stories'),
        reverse('my_students'),
        reverse('profile'),
    ]

    for url in protected_urls:
        response = client.get(url)
        # Anonymous users should get redirected to login
        assert response.status_code == 302
        assert '/login' in response.url or 'accounts/login' in response.url

@pytest.mark.django_db
def test_student_cannot_access_teacher_views(logged_in_client_student, published_story):
    client = logged_in_client_student

    story = published_story

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
def test_student_can_view_story_read_student(logged_in_client_student, published_story):

    client = logged_in_client_student

    url = reverse('story_read_student', args=[published_story.id])
    response = client.get(url)

    assert response.status_code == 200
    assert b'Once upon a published time...' in response.content

@pytest.mark.django_db
def test_student_redirected_to_pre_reading_if_no_progress(published_story, logged_in_client_student):

    client = logged_in_client_student

    url = reverse('story_entry_point', args=[published_story.id])
    response = client.get(url)

    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[published_story.id]) in response.url

@pytest.mark.django_db
def test_teacher_can_view_only_their_own_stories(client):
    # 1. Create two teachers
    teacher1 = User.objects.create_user(username='t1', password='pass123', role='teacher')
    teacher2 = User.objects.create_user(username='t2', password='pass123', role='teacher')

    # 2. Each teacher creates a story
    story1 = Story.objects.create(title='T1 Story', description='desc', content='...', author=teacher1, status='published')
    story2 = Story.objects.create(title='T2 Story', description='desc', content='...', author=teacher2, status='published')

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
def test_student_cannot_access_my_stories(logged_in_client_student):

    # Attempt to access the teacher-only 'my_stories' page
    url = reverse('my_stories')
    response = logged_in_client_student.get(url)

    # Expect redirect to login or 403 Forbidden
    assert response.status_code in [302, 403]

@pytest.mark.django_db
def test_teacher_can_access_story_read_teacher_view(logged_in_client_teacher, published_story):
    # 2. Log in as that teacher
    client = logged_in_client_teacher

    # 3. Access the teacher view for this story
    url = reverse('story_read_teacher', args=[published_story.id])
    response = client.get(url)

    # 4. Confirm successful access and correct content
    assert response.status_code == 200
    assert b'Once upon a published time...' in response.content

@pytest.mark.django_db
def test_other_teacher_cannot_access_teacher_read_view(logged_in_client_intruder, published_story):
    
    # Log in as intruder
    client = logged_in_client_intruder

    # Try to access the teacher-only read view
    response = client.get(reverse('story_read_teacher', args=[published_story.id]))

    # Should be forbidden or redirected
    assert response.status_code in [302, 403]

@pytest.mark.django_db
def test_student_cannot_access_teacher_read_view(published_story, logged_in_client_student):

    # Student logs in
    client = logged_in_client_student

    # Student tries to access the teacher-only view
    url = reverse('story_read_teacher', args=[published_story.id])
    response = client.get(url)

    # Should be forbidden or redirect
    assert response.status_code in [302, 403]

@pytest.mark.django_db
def test_teacher_can_see_pre_and_post_reading_items_in_teacher_read_view(logged_in_client_teacher, published_story):
    # Create teacher and log in
    
    client = logged_in_client_teacher

    # Create pre- and post-reading items
    pre = PreReadingExercise.objects.create(
        story=published_story,
        question_text='What’s the main idea?',
        option_1='Option A',
        option_2='Option B',
        is_option_1_correct=True
    )

    post = PostReadingQuestion.objects.create(
        story=published_story,
        question_text='What happened at the end?',
        option_1='They fought a dragon.',
        option_2='They lived happily ever after.',
        option_3='They moved to Mars.',
        option_4='They went to bed.',
        correct_option=2,  # Option 2 is correct
        explanation='Classic fairy tale ending.'
    )

    # Access the teacher read view
    url = reverse('story_read_teacher', args=[published_story.id])
    response = client.get(url)

    # Confirm everything is there
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Once upon a published time...' in content
    assert 'What’s the main idea?' in content
    assert 'What happened at the end?' in content

@pytest.mark.django_db
def test_student_redirected_to_summary_after_finishing_all_pre_reading(published_story, logged_in_client_student):
    story = published_story

    ex1 = PreReadingExercise.objects.create(
        story=story, question_text="Q1?", option_1="A", option_2="B", is_option_1_correct=True
    )
    ex2 = PreReadingExercise.objects.create(
        story=story, question_text="Q2?", option_1="C", option_2="D", is_option_2_correct=True
    )

    client = logged_in_client_student
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [ex1.id, ex2.id]
    session.save()

    response = client.get(reverse('pre_reading_read', args=[story.id]))

    assert response.status_code == 302
    assert reverse('pre_reading_summary', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_sees_next_pre_reading_question_if_not_all_done(published_story, logged_in_client_student):
    # Create a story
    story = published_story

    # Create 2 exercises
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

    # Login as student
    client = logged_in_client_student

    # Simulate session with only first question done
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [ex1.id]
    session.save()

    # Hit the pre-reading route
    url = reverse('pre_reading_read', args=[story.id])
    response = client.get(url)

    # Should NOT redirect to summary
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Q2?' in content

@pytest.mark.django_db
def test_student_redirected_to_pre_reading_if_no_progress(published_story, logged_in_client_student):
    story = published_story

    client = logged_in_client_student

    url = reverse('story_entry_point', args=[story.id])
    response = client.get(url)

    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_cannot_access_summary_without_completing_all_questions(published_story, logged_in_client_student):
    # Create story
    story = published_story

    # Create two pre-reading exercises
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

    # Log in as student
    client = logged_in_client_student

    # Simulate student only answered ONE question
    session = client.session
    session[f'pre_reading_progress_{story.id}'] = [exercise1.id]  # not all answered!
    session.save()

    # Try to access the summary
    url = reverse('pre_reading_summary', args=[story.id])
    response = client.get(url)

    # Should redirect to continue answering
    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[story.id]) in response.url

@pytest.mark.django_db
def test_student_cannot_see_draft_story_on_homepage(logged_in_client_student, published_story, draft_story):

    response = logged_in_client_student.get(reverse("home"))
    content = response.content.decode()

    assert "Published Story" in content
    assert "Draft Story" not in content

@pytest.mark.django_db
def test_student_sees_published_story_title_and_description_on_homepage(logged_in_client_student, published_story):

    # Go to home page
    response = logged_in_client_student.get(reverse('home'))
    content = response.content.decode()

    # Check that title and description appear
    assert 'Published Story' in content
    assert 'Visible to students' in content

@pytest.mark.django_db
def test_student_cannot_access_teacher_view_directly(published_story, logged_in_client_student):
   
    # Try to access the teacher view URL
    url = reverse('story_read_teacher', args=[published_story.id])
    response = logged_in_client_student.get(url)

    # Expect forbidden or redirect (depends on your view logic)
    assert response.status_code in [302, 403]

# Anonymous user cannot access student view
@pytest.mark.django_db
def test_anonymous_cannot_access_student_view(client, published_story):

    url = reverse('story_read_student', args=[published_story.id])
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url


# Student cannot access another student’s profile
@pytest.mark.django_db
def test_student_cannot_access_others_profile(logged_in_client_student):
    other_student = User.objects.create_user(username='student2', password='pass', role='student')
    client = logged_in_client_student
    url = reverse('profile_detail', args=[other_student.id])
    response = client.get(url)
    assert response.status_code in [403, 302]  # depends on implementation


# Teacher can access another student’s profile
@pytest.mark.django_db
def test_teacher_can_access_student_profile(logged_in_client_teacher):
    student = User.objects.create_user(username='student3', password='pass', role='student')
    client = logged_in_client_teacher
    url = reverse('profile_detail', args=[student.id])
    response = client.get(url)
    assert response.status_code == 200
    assert student.username in response.content.decode()


# Student sees only published stories
@pytest.mark.django_db
def test_student_sees_only_published_stories_on_home(logged_in_client_student, teacher_user):
    Story.objects.create(title="Pub", description="Visible", content="...", author=teacher_user, status="published")
    Story.objects.create(title="Draft", description="Hidden", content="...", author=teacher_user, status="draft")
    client = logged_in_client_student
    response = client.get(reverse("home"))
    content = response.content.decode()
    assert "Pub" in content
    assert "Draft" not in content


# Teacher sees both draft and published stories on home
@pytest.mark.django_db
def test_teacher_sees_all_stories_on_home(logged_in_client_teacher, teacher_user):
    Story.objects.create(title="Pub", description="Visible", content="...", author=teacher_user, status="published")
    Story.objects.create(title="Draft", description="Hidden", content="...", author=teacher_user, status="draft")
    client = logged_in_client_teacher
    response = client.get(reverse("home"))
    content = response.content.decode()
    assert "Pub" in content
    assert "Draft" in content


# Teacher cannot access student-only read view
@pytest.mark.django_db
def test_teacher_cannot_access_student_read_view(logged_in_client_teacher, teacher_user):
    story = Story.objects.create(title='Student View', description='Not for teachers', content='...', author=teacher_user, status='published')
    client = logged_in_client_teacher
    url = reverse('story_read_student', args=[story.id])
    response = client.get(url)
    assert response.status_code in [403, 302]


# Unauthenticated user cannot access profile page
@pytest.mark.django_db
def test_anonymous_cannot_access_profile_page(client):
    response = client.get(reverse('profile'))
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url


# Student cannot access teacher-only 'manage_questions'
@pytest.mark.django_db
def test_student_cannot_access_manage_questions(published_story, logged_in_client_student):
    url = reverse('manage_questions', args=[published_story.id])
    response = logged_in_client_student.get(url)
    assert response.status_code in [403, 302]


# Anonymous user cannot access 'my_stories'
@pytest.mark.django_db
def test_anonymous_cannot_access_my_stories(client):
    url = reverse("my_stories")
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url