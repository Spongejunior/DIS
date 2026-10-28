"""JSON bridge between the Django views and the Next.js frontend.

The views in ``core/views.py`` do all the work (queries, validation, role
checks, flashes, redirects). The HTML is rendered by the Next.js app in
``frontend/``, so this module delivers each view's result as JSON:

* ``render_page(request, name, **context)`` returns the page name and its
  context as JSON. The name (e.g. ``farmer/dashboard.html``) identifies the
  page; the Next.js page for that URL renders the data.
* a request to ``/api/v1/page/<path>`` runs the view for ``<path>`` and turns a
  redirect into ``{"redirect": "/path"}`` so the browser can follow it on the
  Next.js side.
"""
from datetime import date, datetime
from urllib.parse import urlsplit

from django import forms
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpResponseNotAllowed, JsonResponse
from django.urls import resolve

from .forms import PageForm, csrf_token
from .models import Prediction, SymptomReport, Treatment, User

BRIDGE_PREFIX = '/api/v1/page'
FLASH_SESSION_KEY = '_flashes'
REDIRECT_CODES = (301, 302, 303, 307, 308)

# Never sent to the browser.
SENSITIVE_USER_COLUMNS = {'password_hash', 'reset_token', 'reset_token_expires_at'}

# Context keys whose users are listed with their full details by the page.
# Everywhere else a user is reduced to the name fields the pages display.
FULL_USER_KEYS = {'assigned_farmers', 'users_by_status'}


# Flash messages, kept in the session until the next page is rendered.

def flash(request, message, category='message'):
    flashes = request.session.get(FLASH_SESSION_KEY, [])
    flashes.append([category, str(message)])
    request.session[FLASH_SESSION_KEY] = flashes


def pop_flashes(request):
    if not hasattr(request, 'session'):
        return []
    return [list(item) for item in request.session.pop(FLASH_SESSION_KEY, [])]


# Serialization

def _plain(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _columns(obj, exclude=()):
    return {
        field.column: _plain(getattr(obj, field.attname))
        for field in obj._meta.concrete_fields
        if field.column and field.column not in exclude
    }


def _user(user, full=False):
    if not full:
        return {'id': user.id, 'username': user.username, 'full_name': user.full_name}
    data = _columns(user, SENSITIVE_USER_COLUMNS)
    data['animal_types_list'] = user.get_animal_types_list()
    return data


def _report(report):
    data = _columns(report)
    data['symptoms'] = report.get_additional_symptoms_list()
    data['farmer'] = _user(report.farmer) if report.farmer_id else None
    return data


def _prediction(prediction):
    data = _columns(prediction, {'features_used', 'care_plan'})
    data['possible'] = prediction.get_possible_diseases()
    data['care_plan'] = prediction.get_care_plan()
    report = prediction.symptom_report if prediction.symptom_report_id else None
    data['symptom_report'] = _report(report) if report else None
    return data


def _treatment(treatment):
    data = _columns(treatment)
    report = treatment.symptom_report if treatment.symptom_report_id else None
    data['symptom_report'] = _report(report) if report else None
    return data


def _widget_kind(widget):
    if isinstance(widget, forms.Select):
        return 'select'
    if isinstance(widget, forms.Textarea):
        return 'textarea'
    if isinstance(widget, forms.CheckboxInput):
        return 'checkbox'
    return getattr(widget, 'input_type', None) or 'text'


# HTML validation attributes each kind of input carries (as WTForms rendered them).
VALIDATION_ATTRS = {
    'text': ('required', 'maxlength', 'minlength'),
    'password': ('required', 'maxlength', 'minlength'),
    'textarea': ('required', 'maxlength', 'minlength'),
    'number': ('required', 'max', 'min'),
    'date': ('required', 'max', 'min'),
}


def _display(value):
    if value is None:
        return ''
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _field(form, name, field):
    """Describe a form field with the attributes its input would render."""
    bound = form[name]
    kind = _widget_kind(field.widget)

    flags = {
        'required': field.required,
        'minlength': getattr(field, 'min_length', None),
        'maxlength': getattr(field, 'max_length', None),
        'min': getattr(field, 'min_value', None),
        'max': getattr(field, 'max_value', None),
    }
    attrs = {}
    for attr in VALIDATION_ATTRS.get(kind, ('required',)):
        value = flags[attr]
        if value not in (None, False):
            attrs[attr] = value

    errors = [str(error) for error in form.errors.get(name, [])] if form.is_bound else []
    data = {
        'id': bound.auto_id or name,
        'name': name,
        'type': kind,
        'label': str(field.label),
        'errors': errors,
        'attrs': attrs,
    }
    value = bound.value()
    if form.is_bound and name not in form.posted:
        # Not sent by the page: it keeps the saved value (see PageForm).
        value = form.initial.get(name) if kind != 'checkbox' else value
    if kind == 'select':
        # Nothing is selected until there is a value (the browser shows the first option).
        selected = None if value is None else _display(value)
        data['choices'] = [
            [str(choice_value), str(choice_label), str(choice_value) == selected]
            for choice_value, choice_label in field.choices
        ]
    elif kind == 'checkbox':
        data['value'] = 'y'
        data['checked'] = bool(value)
    elif kind == 'password':
        data['value'] = ''
    elif name == 'csrf_token':
        data['value'] = csrf_token(form.request)
    else:
        data['value'] = _display(value)
    return data


def _form(form):
    fields = {name: _field(form, name, field) for name, field in form.fields.items()}
    label = str(form.submit_label)
    fields['submit'] = {
        'id': 'submit', 'name': 'submit', 'type': 'submit', 'label': label,
        'errors': [], 'attrs': {}, 'value': label,
    }
    errors = {}
    if form.is_bound:
        errors = {
            name: [str(error) for error in field_errors]
            for name, field_errors in form.errors.items()
        }
    return {'fields': fields, 'errors': errors}


def serialize(value, full_users=False):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, PageForm):
        return _form(value)
    if isinstance(value, User):
        return _user(value, full=full_users)
    if isinstance(value, SymptomReport):
        return _report(value)
    if isinstance(value, Prediction):
        return _prediction(value)
    if isinstance(value, Treatment):
        return _treatment(value)
    if isinstance(value, models.Model):
        return _columns(value)
    if isinstance(value, dict):
        return {str(key): serialize(item, full_users) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, QuerySet)):
        return [serialize(item, full_users) for item in value]
    return str(value)


def json_response(payload, status=200):
    # Key order is kept: pages iterate some dicts in insertion order.
    return JsonResponse(payload, status=status, safe=False)


def _farmer_profile_extras(request):
    # The farmer profile page lists the farmer's veterinarians.
    return {
        'assigned_vets': [
            {'full_name': vet.full_name, 'phone': vet.phone, 'email': vet.email}
            for vet in request.user.assigned_veterinarians
        ]
    }


# Data a page shows from the current user rather than the view's context.
EXTRA_CONTEXT = {
    'farmer/registration.html': _farmer_profile_extras,
}


def render_page(request, template_name, status=200, **context):
    """The page's data as JSON (in place of rendering an HTML template)."""
    data = {
        key: serialize(value, full_users=key in FULL_USER_KEYS)
        for key, value in context.items()
    }
    extras = EXTRA_CONTEXT.get(template_name)
    if extras:
        data.update(extras(request))

    user = getattr(request, 'user', None)
    return json_response({
        'template': template_name,
        'context': data,
        'user': _user(user, full=True) if user is not None and user.is_authenticated else None,
        'flashes': pop_flashes(request),
    }, status=status)


def frontend_path(location):
    """Turn a redirect target into a path the Next.js router can follow."""
    parts = urlsplit(location)
    # The login redirect's ?next= is built from the bridge URL; point it at the page instead.
    query = parts.query.replace('%2Fapi%2Fv1%2Fpage', '')
    path = parts.path or '/'
    if path.startswith(BRIDGE_PREFIX):
        path = path[len(BRIDGE_PREFIX):] or '/'
    return path + ('?' + query if query else '')


def api_page(request, subpath=''):
    """Run the view for /<subpath> and answer with JSON."""
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])

    # Only the page URLs (core/urls.py) can be reached, never the bridge itself.
    match = resolve('/' + subpath, urlconf='core.urls')
    response = match.func(request, *match.args, **match.kwargs)

    if response.status_code in REDIRECT_CODES and response.get('Location'):
        return json_response({'redirect': frontend_path(response['Location'])})
    return response


# Error pages

def page_not_found(request, exception=None):
    return render_page(request, 'errors/404.html', status=404)


def forbidden(request, exception=None):
    return render_page(request, 'errors/403.html', status=403)


def internal_server_error(request):
    return render_page(request, 'errors/500.html', status=500)
