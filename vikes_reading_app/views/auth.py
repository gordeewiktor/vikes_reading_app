# --- Auth Views ---

# --- Django Imports ---
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect

# --- App Imports ---
from vikes_reading_app.forms import CustomUserCreationForm


# --- Logout Confirmation ---

def logout_confirm(request):
    """
    Display a confirmation page before logging the user out.
    """
    return render(request, 'vikes_reading_app/auth/logout_confirm.html')


# --- User Registration ---

def register_view(request):
    """
    Handle user registration.
    - GET: Display the registration form.
    - POST: Create a student user, log them in, and redirect to home.
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