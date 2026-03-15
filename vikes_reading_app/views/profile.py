# --- Profile Views (Student + Teacher) ---

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect, render

from vikes_reading_app.helpers import is_teacher
from vikes_reading_app.repositories.progress_repository_impl import ORMProgressRepository
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository
from vikes_reading_app.repositories.user_repository_impl import ORMUserRepository


 # --- Helper Function for Teacher View ---
def get_students_with_stories():
    """
    Returns a list of dictionaries containing each student and the titles of stories they've read.
    This is used by teachers to view student progress.
    """
    user_repo = ORMUserRepository()
    progress_repo = ORMProgressRepository()
    students = user_repo.list_students()
    # Prepare a list to collect each student's data
    student_data = []

    for student in students:
        # Get titles of all distinct stories read by this student
        story_titles = progress_repo.list_story_titles_for_student(student)
        student_data.append({
            "student": student,
            "story_titles": story_titles,
        })

    # Return the collected student progress data
    return student_data


 # --- Profile View (Handles Both Roles) ---
@login_required
def profile(request):
    """
    Displays the profile page for the logged-in user.
    - If POST: Update the user's bio.
    - If teacher: Show a list of students and their progress.
    - If student: Show only their own profile.
    """
    # --- Handle Profile Update (POST Request) ---
    if request.method == 'POST':
        user_repo = ORMUserRepository()
        bio = request.POST.get('bio', '')
        user_repo.update_bio(request.user, bio)
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    # --- Teacher View: Show all students and their progress ---
    if request.user.role == 'teacher':
        students_with_stories = get_students_with_stories()
        return render(request, 'vikes_reading_app/profile.html', {
            'user': request.user,
            'students_with_stories': students_with_stories
        })

    # --- Student View: Show only own profile ---
    return render(request, 'vikes_reading_app/profile.html', {'user': request.user})


 # --- Detailed Profile View for Teacher ---
@user_passes_test(is_teacher)
@login_required
def profile_detail(request, student_id):
    """
    View for teachers to inspect detailed progress of a specific student.
    Shows all story progress only for stories authored by the current teacher.
    """
    # Fetch the targeted student object; ensure they are indeed a student
    user_repo = ORMUserRepository()
    story_repo = ORMStoryRepository()
    progress_repo = ORMProgressRepository()
    student = user_repo.get_student(student_id)
    teacher_stories = story_repo.list_author_stories(request.user)
    progress_records = progress_repo.list_progress_records(student, teacher_stories)

    # Prepare context for rendering detailed progress page
    context = {
        'student': student,
        'progress_records': progress_records,
    }
    return render(request, 'vikes_reading_app/profile_detail.html', context)
