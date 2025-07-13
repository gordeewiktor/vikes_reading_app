# --- Imports ---
import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse

from vikes_reading_app.models import Progress, Story


# --- Helper Function ---

def _save_time(request, story_id, time_field, next_stage):
    """
    Shared helper to save time progress for pre-reading, reading, or post-reading.
    Updates or creates a Progress record.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
    try:
        data = json.loads(request.body)
        time_spent = data.get("time_spent", 0)
        story = get_object_or_404(Story, id=story_id)
        progress, _ = Progress.objects.update_or_create(
            student=request.user,
            read_story=story,
            defaults={
                time_field: time_spent,
                'current_stage': next_stage,
            }
        )
        return JsonResponse({"status": "success", "time_spent": time_spent})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# --- Views for Saving Progress ---

@csrf_exempt
@login_required
def save_reading_time(request, story_id):
    """API endpoint to save reading time progress."""
    return _save_time(request, story_id, 'reading_time', 'reading')


@csrf_exempt
@login_required
def save_pre_reading_time(request, story_id):
    """API endpoint to save pre-reading time progress."""
    return _save_time(request, story_id, 'pre_reading_time', 'reading')


@csrf_exempt
@login_required
def save_post_reading_time(request, story_id):
    """API endpoint to save post-reading time progress."""
    return _save_time(request, story_id, 'post_reading_time', 'completed')


# --- View for Resetting Progress ---

@login_required
def reset_progress(request, story_id):
    """
    Resets all progress for the current user and story:
      - Removes session-based pre/post-reading answers and lookups
      - Deletes Progress record from DB
      - Redirects to start pre-reading again
    """
    story = get_object_or_404(Story, id=story_id)

    # Remove session-based pre-reading answers
    session_key = f'pre_reading_progress_{story_id}'
    completed = request.session.get(session_key, [])
    for qid in completed:
        request.session.pop(f'answer_{qid}', None)
    request.session.pop(session_key, None)

    # Remove session-based post-reading answers
    post_reading_key = f'post_reading_progress_{story_id}'
    post_completed = request.session.get(post_reading_key, [])
    for qid in post_completed:
        request.session.pop(f'answer_{qid}', None)
    request.session.pop(post_reading_key, None)

    # Remove lookup-related session data for this story
    keys_to_delete = [key for key in request.session.keys() if key.startswith(f'lookup_story_{story_id}_')]
    for key in keys_to_delete:
        del request.session[key]

    # Remove DB-based progress for this user/story
    Progress.objects.filter(student=request.user, read_story=story).delete()

    # Redirect to start pre-reading again
    return redirect('pre_reading_read', story_id=story_id)