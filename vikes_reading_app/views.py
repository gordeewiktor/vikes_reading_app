from django.shortcuts import render

def home(request):
    return render(request, 'vikes_reading_app/home.html')

def login(request):
    return render(request, 'vikes_reading_app/login.html')

def register(request):
    return render(request, 'vikes_reading_app/register.html')