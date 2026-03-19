# --- Imports and User Model Setup ---

import copy
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from vikes_reading_app.models import Story, PreReadingExercise, PostReadingQuestion, Progress

User = get_user_model()

# ========================
# 📝 Story CRUD & Validation
# ========================

# ✅ Story creation permissions
@pytest.mark.django_db
@pytest.mark.parametrize("client_fixture, expected_status, should_create", [
    ("logged_in_client_teacher", 302, True),           # Teachers can create
    ("logged_in_client_student", [403, 302], False),   # Students cannot
    ("client", 302, False),                            # Anonymous users are redirected
])
def test_story_create_permissions(request, base_story_data, client_fixture, expected_status, should_create):
    client = request.getfixturevalue(client_fixture)
    url = reverse('story_create')
    response = client.post(url, base_story_data)

    story_exists = Story.objects.filter(title=base_story_data['title']).exists()
    assert response.status_code in expected_status if isinstance(expected_status, list) else [expected_status]
    assert story_exists is should_create


# ✏️ Story edit permissions and effects
@pytest.mark.django_db
@pytest.mark.parametrize('client_fixture, expected_status, should_update', [
    ('logged_in_client_teacher', 200, True),               # Author teacher can update
    ('logged_in_client_intruder', [403, 302], False),      # Other users can't
])
def test_story_edit_permissions(request, published_story, base_story_data, client_fixture, expected_status, should_update):
    client = request.getfixturevalue(client_fixture)
    story = published_story

    url = reverse('story_edit', args=[story.id])
    response = client.post(url, base_story_data)

    assert response.status_code in expected_status if isinstance(expected_status, list) else [expected_status]

    story.refresh_from_db()
    if should_update:
        assert story.title == base_story_data['title']
        assert story.description == base_story_data['description']
        assert story.content == base_story_data['content']
    else:
        assert story.title == "Published Story"
        assert story.description == "Visible to students"
        assert story.content == "Once upon a published time..."


# ❌ Story delete permissions
@pytest.mark.django_db
@pytest.mark.parametrize("client_fixture, expected_status, should_exist", [
    ('logged_in_client_teacher', [200, 302], False),       # Author teacher can delete
    ('logged_in_client_intruder', [403, 302], True),       # Other teachers can't
    ('logged_in_client_student', [403, 302], True),        # Students can't
])
def test_story_delete_permissions(request, published_story, client_fixture, expected_status, should_exist):
    client = request.getfixturevalue(client_fixture)
    url = reverse('story_delete', args=[published_story.id])
    response = client.post(url)

    assert response.status_code in expected_status
    assert Story.objects.filter(id=published_story.id).exists() == should_exist


# 🧪 Story creation field validation
@pytest.mark.django_db
@pytest.mark.parametrize("missing_fields, expected_status, should_exist", [
    (['title'], 200, False),                 # Title is required
    (['description'], 200, False),           # Description is required
    (['content'], 302, True),                # Content is optional
    (['title', 'description'], 200, False),  # Both required fields missing
])
def test_teacher_story_creation_variants(logged_in_client_teacher, base_story_data, missing_fields, expected_status, should_exist):
    client = logged_in_client_teacher

    # Copy and blank out specified fields
    invalid_data = copy.deepcopy(base_story_data)
    for field in missing_fields:
        invalid_data[field] = ''

    url = reverse('story_create')
    response = client.post(url, invalid_data)

    assert response.status_code == expected_status

    exists = Story.objects.filter(description=base_story_data['description']).exists()
    assert exists is should_exist

# ========================
# 📚 Permission & Access Tests
# ========================

# 🔒 Unauthorized users (students or anonymous) trying to access teacher-only views
@pytest.mark.django_db
@pytest.mark.parametrize("user_type, client_fixture", [
    ("anonymous", "client"),
    ("student", "logged_in_client_student"),
])
@pytest.mark.parametrize("url_name, use_story_id", [
    ("story_create", False),
    ("story_edit", True),
    ("story_delete", True),
    ("story_read_teacher", True),
    ("manage_questions", True),
    ("my_stories", False),
])
def test_unauthorized_users_cannot_access_teacher_views_combo(
    request, user_type, client_fixture, url_name, use_story_id, published_story
):
    client = request.getfixturevalue(client_fixture)
    story_id = published_story.id if use_story_id else None
    url = reverse(url_name, args=[story_id] if story_id else None)

    response = client.get(url)
    assert response.status_code in [302, 403]

# 🔒 Student cannot view their own or other teachers' "My Stories" page
@pytest.mark.django_db
def test_student_cannot_access_my_stories(logged_in_client_student):
    url = reverse('my_stories')
    response = logged_in_client_student.get(url)
    assert response.status_code in [302, 403]

# ✅ Teacher sees only their own stories on the "My Stories" page
@pytest.mark.django_db
def test_teacher_can_view_only_their_own_stories(client):
    teacher1 = User.objects.create_user(username='t1', password='pass123', role='teacher')
    teacher2 = User.objects.create_user(username='t2', password='pass123', role='teacher')

    Story.objects.create(title='T1 Story', description='desc', content='...', author=teacher1, status='published')
    Story.objects.create(title='T2 Story', description='desc', content='...', author=teacher2, status='published')

    client.login(username='t1', password='pass123')
    url = reverse('my_stories')
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode()
    assert 'T1 Story' in content
    assert 'T2 Story' not in content

# ✅ Access to the teacher's story read view
@pytest.mark.parametrize("client_fixture, expected_status, should_see_content", [
    ("logged_in_client_teacher", 200, True),
    ("logged_in_client_intruder", [302, 403], False),
    ("logged_in_client_student", [302, 403], False),
])
def test_story_read_teacher_permissions(request, client_fixture, expected_status, should_see_content, published_story):
    client = request.getfixturevalue(client_fixture)
    url = reverse("story_read_teacher", args=[published_story.id])
    response = client.get(url)

    assert response.status_code in expected_status if isinstance(expected_status, list) else [expected_status]

    if should_see_content:
        assert b"Once upon a published time..." in response.content
    else:
        assert b"Once upon a published time..." not in response.content

# ✅ Teacher sees both pre-reading and post-reading items in their read view
@pytest.mark.django_db
def test_teacher_can_see_pre_and_post_reading_items_in_teacher_read_view(logged_in_client_teacher, published_story, post_reading_question):
    client = logged_in_client_teacher
    PreReadingExercise.objects.create(
        story=published_story,
        question_text='What’s the main idea?',
        option_1='Option A',
        option_2='Option B',
        is_option_1_correct=True
    )
    url = reverse('story_read_teacher', args=[published_story.id])
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode()
    assert 'Once upon a published time...' in content
    assert 'What’s the main idea?' in content
    assert 'What happened at the end?' in content

# 🔒 Anonymous users are redirected when accessing the student view
@pytest.mark.django_db
def test_anonymous_cannot_access_student_view(client, published_story):
    url = reverse('story_read_student', args=[published_story.id])
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url or 'accounts/login' in response.url

# ✅ Only students should access the student read view
@pytest.mark.django_db
@pytest.mark.parametrize("client_fixture, expected_status", [
    ("logged_in_client_student", 200),
    ("logged_in_client_teacher", [403, 302]),
])
def test_story_read_student_access(request, published_story, client_fixture, expected_status):
    client = request.getfixturevalue(client_fixture)
    url = reverse('story_read_student', args=[published_story.id])
    response = client.get(url)
    expected = expected_status if isinstance(expected_status, list) else [expected_status]
    assert response.status_code in expected
    if response.status_code == 200:
        assert b'Once upon a published time...' in response.content


@pytest.mark.django_db
def test_student_cannot_access_draft_story_via_student_routes(logged_in_client_student, draft_story):
    response = logged_in_client_student.get(reverse('story_read_student', args=[draft_story.id]))

    assert response.status_code == 403

# ✅ Teacher sees students and their read stories on profile page
@pytest.mark.django_db
def test_teacher_profile_shows_students_with_stories(logged_in_client_teacher, published_story):
    student = User.objects.create_user(username='student1', password='pass123', role='student')
    
    Progress.objects.create(
        student=student,
        read_story=published_story,
        score=0.0,
        current_stage="reading"
    )
    
    url = reverse('profile')
    response = logged_in_client_teacher.get(url)
    
    assert response.status_code == 200
    content = response.content.decode()
    assert 'student1' in content
    assert 'Published Story' in content

# ========================
# 🧠 Student Pre-Reading Flow
# ========================

# 🚪 Student should be redirected to pre-reading if no stored progress yet
@pytest.mark.django_db
def test_student_redirected_to_pre_reading_if_no_progress(published_story, logged_in_client_student):
    url = reverse('story_entry_point', args=[published_story.id])
    response = logged_in_client_student.get(url)
    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[published_story.id]) in response.url

# ✅ Student is redirected to summary if all pre-reading questions are done
@pytest.mark.django_db
def test_student_redirected_to_summary_after_finishing_all_pre_reading(
    published_story, logged_in_client_student, student_user, two_pre_reading_exercises
):
    ex1, ex2 = two_pre_reading_exercises
    Progress.objects.create(
        student=student_user,
        read_story=published_story,
        score=0.0,
        current_stage='pre_reading',
        answers_given={
            'pre_reading': {
                str(ex1.id): ex1.option_1,
                str(ex2.id): ex2.option_2,
            },
            'post_reading': {},
        },
    )
    response = logged_in_client_student.get(reverse('pre_reading_read', args=[published_story.id]))
    assert response.status_code == 302
    assert reverse('pre_reading_summary', args=[published_story.id]) in response.url

# ⏭️ Student sees next unanswered question
@pytest.mark.django_db
def test_student_sees_next_pre_reading_question_if_not_all_done(
    published_story, logged_in_client_student, student_user, two_pre_reading_exercises
):
    ex1, ex2 = two_pre_reading_exercises
    Progress.objects.create(
        student=student_user,
        read_story=published_story,
        score=0.0,
        current_stage='pre_reading',
        answers_given={
            'pre_reading': {
                str(ex1.id): ex1.option_1,
            },
            'post_reading': {},
        },
    )
    url = reverse('pre_reading_read', args=[published_story.id])
    response = logged_in_client_student.get(url)
    assert response.status_code == 200
    assert 'Q2?' in response.content.decode()

# ❌ Student should not see summary until all questions are answered
@pytest.mark.django_db
def test_student_cannot_access_summary_without_completing_all_questions(
    published_story, logged_in_client_student, student_user, two_pre_reading_exercises
):
    ex1, ex2 = two_pre_reading_exercises
    Progress.objects.create(
        student=student_user,
        read_story=published_story,
        score=0.0,
        current_stage='pre_reading',
        answers_given={
            'pre_reading': {
                str(ex1.id): ex1.option_1,
            },
            'post_reading': {},
        },
    )
    url = reverse('pre_reading_summary', args=[published_story.id])
    response = logged_in_client_student.get(url)
    assert response.status_code == 302
    assert reverse('pre_reading_read', args=[published_story.id]) in response.url

# ========================
# 🏠 Homepage Visibility
# ========================

# 👀 Student should see only published stories
@pytest.mark.django_db
@pytest.mark.parametrize('expected_text, should_see', [
    ("Published Story", True),
    ("Draft Story", False),
])
def test_student_homepage_visibility(logged_in_client_student, published_story, draft_story, expected_text, should_see):
    response = logged_in_client_student.get(reverse('home'))
    content = response.content.decode()
    if should_see:
        assert expected_text in content
    else:
        assert expected_text not in content

# ========================
# 👤 Profile Access Control
# ========================

# 🔍 Only teachers can access student profiles (or their own?)
@pytest.mark.django_db
@pytest.mark.parametrize('client_fixture, expected_status, should_see_name', [
    ('client', 302, False),
    ('logged_in_client_student', [302, 403], False),
    ('logged_in_client_teacher', 200, True),
])
def test_profile_detail_view_permissions(request, client_fixture, expected_status, should_see_name):
    target_user = User.objects.create_user(username='student_target', password='pass', role='student')
    client = request.getfixturevalue(client_fixture)
    url = reverse('profile_detail', args=[target_user.id])
    response = client.get(url)
    assert response.status_code in expected_status if isinstance(expected_status, list) else [expected_status]
    content = response.content.decode()
    if should_see_name:
        assert target_user.username in content
    else:
        assert target_user.username not in content


# ========================
# 🔍 Story Lookup Rendering
# ========================

@pytest.mark.django_db
def test_story_lookup_renders_story_html_as_markup(logged_in_client_student, teacher_user):
    story = Story.objects.create(
        title='HTML Story',
        description='Rich text story',
        content='<h2>Section Title</h2><p>Hello world</p>',
        author=teacher_user,
        status='published',
    )
    question = PostReadingQuestion.objects.create(
        story=story,
        question_text='What did you see?',
        option_1='A heading',
        option_2='Nothing',
        option_3='A table',
        option_4='A chart',
        correct_option=1,
        explanation='The story includes a heading.',
    )

    response = logged_in_client_student.get(
        reverse('story_lookup', args=[story.id]),
        {'question_id': question.id},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert '<h2>Section Title</h2>' in content
    assert '<p>Hello world</p>' in content
    assert '&lt;h2&gt;Section Title&lt;/h2&gt;' not in content


# ========================
# 📘 Post-Reading Summary
# ========================

@pytest.mark.django_db
def test_post_reading_summary_shows_student_answer_with_correct_emoji(
    logged_in_client_student, student_user, published_story, post_reading_question
):
    Progress.objects.create(
        student=student_user,
        read_story=published_story,
        score=0.0,
        current_stage='post_reading',
        answers_given={
            'pre_reading': {},
            'post_reading': {
                str(post_reading_question.id): {
                    'selected_option': '2',
                    'is_correct': True,
                },
            },
        },
    )

    response = logged_in_client_student.get(reverse('post_reading_summary', args=[published_story.id]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'Your Answer:' in content
    assert 'They lived happily ever after.' in content
    assert '✅' in content


@pytest.mark.django_db
def test_post_reading_summary_shows_incorrect_answer_with_wrong_emoji(
    logged_in_client_student, student_user, published_story, post_reading_question
):
    Progress.objects.create(
        student=student_user,
        read_story=published_story,
        score=0.0,
        current_stage='post_reading',
        answers_given={
            'pre_reading': {},
            'post_reading': {
                str(post_reading_question.id): {
                    'selected_option': '1',
                    'is_correct': False,
                },
            },
        },
    )

    response = logged_in_client_student.get(reverse('post_reading_summary', args=[published_story.id]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'Your Answer:' in content
    assert 'They fought a dragon.' in content
    assert '❌' in content


@pytest.mark.django_db
def test_post_reading_summary_shows_no_answer_when_missing(
    logged_in_client_student, student_user, published_story, post_reading_question
):
    Progress.objects.create(
        student=student_user,
        read_story=published_story,
        score=0.0,
        current_stage='post_reading',
        answers_given={
            'pre_reading': {},
            'post_reading': {},
        },
    )

    response = logged_in_client_student.get(reverse('post_reading_summary', args=[published_story.id]))

    assert response.status_code == 200
    content = response.content.decode()
    assert '(No answer)' in content
    assert '❌' in content
