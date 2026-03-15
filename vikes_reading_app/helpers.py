# --- User Role Helpers ---

# ✅ Check if user is a teacher (for decorators, permissions)
def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'


# --- Session Progress Helpers ---

# ✅ Retrieve session-based pre-reading progress for a specific story
def get_session_progress(request, story_id):
    return request.session.get(f'pre_reading_progress_{story_id}', [])
