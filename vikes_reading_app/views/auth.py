from django.shortcuts import render, redirect
from vikes_reading_app.forms import CustomUserCreationForm
from django.contrib.auth import login
from django.contrib import messages

def logout_confirm(request):
    """
    Presents a confirmation page before logging out the user.
    """
    return render(request, 'vikes_reading_app/auth/logout_confirm.html')

def register_view(request):
    """
    Handles user registration. On GET, shows registration form.
    On POST, creates a new user (default role: student), logs them in, and redirects home.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'  # Default role for new registrations
            user.save()

            login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'vikes_reading_app/auth/register.html', {'form': form})