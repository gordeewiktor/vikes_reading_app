# --- Imports ---
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import JsonResponse

from vikes_reading_app.repositories.progress_repository_impl import ORMProgressRepository
from vikes_reading_app.repositories.story_repository_impl import ORMStoryRepository
from vikes_reading_app.services.reading_flow import ReadingFlowService


# --- Helper Function ---

def _save_time(request, story_id, time_field):
    """
    Shared helper to save time progress for pre-reading, reading, or post-reading.
    Updates or creates a Progress record.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
    try:
        story_repo = ORMStoryRepository()
        progress_repo = ORMProgressRepository()
        data = json.loads(request.body)
        time_spent = data.get("time_spent", 0)
        story = story_repo.get_story_by_id(story_id)
        progress_repo.save_time(
            student=request.user,
            story=story,
            time_field=time_field,
            current_stage=ReadingFlowService.get_next_stage(time_field),
            time_spent=time_spent,
        )
        return JsonResponse({"status": "success", "time_spent": time_spent})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# --- Views for Saving Progress ---

@login_required
def save_reading_time(request, story_id):
    """API endpoint to save reading time progress."""
    return _save_time(request, story_id, 'reading_time')


@login_required
def save_pre_reading_time(request, story_id):
    """API endpoint to save pre-reading time progress."""
    return _save_time(request, story_id, 'pre_reading_time')


@login_required
def save_post_reading_time(request, story_id):
    """API endpoint to save post-reading time progress."""
    return _save_time(request, story_id, 'post_reading_time')


# --- View for Resetting Progress ---

@login_required
def reset_progress(request, story_id):
    """
    Resets all progress for the current user and story:
      - Removes session-based pre/post-reading answers and lookups
      - Deletes Progress record from DB
      - Redirects to start pre-reading again
    """
    story_repo = ORMStoryRepository()
    progress_repo = ORMProgressRepository()
    story = story_repo.get_story_by_id(story_id)

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
    progress_repo.delete_progress(request.user, story)

    # Redirect to start pre-reading again
    return redirect('pre_reading_read', story_id=story_id)
