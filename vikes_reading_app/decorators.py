from django.shortcuts import redirect
from functools import wraps

def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role != 'teacher':
            return redirect('profile')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view