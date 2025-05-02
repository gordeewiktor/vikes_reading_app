from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', LoginView.as_view(template_name='vikes_reading_app/auth/login.html', next_page='/profile/'), name='login'),
    path('logout/perform/', LogoutView.as_view(next_page='home'), name='logout'),
    path('logout/', views.logout_confirm, name='logout_confirm'),
    path('register/', views.register_view, name='register'),
    path('my-stories/', views.my_stories, name='my_stories'),
    path('create-story/', views.story_create, name='story_create'),
    path('read-story/<int:story_id>/', views.story_read_teacher, name='story_read_teacher'),
    path('profile/', views.profile, name='profile'),
    path('edit-story/<int:story_id>/', views.story_edit, name='story_edit'),
    path('delete-story/<int:story_id>/', views.story_delete, name='story_delete'),
    path('post-reading/<int:story_id>/create/', views.post_reading_create, name='post_reading_create'),
    path('post-reading/<int:story_id>/edit/<int:question_id>/', views.post_reading_edit, name='post_reading_edit'),
    path('post-reading/<int:story_id>/delete/<int:question_id>/', views.post_reading_delete, name='post_reading_delete'),
    path('manage-questions/<int:story_id>/', views.manage_questions, name='manage_questions'),
    path('pre-reading/<int:story_id>/create/', views.pre_reading_create, name='pre_reading_create'),
    path('pre-reading/<int:exercise_id>/edit/', views.pre_reading_edit, name='pre_reading_edit'),
    path('pre-reading/<int:exercise_id>/delete/', views.pre_reading_delete, name='pre_reading_delete'),
    path('pre-reading/<int:story_id>/summary/', views.pre_reading_summary, name='pre_reading_summary'),
    path('pre-reading/<int:story_id>/read/', views.pre_reading_read, name='pre_reading_read'),
    path('pre-reading/<int:story_id>/submit/', views.pre_reading_submit, name='pre_reading_submit'),
    path('reading/<int:story_id>/', views.story_read_student, name='story_read_student'),
    path('story-lookup/<int:story_id>/', views.story_lookup, name='story_lookup'),
    path("post-reading/<int:story_id>/<int:question_id>/submit/", views.post_reading_submit, name="post_reading_submit"),
    path("post-reading/<int:story_id>/summary/", views.post_reading_summary, name='post_reading_summary'),
    path("save-reading-time/<int:story_id>/", views.save_reading_time, name="save_reading_time"),
    path('reset-progress/<int:story_id>/', views.reset_progress, name='reset_progress'),
    path("save-pre-reading-time/<int:story_id>/", views.save_pre_reading_time, name="save_pre_reading_time"),
    path("save-post-reading-time/<int:story_id>/", views.save_post_reading_time, name="save_post_reading_time"),
    path('post-reading/<int:story_id>/read/<int:question_index>/', views.post_reading_read, name='post_reading_read'),
    path('story/<int:story_id>/', views.story_entry_point, name='story_entry_point'),
    path("start-lookup/<int:story_id>/<int:question_id>/", views.start_lookup, name="start_lookup"),
    path("return-to-question/<int:story_id>/<int:question_index>/", views.return_to_question, name="return_to_question"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)