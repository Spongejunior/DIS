"""Page views. Each one answers with the page's data as JSON (core/bridge.py)
or with a redirect, which the bridge hands to the Next.js frontend."""
import json
import logging
import secrets
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import login, logout
from django.db import connection, transaction
from django.db.models import Avg, Case, CharField, Count, F, Func, IntegerField, Q, Sum, Value, When
from django.db.models.deletion import ProtectedError, RestrictedError
from django.db.utils import DatabaseError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import PermissionDenied

from .bridge import flash, render_page
from .forms import (
    ForgotPasswordForm, LoginForm, MortalityReportForm, NewTreatmentForm, ProfileForm, RegistrationForm,
    ReportGenerationForm, ResetPasswordForm, SymptomForm, TreatmentForm,
)
from .locations import EPA_NAMES, EPA_SECTIONS
from .models import (
    FarmerVeterinarian, ModelVersion, MortalityReport, Notification, Prediction, Report,
    SymptomReport, SystemLog, Treatment, User, as_malawi_time, malawi_now,
)
from .prediction import (
    FEATURE_ENCODING_PATH, MODEL_PATH, SUPPORTED_ANIMAL_TYPES, categorize_disease, create_prediction,
)
from .services import (
    auto_assign_by_location, build_recipient_lookup, build_sender_lookup, create_notification,
    create_with_record_id,
    external_url, int_arg, is_assigned, log_system_event, login_required, methods, next_record_id,
    role_required, send_approval_email, send_password_reset_email, send_rejection_email,
)

try:
    from . import pdf_utils
    PDF_AVAILABLE = True
except Exception:  # keeps the app usable if the PDF libraries are missing
    pdf_utils = None
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

REPORT_DAY_OPTIONS = (7, 14, 30, 90, 365)


def safe_redirect_back(request, fallback):
    """Back to the page the form was on: only its path, never another site."""
    path = urlsplit(request.META.get('HTTP_REFERER') or '').path
    return redirect(path if path.startswith('/') and not path.startswith('//') else reverse(fallback))


# Public pages

@methods('GET')
def landing_page(request):
    return render_page(request, 'landing_files/landing.html')


@methods('POST')
def set_language(request):
    """Save the selected language for the current visitor.

    Logged-in users have their choice saved to their profile so it is kept
    across devices; anonymous visitors store it in the session.
    """
    language = (request.POST.get('language') or '').strip()
    if language not in settings.APP_LANGUAGES:
        flash(request, _('Unsupported language selected.'), 'danger')
        return safe_redirect_back(request, 'landing_page')

    if request.user.is_authenticated:
        request.user.preferred_language = language
        request.user.save(update_fields=['preferred_language'])
    request.session['language'] = language
    flash(request, _('Language updated successfully.'), 'success')
    return safe_redirect_back(request, 'landing_page')


@methods('GET')
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('landing_page')


# Accounts

@methods('GET', 'POST')
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request)
    if form.validate_on_submit():
        user = User.objects.filter(username=form.value('username')).first()

        if user and user.check_password(form.value('password')):
            if user.status == 'pending':
                flash(request, _('Your account is awaiting admin approval.'), 'warning')
                return redirect('login')
            if user.status == 'rejected':
                flash(request, _('Your account was rejected.'), 'danger')
                return redirect('login')

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # Without "Remember Me" the session ends when the browser closes.
            request.session.set_expiry(timedelta(days=settings.REMEMBER_ME_DAYS) if form.value('remember') else 0)
            user.last_login = malawi_now()
            user.save(update_fields=['last_login'])

            log_system_event(request, 'info', 'auth', f'User {user.username} logged in', user.id)
            flash(request, _('Login successful!'), 'success')
            return redirect('dashboard')
        flash(request, _('Invalid username or password'), 'danger')

    return render_page(request, 'auth/login.html', form=form)


@methods('GET', 'POST')
def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = ForgotPasswordForm(request)
    if form.validate_on_submit():
        identity = form.value('identity').strip()
        user = User.objects.filter(Q(username=identity) | Q(email=identity)).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires_at = malawi_now() + timedelta(hours=1)
            user.save(update_fields=['reset_token', 'reset_token_expires_at'])

            reset_url = external_url(request, reverse('reset_password', args=[token]))
            email_sent = send_password_reset_email(user.email, reset_url)
            log_system_event(request, 'info', 'auth', f'Password reset requested for {user.username}', user.id)

            delivered = email_sent and not settings.MAIL_SUPPRESS_SEND
            if not delivered:
                logger.warning('Password reset email for %s was not sent (MAIL_SUPPRESS_SEND or SMTP failure)',
                               user.username)
                # Shown on screen only in development: anyone can type a
                # username here, so in production the link must go by email.
                if settings.DEBUG:
                    flash(request, _('Password reset link:') + f' {reset_url}', 'info')

        flash(request, _('If an account matched your details, a password reset link has been prepared.'), 'success')
        return redirect('login')

    return render_page(request, 'auth/forgot_password.html', form=form)


@methods('GET', 'POST')
def reset_password(request, token):
    if request.user.is_authenticated:
        return redirect('dashboard')

    user = User.objects.filter(reset_token=token).first()
    expires_at = as_malawi_time(user.reset_token_expires_at) if user else None
    if user is None or not expires_at or expires_at < malawi_now():
        flash(request, _('This password reset link is invalid or has expired.'), 'danger')
        return redirect('forgot_password')

    form = ResetPasswordForm(request)
    if form.validate_on_submit():
        user.set_password(form.value('new_password'))
        user.reset_token = None
        user.reset_token_expires_at = None
        user.save()

        log_system_event(request, 'info', 'auth', f'Password reset completed for {user.username}', user.id)
        flash(request, _('Your password has been reset successfully. You can now sign in.'), 'success')
        return redirect('login')

    return render_page(request, 'auth/reset_password.html', form=form)


@methods('GET', 'POST')
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegistrationForm(request)
    if form.validate_on_submit():
        user = User(
            username=form.value('username'),
            email=form.value('email'),
            full_name=form.value('full_name'),
            phone=form.value('phone'),
            role=form.value('role'),
            location=form.value('location'),
            specific_location=form.value('specific_location'),
            farm_name=form.value('farm_name'),
            animal_types=form.value('animal_types'),
            production_focus=form.value('production_focus'),
            status='pending',
        )
        user.set_password(form.value('password'))
        user.save()

        log_system_event(request, 'info', 'auth', f'New user registered and is awaiting approval: {user.username}', user.id)
        flash(request, _('Registration successful! Your account is awaiting admin approval.'), 'info')
        return redirect('login')

    return render_page(request, 'auth/register.html', form=form, epa_sections=EPA_SECTIONS)


@methods('GET')
@login_required
def logout_view(request):
    log_system_event(request, 'info', 'auth', f'User {request.user.username} logged out', request.user.id)
    logout(request)
    flash(request, _('You have been logged out.'), 'info')
    return redirect('landing_page')


@methods('GET')
@login_required
def dashboard(request):
    user = request.user
    if user.is_farmer():
        return redirect('farmer_dashboard')
    if user.is_veterinarian():
        return redirect('vet_dashboard')
    if user.is_organization_admin():
        return redirect('org_admin_dashboard')
    if user.is_system_admin():
        return redirect('sys_admin_dashboard')
    return redirect('login')


# Farmer pages

@methods('GET')
@role_required('farmer')
def farmer_dashboard(request):
    user = request.user
    total_reports = SymptomReport.objects.filter(farmer=user).count()
    pending_predictions = SymptomReport.objects.filter(farmer=user, status='pending').count()

    recent_predictions = list(
        Prediction.objects.filter(symptom_report__farmer=user).order_by('-predicted_at')[:5]
    )
    notifications = list(
        Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10]
    )

    return render_page(request, 'farmer/dashboard.html',
                       total_reports=total_reports,
                       pending_predictions=pending_predictions,
                       recent_predictions=recent_predictions,
                       notifications=notifications,
                       notification_senders=build_sender_lookup(notifications),
                       assigned_vets=list(user.assigned_veterinarians))


@methods('GET')
@role_required('farmer')
def farmer_notifications(request):
    active_filter = request.GET.get('filter', 'all')
    base_query = Notification.objects.filter(user=request.user)

    if active_filter == 'unread':
        base_query = base_query.filter(is_read=False)
    elif active_filter == 'meeting':
        base_query = base_query.filter(notification_type='meeting')
    else:
        active_filter = 'all'

    notifications = list(base_query.order_by('-created_at'))
    all_notifications = list(Notification.objects.filter(user=request.user))

    return render_page(
        request, 'farmer/notifications.html',
        notifications=notifications,
        notification_senders=build_sender_lookup(notifications),
        unread_count=sum(1 for note in all_notifications if not note.is_read),
        total_notifications=len(all_notifications),
        meetings_count=sum(1 for note in all_notifications if note.notification_type == 'meeting'),
        active_filter=active_filter,
    )


@methods('GET')
@role_required('farmer')
def farmer_notification_detail(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    if notification.user_id != request.user.id:
        raise PermissionDenied

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    sender = User.objects.filter(pk=notification.sender_id).first() if notification.sender_id else None
    return render_page(request, 'farmer/notification_detail.html', notification=notification, sender=sender)


@methods('POST')
@role_required('farmer')
def mark_farmer_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    flash(request, _('All notifications have been marked as read.'), 'success')
    return redirect('farmer_notifications')


@methods('POST')
@role_required('farmer')
def contact_vet(request):
    user = request.user
    assigned_vets = list(user.assigned_veterinarians)
    if not assigned_vets:
        flash(request, _('You do not have an assigned veterinarian yet.'), 'warning')
        return redirect('farmer_dashboard')

    subject = (request.POST.get('subject') or '').strip()
    message = (request.POST.get('message') or '').strip()
    if not message:
        flash(request, _('Please enter a message for your veterinarian.'), 'danger')
        return redirect('farmer_dashboard')

    title = subject[:200] if subject else _('Message from %(name)s') % {'name': user.full_name or user.username}
    for vet in assigned_vets:
        create_notification(vet.id, 'message', title, message, 'high', sender_id=user.id)

    log_system_event(request, 'info', 'notification',
                     f'Farmer {user.username} contacted assigned veterinarian(s)', user.id,
                     {'recipient_count': len(assigned_vets)})
    flash(request, _('Your message has been sent to your assigned veterinarian.'), 'success')
    return redirect('farmer_dashboard')


@methods('GET', 'POST')
@role_required('farmer')
def symptom_form(request):
    user = request.user
    form = SymptomForm(request)
    if form.validate_on_submit():
        animal_type = form.value('animal_type')
        if animal_type not in SUPPORTED_ANIMAL_TYPES:
            flash(request, _('Only cattle and goat cases are supported for prediction.'), 'danger')
            return render_page(request, 'farmer/symptom_form.html', form=form)

        selected_symptoms = request.POST.getlist('symptoms')
        animal_label = animal_type.replace('_', ' ').title()

        report = create_with_record_id(
            SymptomReport, 'report_id', 'R',
            farmer=user,
            animal_name=f'{animal_label} case',
            animal_type=animal_type,
            animal_sex=form.value('animal_sex'),
            animal_age=form.value('animal_age'),
            animal_weight=form.value('animal_weight'),
            animal_breed=None,
            appetite=form.value('appetite'),
            temperature=form.value('temperature'),
            rumen_movement=form.value('rumen_movement'),
            stool_consistency=form.value('stool_consistency'),
            milk_production=form.value('milk_production'),
            additional_symptoms=json.dumps(list(selected_symptoms)),
            feed_type=form.value('feed_type'),
            feed_changes=form.value('feed_changes'),
            housing_conditions=form.value('housing_conditions'),
            recent_treatments=form.value('recent_treatments'),
            status='pending',
        )
        # The case id doubles as the animal id.
        report.animal_id = report.report_id
        report.save(update_fields=['animal_id'])

        try:
            with transaction.atomic():
                prediction = create_prediction(report)
        except Exception as exc:
            logger.exception('Model prediction failed for report %s', report.report_id)
            log_system_event(request, 'error', 'model', f'Model prediction failed for report {report.report_id}', user.id,
                             {'report_id': report.report_id, 'animal_type': report.animal_type, 'error': str(exc)})
            flash(request, _('Symptoms were saved, but the trained model could not generate a prediction. '
                             'Please contact the administrator.'), 'danger')
            return redirect('symptom_history')

        create_notification(
            user.id, 'prediction', _('New Prediction Generated'),
            _('Prediction for %(animal_name)s: %(disease_name)s with %(confidence).1f%% confidence') % {
                'animal_name': report.animal_name, 'disease_name': prediction.disease_name,
                'confidence': prediction.confidence * 100},
            'medium', prediction.id)

        for vet in user.assigned_veterinarians:
            create_notification(
                vet.id, 'review', _('New Prediction Requires Review'),
                _('Prediction for %(animal_name)s needs your review') % {'animal_name': report.animal_name},
                'high', prediction.id)

        log_system_event(request, 'info', 'prediction', f'New symptom report submitted: {report.report_id}', user.id)
        flash(request, _('Symptoms submitted successfully! Prediction generated.'), 'success')
        return redirect('farmer_predictions')

    return render_page(request, 'farmer/symptom_form.html', form=form)


@methods('GET')
@role_required('farmer')
def symptom_history(request):
    page = int_arg(request.GET, 'page', 1)
    per_page = 10
    if page < 1:
        raise Http404

    reports = list(
        SymptomReport.objects.filter(farmer=request.user).order_by('-created_at')[(page - 1) * per_page:page * per_page]
    )
    if not reports and page != 1:
        raise Http404

    # One prediction per report in this system
    reports_with_prediction = [(report, report.prediction) for report in reports]
    return render_page(request, 'farmer/symptom_history.html',
                       reports=reports_with_prediction, page=page, per_page=per_page)


@methods('GET')
@role_required('farmer')
def farmer_predictions(request):
    predictions = list(
        Prediction.objects.filter(symptom_report__farmer=request.user).order_by('-predicted_at')
    )
    return render_page(request, 'farmer/predictions.html', predictions=predictions)


def can_access_prediction(user, prediction):
    """The owner farmer, an assigned vet, or any admin may view a prediction."""
    if user.id == prediction.user_id:
        return True
    if user.role in ('organization_admin', 'system_admin'):
        return True
    if user.role == 'veterinarian':
        return is_assigned(user, prediction.symptom_report.farmer_id)
    return False


@methods('GET')
@login_required
def prediction_detail(request, prediction_id):
    prediction = get_object_or_404(Prediction, pk=prediction_id)
    if not can_access_prediction(request.user, prediction):
        raise PermissionDenied
    return render_page(request, 'farmer/prediction_detail.html',
                       prediction=prediction,
                       report=prediction.symptom_report,
                       possible_diseases=prediction.get_possible_diseases())


@methods('GET')
@login_required
def prediction_pdf(request, prediction_id):
    prediction = get_object_or_404(Prediction, pk=prediction_id)
    if not can_access_prediction(request.user, prediction):
        raise PermissionDenied
    if not PDF_AVAILABLE:
        flash(request, 'PDF export is unavailable: install reportlab and matplotlib.', 'danger')
        return redirect('prediction_detail', prediction_id=prediction_id)

    buf = pdf_utils.build_prediction_pdf(
        prediction, prediction.symptom_report, prediction.get_possible_diseases(),
        malawi_now().strftime('%Y-%m-%d %H:%M'))
    filename = 'prediction_%s.pdf' % (prediction.prediction_id or prediction.id)
    return FileResponse(buf, as_attachment=True, filename=filename, content_type='application/pdf')


def _save_profile(user, form, fields):
    for field in fields:
        setattr(user, field, form.value(field))
    user.save()
    auto_assign_by_location(user)


def _email_taken(form, user):
    return User.objects.filter(email=form.value('email')).exclude(pk=user.pk).exists()


@methods('GET', 'POST')
@role_required('farmer')
def farmer_registration(request):
    user = request.user
    form = ProfileForm(request, instance=user)
    if form.validate_on_submit():
        if _email_taken(form, user):
            flash(request, _('That email address is already in use by another account.'), 'danger')
            return render_page(request, 'farmer/registration.html', form=form)

        _save_profile(user, form, ['full_name', 'email', 'phone', 'farm_name', 'location',
                                   'specific_location', 'animal_types', 'production_focus'])
        flash(request, _('Profile updated successfully!'), 'success')
        return redirect('farmer_registration')

    return render_page(request, 'farmer/registration.html', form=form)


# Veterinarian pages

def pending_review_predictions(vet):
    farmer_ids = list(vet.assigned_farmers.values_list('id', flat=True))
    return Prediction.objects.filter(
        symptom_report__status='predicted',
        review_status='pending',
        symptom_report__farmer_id__in=farmer_ids or [-1],
    )


ACTIVE_TREATMENT_STATUSES = ['prescribed', 'in_progress']


def active_treatments(vet):
    """Treatment plans the vet has given that are under way (a plan saved on
    the "Add Treatment" page is 'prescribed'; an approved placeholder is 'in_progress')."""
    return Treatment.objects.filter(vet=vet, status__in=ACTIVE_TREATMENT_STATUSES)


def can_treat(vet, report):
    """A vet may only act on cases of farmers assigned to them."""
    return is_assigned(vet, report.farmer_id)


@methods('GET')
@role_required('veterinarian')
def vet_dashboard(request):
    vet = request.user
    assigned_farmer_list = list(vet.assigned_farmers)
    farmer_messages = list(
        Notification.objects.filter(user=vet, notification_type='message').order_by('-created_at')[:8]
    )

    return render_page(request, 'veterinarian/dashboard.html',
                       assigned_farmers=len(assigned_farmer_list),
                       assigned_farmer_list=assigned_farmer_list,
                       pending_reviews=pending_review_predictions(vet).count(),
                       active_treatments=active_treatments(vet).count(),
                       recent_mortality=list(MortalityReport.objects.filter(vet=vet).order_by('-created_at')[:5]),
                       farmer_messages=farmer_messages,
                       message_senders=build_sender_lookup(farmer_messages),
                       sent_alerts_count=Notification.objects.filter(sender=vet, notification_type='alert').count(),
                       scheduled_meetings_count=Notification.objects.filter(sender=vet, notification_type='meeting').count())


@methods('GET')
@role_required('veterinarian')
def vet_communications(request):
    vet = request.user
    incoming_messages = list(Notification.objects.filter(user=vet, notification_type='message').order_by('-created_at'))
    sent_alerts = list(Notification.objects.filter(sender=vet, notification_type='alert').order_by('-created_at'))
    scheduled_meetings = list(Notification.objects.filter(sender=vet, notification_type='meeting').order_by('-created_at'))

    return render_page(
        request, 'veterinarian/communications.html',
        incoming_messages=incoming_messages,
        sent_alerts=sent_alerts,
        scheduled_meetings=scheduled_meetings,
        message_senders=build_sender_lookup(incoming_messages),
        alert_recipients=build_recipient_lookup(sent_alerts),
        meeting_recipients=build_recipient_lookup(scheduled_meetings),
    )


@methods('POST')
@role_required('veterinarian')
def send_farmer_alert(request):
    vet = request.user
    assigned_farmer_list = list(vet.assigned_farmers)
    if not assigned_farmer_list:
        flash(request, 'You do not have any assigned farmers to alert yet.', 'warning')
        return redirect('vet_dashboard')

    subject = (request.POST.get('subject') or '').strip()
    message = (request.POST.get('message') or '').strip()
    priority = (request.POST.get('priority') or 'medium').strip().lower()
    if priority not in {'low', 'medium', 'high', 'critical'}:
        priority = 'medium'

    if not message:
        flash(request, 'Please enter an alert message before sending.', 'danger')
        return redirect('vet_dashboard')

    title = subject[:200] if subject else f'Farmer Alert from {vet.full_name or vet.username}'
    for farmer in assigned_farmer_list:
        create_notification(farmer.id, 'alert', title, message, priority, sender_id=vet.id)

    log_system_event(request, 'info', 'notification',
                     f'Veterinarian {vet.username} sent a farmer alert broadcast', vet.id,
                     {'recipient_count': len(assigned_farmer_list), 'priority': priority})
    flash(request, f'Alert sent to {len(assigned_farmer_list)} assigned farmer(s).', 'success')
    return redirect('vet_dashboard')


@methods('POST')
@role_required('veterinarian')
def schedule_farmer_meeting(request):
    vet = request.user
    assigned_farmer_map = {str(farmer.id): farmer for farmer in vet.assigned_farmers}
    if not assigned_farmer_map:
        flash(request, 'You do not have any assigned farmers to schedule yet.', 'warning')
        return redirect('vet_dashboard')

    farmer_id = (request.POST.get('farmer_id') or '').strip()
    title = (request.POST.get('title') or '').strip()
    meeting_date = (request.POST.get('meeting_date') or '').strip()
    meeting_time = (request.POST.get('meeting_time') or '').strip()
    location = (request.POST.get('location') or '').strip()
    notes = (request.POST.get('notes') or '').strip()

    farmer = assigned_farmer_map.get(farmer_id)
    if farmer is None:
        flash(request, 'Please select one of your assigned farmers.', 'danger')
        return redirect('vet_dashboard')

    if not meeting_date or not meeting_time or not location:
        flash(request, 'Meeting date, time, and location are required.', 'danger')
        return redirect('vet_dashboard')

    meeting_title = title[:200] if title else 'Veterinary meeting scheduled'
    meeting_message = f'Your veterinarian scheduled a meeting on {meeting_date} at {meeting_time} for {location}.'
    if notes:
        meeting_message += f' Notes: {notes}'

    create_notification(farmer.id, 'meeting', meeting_title, meeting_message, 'high', sender_id=vet.id)

    log_system_event(request, 'info', 'notification',
                     f'Veterinarian {vet.username} scheduled a meeting with {farmer.username}', vet.id,
                     {'farmer_id': farmer.id, 'meeting_date': meeting_date, 'meeting_time': meeting_time})
    flash(request, f'Meeting scheduled for {farmer.full_name or farmer.username}.', 'success')
    return redirect('vet_communications')


@methods('GET', 'POST')
@role_required('veterinarian')
def vet_profile(request):
    vet = request.user
    form = ProfileForm(request, instance=vet)

    if form.validate_on_submit():
        if _email_taken(form, vet):
            flash(request, _('That email address is already in use by another account.'), 'danger')
        else:
            _save_profile(vet, form, ['full_name', 'email', 'phone', 'location', 'specific_location'])
            flash(request, _('Profile updated successfully!'), 'success')
            return redirect('vet_profile')

    return render_page(
        request, 'veterinarian/profile.html',
        form=form,
        assigned_farmers_count=vet.assigned_farmers.count(),
        pending_reviews=pending_review_predictions(vet).count(),
        active_treatments=active_treatments(vet).count(),
        mortality_reports_count=MortalityReport.objects.filter(vet=vet).count(),
    )


@methods('GET')
@role_required('veterinarian')
def farmer_mapping(request):
    return render_page(request, 'veterinarian/farmer_mapping.html',
                       assigned_farmers=list(request.user.assigned_farmers))


@methods('GET')
@role_required('veterinarian')
def predictions_review(request):
    f_severity = request.GET.get('severity', 'all')
    f_animal = request.GET.get('animal_type', 'all')
    f_confidence = request.GET.get('confidence', 'all')

    pending = pending_review_predictions(request.user)
    if f_severity != 'all':
        pending = pending.filter(severity=f_severity)
    if f_animal != 'all':
        pending = pending.filter(symptom_report__animal_type=f_animal)
    if f_confidence == 'high':
        pending = pending.filter(confidence__gte=0.9)
    elif f_confidence == 'medium':
        pending = pending.filter(confidence__gte=0.7, confidence__lt=0.9)
    elif f_confidence == 'low':
        pending = pending.filter(confidence__lt=0.7)

    reviewed = Prediction.objects.filter(
        review_status__in=['confirmed', 'modified'], reviewed_by=request.user,
    ).order_by('-reviewed_at')[:10]

    return render_page(request, 'veterinarian/prediction_review.html',
                       pending_predictions=list(pending.order_by('-predicted_at')),
                       reviewed_predictions=list(reviewed),
                       f_severity=f_severity,
                       f_animal=f_animal,
                       f_confidence=f_confidence)


def _apply_treatment_form(treatment, form):
    treatment.medication = form.value('medication')
    treatment.medication_type = form.value('medication_type')
    treatment.dosage = form.value('dosage')
    treatment.dosage_per_kg = form.value('dosage_per_kg')
    treatment.frequency = form.value('frequency')
    duration = form.value('duration')
    treatment.duration = str(duration) if duration is not None else None
    treatment.route = form.value('route')
    treatment.supportive_care = form.value('supportive_care')
    treatment.diet_recommendations = form.value('diet_recommendations')
    treatment.follow_up_required = form.value('follow_up_required')
    treatment.follow_up_date = form.value('follow_up_date')
    treatment.milk_withdrawal_days = form.value('milk_withdrawal_days')
    treatment.meat_withdrawal_days = form.value('meat_withdrawal_days')


def case_choices(vet):
    """The vet's cases (predictions of assigned farmers), newest first, for a select."""
    predictions = (Prediction.objects
                   .filter(symptom_report__farmer__in=vet.assigned_farmers)
                   .select_related('symptom_report__farmer').order_by('-predicted_at'))
    return [
        (str(p.id), f'{p.symptom_report.report_id} - '
                    f'{p.symptom_report.farmer.full_name or p.symptom_report.farmer.username} - '
                    f'{p.symptom_report.animal_name} ({p.disease_name})')
        for p in predictions
    ]


def save_treatment(request, vet, prediction, form):
    """Save the form as the case's treatment plan (updating a placeholder from
    "Confirm"), confirm the prediction and tell the farmer."""
    report = prediction.symptom_report
    with transaction.atomic():
        treatment = report.treatment
        if treatment is None:
            treatment = Treatment(symptom_report=report,
                                  treatment_id=next_record_id(Treatment, 'treatment_id', 'T'))
        treatment.vet = vet
        _apply_treatment_form(treatment, form)
        treatment.status = 'prescribed'
        treatment.save()
        # Issuing a treatment confirms the prediction.
        if prediction.review_status == 'pending':
            prediction.review_status = 'confirmed'
            prediction.reviewed_by = vet
            prediction.reviewed_at = malawi_now()
            prediction.save()
        report.status = 'reviewed'
        report.save()

    create_notification(
        report.farmer_id, 'treatment', 'Treatment Recommendation Available',
        f'Your veterinarian added a treatment plan for {report.animal_name} ({prediction.disease_name}).',
        'high', treatment.id)
    log_system_event(request, 'info', 'treatment', f'Treatment recommendation saved for {report.report_id}', vet.id)
    return treatment


@methods('GET', 'POST')
@role_required('veterinarian')
def treatment_suggestions(request):
    vet = request.user
    form = NewTreatmentForm(request, case_choices(vet))

    if form.validate_on_submit():
        prediction = get_object_or_404(Prediction, pk=form.value('case'))
        if not can_treat(vet, prediction.symptom_report):
            raise PermissionDenied
        save_treatment(request, vet, prediction, form)
        flash(request, 'Treatment plan created successfully!', 'success')
        return redirect('treatment_suggestions')

    return render_page(request, 'veterinarian/treatment_suggestions.html',
                       form=form,
                       pending_treatments=list(Treatment.objects.filter(vet=vet, status='pending_approval')),
                       active_treatments=list(active_treatments(vet)))


@methods('GET', 'POST')
@role_required('veterinarian')
def add_treatment(request, prediction_id):
    vet = request.user
    prediction = get_object_or_404(Prediction, pk=prediction_id)
    report = prediction.symptom_report
    if not can_treat(vet, report):
        raise PermissionDenied

    existing = report.treatment  # may be None, or a placeholder from "confirm"
    form = TreatmentForm(request, instance=existing if request.method == 'GET' else None)

    if form.validate_on_submit():
        save_treatment(request, vet, prediction, form)
        flash(request, 'Treatment recommendation saved and shared with the farmer.', 'success')
        return redirect('predictions_review')

    return render_page(request, 'veterinarian/add_treatment.html',
                       form=form, prediction=prediction, report=report, existing=existing,
                       possible_diseases=prediction.get_possible_diseases())


@methods('GET', 'POST')
@role_required('veterinarian')
def mortality_reports(request):
    vet = request.user
    farmers = [(str(farmer.id), farmer.full_name or farmer.username) for farmer in vet.assigned_farmers]
    form = MortalityReportForm(request, farmers)

    if form.validate_on_submit():
        report = create_with_record_id(
            MortalityReport, 'report_id', 'M',
            farmer=vet.assigned_farmers.get(pk=form.value('farmer')),
            vet=vet,
            animal_type=form.value('animal_type'),
            age=form.value('age'),
            date_of_death=form.value('date_of_death'),
            suspected_cause=form.value('suspected_cause'),
            last_milk_production=form.value('last_milk_production'),
            symptoms_before_death=form.value('symptoms_before_death'),
            was_dairy=form.value('was_dairy'),
            requires_investigation=form.value('requires_investigation'),
            investigation_notes=form.value('additional_notes'),
            lab_results=form.value('lab_results'),
        )

        log_system_event(request, 'info', 'mortality', f'Mortality report created: {report.report_id}', vet.id)
        flash(request, 'Mortality report submitted successfully!', 'success')
        return redirect('mortality_reports')

    return render_page(request, 'veterinarian/mortality_reports.html',
                       form=form,
                       recent_reports=list(MortalityReport.objects.filter(vet=vet).order_by('-created_at')[:10]),
                       monthly_count=MortalityReport.objects.filter(
                           vet=vet, created_at__gte=malawi_now() - timedelta(days=30)).count())


# Organization admin pages

@methods('GET')
@role_required('organization_admin')
def org_admin_dashboard(request):
    # Model accuracy: the production model's recorded accuracy, otherwise the
    # average confidence of generated predictions.
    production_model = ModelVersion.objects.filter(status='production').order_by('-id').first()
    if production_model and production_model.accuracy:
        system_accuracy = production_model.accuracy
    else:
        avg_conf = Prediction.objects.aggregate(value=Avg('confidence'))['value']
        system_accuracy = float(avg_conf) if avg_conf else None

    # Farmers per location
    location_counts = (User.objects.filter(role='farmer')
                       .values('location').annotate(count=Count('id')).order_by())

    return render_page(request, 'organization_admin/dashboard.html',
                       total_farmers=User.objects.filter(role='farmer').count(),
                       total_veterinarians=User.objects.filter(role='veterinarian').count(),
                       active_predictions=SymptomReport.objects.filter(status='predicted').count(),
                       system_accuracy=system_accuracy,
                       recent_logs=list(SystemLog.objects.order_by('-timestamp')[:10]),
                       location_labels=[row['location'] or 'Unknown' for row in location_counts],
                       location_values=[row['count'] for row in location_counts])


@methods('GET')
@role_required('organization_admin')
def org_admin_profile(request):
    return render_page(request, 'organization_admin/my_profile.html')


@methods('GET')
@role_required('organization_admin')
def org_admin_users(request):
    users = list(User.objects.order_by('-registration_date'))
    users_by_status = {
        'pending': [user for user in users if user.status == 'pending'],
        'approved': [user for user in users if user.status == 'approved'],
        'rejected': [user for user in users if user.status == 'rejected'],
    }
    return render_page(request, 'organization_admin/user_management.html',
                       users_by_status=users_by_status,
                       total_users=len(users),
                       active_users=sum(1 for user in users if user.is_active),
                       admin_users=sum(1 for user in users if user.role in ['organization_admin', 'system_admin']))


@methods('POST')
@role_required('organization_admin')
def approve_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_organization_admin() or user.is_system_admin():
        flash(request, 'Administrator accounts cannot be approved from this panel.', 'warning')
        return redirect('org_admin_users')

    user.status = 'approved'
    user.approved_at = malawi_now()
    user.rejected_at = None
    user.save()
    auto_assign_by_location(user)

    send_approval_email(user.email)
    log_system_event(request, 'info', 'auth', f'User approved: {user.username}', request.user.id)
    flash(request, f'{user.username} approved successfully.', 'success')
    return redirect('org_admin_users')


@methods('POST')
@role_required('organization_admin')
def reject_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_organization_admin() or user.is_system_admin():
        flash(request, 'Administrator accounts cannot be rejected from this panel.', 'warning')
        return redirect('org_admin_users')

    user.status = 'rejected'
    user.rejected_at = malawi_now()
    user.approved_at = None
    user.save()
    auto_assign_by_location(user)  # a rejected user loses their farmer/vet links

    send_rejection_email(user.email)
    log_system_event(request, 'info', 'auth', f'User rejected: {user.username}', request.user.id)
    flash(request, f'{user.username} rejected successfully.', 'warning')
    return redirect('org_admin_users')


@methods('POST')
@role_required('organization_admin')
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if user.id == request.user.id:
        flash(request, 'You cannot delete your own account.', 'danger')
        return redirect('org_admin_users')
    if user.is_system_admin():
        flash(request, 'System administrator accounts cannot be deleted from this panel.', 'warning')
        return redirect('org_admin_users')

    username = user.username
    try:
        with transaction.atomic():
            FarmerVeterinarian.objects.filter(Q(farmer=user) | Q(veterinarian=user)).delete()
            user.delete()
    except (ProtectedError, RestrictedError, DatabaseError):
        flash(request, 'This user could not be deleted because related records still exist.', 'danger')
        return redirect('org_admin_users')

    log_system_event(request, 'warning', 'auth', f'User deleted: {username}', request.user.id)
    flash(request, f'{username} deleted successfully.', 'success')
    return redirect('org_admin_users')


def date_bucket(field, weekly=False):
    """SQL expression turning a datetime into a day ('2026-10-25') or week
    ('2026-W43') label, for grouping. SQLite and PostgreSQL format dates differently."""
    if connection.vendor == 'postgresql':
        return Func(F(field), Value('IYYY-"W"IW' if weekly else 'YYYY-MM-DD'),
                    function='to_char', output_field=CharField())
    return Func(Value('%Y-W%W' if weekly else '%Y-%m-%d'), F(field),
                function='strftime', output_field=CharField())


def compute_report_analytics(location='all', animal_type='all', days=30):
    """Filtered disease analytics shared by the reports page and its PDF export."""
    cutoff = malawi_now() - timedelta(days=days)

    predictions = Prediction.objects.filter(predicted_at__gte=cutoff)
    if location and location != 'all':
        predictions = predictions.filter(symptom_report__farmer__location=location)
    if animal_type and animal_type != 'all':
        predictions = predictions.filter(symptom_report__animal_type=animal_type)

    # Most frequent diseases
    disease_distribution = (predictions.values('disease_name')
                            .annotate(count=Count('id')).order_by('-count', 'disease_name'))
    disease_rows = [(row['disease_name'] or 'Unknown disease', row['count']) for row in disease_distribution]

    # Dominant disease per location
    location_counts = (predictions.values('symptom_report__farmer__location', 'disease_name')
                       .annotate(count=Count('id')).order_by())
    dominant = {}
    for row in location_counts:
        loc, freq = row['symptom_report__farmer__location'], row['count']
        candidate = {'location': loc or 'Unknown', 'disease_name': row['disease_name'] or 'Unknown disease', 'frequency': freq}
        current = dominant.get(loc)
        if current is None or freq > current['frequency'] or (
                freq == current['frequency'] and candidate['disease_name'] < current['disease_name']):
            dominant[loc] = candidate
    scope_locations = [location] if (location and location != 'all') else EPA_NAMES
    location_summary = [
        dominant.get(loc, {'location': loc, 'disease_name': 'No data yet', 'frequency': 0})
        for loc in scope_locations
    ]

    # Trend over time (daily buckets for short ranges, weekly otherwise)
    trend = (predictions.annotate(bucket=date_bucket('predicted_at', weekly=days > 14))
             .values('bucket').annotate(count=Count('id')).order_by('bucket'))
    trend = [row for row in trend if row['bucket']]

    return {
        'disease_rows': disease_rows,
        'disease_labels': [name for name, _count in disease_rows],
        'disease_values': [count for _name, count in disease_rows],
        'location_summary': location_summary,
        'trend_labels': [row['bucket'] for row in trend],
        'trend_values': [row['count'] for row in trend],
        'location_options': list(EPA_NAMES),
    }


def build_vet_summary():
    summary = []
    for vet in User.objects.filter(role='veterinarian').order_by('full_name'):
        summary.append({
            'full_name': vet.full_name or vet.username,
            'service_location': vet.location or vet.specific_location or 'Location not set',
            'status': vet.status or 'unknown',
            'reviewed_predictions_count': Prediction.objects.filter(
                reviewed_by=vet, review_status__in=['confirmed', 'modified']).count(),
            'assigned_farmers_count': vet.assigned_farmers.count(),
        })
    summary.sort(key=lambda item: (-item['reviewed_predictions_count'], -item['assigned_farmers_count'],
                                   item['full_name'].lower()))
    return summary


def report_filters(request):
    days = int_arg(request.GET, 'days', 30)
    if days not in REPORT_DAY_OPTIONS:
        days = 30
    return request.GET.get('location', 'all'), request.GET.get('animal_type', 'all'), days


@methods('GET', 'POST')
@role_required('organization_admin')
def org_reports(request):
    form = ReportGenerationForm(request)

    if form.validate_on_submit():
        frequency = form.value('schedule_frequency')
        report = create_with_record_id(
            Report, 'report_id', 'REP',
            report_type=form.value('report_type'),
            period_start=form.value('period_start'),
            period_end=form.value('period_end'),
            generated_by=request.user,
            is_scheduled=frequency != 'once',
            schedule_frequency=frequency if frequency != 'once' else None,
        )
        flash(request, f'Report {report.report_id} generation started!', 'success')
        return redirect('org_reports')

    f_location, f_animal, f_days = report_filters(request)
    analytics = compute_report_analytics(f_location, f_animal, f_days)

    return render_page(request, 'organization_admin/reports.html',
                       form=form,
                       reports=list(Report.objects.order_by('-generated_at')[:20]),
                       disease_labels=analytics['disease_labels'],
                       disease_values=analytics['disease_values'],
                       disease_rows=analytics['disease_rows'],
                       location_disease_summary=analytics['location_summary'],
                       trend_labels=analytics['trend_labels'],
                       trend_values=analytics['trend_values'],
                       veterinarian_summary=build_vet_summary(),
                       location_options=analytics['location_options'],
                       f_location=f_location,
                       f_animal=f_animal,
                       f_days=f_days)


@methods('GET')
@role_required('organization_admin')
def org_reports_pdf(request):
    if not PDF_AVAILABLE:
        flash(request, 'PDF export is unavailable: install reportlab and matplotlib.', 'danger')
        return redirect('org_reports')

    f_location, f_animal, f_days = report_filters(request)
    analytics = compute_report_analytics(f_location, f_animal, f_days)
    generated_on = malawi_now().strftime('%Y-%m-%d %H:%M')
    meta = {
        'title': 'Disease Analytics Report',
        'subtitle': 'Generated %s' % generated_on,
        'filters': [
            ('Location', f_location if f_location != 'all' else 'All blocks'),
            ('Animal type', f_animal.capitalize() if f_animal != 'all' else 'All species'),
            ('Period', 'Last %d days' % f_days),
        ],
    }
    buf = pdf_utils.build_reports_pdf(
        meta, analytics['disease_rows'], analytics['location_summary'], build_vet_summary(),
        trend_labels=analytics['trend_labels'], trend_values=analytics['trend_values'],
        generated_on=generated_on)
    filename = 'disease_analytics_%s.pdf' % malawi_now().strftime('%Y%m%d_%H%M')
    return FileResponse(buf, as_attachment=True, filename=filename, content_type='application/pdf')


# System admin pages

def host_usage(as_fraction=False):
    """CPU, memory and disk use of the server (None if psutil is missing)."""
    try:
        import psutil
        values = (psutil.cpu_percent(interval=0.3), psutil.virtual_memory().percent,
                  psutil.disk_usage(str(Path(settings.BASE_DIR))).percent)
    except Exception:
        return None, None, None
    return tuple(value / 100.0 for value in values) if as_fraction else values


@methods('GET')
@role_required('system_admin')
def sys_admin_dashboard(request):
    day_ago = malawi_now() - timedelta(days=1)
    recent_logs = SystemLog.objects.filter(timestamp__gte=day_ago)
    errors = recent_logs.filter(level__in=['error', 'critical'])

    # "Requests" = logged system events in the last 24h; uptime = share that were not errors.
    logs_last_day = recent_logs.count()
    error_logs_last_day = errors.count()
    uptime = (1 - (error_logs_last_day / logs_last_day)) if logs_last_day else 1.0

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        database_status = 'running'
    except Exception:
        database_status = 'down'
    prediction_status = 'running' if MODEL_PATH.exists() and FEATURE_ENCODING_PATH.exists() else 'down'

    cpu_usage, memory_usage, disk_usage = host_usage()
    return render_page(request, 'system_admin/dashboard.html',
                       uptime=uptime,
                       active_users=User.objects.filter(last_login__gte=malawi_now() - timedelta(hours=1)).count(),
                       api_requests=logs_last_day,
                       system_alerts=list(errors.order_by('-timestamp')[:5]),
                       component_status={
                           'web_server': 'running',
                           'database': database_status,
                           'prediction_engine': prediction_status,
                       },
                       cpu_usage=cpu_usage,
                       memory_usage=memory_usage,
                       disk_usage=disk_usage)


LOG_TIME_RANGES = {
    '1h': timedelta(hours=1),
    '24h': timedelta(days=1),
    '7d': timedelta(days=7),
    '30d': timedelta(days=30),
}


@methods('GET')
@role_required('system_admin')
def system_logs(request):
    level = request.GET.get('level', 'all')
    component = request.GET.get('component', 'all')
    time_range = request.GET.get('time_range', '24h')

    query = SystemLog.objects.filter(
        timestamp__gte=malawi_now() - LOG_TIME_RANGES.get(time_range, timedelta(days=1)))
    if level != 'all':
        query = query.filter(level=level)
    if component != 'all':
        query = query.filter(component=component)

    logs = list(query.order_by('-timestamp')[:100])
    return render_page(request, 'system_admin/system_logs.html',
                       logs=logs,
                       total_logs=len(logs),
                       error_count=len([log for log in logs if log.level == 'error']),
                       warning_count=len([log for log in logs if log.level == 'warning']),
                       current_level=level,
                       current_component=component,
                       current_time_range=time_range)


@methods('GET')
@role_required('system_admin')
def performance_reports(request):
    day_ago = malawi_now() - timedelta(days=1)
    recent_logs = SystemLog.objects.filter(timestamp__gte=day_ago)
    total_logs = recent_logs.count()
    error_logs = recent_logs.filter(level__in=['error', 'critical']).count()
    error_rate = (error_logs / total_logs) if total_logs else 0.0

    cpu_usage, memory_usage, disk_usage = host_usage(as_fraction=True)
    metrics = {
        'response_time': None,  # no request timing is recorded
        'error_rate': error_rate,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage,
        'api_success_rate': 1 - error_rate,
    }

    # Activity by logged component over the last 24h.
    component_rows = recent_logs.values('component').annotate(
        count=Count('id'),
        errors=Sum(Case(When(level__in=['error', 'critical'], then=1), default=0, output_field=IntegerField())),
    ).order_by()
    api_performance = [
        {
            'endpoint': row['component'] or 'unknown',
            'avg_response': None,
            'success_rate': (1 - (row['errors'] or 0) / row['count']) if row['count'] else 1.0,
            'requests': row['count'],
        }
        for row in component_rows
    ]

    return render_page(request, 'system_admin/performance_report.html',
                       metrics=metrics, api_performance=api_performance)


@methods('GET')
@role_required('system_admin')
def model_updates(request):
    available_updates = [
        {
            'id': mv.version,
            'version': mv.version,
            'type': mv.algorithm or 'model',
            'size': mv.training_data_size,
            'status': mv.status or 'unknown',
            'accuracy': mv.accuracy,
            'deployment_date': mv.deployment_date,
        }
        for mv in ModelVersion.objects.order_by('-id')
    ]
    return render_page(request, 'system_admin/model_updates.html',
                       available_updates=available_updates, deployment_schedule=[])


# Actions posted by the veterinarian pages

def _is_json(request):
    content_type = request.content_type or ''
    return content_type == 'application/json' or content_type.endswith('+json')


@methods('POST')
@role_required('veterinarian')
def review_prediction(request, prediction_id):
    vet = request.user
    prediction = get_object_or_404(Prediction, pk=prediction_id)
    report = prediction.symptom_report
    if not can_treat(vet, report):
        raise PermissionDenied

    payload = None
    if _is_json(request):
        try:
            payload = json.loads(request.body or b'null')
        except ValueError:
            payload = None
    if not isinstance(payload, dict) or not payload:
        payload = request.POST
    action = payload.get('action')
    notes = payload.get('notes', '')
    new_diagnosis = (payload.get('diagnosis') or '').strip()

    if action == 'confirm':
        with transaction.atomic():
            prediction.review_status = 'confirmed'
            prediction.review_notes = notes
            prediction.reviewed_by = vet
            prediction.reviewed_at = malawi_now()
            prediction.save()

            # A placeholder treatment, only if the vet has not added one yet
            # (a detailed plan can be added via "Add Treatment").
            treatment = report.treatment
            # A new placeholder is not linked from the farmer's notification.
            linked_treatment_id = treatment.id if treatment else None
            if treatment is None:
                treatment = create_with_record_id(
                    Treatment, 'treatment_id', 'T',
                    symptom_report=report,
                    vet=vet,
                    medication='To be prescribed',
                    dosage='As advised',
                    frequency='As advised',
                    duration='As advised',
                    route='oral',
                    status='pending_approval',
                )
            report.status = 'reviewed'
            report.save()

        create_notification(report.farmer_id, 'treatment', 'Treatment Plan Available',
                            f'Treatment plan available for {report.animal_name}', 'medium', linked_treatment_id)
        flash(request, 'Prediction confirmed and treatment plan created!', 'success')

    elif action == 'modify':
        prediction.review_status = 'modified'
        prediction.review_notes = notes
        if new_diagnosis:
            prediction.disease_name = new_diagnosis
            prediction.disease_category = categorize_disease(new_diagnosis)
        prediction.reviewed_by = vet
        prediction.reviewed_at = malawi_now()
        with transaction.atomic():
            prediction.save()
            report.status = 'reviewed'
            report.save()

        # Tell the farmer about the vet's revised diagnosis
        create_notification(
            report.farmer_id, 'review', 'Diagnosis Updated by Veterinarian',
            f'Your veterinarian updated the diagnosis for {report.animal_name} to {prediction.disease_name}',
            'medium', prediction.id)
        flash(request, 'Prediction modified successfully!', 'success')
    else:
        flash(request, 'Unknown review action.', 'danger')
        if _is_json(request):
            return JsonResponse({'success': False, 'error': 'unknown action'}, status=400)
        return redirect('predictions_review')

    log_system_event(request, 'info', 'review', f'Prediction {prediction_id} reviewed by {vet.username}', vet.id)

    if _is_json(request):
        return JsonResponse({'success': True})
    return redirect('predictions_review')


@methods('POST')
@role_required('veterinarian')
def approve_treatment(request, treatment_id):
    treatment = get_object_or_404(Treatment, pk=treatment_id)
    report = treatment.symptom_report
    if not can_treat(request.user, report):
        raise PermissionDenied

    treatment.status = 'in_progress'
    treatment.start_date = malawi_now().date()
    treatment.save()

    create_notification(report.farmer_id, 'treatment', 'Treatment Approved',
                        f'Treatment for {report.animal_name} has been approved', 'medium', treatment.id)
    log_system_event(request, 'info', 'treatment',
                     f'Treatment {treatment_id} approved by {request.user.username}', request.user.id)
    if _is_json(request):
        return JsonResponse({'success': True})
    flash(request, 'Treatment approved and the farmer has been notified.', 'success')
    return redirect('treatment_suggestions')
