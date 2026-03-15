# --- User Role Helpers ---

# ✅ Check if user is a teacher (for decorators, permissions)
def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'
