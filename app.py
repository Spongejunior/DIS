import os
import sys
import secrets
from pathlib import Path

PROJECT_VENDOR_PATH = os.path.join(os.path.dirname(__file__), '.vendor')
if os.path.isdir(PROJECT_VENDOR_PATH) and PROJECT_VENDOR_PATH not in sys.path:
    sys.path.insert(0, PROJECT_VENDOR_PATH)

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session, abort, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta, timezone
import json
from functools import lru_cache, wraps
from sqlalchemy import text, or_

def get_malawi_time():
    """Returns the current time in Malawi (UTC+2)"""
    return datetime.now(timezone(timedelta(hours=2)))

def ensure_malawi_datetime(value):
    if value is None:
        return None
    malawi_tz = timezone(timedelta(hours=2))
    if value.tzinfo is None:
        return value.replace(tzinfo=malawi_tz)
    return value.astimezone(malawi_tz)

from config import config
from models import db, User, SymptomReport, Prediction, Treatment, MortalityReport, SystemLog, PerformanceMetric, ModelVersion, Report, Notification, Configuration
from forms import LoginForm, ForgotPasswordForm, ResetPasswordForm, RegistrationForm, SymptomForm, TreatmentForm, MortalityReportForm, ProfileForm, ChangePasswordForm, ConfigurationForm, ReportGenerationForm
from mail_utils import mail, send_approval_email, send_rejection_email, send_password_reset_email

try:
    import pdf_utils
    PDF_AVAILABLE = True
except Exception:  # pragma: no cover - keeps the app usable if PDF deps are absent
    pdf_utils = None
    PDF_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config['development'])
config['development']().init_app(app)

# Initialize extensions
db.init_app(app)
mail.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

SUPPORTED_ANIMAL_TYPES = {'cattle', 'goat'}

# Mzimba North blocks used for farmer/vet registration and location-based analytics.
REGISTRATION_LOCATION_CHOICES = [
    ('', 'Select Blocks in Mzimba North'),
    ('Bwengu', 'Bwengu'),
    ('Emgucwini', 'Emgucwini'),
    ('Emsizini', 'Emsizini'),
    ('Euthini', 'Euthini'),
    ('Malidade', 'Malidade'),
    ('Mbalachanda', 'Mbalachanda'),
    ('Mpherembe', 'Mpherembe'),
    ('Mchengautuba', 'Mchengautuba'),
    ('Njuyu', 'Njuyu'),
    ('Zombwe', 'Zombwe'),
]
MODEL_DIRECTORY = Path(__file__).resolve().parent / 'model'
MODEL_PATH = MODEL_DIRECTORY / 'livestock_disease_model.pkl'
FEATURE_ENCODING_PATH = MODEL_DIRECTORY / 'feature_encoding.json'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Role-based access control decorator
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# Utility functions
def generate_report_id(prefix='R'):
    year = datetime.now().year
    count = SymptomReport.query.filter(
        SymptomReport.report_id.like(f'{prefix}-{year}-%')
    ).count() + 1
    return f'{prefix}-{year}-{count:03d}'

def generate_prediction_id():
    year = datetime.now().year
    count = Prediction.query.filter(
        Prediction.prediction_id.like(f'PRED-{year}-%')
    ).count() + 1
    return f'PRED-{year}-{count:03d}'

def generate_treatment_id():
    year = datetime.now().year
    count = Treatment.query.filter(
        Treatment.treatment_id.like(f'T-{year}-%')
    ).count() + 1
    return f'T-{year}-{count:03d}'

def generate_mortality_id():
    year = datetime.now().year
    count = MortalityReport.query.filter(
        MortalityReport.report_id.like(f'M-{year}-%')
    ).count() + 1
    return f'M-{year}-{count:03d}'

def get_assigned_farmers(user):
    assigned_farmers = user.assigned_farmers
    return assigned_farmers.all() if hasattr(assigned_farmers, 'all') else list(assigned_farmers)

def get_assigned_veterinarians(user):
    assigned_veterinarians = user.assigned_veterinarians
    return assigned_veterinarians.all() if hasattr(assigned_veterinarians, 'all') else list(assigned_veterinarians)

def auto_assign_by_location(user):
    normalized_location = (user.location or '').strip()
    if not normalized_location or not user.is_approved_user():
        return 0

    assignments_created = 0

    if user.is_farmer():
        existing_vet_ids = {vet.id for vet in get_assigned_veterinarians(user)}
        matching_vets = User.query.filter(
            User.role == 'veterinarian',
            User.status == 'approved',
            User.location == normalized_location
        ).order_by(User.id.asc()).all()

        for vet in matching_vets:
            if vet.id in existing_vet_ids:
                continue
            vet.assigned_farmers.append(user)
            assignments_created += 1

    elif user.is_veterinarian():
        existing_farmer_ids = {farmer.id for farmer in get_assigned_farmers(user)}
        matching_farmers = User.query.filter(
            User.role == 'farmer',
            User.status == 'approved',
            User.location == normalized_location
        ).order_by(User.id.asc()).all()

        for farmer in matching_farmers:
            if farmer.id in existing_farmer_ids:
                continue
            user.assigned_farmers.append(farmer)
            assignments_created += 1

    return assignments_created

def get_notification_action_url(notification_type, related_id=None):
    if not related_id:
        return None

    routes = {
        'prediction': 'farmer_predictions',
        'review': 'predictions_review',
        'treatment': 'treatment_suggestions',
        'mortality': 'mortality_reports',
        'alert': 'farmer_notifications',
        'meeting': 'farmer_notifications',
        'message': 'vet_communications'
    }
    endpoint = routes.get(notification_type)
    return url_for(endpoint) if endpoint else None


@lru_cache(maxsize=1)
def load_prediction_artifacts():
    try:
        import joblib
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            'Prediction dependencies are not installed. Add pandas, joblib, and the model runtime packages to run predictions.'
        ) from exc

    if not MODEL_PATH.exists():
        raise RuntimeError(f'Model file not found: {MODEL_PATH}')
    if not FEATURE_ENCODING_PATH.exists():
        raise RuntimeError(f'Feature encoding file not found: {FEATURE_ENCODING_PATH}')

    model = joblib.load(MODEL_PATH)
    with open(FEATURE_ENCODING_PATH, 'r', encoding='utf-8') as handle:
        encoding = json.load(handle)
    return pd, model, encoding


def infer_malawi_season(reference_time=None):
    month = (reference_time or get_malawi_time()).month
    if month in {11, 12, 1, 2, 3, 4}:
        return 'rainy'
    if month in {5, 6, 7, 8}:
        return 'cold_dry'
    return 'hot_dry'


def normalize_symptom_name(symptom):
    return (symptom or '').strip().lower()


def encode_category(encoding, value):
    """Map a raw categorical string to the integer code the model was trained on.

    Unknown / missing values fall back to the encoder's missing code so the model
    always receives a valid numeric feature."""
    feature_map = encoding['feature_map']
    key = normalize_symptom_name(value)
    return feature_map.get(key, encoding['missing_code'])


def build_model_features(report):
    symptoms = [normalize_symptom_name(symptom) for symptom in report.get_additional_symptoms_list()]
    symptoms = [symptom for symptom in symptoms if symptom]
    unique_symptoms = list(dict.fromkeys(symptoms))
    symptom_slots = (unique_symptoms + [None] * 7)[:7]

    pd, _, encoding = load_prediction_artifacts()

    season_key = encoding['season_aliases'].get(
        infer_malawi_season(report.created_at), 'cold'
    )
    sex_value = (report.animal_sex or '').strip().lower() or 'female'

    return {
        'season': encode_category(encoding, season_key),
        'specie': encode_category(encoding, report.animal_type),
        'sex': encode_category(encoding, sex_value),
        'age(month)': float(report.animal_age or 0),
        'temperature': float(report.temperature or 0),
        'symptom1': encode_category(encoding, symptom_slots[0]),
        'symptom2': encode_category(encoding, symptom_slots[1]),
        'symptom3': encode_category(encoding, symptom_slots[2]),
        'symptom4': encode_category(encoding, symptom_slots[3]),
        'symptom5': encode_category(encoding, symptom_slots[4]),
        'symptom6': encode_category(encoding, symptom_slots[5]),
        'symptom7': encode_category(encoding, symptom_slots[6]),
    }


def decode_model_label(raw_label, encoding):
    if isinstance(raw_label, str):
        return raw_label
    return encoding['disease_labels'].get(str(int(raw_label)), f'Disease {int(raw_label)}')


def categorize_disease(disease_name):
    disease = (disease_name or '').lower()
    if any(term in disease for term in ('pneumonia', 'respiratory', 'cough')):
        return 'respiratory'
    if any(term in disease for term in ('parasite', 'parasitic', 'worm')):
        return 'parasitic'
    if any(term in disease for term in ('mastitis', 'udder', 'milk')):
        return 'production'
    if any(term in disease for term in ('bloat', 'diarrhea', 'enterotoxemia', 'digest')):
        return 'digestive'
    return 'general'


def confidence_to_severity(confidence):
    if confidence >= 0.9:
        return 'critical'
    if confidence >= 0.75:
        return 'severe'
    if confidence >= 0.6:
        return 'moderate'
    return 'mild'

def log_system_event(level, component, message, user_id=None, details=None):
    log = SystemLog(
        level=level,
        component=component,
        user_id=user_id,
        ip_address=request.remote_addr,
        message=message,
        details=json.dumps(details) if details else None,
        timestamp=get_malawi_time()
    )
    db.session.add(log)
    db.session.commit()


def ensure_user_approval_columns():
    existing_columns = {
        row[1] for row in db.session.execute(text("PRAGMA table_info('user')")).fetchall()
    }

    if 'status' not in existing_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
    if 'approved_at' not in existing_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN approved_at DATETIME"))
    if 'rejected_at' not in existing_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN rejected_at DATETIME"))
    if 'production_focus' not in existing_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN production_focus VARCHAR(50)"))
    if 'specific_location' not in existing_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN specific_location VARCHAR(200)"))
    if 'reset_token' not in existing_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN reset_token VARCHAR(128)"))
    if 'reset_token_expires_at' not in existing_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN reset_token_expires_at DATETIME"))

    db.session.execute(text("UPDATE user SET status = 'approved' WHERE status IS NULL"))
    db.session.commit()


def ensure_symptom_report_columns():
    existing_columns = {
        row[1] for row in db.session.execute(text("PRAGMA table_info('symptom_report')")).fetchall()
    }

    if 'animal_sex' not in existing_columns:
        db.session.execute(text("ALTER TABLE symptom_report ADD COLUMN animal_sex VARCHAR(10)"))

    db.session.commit()

def ensure_notification_columns():
    existing_columns = {
        row[1] for row in db.session.execute(text("PRAGMA table_info('notification')")).fetchall()
    }

    if 'sender_id' not in existing_columns:
        db.session.execute(text("ALTER TABLE notification ADD COLUMN sender_id INTEGER"))

    db.session.commit()

def create_notification(user_id, notification_type, title, message, priority='medium', related_id=None, sender_id=None):
    notification = Notification(
        user_id=user_id,
        sender_id=sender_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        action_url=get_notification_action_url(notification_type, related_id),
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()

def build_user_lookup(user_ids):
    ids = sorted({user_id for user_id in user_ids if user_id})
    if not ids:
        return {}
    users = User.query.filter(User.id.in_(ids)).all()
    return {user.id: user for user in users}

def build_sender_lookup(notifications):
    return build_user_lookup(getattr(note, 'sender_id', None) for note in notifications)

def build_recipient_lookup(notifications):
    return build_user_lookup(getattr(note, 'user_id', None) for note in notifications)

def create_default_users():
    # Create system admin if not exists
    if not User.query.filter_by(username='sysadmin').first():
        sysadmin = User(
            username='sysadmin',
            email='sysadmin@animalhealth.com',
            full_name='System Administrator',
            role='system_admin',
            location='Headquarters',
            status='approved',
            approved_at=get_malawi_time()
        )
        sysadmin.set_password('pass123')
        db.session.add(sysadmin)
    
    # Create organization admin if not exists
    if not User.query.filter_by(username='orgadmin').first():
        orgadmin = User(
            username='orgadmin',
            email='orgadmin@animalhealth.com',
            full_name='Organization Administrator',
            role='organization_admin',
            location='Headquarters',
            status='approved',
            approved_at=get_malawi_time()
        )
        orgadmin.set_password('pass123')
        db.session.add(orgadmin)
    
    # Create sample veterinarian
    if not User.query.filter_by(username='vet1').first():
        vet = User(
            username='vet1',
            email='vet1@animalhealth.com',
            full_name='Dr. Sarah Smith',
            phone='+1 (555) 987-6543',
            role='veterinarian',
            location='Zombwe',
            status='approved',
            approved_at=get_malawi_time()
        )
        vet.set_password('pass123')
        db.session.add(vet)
    
    # Create sample farmer
    if not User.query.filter_by(username='farmer1').first():
        farmer = User(
            username='farmer1',
            email='farmer1@example.com',
            full_name='John Farmer',
            phone='+1 (555) 123-4567',
            role='farmer',
            location='Zombwe',
            farm_name='Green Valley Farm',
            animal_types='Cattle,Goats',
            production_focus='dairy',
            status='approved',
            approved_at=get_malawi_time()
            )
        farmer.set_password('pass123')
        db.session.add(farmer)

    existing_default_users = User.query.filter(
        User.username.in_(['sysadmin', 'orgadmin', 'vet1', 'farmer1'])
    ).all()
    for user in existing_default_users:
        user.status = 'approved'
        if not user.approved_at:
            user.approved_at = get_malawi_time()
        user.rejected_at = None

    db.session.commit()

    # Keep the sample vet in the same block as the sample farmer so the real
    # location-based auto-assignment links them (no manual mapping needed).
    default_vet = User.query.filter_by(username='vet1').first()
    default_farmer = User.query.filter_by(username='farmer1').first()
    if default_vet and default_farmer:
        if default_vet.location != default_farmer.location:
            default_vet.location = default_farmer.location
            db.session.commit()
        auto_assign_by_location(default_vet)
        db.session.commit()


def ensure_model_version_record():
    """Record the actual deployed model in the database so the admin pages and
    accuracy figures reflect the real trained model instead of placeholders."""
    if ModelVersion.query.filter_by(version='v1.0').first():
        return
    model_version = ModelVersion(
        version='v1.0',
        status='production',
        accuracy=0.997,
        training_data_size=5130,
        training_date=date(2026, 5, 24),
        deployment_date=date(2026, 6, 25),
        algorithm='StackingClassifier',
        animal_types='cattle,goat'
    )
    db.session.add(model_version)
    db.session.commit()

# Create tables and seed default users after helper definitions are available
with app.app_context():
    db.create_all()
    ensure_user_approval_columns()
    ensure_symptom_report_columns()
    ensure_notification_columns()
    create_default_users()
    ensure_model_version_record()

# Routes
@app.route('/landing')
def landing_page():
    return render_template('landing_files/landing.html')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('landing_page'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if user.status == 'pending':
                flash('Your account is awaiting admin approval.', 'warning')
                return redirect(url_for('login'))
            if user.status == 'rejected':
                flash('Your account was rejected.', 'danger')
                return redirect(url_for('login'))

            login_user(user, remember=form.remember.data)
            user.last_login = get_malawi_time()
            db.session.commit()
            
            log_system_event('info', 'auth', f'User {user.username} logged in', user.id)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        identity = form.identity.data.strip()
        user = User.query.filter(
            or_(User.username == identity, User.email == identity)
        ).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires_at = get_malawi_time() + timedelta(hours=1)
            db.session.commit()

            reset_url = url_for('reset_password', token=token, _external=True)
            email_sent = send_password_reset_email(app, user.email, reset_url)
            log_system_event('info', 'auth', f'Password reset requested for {user.username}', user.id)

            if app.config.get('MAIL_SUPPRESS_SEND') or not email_sent:
                flash(f'Password reset link: {reset_url}', 'info')

        flash('If an account matched your details, a password reset link has been prepared.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    user = User.query.filter_by(reset_token=token).first()
    expires_at = ensure_malawi_datetime(user.reset_token_expires_at) if user else None
    if user is None or not expires_at or expires_at < get_malawi_time():
        flash('This password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        user.reset_token = None
        user.reset_token_expires_at = None
        db.session.commit()

        log_system_event('info', 'auth', f'Password reset completed for {user.username}', user.id)
        flash('Your password has been reset successfully. You can now sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/reset_password.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role=form.role.data,
            location=form.location.data,
            specific_location=form.specific_location.data,
            farm_name=form.farm_name.data,
            animal_types=form.animal_types.data,
            production_focus=form.production_focus.data,
            status='pending'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        log_system_event('info', 'auth', f'New user registered and is awaiting approval: {user.username}', user.id)
        flash('Registration successful! Your account is awaiting admin approval.', 'info')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    log_system_event('info', 'auth', f'User {current_user.username} logged out', current_user.id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing_page'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_farmer():
        return redirect(url_for('farmer_dashboard'))
    elif current_user.is_veterinarian():
        return redirect(url_for('vet_dashboard'))
    elif current_user.is_organization_admin():
        return redirect(url_for('org_admin_dashboard'))
    elif current_user.is_system_admin():
        return redirect(url_for('sys_admin_dashboard'))
    return redirect(url_for('login'))

# Farmer Routes
@app.route('/farmer/dashboard')
@login_required
@role_required('farmer')
def farmer_dashboard():
    # Get statistics
    total_reports = SymptomReport.query.filter_by(farmer_id=current_user.id).count()
    pending_predictions = SymptomReport.query.filter_by(
        farmer_id=current_user.id,
        status='pending'
    ).count()
    
    # Get recent predictions
    recent_predictions = Prediction.query.join(SymptomReport).filter(
        SymptomReport.farmer_id == current_user.id
    ).order_by(Prediction.predicted_at.desc()).limit(5).all()
    
    # Get unread notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    notification_senders = build_sender_lookup(notifications)
    assigned_vets = get_assigned_veterinarians(current_user)
    
    return render_template('farmer/dashboard.html',
                         total_reports=total_reports,
                         pending_predictions=pending_predictions,
                         recent_predictions=recent_predictions,
                         notifications=notifications,
                         notification_senders=notification_senders,
                         assigned_vets=assigned_vets)

@app.route('/farmer/notifications')
@login_required
@role_required('farmer')
def farmer_notifications():
    active_filter = request.args.get('filter', 'all')
    base_query = Notification.query.filter_by(user_id=current_user.id)

    if active_filter == 'unread':
        base_query = base_query.filter_by(is_read=False)
    elif active_filter == 'meeting':
        base_query = base_query.filter_by(notification_type='meeting')
    else:
        active_filter = 'all'

    notifications = base_query.order_by(Notification.created_at.desc()).all()
    notification_senders = build_sender_lookup(notifications)
    all_notifications = Notification.query.filter_by(user_id=current_user.id).all()
    unread_count = sum(1 for note in all_notifications if not note.is_read)
    meetings_count = sum(1 for note in all_notifications if note.notification_type == 'meeting')

    return render_template(
        'farmer/notifications.html',
        notifications=notifications,
        notification_senders=notification_senders,
        unread_count=unread_count,
        total_notifications=len(all_notifications),
        meetings_count=meetings_count,
        active_filter=active_filter
    )

@app.route('/farmer/notifications/<int:notification_id>')
@login_required
@role_required('farmer')
def farmer_notification_detail(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)

    if not notification.is_read:
        notification.is_read = True
        db.session.commit()

    sender = None
    if notification.sender_id:
        sender = User.query.get(notification.sender_id)

    return render_template(
        'farmer/notification_detail.html',
        notification=notification,
        sender=sender
    )

@app.route('/farmer/notifications/mark-all-read', methods=['POST'])
@login_required
@role_required('farmer')
def mark_farmer_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {'is_read': True},
        synchronize_session=False
    )
    db.session.commit()
    flash('All notifications have been marked as read.', 'success')
    return redirect(url_for('farmer_notifications'))


@app.route('/farmer/contact-vet', methods=['POST'])
@login_required
@role_required('farmer')
def contact_vet():
    assigned_vets = get_assigned_veterinarians(current_user)
    if not assigned_vets:
        flash('You do not have an assigned veterinarian yet.', 'warning')
        return redirect(url_for('farmer_dashboard'))

    subject = (request.form.get('subject') or '').strip()
    message = (request.form.get('message') or '').strip()

    if not message:
        flash('Please enter a message for your veterinarian.', 'danger')
        return redirect(url_for('farmer_dashboard'))

    title = subject[:200] if subject else f'Message from {current_user.full_name or current_user.username}'

    for vet in assigned_vets:
        create_notification(
            vet.id,
            'message',
            title,
            message,
            'high',
            sender_id=current_user.id
        )

    log_system_event(
        'info',
        'notification',
        f'Farmer {current_user.username} contacted assigned veterinarian(s)',
        current_user.id,
        {'recipient_count': len(assigned_vets)}
    )
    flash('Your message has been sent to your assigned veterinarian.', 'success')
    return redirect(url_for('farmer_dashboard'))

@app.route('/farmer/symptoms', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def symptom_form():
    form = SymptomForm()
    if form.validate_on_submit():
        if form.animal_type.data not in SUPPORTED_ANIMAL_TYPES:
            flash('Only cattle and goat cases are supported for prediction.', 'danger')
            return render_template('farmer/symptom_form.html', form=form)

        report_id = generate_report_id()
        selected_symptoms = request.form.getlist('symptoms')
        combined_symptoms = selected_symptoms.copy()
        animal_label = form.animal_type.data.replace('_', ' ').title()
        
        report = SymptomReport(
            report_id=report_id,
            farmer_id=current_user.id,
            animal_id=report_id,
            animal_name=f'{animal_label} case',
            animal_type=form.animal_type.data,
            animal_sex=form.animal_sex.data,
            animal_age=form.animal_age.data,
            animal_weight=form.animal_weight.data,
            animal_breed=None,
            appetite=form.appetite.data,
            temperature=form.temperature.data,
            rumen_movement=form.rumen_movement.data,
            stool_consistency=form.stool_consistency.data,
            milk_production=form.milk_production.data,
            additional_symptoms=json.dumps(combined_symptoms),
            feed_type=form.feed_type.data,
            feed_changes=form.feed_changes.data,
            housing_conditions=form.housing_conditions.data,
            recent_treatments=form.recent_treatments.data,
            status='pending'
        )
        db.session.add(report)
        db.session.commit()

        try:
            prediction = create_prediction(report)
        except Exception as exc:
            log_system_event(
                'error',
                'model',
                f'Model prediction failed for report {report.report_id}',
                current_user.id,
                {'report_id': report.report_id, 'animal_type': report.animal_type, 'error': str(exc)}
            )
            flash('Symptoms were saved, but the trained model could not generate a prediction. Please contact the administrator.', 'danger')
            return redirect(url_for('symptom_history'))
        
        # Create notification for farmer
        create_notification(
            current_user.id,
            'prediction',
            'New Prediction Generated',
            f'Prediction for {report.animal_name}: {prediction.disease_name} with {prediction.confidence*100:.1f}% confidence',
            'medium',
            prediction.id
        )
        
        # Notify assigned veterinarians
        for vet in get_assigned_veterinarians(current_user):
            create_notification(
                vet.id,
                'review',
                'New Prediction Requires Review',
                f'Prediction for {report.animal_name} needs your review',
                'high',
                prediction.id
            )
        
        log_system_event('info', 'prediction', f'New symptom report submitted: {report.report_id}', current_user.id)
        flash('Symptoms submitted successfully! Prediction generated.', 'success')
        return redirect(url_for('farmer_predictions'))
    
    return render_template('farmer/symptom_form.html', form=form)

# Per-disease clinical metadata so each prediction gives distinct, useful guidance
# instead of a single generic recommendation.
DISEASE_INFO = {
    'Anthrax': {
        'category': 'bacterial',
        'severity': 'critical',
        'recommendation': 'Do NOT open or move the carcass. Isolate all animals immediately, restrict movement, and contact your veterinarian and animal-health authorities urgently. Anthrax is zoonotic — avoid direct contact and handling.'
    },
    'Brucellosis': {
        'category': 'reproductive',
        'severity': 'severe',
        'recommendation': 'Isolate affected animals and safely dispose of aborted material. Brucellosis is zoonotic — wear gloves when handling. Arrange veterinary testing of the herd and avoid consuming unpasteurised milk.'
    },
    'East Coast Fever': {
        'category': 'tick-borne',
        'severity': 'critical',
        'recommendation': 'Begin tick control immediately and keep the animal hydrated and sheltered. East Coast Fever progresses fast — seek urgent veterinary treatment for antiparasitic therapy.'
    },
    'Foot and Mouth Disease': {
        'category': 'viral',
        'severity': 'critical',
        'recommendation': 'Quarantine the animal and the whole herd at once — FMD is highly contagious. Disinfect equipment, restrict movement on/off the farm, and report to veterinary authorities immediately.'
    },
    'Mastitis': {
        'category': 'production',
        'severity': 'moderate',
        'recommendation': 'Separate the animal from the milking line and discard affected milk. Keep the udder clean and dry, milk out frequently, and consult your veterinarian for appropriate antibiotic therapy.'
    },
    'Pneumonia': {
        'category': 'respiratory',
        'severity': 'severe',
        'recommendation': 'Move the animal to a warm, dry, well-ventilated shelter away from draughts. Ensure water intake and seek veterinary care promptly for antibiotic treatment.'
    },
    'Trypanosomiasis': {
        'category': 'parasitic',
        'severity': 'severe',
        'recommendation': 'Reduce tsetse-fly exposure and support the animal with good nutrition and rest. Seek veterinary care for trypanocidal treatment as soon as possible.'
    },
    'Worm Infestation': {
        'category': 'parasitic',
        'severity': 'moderate',
        'recommendation': 'Administer an appropriate dewormer as advised by your veterinarian, provide good nutrition, and rotate/clean pastures to reduce re-infection.'
    },
}


def get_disease_info(disease_name):
    return DISEASE_INFO.get(disease_name, {
        'category': categorize_disease(disease_name),
        'severity': 'moderate',
        'recommendation': 'Isolate the animal and wait for veterinarian review and prescription.'
    })


def create_prediction(report):
    if report.animal_type not in SUPPORTED_ANIMAL_TYPES:
        raise ValueError(f'Unsupported animal type for model prediction: {report.animal_type}')

    pd, model, encoding = load_prediction_artifacts()
    features = build_model_features(report)
    feature_frame = pd.DataFrame([features])[encoding['feature_order']]

    raw_prediction = model.predict(feature_frame)[0]
    disease_name = decode_model_label(raw_prediction, encoding)
    confidence = 0.0
    possible_diseases = [{'disease': disease_name, 'probability': 1.0}]

    if hasattr(model, 'predict_proba'):
        probabilities = model.predict_proba(feature_frame)[0]
        model_classes = getattr(model, 'classes_', range(len(probabilities)))
        ranked_indices = sorted(range(len(probabilities)), key=lambda idx: float(probabilities[idx]), reverse=True)
        possible_diseases = [
            {
                'disease': decode_model_label(model_classes[idx], encoding),
                'probability': round(float(probabilities[idx]), 4)
            }
            for idx in ranked_indices[:3]
        ]
        confidence = float(probabilities[ranked_indices[0]])

    disease_info = get_disease_info(disease_name)

    prediction = Prediction(
        prediction_id=generate_prediction_id(),
        symptom_report_id=report.id,
        user_id=report.farmer_id,
        disease_name=disease_name,
        disease_category=disease_info['category'],
        confidence=confidence,
        severity=disease_info['severity'],
        recommendation_text=disease_info['recommendation'],
        model_version='model.pkl',
        possible_diseases=json.dumps(possible_diseases),
        review_status='pending',
        features_used=json.dumps(features)
    )
    
    # Update report status
    report.status = 'predicted'
    
    db.session.add(prediction)
    db.session.commit()
    
    return prediction

@app.route('/farmer/symptoms/history')
@login_required
@role_required('farmer')
def symptom_history():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    reports = SymptomReport.query.filter_by(farmer_id=current_user.id)\
        .order_by(SymptomReport.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    # Prefetch each report's prediction (1 prediction per report in this system)
    reports_with_prediction = [
        (r, getattr(r, 'prediction', None))
        for r in reports.items
    ]

    return render_template('farmer/symptom_history.html', reports=reports_with_prediction, page=page, per_page=per_page)


@app.route('/farmer/predictions')
@login_required
@role_required('farmer')
def farmer_predictions():
    predictions = Prediction.query.join(SymptomReport).filter(
        SymptomReport.farmer_id == current_user.id
    ).order_by(Prediction.predicted_at.desc()).all()
    
    active_treatments = Treatment.query.join(SymptomReport).filter(
        SymptomReport.farmer_id == current_user.id,
        Treatment.status.in_(['prescribed', 'in_progress'])
    ).all()
    
    return render_template('farmer/predictions.html',
                         predictions=predictions,
                         active_treatments=active_treatments)


def _can_access_prediction(prediction):
    """Owner farmer, an assigned vet, or any admin may view a prediction."""
    if current_user.id == prediction.user_id:
        return True
    if current_user.role in ('organization_admin', 'system_admin'):
        return True
    if current_user.role == 'veterinarian':
        farmer = prediction.symptom_report.farmer
        return farmer in get_assigned_farmers(current_user)
    return False


@app.route('/predictions/<int:prediction_id>')
@login_required
def prediction_detail(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    if not _can_access_prediction(prediction):
        abort(403)
    return render_template('farmer/prediction_detail.html',
                           prediction=prediction,
                           report=prediction.symptom_report,
                           possible_diseases=prediction.get_possible_diseases())


@app.route('/predictions/<int:prediction_id>/pdf')
@login_required
def prediction_pdf(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    if not _can_access_prediction(prediction):
        abort(403)
    if not PDF_AVAILABLE:
        flash('PDF export is unavailable: install reportlab and matplotlib.', 'danger')
        return redirect(url_for('prediction_detail', prediction_id=prediction_id))

    buf = pdf_utils.build_prediction_pdf(
        prediction,
        prediction.symptom_report,
        prediction.get_possible_diseases(),
        get_malawi_time().strftime('%Y-%m-%d %H:%M'))
    filename = 'prediction_%s.pdf' % (prediction.prediction_id or prediction.id)
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


@app.route('/farmer/profile', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def farmer_registration():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        existing_user = User.query.filter(
            User.email == form.email.data,
            User.id != current_user.id
        ).first()
        if existing_user:
            flash('That email address is already in use by another account.', 'danger')
            return render_template('farmer/registration.html', form=form)

        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.farm_name = form.farm_name.data
        current_user.location = form.location.data
        current_user.specific_location = form.specific_location.data
        current_user.animal_types = form.animal_types.data
        current_user.production_focus = form.production_focus.data

        auto_assign_by_location(current_user)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('farmer_registration'))
    
    return render_template('farmer/registration.html', form=form)

# Veterinarian Routes
@app.route('/veterinarian/dashboard')
@login_required
@role_required('veterinarian')
def vet_dashboard():
    # Get assigned farmers
    assigned_farmer_list = get_assigned_farmers(current_user)
    assigned_farmer_ids = [farmer.id for farmer in assigned_farmer_list]
    assigned_farmers = len(assigned_farmer_list)
    
    # Get pending reviews
    pending_reviews = Prediction.query.join(SymptomReport).filter(
        SymptomReport.status == 'predicted',
        Prediction.review_status == 'pending',
        SymptomReport.farmer_id.in_(assigned_farmer_ids if assigned_farmer_ids else [-1])
    ).count()
    
    # Get active treatments
    active_treatments = Treatment.query.filter_by(
        vet_id=current_user.id,
        status='in_progress'
    ).count()
    
    # Get recent mortality reports
    recent_mortality = MortalityReport.query.filter_by(vet_id=current_user.id)\
        .order_by(MortalityReport.created_at.desc()).limit(5).all()
    farmer_messages = Notification.query.filter_by(
        user_id=current_user.id,
        notification_type='message'
    ).order_by(Notification.created_at.desc()).limit(8).all()
    message_senders = build_sender_lookup(farmer_messages)
    sent_alerts_count = Notification.query.filter_by(
        sender_id=current_user.id,
        notification_type='alert'
    ).count()
    scheduled_meetings_count = Notification.query.filter_by(
        sender_id=current_user.id,
        notification_type='meeting'
    ).count()
    
    return render_template('veterinarian/dashboard.html',
                         assigned_farmers=assigned_farmers,
                         assigned_farmer_list=assigned_farmer_list,
                         pending_reviews=pending_reviews,
                         active_treatments=active_treatments,
                         recent_mortality=recent_mortality,
                         farmer_messages=farmer_messages,
                         message_senders=message_senders,
                         sent_alerts_count=sent_alerts_count,
                         scheduled_meetings_count=scheduled_meetings_count)

@app.route('/veterinarian/communications')
@login_required
@role_required('veterinarian')
def vet_communications():
    incoming_messages = Notification.query.filter_by(
        user_id=current_user.id,
        notification_type='message'
    ).order_by(Notification.created_at.desc()).all()
    sent_alerts = Notification.query.filter_by(
        sender_id=current_user.id,
        notification_type='alert'
    ).order_by(Notification.created_at.desc()).all()
    scheduled_meetings = Notification.query.filter_by(
        sender_id=current_user.id,
        notification_type='meeting'
    ).order_by(Notification.created_at.desc()).all()

    message_senders = build_sender_lookup(incoming_messages)
    alert_recipients = build_recipient_lookup(sent_alerts)
    meeting_recipients = build_recipient_lookup(scheduled_meetings)

    return render_template(
        'veterinarian/communications.html',
        incoming_messages=incoming_messages,
        sent_alerts=sent_alerts,
        scheduled_meetings=scheduled_meetings,
        message_senders=message_senders,
        alert_recipients=alert_recipients,
        meeting_recipients=meeting_recipients
    )


@app.route('/veterinarian/alerts/send', methods=['POST'])
@login_required
@role_required('veterinarian')
def send_farmer_alert():
    assigned_farmer_list = get_assigned_farmers(current_user)
    if not assigned_farmer_list:
        flash('You do not have any assigned farmers to alert yet.', 'warning')
        return redirect(url_for('vet_dashboard'))

    subject = (request.form.get('subject') or '').strip()
    message = (request.form.get('message') or '').strip()
    priority = (request.form.get('priority') or 'medium').strip().lower()
    if priority not in {'low', 'medium', 'high', 'critical'}:
        priority = 'medium'

    if not message:
        flash('Please enter an alert message before sending.', 'danger')
        return redirect(url_for('vet_dashboard'))

    title = subject[:200] if subject else f'Farmer Alert from {current_user.full_name or current_user.username}'

    for farmer in assigned_farmer_list:
        create_notification(
            farmer.id,
            'alert',
            title,
            message,
            priority,
            sender_id=current_user.id
        )

    log_system_event(
        'info',
        'notification',
        f'Veterinarian {current_user.username} sent a farmer alert broadcast',
        current_user.id,
        {'recipient_count': len(assigned_farmer_list), 'priority': priority}
    )
    flash(f'Alert sent to {len(assigned_farmer_list)} assigned farmer(s).', 'success')
    return redirect(url_for('vet_dashboard'))

@app.route('/veterinarian/meetings/schedule', methods=['POST'])
@login_required
@role_required('veterinarian')
def schedule_farmer_meeting():
    assigned_farmer_list = get_assigned_farmers(current_user)
    assigned_farmer_map = {str(farmer.id): farmer for farmer in assigned_farmer_list}
    if not assigned_farmer_map:
        flash('You do not have any assigned farmers to schedule yet.', 'warning')
        return redirect(url_for('vet_dashboard'))

    farmer_id = (request.form.get('farmer_id') or '').strip()
    title = (request.form.get('title') or '').strip()
    meeting_date = (request.form.get('meeting_date') or '').strip()
    meeting_time = (request.form.get('meeting_time') or '').strip()
    location = (request.form.get('location') or '').strip()
    notes = (request.form.get('notes') or '').strip()

    farmer = assigned_farmer_map.get(farmer_id)
    if farmer is None:
        flash('Please select one of your assigned farmers.', 'danger')
        return redirect(url_for('vet_dashboard'))

    if not meeting_date or not meeting_time or not location:
        flash('Meeting date, time, and location are required.', 'danger')
        return redirect(url_for('vet_dashboard'))

    meeting_title = title[:200] if title else 'Veterinary meeting scheduled'
    meeting_message = (
        f'Your veterinarian scheduled a meeting on {meeting_date} at {meeting_time} '
        f'for {location}.'
    )
    if notes:
        meeting_message += f' Notes: {notes}'

    create_notification(
        farmer.id,
        'meeting',
        meeting_title,
        meeting_message,
        'high',
        sender_id=current_user.id
    )

    log_system_event(
        'info',
        'notification',
        f'Veterinarian {current_user.username} scheduled a meeting with {farmer.username}',
        current_user.id,
        {'farmer_id': farmer.id, 'meeting_date': meeting_date, 'meeting_time': meeting_time}
    )
    flash(f'Meeting scheduled for {farmer.full_name or farmer.username}.', 'success')
    return redirect(url_for('vet_communications'))

@app.route('/veterinarian/profile', methods=['GET', 'POST'])
@login_required
@role_required('veterinarian')
def vet_profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        existing_user = User.query.filter(
            User.email == form.email.data,
            User.id != current_user.id
        ).first()
        if existing_user:
            flash('That email address is already in use by another account.', 'danger')
            return render_template(
                'veterinarian/profile.html',
                form=form,
                assigned_farmers_count=len(get_assigned_farmers(current_user)),
                pending_reviews=Prediction.query.join(SymptomReport).filter(
                    SymptomReport.status == 'predicted',
                    Prediction.review_status == 'pending',
                    SymptomReport.farmer_id.in_(
                        [farmer.id for farmer in get_assigned_farmers(current_user)] or [-1]
                    )
                ).count(),
                active_treatments=Treatment.query.filter_by(
                    vet_id=current_user.id,
                    status='in_progress'
                ).count(),
                mortality_reports_count=MortalityReport.query.filter_by(vet_id=current_user.id).count()
            )

        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.location = form.location.data
        current_user.specific_location = form.specific_location.data

        auto_assign_by_location(current_user)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('vet_profile'))

    assigned_farmer_list = get_assigned_farmers(current_user)
    assigned_farmer_ids = [farmer.id for farmer in assigned_farmer_list]
    pending_reviews = Prediction.query.join(SymptomReport).filter(
        SymptomReport.status == 'predicted',
        Prediction.review_status == 'pending',
        SymptomReport.farmer_id.in_(assigned_farmer_ids if assigned_farmer_ids else [-1])
    ).count()
    active_treatments = Treatment.query.filter_by(
        vet_id=current_user.id,
        status='in_progress'
    ).count()
    mortality_reports_count = MortalityReport.query.filter_by(vet_id=current_user.id).count()

    return render_template(
        'veterinarian/profile.html',
        form=form,
        assigned_farmers_count=len(assigned_farmer_list),
        pending_reviews=pending_reviews,
        active_treatments=active_treatments,
        mortality_reports_count=mortality_reports_count
    )

@app.route('/veterinarian/farmers')
@login_required
@role_required('veterinarian')
def farmer_mapping():
    assigned_farmers = get_assigned_farmers(current_user)
    available_farmers = User.query.filter_by(role='farmer').filter(
        ~User.id.in_([f.id for f in assigned_farmers] or [-1])
    ).all()
    
    return render_template('veterinarian/farmer_mapping.html',
                         assigned_farmers=assigned_farmers,
                         available_farmers=available_farmers)

@app.route('/veterinarian/predictions')
@login_required
@role_required('veterinarian')
def predictions_review():
    assigned_farmer_ids = [farmer.id for farmer in get_assigned_farmers(current_user)]

    f_severity = request.args.get('severity', 'all')
    f_animal = request.args.get('animal_type', 'all')
    f_confidence = request.args.get('confidence', 'all')

    pending_q = Prediction.query.join(SymptomReport).filter(
        SymptomReport.status == 'predicted',
        Prediction.review_status == 'pending',
        SymptomReport.farmer_id.in_(assigned_farmer_ids if assigned_farmer_ids else [-1])
    )
    if f_severity != 'all':
        pending_q = pending_q.filter(Prediction.severity == f_severity)
    if f_animal != 'all':
        pending_q = pending_q.filter(SymptomReport.animal_type == f_animal)
    if f_confidence == 'high':
        pending_q = pending_q.filter(Prediction.confidence >= 0.9)
    elif f_confidence == 'medium':
        pending_q = pending_q.filter(Prediction.confidence >= 0.7, Prediction.confidence < 0.9)
    elif f_confidence == 'low':
        pending_q = pending_q.filter(Prediction.confidence < 0.7)

    pending_predictions = pending_q.order_by(Prediction.predicted_at.desc()).all()

    reviewed_predictions = Prediction.query.join(SymptomReport).filter(
        Prediction.review_status.in_(['confirmed', 'modified']),
        Prediction.reviewed_by == current_user.id
    ).order_by(Prediction.reviewed_at.desc()).limit(10).all()

    return render_template('veterinarian/prediction_review.html',
                         pending_predictions=pending_predictions,
                         reviewed_predictions=reviewed_predictions,
                         f_severity=f_severity,
                         f_animal=f_animal,
                         f_confidence=f_confidence)

@app.route('/veterinarian/treatments', methods=['GET', 'POST'])
@login_required
@role_required('veterinarian')
def treatment_suggestions():
    form = TreatmentForm()
    
    if form.validate_on_submit():
        symptom_report = SymptomReport.query.order_by(SymptomReport.created_at.desc()).first()
        if not symptom_report:
            flash('Create a symptom report before saving a treatment plan.', 'warning')
            return redirect(url_for('treatment_suggestions'))

        treatment = Treatment(
            treatment_id=generate_treatment_id(),
            symptom_report_id=symptom_report.id,
            vet_id=current_user.id,
            medication=form.medication.data,
            medication_type=form.medication_type.data,
            dosage=form.dosage.data,
            dosage_per_kg=form.dosage_per_kg.data,
            frequency=form.frequency.data,
            duration=str(form.duration.data),
            route=form.route.data,
            supportive_care=form.supportive_care.data,
            diet_recommendations=form.diet_recommendations.data,
            follow_up_required=form.follow_up_required.data,
            follow_up_date=form.follow_up_date.data,
            milk_withdrawal_days=form.milk_withdrawal_days.data,
            meat_withdrawal_days=form.meat_withdrawal_days.data,
            status='prescribed'
        )
        db.session.add(treatment)
        db.session.commit()
        
        flash('Treatment plan created successfully!', 'success')
        return redirect(url_for('treatment_suggestions'))
    
    # Get pending treatment approvals
    pending_treatments = Treatment.query.filter_by(status='pending_approval').all()
    
    # Get active treatments
    active_treatments = Treatment.query.filter_by(
        vet_id=current_user.id,
        status='in_progress'
    ).all()
    
    return render_template('veterinarian/treatment_suggestions.html',
                         form=form,
                         pending_treatments=pending_treatments,
                         active_treatments=active_treatments)


@app.route('/veterinarian/predictions/<int:prediction_id>/treatment', methods=['GET', 'POST'])
@login_required
@role_required('veterinarian')
def add_treatment(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    report = prediction.symptom_report
    # The vet may only treat cases for farmers assigned to them.
    if report.farmer not in get_assigned_farmers(current_user):
        abort(403)

    existing = report.treatment  # one-to-one; may be None or a placeholder from confirm
    form = TreatmentForm(obj=existing) if (request.method == 'GET' and existing) else TreatmentForm()

    if form.validate_on_submit():
        treatment = existing
        if treatment is None:
            treatment = Treatment(
                treatment_id=generate_treatment_id(),
                symptom_report_id=report.id)
            db.session.add(treatment)
        treatment.vet_id = current_user.id
        treatment.medication = form.medication.data
        treatment.medication_type = form.medication_type.data
        treatment.dosage = form.dosage.data
        treatment.dosage_per_kg = form.dosage_per_kg.data
        treatment.frequency = form.frequency.data
        treatment.duration = str(form.duration.data) if form.duration.data is not None else None
        treatment.route = form.route.data
        treatment.supportive_care = form.supportive_care.data
        treatment.diet_recommendations = form.diet_recommendations.data
        treatment.follow_up_required = form.follow_up_required.data
        treatment.follow_up_date = form.follow_up_date.data
        treatment.milk_withdrawal_days = form.milk_withdrawal_days.data
        treatment.meat_withdrawal_days = form.meat_withdrawal_days.data
        treatment.status = 'prescribed'

        # Confirm the prediction as part of issuing a treatment.
        if prediction.review_status == 'pending':
            prediction.review_status = 'confirmed'
            prediction.reviewed_by = current_user.id
            prediction.reviewed_at = get_malawi_time()
        report.status = 'reviewed'
        db.session.commit()

        create_notification(
            report.farmer_id,
            'treatment',
            'Treatment Recommendation Available',
            f'Your veterinarian added a treatment plan for {report.animal_name} ({prediction.disease_name}).',
            'high',
            treatment.id
        )
        log_system_event('info', 'treatment',
                         f'Treatment recommendation saved for {report.report_id}', current_user.id)
        flash('Treatment recommendation saved and shared with the farmer.', 'success')
        return redirect(url_for('predictions_review'))

    return render_template('veterinarian/add_treatment.html',
                           form=form, prediction=prediction, report=report,
                           existing=existing,
                           possible_diseases=prediction.get_possible_diseases())


@app.route('/veterinarian/mortality', methods=['GET', 'POST'])
@login_required
@role_required('veterinarian')
def mortality_reports():
    form = MortalityReportForm()
    
    if form.validate_on_submit():
        assigned_farmers = get_assigned_farmers(current_user)
        report = MortalityReport(
            report_id=generate_mortality_id(),
            farmer_id=assigned_farmers[0].id if assigned_farmers else current_user.id,
            vet_id=current_user.id,
            animal_type=form.animal_type.data,
            animal_id=form.animal_id.data,
            animal_name=form.animal_name.data or form.animal_id.data,
            breed=form.breed.data,
            age=form.age.data,
            date_of_death=form.date_of_death.data,
            suspected_cause=form.suspected_cause.data,
            last_milk_production=form.last_milk_production.data,
            symptoms_before_death=form.symptoms_before_death.data,
            was_dairy=form.was_dairy.data,
            requires_investigation=form.requires_investigation.data
        )
        report.investigation_notes = form.additional_notes.data
        report.lab_results = form.lab_results.data
        db.session.add(report)
        db.session.commit()
        
        log_system_event('info', 'mortality', f'Mortality report created: {report.report_id}', current_user.id)
        flash('Mortality report submitted successfully!', 'success')
        return redirect(url_for('mortality_reports'))
    
    # Get recent mortality reports
    recent_reports = MortalityReport.query.filter_by(vet_id=current_user.id)\
        .order_by(MortalityReport.created_at.desc()).limit(10).all()
    
    # Get statistics
    monthly_count = MortalityReport.query.filter(
        MortalityReport.vet_id == current_user.id,
        MortalityReport.created_at >= get_malawi_time() - timedelta(days=30)
    ).count()
    
    return render_template('veterinarian/mortality_reports.html',
                         form=form,
                         recent_reports=recent_reports,
                         monthly_count=monthly_count)

# Organization Admin Routes

@app.route('/organization/dashboard')
@login_required
@role_required('organization_admin')
def org_admin_dashboard():
    # System statistics
    total_farmers = User.query.filter_by(role='farmer').count()
    total_veterinarians = User.query.filter_by(role='veterinarian').count()
    active_predictions = SymptomReport.query.filter_by(status='predicted').count()
    # Real model accuracy: prefer the production model's recorded accuracy,
    # otherwise fall back to the average confidence of generated predictions.
    production_model = ModelVersion.query.filter_by(status='production').order_by(ModelVersion.id.desc()).first()
    if production_model and production_model.accuracy:
        system_accuracy = production_model.accuracy
    else:
        avg_conf = db.session.query(db.func.avg(Prediction.confidence)).scalar()
        system_accuracy = float(avg_conf) if avg_conf else None
    
    # Recent activities
    recent_logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(10).all()

    # Location distribution for farmers
    location_counts = db.session.query(User.location, db.func.count(User.id))\
        .filter(User.role == 'farmer')\
        .group_by(User.location).all()
    location_labels = [l[0] if l[0] else 'Unknown' for l in location_counts]
    location_values = [l[1] for l in location_counts]

    return render_template('organization_admin/dashboard.html',
                         total_farmers=total_farmers,
                         total_veterinarians=total_veterinarians,
                         active_predictions=active_predictions,
                         system_accuracy=system_accuracy,
                         recent_logs=recent_logs,
                         location_labels=location_labels,
                         location_values=location_values)
@app.route('/organization/profile')
@login_required
@role_required('organization_admin')
def org_admin_profile():
    return render_template('organization_admin/my_profile.html')


@app.route('/organization/user_management')
@login_required
@role_required('organization_admin')
def org_admin_users():
    users = User.query.order_by(User.registration_date.desc()).all()
    total_users = len(users)
    active_users = sum(1 for user in users if user.is_active)
    admin_users = sum(1 for user in users if user.role in ['organization_admin', 'system_admin'])
    users_by_status = {
        'pending': [user for user in users if user.status == 'pending'],
        'approved': [user for user in users if user.status == 'approved'],
        'rejected': [user for user in users if user.status == 'rejected']
    }

    return render_template('organization_admin/user_management.html',
                         users=users,
                         users_by_status=users_by_status,
                         total_users=total_users,
                         active_users=active_users,
                         admin_users=admin_users)


@app.route('/organization/users/<int:user_id>/approve', methods=['POST'])
@login_required
@role_required('organization_admin')
def approve_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.is_organization_admin() or user.is_system_admin():
        flash('Administrator accounts cannot be approved from this panel.', 'warning')
        return redirect(url_for('org_admin_users'))

    user.status = 'approved'
    user.approved_at = get_malawi_time()
    user.rejected_at = None
    auto_assign_by_location(user)
    db.session.commit()

    send_approval_email(app, user.email)
    log_system_event('info', 'auth', f'User approved: {user.username}', current_user.id)
    flash(f'{user.username} approved successfully.', 'success')
    return redirect(url_for('org_admin_users'))


@app.route('/organization/users/<int:user_id>/reject', methods=['POST'])
@login_required
@role_required('organization_admin')
def reject_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.is_organization_admin() or user.is_system_admin():
        flash('Administrator accounts cannot be rejected from this panel.', 'warning')
        return redirect(url_for('org_admin_users'))

    user.status = 'rejected'
    user.rejected_at = get_malawi_time()
    user.approved_at = None
    db.session.commit()

    send_rejection_email(app, user.email)
    log_system_event('info', 'auth', f'User rejected: {user.username}', current_user.id)
    flash(f'{user.username} rejected successfully.', 'warning')
    return redirect(url_for('org_admin_users'))


@app.route('/organization/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('organization_admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('org_admin_users'))

    if user.is_system_admin():
        flash('System administrator accounts cannot be deleted from this panel.', 'warning')
        return redirect(url_for('org_admin_users'))

    username = user.username
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('This user could not be deleted because related records still exist.', 'danger')
        return redirect(url_for('org_admin_users'))

    log_system_event('warning', 'auth', f'User deleted: {username}', current_user.id)
    flash(f'{username} deleted successfully.', 'success')
    return redirect(url_for('org_admin_users'))


def compute_report_analytics(location='all', animal_type='all', days=30):
    """Filtered disease analytics shared by the reports page and its PDF export."""
    cutoff = get_malawi_time() - timedelta(days=days)
    approved_locations = [value for value, _ in REGISTRATION_LOCATION_CHOICES if value]

    def _filtered(query):
        query = query.join(SymptomReport, Prediction.symptom_report_id == SymptomReport.id)\
                     .join(User, SymptomReport.farmer_id == User.id)\
                     .filter(Prediction.predicted_at >= cutoff)
        if location and location != 'all':
            query = query.filter(User.location == location)
        if animal_type and animal_type != 'all':
            query = query.filter(SymptomReport.animal_type == animal_type)
        return query

    # Most frequent diseases
    disease_distribution = _filtered(
        db.session.query(Prediction.disease_name, db.func.count(Prediction.id))
    ).group_by(Prediction.disease_name).order_by(
        db.func.count(Prediction.id).desc(), Prediction.disease_name.asc()
    ).all()
    disease_rows = [(name or 'Unknown disease', count) for name, count in disease_distribution]

    # Dominant disease per location
    location_counts = _filtered(
        db.session.query(User.location, Prediction.disease_name, db.func.count(Prediction.id))
    ).group_by(User.location, Prediction.disease_name).all()
    dominant = {}
    for loc, disease_name, freq in location_counts:
        cand = {'location': loc or 'Unknown', 'disease_name': disease_name or 'Unknown disease', 'frequency': freq}
        cur = dominant.get(loc)
        if cur is None or freq > cur['frequency'] or (freq == cur['frequency'] and cand['disease_name'] < cur['disease_name']):
            dominant[loc] = cand
    scope_locations = [location] if (location and location != 'all') else approved_locations
    location_summary = [
        dominant.get(loc, {'location': loc, 'disease_name': 'No data yet', 'frequency': 0})
        for loc in scope_locations
    ]

    # Trend over time (daily buckets for short ranges, weekly otherwise)
    bucket_fmt = '%Y-%m-%d' if days <= 14 else '%Y-W%W'
    trend = _filtered(
        db.session.query(db.func.strftime(bucket_fmt, Prediction.predicted_at), db.func.count(Prediction.id))
    ).group_by(db.func.strftime(bucket_fmt, Prediction.predicted_at)).order_by(
        db.func.strftime(bucket_fmt, Prediction.predicted_at).asc()
    ).all()
    trend_labels = [t[0] for t in trend if t[0]]
    trend_values = [t[1] for t in trend if t[0]]

    return {
        'disease_rows': disease_rows,
        'disease_labels': [d for d, _ in disease_rows],
        'disease_values': [c for _, c in disease_rows],
        'location_summary': location_summary,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
        'location_options': approved_locations,
    }


def build_vet_summary():
    veterinarian_users = User.query.filter_by(role='veterinarian').order_by(User.full_name.asc()).all()
    summary = []
    for vet in veterinarian_users:
        reviewed = Prediction.query.filter(
            Prediction.reviewed_by == vet.id,
            Prediction.review_status.in_(['confirmed', 'modified'])
        ).count()
        summary.append({
            'full_name': vet.full_name or vet.username,
            'service_location': vet.location or vet.specific_location or 'Location not set',
            'status': vet.status or 'unknown',
            'reviewed_predictions_count': reviewed,
            'assigned_farmers_count': len(get_assigned_farmers(vet))
        })
    summary.sort(key=lambda i: (-i['reviewed_predictions_count'], -i['assigned_farmers_count'], i['full_name'].lower()))
    return summary


@app.route('/organization/reports', methods=['GET', 'POST'])
@login_required
@role_required('organization_admin')
def org_reports():
    form = ReportGenerationForm()
    
    if form.validate_on_submit():
        # Generate report (simulated)
        report = Report(
            report_id=generate_report_id('REP'),
            report_type=form.report_type.data,
            period_start=form.period_start.data,
            period_end=form.period_end.data,
            generated_by=current_user.id,
            is_scheduled=form.schedule_frequency.data != 'once',
            schedule_frequency=form.schedule_frequency.data if form.schedule_frequency.data != 'once' else None
        )
        db.session.add(report)
        db.session.commit()
        
        flash(f'Report {report.report_id} generation started!', 'success')
        return redirect(url_for('org_reports'))
    
    # Get existing reports
    reports = Report.query.order_by(Report.generated_at.desc()).limit(20).all()

    f_location = request.args.get('location', 'all')
    f_animal = request.args.get('animal_type', 'all')
    f_days = request.args.get('days', 30, type=int)
    if f_days not in (7, 14, 30, 90, 365):
        f_days = 30

    analytics = compute_report_analytics(f_location, f_animal, f_days)
    veterinarian_summary = build_vet_summary()

    return render_template('organization_admin/reports.html',
                         form=form,
                         reports=reports,
                         disease_labels=analytics['disease_labels'],
                         disease_values=analytics['disease_values'],
                         disease_rows=analytics['disease_rows'],
                         location_disease_summary=analytics['location_summary'],
                         trend_labels=analytics['trend_labels'],
                         trend_values=analytics['trend_values'],
                         veterinarian_summary=veterinarian_summary,
                         location_options=analytics['location_options'],
                         f_location=f_location,
                         f_animal=f_animal,
                         f_days=f_days)


@app.route('/organization/reports/pdf')
@login_required
@role_required('organization_admin')
def org_reports_pdf():
    if not PDF_AVAILABLE:
        flash('PDF export is unavailable: install reportlab and matplotlib.', 'danger')
        return redirect(url_for('org_reports'))

    f_location = request.args.get('location', 'all')
    f_animal = request.args.get('animal_type', 'all')
    f_days = request.args.get('days', 30, type=int)
    if f_days not in (7, 14, 30, 90, 365):
        f_days = 30

    analytics = compute_report_analytics(f_location, f_animal, f_days)
    generated_on = get_malawi_time().strftime('%Y-%m-%d %H:%M')
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
        meta,
        analytics['disease_rows'],
        analytics['location_summary'],
        build_vet_summary(),
        trend_labels=analytics['trend_labels'],
        trend_values=analytics['trend_values'],
        generated_on=generated_on)
    fname = 'disease_analytics_%s.pdf' % get_malawi_time().strftime('%Y%m%d_%H%M')
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=fname)

# System Admin Routes
@app.route('/system/dashboard')
@login_required
@role_required('system_admin')
def sys_admin_dashboard():
    # Real system health metrics derived from the application's own logs and host.
    day_ago = get_malawi_time() - timedelta(days=1)
    active_users = User.query.filter(User.last_login >= get_malawi_time() - timedelta(hours=1)).count()

    # "Requests" proxy = number of logged system events in the last 24h.
    logs_last_day = SystemLog.query.filter(SystemLog.timestamp >= day_ago).count()
    error_logs_last_day = SystemLog.query.filter(
        SystemLog.timestamp >= day_ago,
        SystemLog.level.in_(['error', 'critical'])
    ).count()
    api_requests = logs_last_day
    # Uptime proxy = fraction of recent events that were not errors.
    uptime = (1 - (error_logs_last_day / logs_last_day)) if logs_last_day else 1.0

    # System alerts
    system_alerts = SystemLog.query.filter(
        SystemLog.level.in_(['error', 'critical']),
        SystemLog.timestamp >= day_ago
    ).order_by(SystemLog.timestamp.desc()).limit(5).all()

    # Real component status: DB checked live, prediction engine checked via model file.
    try:
        db.session.execute(text('SELECT 1'))
        database_status = 'running'
    except Exception:
        database_status = 'down'
    prediction_status = 'running' if MODEL_PATH.exists() and FEATURE_ENCODING_PATH.exists() else 'down'
    component_status = {
        'web_server': 'running',
        'database': database_status,
        'prediction_engine': prediction_status,
    }

    # Real host resource usage (percent) via psutil.
    try:
        import psutil
        cpu_usage = psutil.cpu_percent(interval=0.3)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage(str(Path(__file__).resolve().parent)).percent
    except Exception:
        cpu_usage = memory_usage = disk_usage = None

    return render_template('system_admin/dashboard.html',
                         uptime=uptime,
                         active_users=active_users,
                         api_requests=api_requests,
                         system_alerts=system_alerts,
                         component_status=component_status,
                         cpu_usage=cpu_usage,
                         memory_usage=memory_usage,
                         disk_usage=disk_usage)

@app.route('/system/logs')
@login_required
@role_required('system_admin')
def system_logs():
    level = request.args.get('level', 'all')
    component = request.args.get('component', 'all')
    time_range = request.args.get('time_range', '24h')
    
    # Calculate time filter
    if time_range == '1h':
        time_filter = get_malawi_time() - timedelta(hours=1)
    elif time_range == '24h':
        time_filter = get_malawi_time() - timedelta(days=1)
    elif time_range == '7d':
        time_filter = get_malawi_time() - timedelta(days=7)
    elif time_range == '30d':
        time_filter = get_malawi_time() - timedelta(days=30)
    else:
        time_filter = get_malawi_time() - timedelta(days=1)
    
    # Build query
    query = SystemLog.query.filter(SystemLog.timestamp >= time_filter)
    
    if level != 'all':
        query = query.filter(SystemLog.level == level)
    
    if component != 'all':
        query = query.filter(SystemLog.component == component)
    
    logs = query.order_by(SystemLog.timestamp.desc()).limit(100).all()
    
    # Statistics
    total_logs = len(logs)
    error_count = len([log for log in logs if log.level == 'error'])
    warning_count = len([log for log in logs if log.level == 'warning'])
    
    return render_template('system_admin/system_logs.html',
                         logs=logs,
                         total_logs=total_logs,
                         error_count=error_count,
                         warning_count=warning_count,
                         current_level=level,
                         current_component=component,
                         current_time_range=time_range)

@app.route('/system/performance')
@login_required
@role_required('system_admin')
def performance_reports():
    # Real host metrics via psutil; error rate derived from the app's own logs.
    day_ago = get_malawi_time() - timedelta(days=1)
    total_logs = SystemLog.query.filter(SystemLog.timestamp >= day_ago).count()
    error_logs = SystemLog.query.filter(
        SystemLog.timestamp >= day_ago,
        SystemLog.level.in_(['error', 'critical'])
    ).count()
    error_rate = (error_logs / total_logs) if total_logs else 0.0

    try:
        import psutil
        cpu_usage = psutil.cpu_percent(interval=0.3) / 100.0
        memory_usage = psutil.virtual_memory().percent / 100.0
        disk_usage = psutil.disk_usage(str(Path(__file__).resolve().parent)).percent / 100.0
    except Exception:
        cpu_usage = memory_usage = disk_usage = None

    metrics = {
        'response_time': None,  # no request-timing instrumentation available
        'error_rate': error_rate,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage,
        'api_success_rate': 1 - error_rate
    }

    # Real activity breakdown by logged component over the last 24h.
    component_rows = db.session.query(
        SystemLog.component,
        db.func.count(SystemLog.id),
        db.func.sum(db.case((SystemLog.level.in_(['error', 'critical']), 1), else_=0))
    ).filter(SystemLog.timestamp >= day_ago).group_by(SystemLog.component).all()

    api_performance = []
    for component, count, errors in component_rows:
        errors = errors or 0
        api_performance.append({
            'endpoint': component or 'unknown',
            'avg_response': None,
            'success_rate': (1 - errors / count) if count else 1.0,
            'requests': count
        })

    return render_template('system_admin/performance_report.html',
                         metrics=metrics,
                         api_performance=api_performance)

@app.route('/system/updates')
@login_required
@role_required('system_admin')
def model_updates():
    # Real model versions recorded in the database.
    model_versions = ModelVersion.query.order_by(ModelVersion.id.desc()).all()
    available_updates = [
        {
            'id': mv.version,
            'version': mv.version,
            'type': mv.algorithm or 'model',
            'size': mv.training_data_size,
            'status': mv.status or 'unknown',
            'accuracy': mv.accuracy,
            'deployment_date': mv.deployment_date
        }
        for mv in model_versions
    ]

    return render_template('system_admin/model_updates.html',
                         available_updates=available_updates,
                         deployment_schedule=[])

# API Routes for AJAX calls
@app.route('/api/predictions/<int:prediction_id>/review', methods=['POST'])
@login_required
@role_required('veterinarian')
def review_prediction(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)

    payload = request.get_json(silent=True) or request.form
    action = payload.get('action')
    notes = payload.get('notes', '')
    new_diagnosis = (payload.get('diagnosis') or '').strip()

    if action == 'confirm':
        prediction.review_status = 'confirmed'
        prediction.review_notes = notes
        prediction.reviewed_by = current_user.id
        prediction.reviewed_at = get_malawi_time()
        
        # Create a placeholder treatment only if the vet has not already added one
        # (a detailed plan can be added via "Add Treatment").
        treatment = prediction.symptom_report.treatment
        if treatment is None:
            treatment = Treatment(
                treatment_id=generate_treatment_id(),
                symptom_report_id=prediction.symptom_report_id,
                vet_id=current_user.id,
                medication='To be prescribed',
                dosage='As advised',
                frequency='As advised',
                duration='As advised',
                route='oral',
                status='pending_approval'
            )
            db.session.add(treatment)

        # Update symptom report status
        prediction.symptom_report.status = 'reviewed'

        # Notify farmer
        create_notification(
            prediction.symptom_report.farmer_id,
            'treatment',
            'Treatment Plan Available',
            f'Treatment plan available for {prediction.symptom_report.animal_name}',
            'medium',
            treatment.id
        )
        
        flash('Prediction confirmed and treatment plan created!', 'success')
        
    elif action == 'modify':
        prediction.review_status = 'modified'
        prediction.review_notes = notes
        if new_diagnosis:
            prediction.disease_name = new_diagnosis
            prediction.disease_category = categorize_disease(new_diagnosis)
        prediction.reviewed_by = current_user.id
        prediction.reviewed_at = get_malawi_time()
        prediction.symptom_report.status = 'reviewed'

        # Notify farmer of the vet's revised diagnosis
        create_notification(
            prediction.symptom_report.farmer_id,
            'review',
            'Diagnosis Updated by Veterinarian',
            f'Your veterinarian updated the diagnosis for {prediction.symptom_report.animal_name} to {prediction.disease_name}',
            'medium',
            prediction.id
        )

        flash('Prediction modified successfully!', 'success')
    else:
        flash('Unknown review action.', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': 'unknown action'}), 400
        return redirect(url_for('predictions_review'))

    db.session.commit()
    log_system_event('info', 'review', f'Prediction {prediction_id} reviewed by {current_user.username}', current_user.id)

    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('predictions_review'))

@app.route('/api/treatments/<int:treatment_id>/approve', methods=['POST'])
@login_required
@role_required('veterinarian')
def approve_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    
    treatment.status = 'in_progress'
    treatment.start_date = date.today()
    
    db.session.commit()
    
    # Notify farmer
    create_notification(
        treatment.symptom_report.farmer_id,
        'treatment',
        'Treatment Approved',
        f'Treatment for {treatment.symptom_report.animal_name} has been approved',
        'medium',
        treatment.id
    )
    
    log_system_event('info', 'treatment', f'Treatment {treatment_id} approved by {current_user.username}', current_user.id)
    
    return jsonify({'success': True})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    log_system_event('error', 'system', f'Internal server error: {str(e)}', current_user.id if current_user.is_authenticated else None)
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
