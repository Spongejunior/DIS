"""Django settings for the Mzimba North VetAssistant backend.

Settings such as DATABASE_URL can live in backend/.env (not committed to git).
Real environment variables win over the file.
"""
import os
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


# development, production or testing
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development').strip().lower()
DEBUG = ENVIRONMENT == 'development'
TESTING = ENVIRONMENT == 'testing'

# Security - must be overridden in production
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '*')


def database_from_url(url):
    """Django database settings from a DATABASE_URL.

    PostgreSQL when DATABASE_URL is set (see backend/.env), otherwise the local
    SQLite file instance/database.db. Special characters in the password must
    be URL-encoded (e.g. $ -> %24, @ -> %40).
    """
    if not url:
        url = 'sqlite:///database.db'
    parts = urlsplit(url)
    scheme = parts.scheme.split('+')[0]

    if scheme in ('postgres', 'postgresql'):
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': unquote(parts.path.lstrip('/')),
            'USER': unquote(parts.username or ''),
            'PASSWORD': unquote(parts.password or ''),
            'HOST': parts.hostname or '',
            'PORT': str(parts.port or ''),
            # e.g. ?sslmode=require for hosted databases
            'OPTIONS': dict(parse_qsl(parts.query)),
            'CONN_MAX_AGE': 60,
            # Re-check kept connections so a restarted PostgreSQL server does
            # not cause errors on the next request.
            'CONN_HEALTH_CHECKS': True,
        }

    if scheme == 'sqlite':
        path = url[len('sqlite:///'):] if url.startswith('sqlite:///') else ''
        if path in ('', ':memory:'):
            name = ':memory:'
        else:
            # A relative path is inside instance/, as it was with Flask.
            name = Path(path) if Path(path).is_absolute() else BASE_DIR / 'instance' / path
        return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': name}

    raise ValueError(f'Unsupported DATABASE_URL scheme: {parts.scheme}')


DATABASES = {
    'default': database_from_url(
        'sqlite:///:memory:' if TESTING else os.environ.get('DATABASE_URL')
    ),
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = [
    'core',  # first, so its runserver (port 80) replaces Django's
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
]

# No CSRF middleware: like Flask-WTF, the forms carry their own csrf_token
# field (see core/forms.py). Pages are JSON for the Next.js frontend.
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.LanguageMiddleware',
    'core.middleware.JsonErrorMiddleware',
]

ROOT_URLCONF = 'vetassistant.urls'
WSGI_APPLICATION = 'vetassistant.wsgi.application'
APPEND_SLASH = False

AUTH_USER_MODEL = 'core.User'
AUTH_PASSWORD_VALIDATORS = []

# Sessions end when the browser closes unless "Remember Me" is ticked.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = not DEBUG and not TESTING  # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
REMEMBER_ME_DAYS = 365

# Forms check their csrf_token field (switched off for tests).
CSRF_FORMS_ENABLED = not TESTING

DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024  # 16MB max request body

# Time: stored as Malawi local time (UTC+2, no daylight saving), without a
# time zone, which is how the existing database holds it.
TIME_ZONE = 'Africa/Blantyre'
USE_TZ = False

# Internationalization (i18n)
LANGUAGE_CODE = 'en'
USE_I18N = True
APP_LANGUAGES = ['en', 'chi', 'tum']
LOCALE_PATHS = [BASE_DIR / 'locale']

# Email (Gmail SMTP by default)
EMAIL_HOST = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('MAIL_USERNAME', '')
EMAIL_HOST_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('MAIL_DEFAULT_SENDER') or 'no-reply@vetassistant.local'
MAIL_SUPPRESS_SEND = env_bool('MAIL_SUPPRESS_SEND', True)
EMAIL_TIMEOUT = 20
if MAIL_SUPPRESS_SEND or TESTING:
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

APP_NAME = 'Mzimba North VetAssistant'
VERSION = '2.1.4'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'core': {'handlers': ['console'], 'level': os.environ.get('LOG_LEVEL', 'INFO')},
    },
}
