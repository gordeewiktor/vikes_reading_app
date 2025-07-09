from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from vikes_reading_app.models import Story, PostReadingQuestion, Progress
from django.contrib import messages

@login_required
def story_lookup(request, story_id):
    """
    Temporarily displays the story text for a post-reading question lookup.
    Tracks and limits lookup count per question in session.
    After max lookups, redirects back to the question.
    """
    story = get_object_or_404(Story, id=story_id)
    question_id = int(request.GET.get('question_id'))
    # Track lookup count in session
    lookup_key = f'lookup_story_{story_id}_q{question_id}'
    lookup_count = request.session.get(lookup_key, 0)
    # Find the index for this question (for returning)
    questions = list(PostReadingQuestion.objects.filter(story=story).order_by('id'))
    question_index = next((index for index, q in enumerate(questions) if q.id == question_id), 0)
    if lookup_count >= 3:
        # No more lookups allowed; return to question
        return redirect('post_reading_read', story_id=story.id, question_index=question_index)
    lookup_count += 1
    request.session[lookup_key] = lookup_count
    # Set time limit for this lookup (in seconds)
    times = {1: 30, 2: 45, 3: 60}
    time_limit = times.get(lookup_count, 60)
    return render(request, 'vikes_reading_app/story_lookup.html', {
        'story': story,
        'time_limit': time_limit,
        'story_id': story_id,
        'question_id': question_id,
        'question_index': question_index,
    })

@require_POST
@login_required
def start_lookup(request, story_id, question_id):
    """
    Handles tracking of post-reading lookups at the DB level (if used).
    Increments lookup count for a specific question and user.
    Redirects to the story lookup page with appropriate time limit.
    """
    story = get_object_or_404(Story, id=story_id)
    question = get_object_or_404(PostReadingQuestion, id=question_id, story=story)
    progress, _ = Progress.objects.get_or_create(student=request.user, read_story=story)
    lookups = progress.post_reading_lookups or {}
    current_count = lookups.get(str(question_id), 0)
    if current_count >= 3:
        messages.error(request, "No more lookups left for this question.")
        return redirect("post_reading_read", story_id=story.id, question_index=0)
    current_count += 1
    lookups[str(question_id)] = current_count
    progress.post_reading_lookups = lookups
    progress.save()
    time_limit = {1: 30, 2: 45, 3: 60}.get(current_count, 60)
    return redirect(f"/story-lookup/{story_id}/?question_id={question_id}&time_limit={time_limit}")

@require_POST
@login_required
def return_to_question(request, story_id, question_index):
    """
    Redirects user back to the post-reading question after a lookup.
    """
    return redirect("post_reading_read", story_id=story_id, question_index=question_index)

def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'