"""Helpers shared by the views: access checks, record ids, farmer/vet
assignment, notifications, the system log and email."""
import json
import logging
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from .bridge import flash
from .models import FarmerVeterinarian, Notification, SystemLog, User, malawi_now

logger = logging.getLogger(__name__)


# Access control

def methods(*allowed):
    """Allowed HTTP methods for a view (HEAD comes with GET)."""
    allowed = list(allowed) + (['HEAD'] if 'GET' in allowed else [])
    return require_http_methods(allowed)


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            flash(request, _('Please log in to access this page.'), 'message')
            return redirect(reverse('login') + '?' + urlencode({'next': request.get_full_path()}))
        return view(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                flash(request, _('You do not have permission to access this page.'), 'danger')
                return redirect('dashboard')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


# Request helpers

def int_arg(params, name, default):
    """``request.GET.get(name, default, type=int)``: the default when missing or not a number."""
    try:
        return int(params.get(name, default))
    except (TypeError, ValueError):
        return default


def client_ip(request):
    return request.META.get('REMOTE_ADDR')


def external_url(request, path):
    """An absolute URL on the host the browser used.

    The Next.js server proxies the requests and reports that host in
    X-Forwarded-Host (used for password reset links).
    """
    forwarded_host = request.headers.get('X-Forwarded-Host')
    if not forwarded_host:
        return request.build_absolute_uri(path)
    host = forwarded_host.split(',')[0].strip()
    scheme = (request.headers.get('X-Forwarded-Proto') or request.scheme).split(',')[0].strip()
    return f'{scheme}://{host}{path}'


# Record ids such as R-2026-001

def next_record_id(model, field, prefix):
    """The next id after the highest one used this year (gaps and imported
    rows do not cause duplicates)."""
    year = malawi_now().year
    start = f'{prefix}-{year}-'
    highest = 0
    for value in model.objects.filter(**{f'{field}__startswith': start}).values_list(field, flat=True):
        suffix = value[len(start):]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f'{start}{highest + 1:03d}'


def create_with_record_id(model, field, prefix, attempts=5, **values):
    """Create a row with the next record id, retrying if another request took
    that id at the same moment."""
    from django.db import IntegrityError, transaction
    for attempt in range(attempts):
        try:
            with transaction.atomic():
                return model.objects.create(**{field: next_record_id(model, field, prefix)}, **values)
        except IntegrityError:
            if attempt == attempts - 1:
                raise


# Farmer <-> veterinarian assignment

def is_assigned(veterinarian, farmer_id):
    return FarmerVeterinarian.objects.filter(veterinarian=veterinarian, farmer_id=farmer_id).exists()


def auto_assign_by_location(user):
    """Keep a farmer's or vet's links in line with their EPA: links to someone
    in another EPA (or any links, if the user is not approved) are removed,
    then the approved users of the other role in the same EPA are linked.
    Returns the number of new links."""
    normalized_location = (user.location or '').strip()
    own_links = FarmerVeterinarian.objects.filter(farmer=user) if user.is_farmer() else (
        FarmerVeterinarian.objects.filter(veterinarian=user) if user.is_veterinarian() else None)
    if own_links is None:
        return 0
    if not normalized_location or not user.is_approved_user():
        own_links.delete()
        return 0
    other = 'veterinarian' if user.is_farmer() else 'farmer'
    own_links.exclude(**{f'{other}__location': normalized_location}).delete()

    if user.is_farmer():
        existing = set(user.assigned_veterinarians.values_list('id', flat=True))
        matches = User.objects.filter(role='veterinarian', status='approved', location=normalized_location)
        links = [FarmerVeterinarian(farmer=user, veterinarian=vet)
                 for vet in matches.order_by('id') if vet.id not in existing]
    elif user.is_veterinarian():
        existing = set(user.assigned_farmers.values_list('id', flat=True))
        matches = User.objects.filter(role='farmer', status='approved', location=normalized_location)
        links = [FarmerVeterinarian(farmer=farmer, veterinarian=user)
                 for farmer in matches.order_by('id') if farmer.id not in existing]
    else:
        return 0

    for link in links:
        link.save(force_insert=True)
    return len(links)


# Notifications

NOTIFICATION_PAGES = {
    'prediction': 'farmer_predictions',
    'review': 'predictions_review',
    'treatment': 'treatment_suggestions',
    'mortality': 'mortality_reports',
    'alert': 'farmer_notifications',
    'meeting': 'farmer_notifications',
    'message': 'vet_communications',
}


# Farmers are sent to their own pages, not the vet's.
FARMER_NOTIFICATION_PAGES = {
    'prediction': 'farmer_predictions',
    'review': 'farmer_predictions',
    'treatment': 'farmer_predictions',
    'alert': 'farmer_notifications',
    'meeting': 'farmer_notifications',
}


def get_notification_action_url(notification_type, related_id=None, recipient_role=None):
    if not related_id:
        return None
    pages = FARMER_NOTIFICATION_PAGES if recipient_role == 'farmer' else NOTIFICATION_PAGES
    page = pages.get(notification_type)
    return reverse(page) if page else None


def create_notification(user_id, notification_type, title, message, priority='medium',
                        related_id=None, sender_id=None):
    recipient_role = User.objects.filter(pk=user_id).values_list('role', flat=True).first()
    return Notification.objects.create(
        user_id=user_id,
        sender_id=sender_id,
        notification_type=notification_type,
        title=str(title),
        message=str(message),
        priority=priority,
        action_url=get_notification_action_url(notification_type, related_id, recipient_role),
        related_id=related_id,
    )


def build_user_lookup(user_ids):
    ids = sorted({user_id for user_id in user_ids if user_id})
    if not ids:
        return {}
    return {user.id: user for user in User.objects.filter(id__in=ids)}


def build_sender_lookup(notifications):
    return build_user_lookup(note.sender_id for note in notifications)


def build_recipient_lookup(notifications):
    return build_user_lookup(note.user_id for note in notifications)


# System log

def log_system_event(request, level, component, message, user_id=None, details=None):
    SystemLog.objects.create(
        level=level,
        component=component,
        user_id=user_id,
        ip_address=client_ip(request) if request is not None else None,
        message=message,
        details=json.dumps(details) if details else None,
        timestamp=malawi_now(),
    )


# Email

def _send_simple_email(subject, recipient, body):
    if not recipient:
        return False
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient])
        return True
    except Exception as exc:  # depends on the SMTP server
        logger.warning('Email delivery failed for %s: %s', recipient, exc)
        return False


def send_approval_email(email):
    return _send_simple_email(
        'Your Mzimba North VetAssistant account has been approved',
        email,
        'Hello,\n\nYour Mzimba North VetAssistant account has been approved. '
        'You can now sign in and access the system.\n\nThank you.'
    )


def send_rejection_email(email):
    return _send_simple_email(
        'Your Mzimba North VetAssistant account request was rejected',
        email,
        'Hello,\n\nYour Mzimba North VetAssistant account request was reviewed and rejected. '
        'Please contact an administrator if you need more information.\n\nThank you.'
    )


def send_password_reset_email(email, reset_url):
    return _send_simple_email(
        'Reset your Mzimba North VetAssistant password',
        email,
        'Hello,\n\nWe received a request to reset your Mzimba North VetAssistant password.\n\n'
        f'Open this link to set a new password:\n{reset_url}\n\n'
        'If you did not request this change, you can safely ignore this email.\n\n'
        'Thank you.'
    )
