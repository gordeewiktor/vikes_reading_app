from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from vikes_reading_app.models import Progress, CustomUser
from vikes_reading_app.helpers import is_teacher

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
        progress_list = Progress.objects.select_related('student', 'read_story')
        students_progress = {}
        for progress in progress_list:
            student = progress.student
            story = progress.read_story
            if student not in students_progress:
                students_progress[student] = []
            students_progress[student].append({
                "story": story,
                "pre_reading_time": progress.pre_reading_time,
                # Pre-reading score logic: count of pre-reading answers (if present)
                "pre_reading_score": len(progress.answers_given.get("pre_reading", {})) if progress.answers_given else 0,
                "reading_time": progress.reading_time,
                # Post-reading score: count of correct answers (True)
                "post_reading_score": sum(1 for value in progress.answers_given.values() if value) if progress.answers_given else 0,
                "post_reading_time": progress.post_reading_time
            })
        return render(request, 'vikes_reading_app/profile.html', {
            'user': request.user,
            'students_progress': students_progress
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

# View accessible only to teachers, showing all students and whether they have any progress
@user_passes_test(is_teacher)
def my_students(request):
    # Get all users who are students
    students = CustomUser.objects.filter(role='student')

    # Create a list of tuples (student, has_progress)
    # has_progress is True if any Progress record exists for that student
    student_status = [
        (student, Progress.objects.filter(student=student).exists())
        for student in students
    ]

    # Pass the list to the template
    context = {
        'student_status': student_status
    }
    return render(request, 'vikes_reading_app/my_students.html', context)