# --- Profile Views (Student + Teacher) ---

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404

from vikes_reading_app.models import Progress, CustomUser
from vikes_reading_app.helpers import is_teacher


def get_students_with_stories():
    """
    Returns a list of dictionaries containing each student and the titles of stories they've read.
    This is used by teachers to view student progress.
    """
    # Fetch all users who are students
    students = CustomUser.objects.filter(role='student')
    # Prepare a list to collect each student's data
    student_data = []

    for student in students:
        # Get titles of all distinct stories read by this student
        story_titles = (
            Progress.objects
            .filter(student=student)
            .select_related('read_story')
            .values_list('read_story__title', flat=True)
            .distinct()
        )
        student_data.append({
            "student": student,
            "story_titles": list(story_titles),
        })

    # Return the collected student progress data
    return student_data


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
        bio = request.POST.get('bio', '')
        user = request.user
        user.bio = bio
        user.save()
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


@user_passes_test(is_teacher)
@login_required
def profile_detail(request, student_id):
    """
    View for teachers to inspect detailed progress of a specific student.
    Shows all story progress only for stories authored by the current teacher.
    """
    # Fetch the targeted student object; ensure they are indeed a student
    student = get_object_or_404(CustomUser, id=student_id, role='student')

    # Fetch all stories authored by the current teacher
    teacher_stories = request.user.story_set.all()
    # Fetch progress only for stories authored by this teacher
    progress_records = Progress.objects.filter(
        student=student,
        read_story__in=teacher_stories
    ).select_related('read_story')

    # Prepare context for rendering detailed progress page
    context = {
        'student': student,
        'progress_records': progress_records,
    }
    return render(request, 'vikes_reading_app/profile_detail.html', context)