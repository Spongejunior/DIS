from django.core.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    """``python manage.py runserver`` on port 80, where the frontend expects the
    backend (BACKEND_URL). Pass a port to use another, e.g. ``runserver 8000``."""
    default_port = '80'
