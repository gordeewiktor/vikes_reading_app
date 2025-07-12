from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from vikes_reading_app.forms import CustomUserCreationForm

def logout_confirm(request):
    """
    Displays a confirmation page before logging out.
    """
    return render(request, 'vikes_reading_app/auth/logout_confirm.html')

def register_view(request):
    """
    Handles user registration.
    GET: Shows the registration form.
    POST: Creates a student user, logs them in, and redirects home.
    """
    form = CustomUserCreationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'student'
        user.save()
        login(request, user)
        messages.success(request, "Registration successful! You are now logged in.")
        return redirect('home')

    return render(request, 'vikes_reading_app/auth/register.html', {'form': form})