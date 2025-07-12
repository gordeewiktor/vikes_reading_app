from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from vikes_reading_app.views.home import home
from vikes_reading_app.views.auth import logout_confirm, register_view
from vikes_reading_app.views.story_management import my_stories, story_create, story_edit, story_delete
from vikes_reading_app.views.profile import profile, profile_detail
from vikes_reading_app.views.story_read import story_read_teacher, story_read_student, story_entry_point
from vikes_reading_app.views.questions import manage_questions
from vikes_reading_app.views.post_reading import post_reading_create, post_reading_edit, post_reading_delete, post_reading_read, post_reading_submit, post_reading_summary
from vikes_reading_app.views.pre_reading import pre_reading_create, pre_reading_edit, pre_reading_delete, pre_reading_read, pre_reading_submit, pre_reading_summary
from vikes_reading_app.views.navigation import story_lookup, start_lookup, return_to_question
from vikes_reading_app.views.progress import reset_progress, save_post_reading_time, save_pre_reading_time, save_reading_time
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('login/', LoginView.as_view(template_name='vikes_reading_app/auth/login.html', next_page='/profile/'), name='login'),
    path('logout/perform/', LogoutView.as_view(next_page='home'), name='logout'),
    path('logout/', logout_confirm, name='logout_confirm'),
    path('register/', register_view, name='register'),
    path('my-stories/', my_stories, name='my_stories'),
    path('create-story/', story_create, name='story_create'),
    path('read-story/<int:story_id>/', story_read_teacher, name='story_read_teacher'),
    path('profile/', profile, name='profile'),
    path('profile-detail/<int:student_id>/', profile_detail, name='profile_detail'),
    path('edit-story/<int:story_id>/', story_edit, name='story_edit'),
    path('delete-story/<int:story_id>/', story_delete, name='story_delete'),
    path('post-reading/<int:story_id>/create/', post_reading_create, name='post_reading_create'),
    path('post-reading/<int:story_id>/edit/<int:question_id>/', post_reading_edit, name='post_reading_edit'),
    path('post-reading/<int:story_id>/delete/<int:question_id>/', post_reading_delete, name='post_reading_delete'),
    path('manage-questions/<int:story_id>/', manage_questions, name='manage_questions'),
    path('pre-reading/<int:story_id>/create/', pre_reading_create, name='pre_reading_create'),
    path('pre-reading/<int:exercise_id>/edit/', pre_reading_edit, name='pre_reading_edit'),
    path('pre-reading/<int:exercise_id>/delete/', pre_reading_delete, name='pre_reading_delete'),
    path('pre-reading/<int:story_id>/summary/', pre_reading_summary, name='pre_reading_summary'),
    path('pre-reading/<int:story_id>/read/', pre_reading_read, name='pre_reading_read'),
    path('pre-reading/<int:story_id>/submit/', pre_reading_submit, name='pre_reading_submit'),
    path('reading/<int:story_id>/', story_read_student, name='story_read_student'),
    path('story-lookup/<int:story_id>/', story_lookup, name='story_lookup'),
    path("post-reading/<int:story_id>/<int:question_id>/submit/", post_reading_submit, name="post_reading_submit"),
    path("post-reading/<int:story_id>/summary/", post_reading_summary, name='post_reading_summary'),
    path("save-reading-time/<int:story_id>/", save_reading_time, name="save_reading_time"),
    path('reset-progress/<int:story_id>/', reset_progress, name='reset_progress'),
    path("save-pre-reading-time/<int:story_id>/", save_pre_reading_time, name="save_pre_reading_time"),
    path("save-post-reading-time/<int:story_id>/", save_post_reading_time, name="save_post_reading_time"),
    path('post-reading/<int:story_id>/read/<int:question_index>/', post_reading_read, name='post_reading_read'),
    path('story/<int:story_id>/', story_entry_point, name='story_entry_point'),
    path("start-lookup/<int:story_id>/<int:question_id>/", start_lookup, name="start_lookup"),
    path("return-to-question/<int:story_id>/<int:question_index>/", return_to_question, name="return_to_question"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)