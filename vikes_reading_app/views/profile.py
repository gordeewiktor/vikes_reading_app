from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from vikes_reading_app.models import Progress, CustomUser
from vikes_reading_app.helpers import is_teacher

def get_students_with_stories():
    students = CustomUser.objects.filter(role='student')
    student_data = []

    for student in students:
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

    return student_data

@login_required
def profile(request):
    """
    Allow users to view and edit their own profile.
    - If POST: Update profile details (currently only bio).
    - If teacher: Show progress of all students.
    - If student: Show own profile.
    """
    if request.method == 'POST':
        bio = request.POST.get('bio', '')
        user = request.user  # The logged-in user
        user.bio = bio
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    # If teacher, aggregate all students' progress for display
    if request.user.role == 'teacher':
        students_with_stories = get_students_with_stories()
        return render(request, 'vikes_reading_app/profile.html', {
            'user': request.user,
            'students_with_stories': students_with_stories
        })

    # Default for student users: show only their own profile
    return render(request, 'vikes_reading_app/profile.html', {'user': request.user})

# View to display detailed profile and progress of a specific student
@user_passes_test(is_teacher)
@login_required
def profile_detail(request, student_id):
    # Get the student object or 404 if not found or not a student
    student = get_object_or_404(CustomUser, id=student_id, role='student')

    # Fetch all progress objects for this student on stories created by the current teacher
    teacher_stories = request.user.story_set.all()
    progress_records = Progress.objects.filter(
        student=student,
        read_story__in=teacher_stories
    ).select_related('read_story')

    context = {
        'student': student,
        'progress_records': progress_records,  # Renamed for template consistency
    }
    return render(request, 'vikes_reading_app/profile_detail.html', context)