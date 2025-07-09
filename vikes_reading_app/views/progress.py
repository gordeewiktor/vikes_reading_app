from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import get_object_or_404, redirect
from vikes_reading_app.models import Progress, Story
from django.http import JsonResponse

@csrf_exempt
@login_required
def save_reading_time(request, story_id):
    """
    API endpoint to save the time spent reading a story.
    Updates or creates Progress record for the user/story.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            time_spent = data.get("time_spent", 0)
            # Save or update the progress
            story = get_object_or_404(Story, id=story_id)
            progress, _ = Progress.objects.update_or_create(
                student=request.user,
                read_story=story,
                defaults={
                    'reading_time': time_spent,
                    'score': 0.0,
                    'current_stage': 'reading'
                }
            )
            return JsonResponse({"status": "success", "time_spent": time_spent})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
@login_required
def save_pre_reading_time(request, story_id):
    """
    API endpoint to save time spent in pre-reading exercises.
    Updates or creates Progress record for the user/story.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            time_spent = data.get("time_spent", 0)
            # Save or update the progress
            story = get_object_or_404(Story, id=story_id)
            progress, _ = Progress.objects.update_or_create(
                student=request.user,
                read_story=story,
                defaults={
                    'pre_reading_time': time_spent,
                    'current_stage': 'reading'
                }
            )
            print(f"Pre-reading time saved: {time_spent} seconds")
            return JsonResponse({"status": "success", "time_spent": time_spent})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
@login_required
def save_post_reading_time(request, story_id):
    """
    API endpoint to save time spent in post-reading questions.
    Updates or creates Progress record for the user/story.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            time_spent = data.get("time_spent", 0)
            # Save or update the progress
            story = get_object_or_404(Story, id=story_id)
            progress, _ = Progress.objects.update_or_create(
                student=request.user,
                read_story=story,
                defaults={
                    'post_reading_time': time_spent,
                    'current_stage': 'completed'
                }
            )
            print(f"Post-reading time saved: {time_spent} seconds")
            return JsonResponse({"status": "success", "time_spent": time_spent})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

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