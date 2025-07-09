from django.contrib.auth.decorators import user_passes_test
from vikes_reading_app.models import CustomUser, Progress
from django.shortcuts import render

# Function to check if the user is a teacher
# This will be used as a decorator to restrict access to views
# Only authenticated users with the role 'teacher' will pass this test
def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'