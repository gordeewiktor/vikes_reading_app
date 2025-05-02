# Admin configuration for Vike's Reading App models
from django.contrib import admin
from .models import CustomUser

# Customize admin interface for CustomUser to display username, email, and role
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')

# Register your models here.
