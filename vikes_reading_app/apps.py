# --- App Configuration for Django ---

from django.apps import AppConfig

# Defines the Django app configuration for Vike's Reading App.
class VikesReadingAppConfig(AppConfig):
    """Configuration for the Vike's Reading App."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vikes_reading_app'
