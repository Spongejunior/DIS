import os
import sys

PROJECT_VENDOR_PATH = os.path.join(os.path.dirname(__file__), '.vendor')
if os.path.isdir(PROJECT_VENDOR_PATH) and PROJECT_VENDOR_PATH not in sys.path:
    sys.path.insert(0, PROJECT_VENDOR_PATH)

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session, abort, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import json
import random
import string
from functools import wraps

from config import config
from models import db, User, SymptomReport, Prediction, Treatment, MortalityReport, SystemLog, PerformanceMetric, ModelVersion, Report, Notification, Configuration
from forms import LoginForm, RegistrationForm, SymptomForm, TreatmentForm, MortalityReportForm, ProfileForm, ChangePasswordForm, ConfigurationForm, ReportGenerationForm

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config['development'])
config['development'].init_app(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

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

def get_notification_action_url(notification_type, related_id=None):
    if not related_id:
        return None

    routes = {
        'prediction': 'farmer_predictions',
        'review': 'predictions_review',
        'treatment': 'treatment_suggestions',
        'mortality': 'mortality_reports'
    }
    endpoint = routes.get(notification_type)
    return url_for(endpoint) if endpoint else None

def log_system_event(level, component, message, user_id=None, details=None):
    log = SystemLog(
        level=level,
        component=component,
        user_id=user_id,
        ip_address=request.remote_addr,
        message=message,
        details=json.dumps(details) if details else None
    )
    db.session.add(log)
    db.session.commit()

def create_notification(user_id, notification_type, title, message, priority='medium', related_id=None):
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        action_url=get_notification_action_url(notification_type, related_id),
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()

def create_default_users():
    # Create system admin if not exists
    if not User.query.filter_by(username='sysadmin').first():
        sysadmin = User(
            username='sysadmin',
            email='sysadmin@animalhealth.com',
            full_name='System Administrator',
            role='system_admin',
            location='Headquarters'
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
            location='Headquarters'
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
            location='Central District'
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
            location='123 Farm Road, Green Valley',
            farm_name='Green Valley Farm',
            farm_size='50 acres',
            animal_types='Cattle,Poultry,Goats'
        )
        farmer.set_password('pass123')
        db.session.add(farmer)
    
    db.session.commit()

# Create tables and seed default users after helper definitions are available
with app.app_context():
    db.create_all()
    create_default_users()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            # Check role
            if user.role != form.role.data:
                flash(f'Please select correct role: {user.role}', 'warning')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            log_system_event('info', 'auth', f'User {user.username} logged in', user.id)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)

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
            location=form.location.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        log_system_event('info', 'auth', f'New user registered: {user.username}', user.id)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    log_system_event('info', 'auth', f'User {current_user.username} logged out', current_user.id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

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
    
    return render_template('farmer/dashboard.html',
                         total_reports=total_reports,
                         pending_predictions=pending_predictions,
                         recent_predictions=recent_predictions,
                         notifications=notifications)

@app.route('/farmer/symptoms', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def symptom_form():
    form = SymptomForm()
    if form.validate_on_submit():
        selected_symptoms = request.form.getlist('symptoms')
        free_text_symptoms = form.additional_symptoms.data.strip() if form.additional_symptoms.data else ''
        combined_symptoms = selected_symptoms.copy()
        if free_text_symptoms:
            combined_symptoms.append(f'notes:{free_text_symptoms}')
        
        report = SymptomReport(
            report_id=generate_report_id(),
            farmer_id=current_user.id,
            animal_id=form.animal_id.data,
            animal_name=form.animal_name.data or form.animal_id.data,
            animal_type=form.animal_type.data,
            animal_age=form.animal_age.data,
            animal_weight=form.animal_weight.data,
            animal_breed=form.animal_breed.data,
            appetite=form.appetite.data,
            temperature=form.temperature.data,
            heart_rate=form.heart_rate.data,
            respiration_rate=form.respiration_rate.data,
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
        
        # Create prediction (simulated)
        prediction = create_prediction(report)
        
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

def create_prediction(report):
    # Simulate AI prediction
    diseases = {
        'cattle': ['Respiratory Infection', 'Foot Rot', 'Mastitis', 'Bloat'],
        'poultry': ['Avian Influenza', 'Newcastle Disease', 'Coccidiosis', 'Fowl Pox'],
        'goat': ['Parasitic Infection', 'Pneumonia', 'Enterotoxemia', 'Caseous Lymphadenitis'],
        'sheep': ['Foot Rot', 'Pneumonia', 'Enterotoxemia', 'Scrapie'],
        'pig': ['Swine Flu', 'Porcine Reproductive', 'Respiratory Syndrome', 'Diarrhea']
    }
    
    animal_type = report.animal_type
    possible_diseases = diseases.get(animal_type, ['General Infection'])
    
    # Simple rule-based prediction
    confidence = 0.7
    if report.temperature and report.temperature > 39.5:
        confidence += 0.15
    if report.appetite == 'none':
        confidence += 0.1
    confidence = min(confidence, 0.95)
    
    prediction = Prediction(
        prediction_id=generate_prediction_id(),
        symptom_report_id=report.id,
        user_id=report.farmer_id,
        disease_name=random.choice(possible_diseases),
        disease_category='general',
        confidence=confidence,
        severity='moderate' if confidence < 0.8 else 'high',
        model_version='v2.1.4',
        possible_diseases=json.dumps(possible_diseases),
        review_status='pending'
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
    
    return render_template('farmer/symptom_history.html', reports=reports)

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

@app.route('/farmer/profile', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def farmer_registration():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.farm_name = form.farm_name.data
        current_user.location = form.location.data
        current_user.farm_size = form.farm_size.data
        current_user.animal_types = form.animal_types.data
        
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
    
    return render_template('veterinarian/dashboard.html',
                         assigned_farmers=assigned_farmers,
                         pending_reviews=pending_reviews,
                         active_treatments=active_treatments,
                         recent_mortality=recent_mortality)

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
    pending_predictions = Prediction.query.join(SymptomReport).filter(
        SymptomReport.status == 'predicted',
        Prediction.review_status == 'pending',
        SymptomReport.farmer_id.in_(assigned_farmer_ids if assigned_farmer_ids else [-1])
    ).order_by(Prediction.predicted_at.desc()).all()
    
    reviewed_predictions = Prediction.query.join(SymptomReport).filter(
        Prediction.review_status.in_(['confirmed', 'modified']),
        Prediction.reviewed_by == current_user.id
    ).order_by(Prediction.reviewed_at.desc()).limit(10).all()
    
    return render_template('veterinarian/prediction_review.html',
                         pending_predictions=pending_predictions,
                         reviewed_predictions=reviewed_predictions)

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
        MortalityReport.created_at >= datetime.utcnow() - timedelta(days=30)
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
    system_accuracy = 0.892  # This would come from performance metrics
    
    # Recent activities
    recent_logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(10).all()
    
    return render_template('organization_admin/dashboard.html',
                         total_farmers=total_farmers,
                         total_veterinarians=total_veterinarians,
                         active_predictions=active_predictions,
                         system_accuracy=system_accuracy,
                         recent_logs=recent_logs)

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
    
    return render_template('organization_admin/reports.html',
                         form=form,
                         reports=reports)

@app.route('/organization/configuration', methods=['GET', 'POST'])
@login_required
@role_required('organization_admin')
def system_config():
    form = ConfigurationForm()
    
    # Load current configuration
    if request.method == 'GET':
        # This would load from Configuration table
        form.system_name.data = app.config['APP_NAME']
        form.prediction_timeout.data = app.config['PREDICTION_TIMEOUT']
        form.max_predictions_per_day.data = app.config['MAX_PREDICTIONS_PER_DAY']
    
    if form.validate_on_submit():
        # Save configuration (simulated - would save to Configuration table)
        flash('System configuration updated successfully!', 'success')
        return redirect(url_for('system_config'))
    
    return render_template('organization_admin/system_config.html', form=form)

@app.route('/organization/model-management')
@login_required
@role_required('organization_admin')
def model_management():
    # Get model versions
    model_versions = ModelVersion.query.order_by(ModelVersion.created_at.desc()).all()
    
    # Get performance metrics
    performance_data = {
        'current_accuracy': 0.892,
        'training_data_size': 45230,
        'monthly_predictions': 12400,
        'accuracy_trend': 'up'
    }
    
    return render_template('organization_admin/model_management.html',
                         model_versions=model_versions,
                         performance_data=performance_data)

# System Admin Routes
@app.route('/system/dashboard')
@login_required
@role_required('system_admin')
def sys_admin_dashboard():
    # System health metrics
    uptime = 0.998  # This would come from monitoring system
    active_users = User.query.filter(User.last_login >= datetime.utcnow() - timedelta(hours=1)).count()
    api_requests = 12400  # Simulated
    
    # System alerts
    system_alerts = SystemLog.query.filter(
        SystemLog.level.in_(['error', 'critical']),
        SystemLog.timestamp >= datetime.utcnow() - timedelta(days=1)
    ).order_by(SystemLog.timestamp.desc()).limit(5).all()
    
    # Component status (simulated)
    component_status = {
        'web_server': 'running',
        'database': 'running',
        'prediction_engine': 'running',
        'api_gateway': 'running',
        'cache_server': 'running',
        'notification_service': 'degraded'
    }
    
    return render_template('system_admin/dashboard.html',
                         uptime=uptime,
                         active_users=active_users,
                         api_requests=api_requests,
                         system_alerts=system_alerts,
                         component_status=component_status)

@app.route('/system/logs')
@login_required
@role_required('system_admin')
def system_logs():
    level = request.args.get('level', 'all')
    component = request.args.get('component', 'all')
    time_range = request.args.get('time_range', '24h')
    
    # Calculate time filter
    if time_range == '1h':
        time_filter = datetime.utcnow() - timedelta(hours=1)
    elif time_range == '24h':
        time_filter = datetime.utcnow() - timedelta(days=1)
    elif time_range == '7d':
        time_filter = datetime.utcnow() - timedelta(days=7)
    elif time_range == '30d':
        time_filter = datetime.utcnow() - timedelta(days=30)
    else:
        time_filter = datetime.utcnow() - timedelta(days=1)
    
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
    # Performance metrics (simulated)
    metrics = {
        'response_time': 42,  # ms
        'error_rate': 0.0012,  # 0.12%
        'cpu_usage': 0.42,  # 42%
        'memory_usage': 0.68,  # 68%
        'disk_usage': 0.85,  # 85%
        'api_success_rate': 0.998  # 99.8%
    }
    
    # API performance breakdown
    api_performance = [
        {'endpoint': 'GET /api/symptoms', 'avg_response': 45, 'success_rate': 0.998, 'requests': 1245},
        {'endpoint': 'POST /api/predict', 'avg_response': 128, 'success_rate': 0.985, 'requests': 842},
        {'endpoint': 'GET /api/treatments', 'avg_response': 62, 'success_rate': 0.992, 'requests': 568},
        {'endpoint': 'POST /api/reports', 'avg_response': 89, 'success_rate': 0.978, 'requests': 324}
    ]
    
    return render_template('system_admin/performance_report.html',
                         metrics=metrics,
                         api_performance=api_performance)

@app.route('/system/updates')
@login_required
@role_required('system_admin')
def model_updates():
    # Available updates (simulated)
    available_updates = [
        {
            'id': 'UPD-2024-015',
            'version': 'v2.1.5',
            'type': 'minor',
            'size': 245,
            'status': 'available'
        },
        {
            'id': 'UPD-2024-014',
            'version': 'v2.1.4',
            'type': 'security',
            'size': 128,
            'status': 'installed'
        }
    ]
    
    # Update deployment schedule
    deployment_schedule = [
        {'step': 'Pre-deployment Check', 'status': 'completed'},
        {'step': 'Backup Services', 'status': 'completed'},
        {'step': 'Deploy Update', 'status': 'pending'},
        {'step': 'Verification', 'status': 'scheduled'},
        {'step': 'Post-deployment', 'status': 'scheduled'}
    ]
    
    return render_template('system_admin/model_updates.html',
                         available_updates=available_updates,
                         deployment_schedule=deployment_schedule)

# API Routes for AJAX calls
@app.route('/api/predictions/<int:prediction_id>/review', methods=['POST'])
@login_required
@role_required('veterinarian')
def review_prediction(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    
    action = request.json.get('action')
    notes = request.json.get('notes', '')
    
    if action == 'confirm':
        prediction.review_status = 'confirmed'
        prediction.review_notes = notes
        prediction.reviewed_by = current_user.id
        prediction.reviewed_at = datetime.utcnow()
        
        # Create treatment suggestion
        treatment = Treatment(
            treatment_id=generate_treatment_id(),
            symptom_report_id=prediction.symptom_report_id,
            vet_id=current_user.id,
            medication='Antibiotic Treatment',
            dosage='As prescribed',
            frequency='Twice daily',
            duration='5 days',
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
        prediction.reviewed_by = current_user.id
        prediction.reviewed_at = datetime.utcnow()
        
        flash('Prediction modified successfully!', 'success')
    
    db.session.commit()
    log_system_event('info', 'review', f'Prediction {prediction_id} reviewed by {current_user.username}', current_user.id)
    
    return jsonify({'success': True})

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
