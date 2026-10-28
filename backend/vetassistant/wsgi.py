"""WSGI entry point (gunicorn vetassistant.wsgi:application, and runserver)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vetassistant.settings')

application = get_wsgi_application()

# Load the prediction model in the background now that the server is starting,
# not on the first farmer submission.
from core.prediction import start_model_warm_up  # noqa: E402

start_model_warm_up()
