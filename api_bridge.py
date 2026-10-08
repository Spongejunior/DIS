"""JSON bridge between the existing Flask views and the Next.js frontend.

The views in ``app.py`` keep doing all the work (queries, validation, role
checks, flashes, redirects). This module only changes how their result is
delivered when a request arrives through ``/api/v1/page/<path>``:

* ``render_template(...)`` returns the template name and its context as JSON
  instead of HTML, so the Next.js page can render the same data.
* a redirect is returned as ``{"redirect": "/path"}`` so the browser can follow
  it on the Next.js side.

Requests to the original URLs are untouched and still render the Jinja
templates.
"""
import json
from datetime import date, datetime
from urllib.parse import urlsplit

from flask import current_app, g, get_flashed_messages, request
from flask import render_template as _flask_render_template
from flask.globals import request_ctx
from flask_login import current_user
from flask_wtf import FlaskForm
from werkzeug.exceptions import NotFound
from werkzeug.routing import RequestRedirect
from wtforms import widgets

from models import db, User, SymptomReport, Prediction, Treatment

BRIDGE_PREFIX = '/api/v1/page'
BRIDGE_ENDPOINT = 'api_page'

# Never sent to the browser.
SENSITIVE_USER_COLUMNS = {'password_hash', 'reset_token', 'reset_token_expires_at'}

# Context keys whose users are listed with their full details by the template.
# Everywhere else a user is reduced to the name fields the templates display.
FULL_USER_KEYS = {'assigned_farmers', 'users_by_status'}

# Context values the templates never read; left out of the JSON.
UNUSED_CONTEXT = {
    'veterinarian/farmer_mapping.html': {'available_farmers'},
    'organization_admin/user_management.html': {'users'},
    'farmer/predictions.html': {'active_treatments'},
}


def _farmer_profile_extras():
    # farmer/registration.html reads current_user.assigned_veterinarians directly.
    return {
        'assigned_vets': [
            {'full_name': vet.full_name, 'phone': vet.phone, 'email': vet.email}
            for vet in current_user.assigned_veterinarians.all()
        ]
    }


# Data a template pulls from current_user relationships rather than the context.
EXTRA_CONTEXT = {
    'farmer/registration.html': _farmer_profile_extras,
}


def _plain(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _columns(obj, exclude=()):
    return {
        column.key: _plain(getattr(obj, column.key))
        for column in obj.__table__.columns
        if column.key not in exclude
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
    data['farmer'] = _user(report.farmer) if report.farmer else None
    return data


def _prediction(prediction):
    data = _columns(prediction, {'features_used'})
    data['possible'] = prediction.get_possible_diseases()
    report = prediction.symptom_report
    data['symptom_report'] = _report(report) if report else None
    return data


def _treatment(treatment):
    data = _columns(treatment)
    report = treatment.symptom_report
    data['symptom_report'] = _report(report) if report else None
    return data


def _field(field):
    """Describe a WTForms field with the same attributes its widget would render."""
    widget = field.widget
    if isinstance(widget, widgets.Select):
        kind = 'select'
    elif isinstance(widget, widgets.TextArea):
        kind = 'textarea'
    else:
        kind = getattr(widget, 'input_type', None) or 'text'

    attrs = {}
    for name in getattr(widget, 'validation_attrs', ()):
        value = getattr(field.flags, name, None)
        if value not in (None, False):
            attrs[name] = value
    if field.render_kw:
        attrs.update(field.render_kw)

    data = {
        'id': field.id,
        'name': field.name,
        'type': kind,
        'label': str(field.label.text),
        'errors': [str(error) for error in field.errors],
        'attrs': attrs,
    }
    if kind == 'select':
        data['choices'] = [
            [str(choice[0]), str(choice[1]), bool(choice[2])]
            for choice in field.iter_choices()
        ]
    elif kind == 'checkbox':
        data['value'] = field._value()
        data['checked'] = bool(field.data)
    elif kind == 'submit':
        data['value'] = str(field.label.text)
    elif kind == 'password':
        data['value'] = ''
    else:
        data['value'] = field._value()
    return data


def _form(form):
    return {
        'fields': {field.name: _field(field) for field in form},
        'errors': {
            name: [str(error) for error in errors]
            for name, errors in form.errors.items()
        },
    }


def _serialize(value, full_users=False):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, FlaskForm):
        return _form(value)
    if isinstance(value, User):
        return _user(value, full=full_users)
    if isinstance(value, SymptomReport):
        return _report(value)
    if isinstance(value, Prediction):
        return _prediction(value)
    if isinstance(value, Treatment):
        return _treatment(value)
    if isinstance(value, db.Model):
        return _columns(value)
    if isinstance(value, dict):
        return {str(key): _serialize(item, full_users) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize(item, full_users) for item in value]
    return str(value)


def _json_response(payload, status=200):
    # sort_keys stays off: templates iterate some dicts in insertion order.
    return current_app.response_class(
        json.dumps(payload, sort_keys=False),
        status=status,
        mimetype='application/json',
    )


def render_template(template_name, **context):
    """Drop-in for ``flask.render_template`` used by the views in ``app.py``."""
    if not g.get('api_bridge'):
        return _flask_render_template(template_name, **context)

    unused = UNUSED_CONTEXT.get(template_name, ())
    data = {
        key: _serialize(value, full_users=key in FULL_USER_KEYS)
        for key, value in context.items()
        if key not in unused
    }
    extras = EXTRA_CONTEXT.get(template_name)
    if extras:
        data.update(extras())

    return _json_response({
        'template': template_name,
        'context': data,
        'user': _user(current_user, full=True) if current_user.is_authenticated else None,
        'flashes': [list(flash) for flash in get_flashed_messages(with_categories=True)],
    })


def _frontend_path(location):
    """Turn a redirect target into a path the Next.js router can follow."""
    parts = urlsplit(location)
    # Flask-Login builds ?next= from the bridge URL; point it at the page instead.
    query = parts.query.replace('%2Fapi%2Fv1%2Fpage', '')
    path = parts.path or '/'
    if path.startswith(BRIDGE_PREFIX):
        path = path[len(BRIDGE_PREFIX):] or '/'
    return path + ('?' + query if query else '')


def _apply_forwarded_host():
    """Build external URLs (password reset links) against the frontend's host.

    The Next.js server proxies bridge requests and reports the host the browser
    used in X-Forwarded-Host.
    """
    forwarded_host = request.headers.get('X-Forwarded-Host')
    if not forwarded_host:
        return
    request.environ['HTTP_HOST'] = forwarded_host.split(',')[0].strip()
    forwarded_proto = request.headers.get('X-Forwarded-Proto')
    if forwarded_proto:
        request.environ['wsgi.url_scheme'] = forwarded_proto.split(',')[0].strip()
    for cached in ('host', 'host_url', 'url', 'base_url', 'url_root', 'root_url'):
        request.__dict__.pop(cached, None)
    request_ctx.url_adapter = current_app.create_url_adapter(request)


def register_api_bridge(app):
    def api_page(subpath=''):
        g.api_bridge = True
        _apply_forwarded_host()

        try:
            endpoint, view_args = request_ctx.url_adapter.match(
                '/' + subpath, method=request.method
            )
        except RequestRedirect as redirect_exc:
            return _json_response({'redirect': _frontend_path(redirect_exc.new_url)})

        if endpoint in ('static', BRIDGE_ENDPOINT):
            raise NotFound()

        view = current_app.ensure_sync(app.view_functions[endpoint])
        response = app.make_response(view(**view_args))

        if response.status_code in (301, 302, 303, 307, 308) and response.headers.get('Location'):
            return _json_response({'redirect': _frontend_path(response.headers['Location'])})
        return response

    app.add_url_rule(BRIDGE_PREFIX, BRIDGE_ENDPOINT, api_page, methods=['GET', 'POST'])
    app.add_url_rule(
        BRIDGE_PREFIX + '/<path:subpath>', BRIDGE_ENDPOINT, api_page, methods=['GET', 'POST']
    )
