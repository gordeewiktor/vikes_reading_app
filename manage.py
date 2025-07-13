# --- Django Management Utility ---
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


 # Entry point for running Django management commands
def main():
    """Run administrative tasks."""
    # Set the default Django settings module for the 'manage.py' utility
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vikes_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Execute the management command passed via the command line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
