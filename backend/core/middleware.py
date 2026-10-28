import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import translation

from . import bridge

logger = logging.getLogger(__name__)


class LanguageMiddleware:
    """Activate the visitor's language.

    Priority: the logged-in user's saved ``preferred_language``, then the
    session value (anonymous visitors), then English.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = None
        if request.user.is_authenticated:
            language = request.user.preferred_language or None
        if not language:
            language = request.session.get('language')
        if language not in settings.APP_LANGUAGES:
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = language
        return self.get_response(request)


class JsonErrorMiddleware:
    """Answer 404/403/500 with the error page's JSON, as the frontend expects."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return bridge.page_not_found(request)
        if isinstance(exception, PermissionDenied):
            return bridge.forbidden(request)

        logger.exception('Internal server error on %s', request.path)
        try:
            from .services import log_system_event
            user = getattr(request, 'user', None)
            log_system_event(request, 'error', 'system', f'Internal server error: {exception}',
                             user.id if user is not None and user.is_authenticated else None)
        except Exception:
            logger.exception('Could not record the error in the system log')
        return bridge.internal_server_error(request)
