from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta, timezone
import json

def get_malawi_time():
    return datetime.now(timezone(timedelta(hours=2)))

db = SQLAlchemy()

# Association table for farmer-veterinarian mapping
farmer_veterinarian = db.Table('farmer_veterinarian',
    db.Column('farmer_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('veterinarian_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('assigned_date', db.DateTime, default=get_malawi_time)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)  # farmer, veterinarian, organization_admin, system_admin
    location = db.Column(db.String(200))
    specific_location = db.Column(db.String(200))
    farm_name = db.Column(db.String(100))
    animal_types = db.Column(db.String(200))  # Will be 'cattle', 'goat', or 'cattle,goat'
    production_focus = db.Column(db.String(50))  # dairy, meat, dual, breeding
    registration_date = db.Column(db.DateTime, default=get_malawi_time)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected
    approved_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    
    # Relationships
    symptoms = db.relationship('SymptomReport', backref='farmer', foreign_keys='SymptomReport.farmer_id')
    predictions = db.relationship('Prediction', backref='user', foreign_keys='Prediction.user_id')
    treatments = db.relationship('Treatment', backref='veterinarian', foreign_keys='Treatment.vet_id')
    
    # Many-to-many relationship for farmer-vet mapping
    assigned_farmers = db.relationship('User',
        secondary=farmer_veterinarian,
        primaryjoin=(farmer_veterinarian.c.veterinarian_id == id),
        secondaryjoin=(farmer_veterinarian.c.farmer_id == id),
        backref=db.backref('assigned_veterinarians', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_farmer(self):
        return self.role == 'farmer'
    
    def is_veterinarian(self):
        return self.role == 'veterinarian'
    
    def is_organization_admin(self):
        return self.role == 'organization_admin'
    
    def is_system_admin(self):
        return self.role == 'system_admin'

    def is_approved_user(self):
        return self.status == 'approved'
    
    def get_animal_types_list(self):
        if self.animal_types:
            return [at.strip() for at in self.animal_types.split(',')]
        return []

class SymptomReport(db.Model):
    __tablename__ = 'symptom_report'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(20), unique=True, nullable=False)  # Format: R-YYYY-NNN
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    animal_id = db.Column(db.String(50))
    animal_name = db.Column(db.String(100))
    animal_type = db.Column(db.String(10))  # 'cattle' or 'goat'
    animal_age = db.Column(db.Integer)  # in months
    animal_weight = db.Column(db.Float)  # in kg
    animal_breed = db.Column(db.String(50))  # e.g., Holstein, Saanen
    
    # Symptoms specific to cattle and goats
    appetite = db.Column(db.String(20))  # normal, reduced, none, increased
    temperature = db.Column(db.Float)  # in Celsius
    heart_rate = db.Column(db.Integer)  # beats per minute
    respiration_rate = db.Column(db.Integer)  # breaths per minute
    rumen_movement = db.Column(db.String(20))  # normal, reduced, absent
    stool_consistency = db.Column(db.String(20))  # normal, loose, watery, firm
    milk_production = db.Column(db.String(20))  # normal, reduced, stopped (for dairy)
    additional_symptoms = db.Column(db.Text)  # JSON string of symptoms
    
    # Environmental factors
    feed_type = db.Column(db.String(100))
    feed_changes = db.Column(db.Text)
    housing_conditions = db.Column(db.String(100))
    recent_treatments = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, predicted, reviewed, resolved
    created_at = db.Column(db.DateTime, default=get_malawi_time)
    updated_at = db.Column(db.DateTime, default=get_malawi_time, onupdate=get_malawi_time)
    
    # Relationships
    prediction = db.relationship('Prediction', backref='symptom_report', uselist=False)
    treatment = db.relationship('Treatment', backref='symptom_report', uselist=False)
    
    # Cattle specific fields
    is_dairy = db.Column(db.Boolean, default=False)
    lactation_stage = db.Column(db.String(20))  # early, mid, late, dry
    
    # Goat specific fields
    is_dairy_goat = db.Column(db.Boolean, default=False)
    horn_status = db.Column(db.String(20))  # horned, polled, disbudded
    
    def get_additional_symptoms_list(self):
        if self.additional_symptoms:
            return json.loads(self.additional_symptoms)
        return []

class Prediction(db.Model):
    __tablename__ = 'prediction'
    
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.String(20), unique=True, nullable=False)  # Format: PRED-YYYY-NNN
    symptom_report_id = db.Column(db.Integer, db.ForeignKey('symptom_report.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Prediction details
    disease_name = db.Column(db.String(100))
    disease_category = db.Column(db.String(50))  # respiratory, parasitic, nutritional, metabolic, other
    confidence = db.Column(db.Float)  # 0.0 to 1.0
    severity = db.Column(db.String(20))  # mild, moderate, severe, critical
    predicted_at = db.Column(db.DateTime, default=get_malawi_time)
    
    # Common cattle/goat diseases
    possible_diseases = db.Column(db.Text)  # JSON list of possible diseases with probabilities
    
    # Review status
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_status = db.Column(db.String(20), default='pending')  # pending, confirmed, modified, rejected
    review_notes = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    
    # Model info
    model_version = db.Column(db.String(20))
    features_used = db.Column(db.Text)  # JSON string of features
    
    def get_possible_diseases(self):
        if self.possible_diseases:
            return json.loads(self.possible_diseases)
        return []

class Treatment(db.Model):
    __tablename__ = 'treatment'
    
    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.String(20), unique=True, nullable=False)  # Format: T-YYYY-NNN
    symptom_report_id = db.Column(db.Integer, db.ForeignKey('symptom_report.id'), nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Treatment details for cattle/goats
    medication = db.Column(db.String(200))
    medication_type = db.Column(db.String(50))  # antibiotic, antiparasitic, vitamin, other
    dosage = db.Column(db.String(100))
    dosage_per_kg = db.Column(db.Float)
    frequency = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    route = db.Column(db.String(20))  # oral, injection, topical, inhalation
    withdrawal_period = db.Column(db.Integer)  # days (important for milk/meat)
    
    # Supportive care
    supportive_care = db.Column(db.Text)  # e.g., "Provide clean water, isolate animal"
    diet_recommendations = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='prescribed')  # prescribed, in_progress, completed, cancelled
    prescribed_at = db.Column(db.DateTime, default=get_malawi_time)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # Outcome
    outcome = db.Column(db.String(20))  # cured, improved, no_change, worsened
    effectiveness = db.Column(db.Float)  # 0.0 to 1.0
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    
    # For dairy animals
    milk_withdrawal_days = db.Column(db.Integer)
    meat_withdrawal_days = db.Column(db.Integer)

class MortalityReport(db.Model):
    __tablename__ = 'mortality_report'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(20), unique=True, nullable=False)  # Format: M-YYYY-NNN
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Animal details
    animal_type = db.Column(db.String(10))  # 'cattle' or 'goat'
    animal_id = db.Column(db.String(50))
    animal_name = db.Column(db.String(100))
    age = db.Column(db.Integer)  # in months
    breed = db.Column(db.String(50))
    
    # Mortality details
    date_of_death = db.Column(db.Date)
    suspected_cause = db.Column(db.String(100))
    confirmed_cause = db.Column(db.String(100))
    symptoms_before_death = db.Column(db.Text)
    
    # For cattle/goats
    was_dairy = db.Column(db.Boolean, default=False)
    last_milk_production = db.Column(db.String(50))
    
    # Investigation
    requires_investigation = db.Column(db.Boolean, default=False)
    investigation_notes = db.Column(db.Text)
    lab_results = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_malawi_time)

class DiseaseLibrary(db.Model):
    __tablename__ = 'disease_library'
    
    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(100), nullable=False)
    animal_type = db.Column(db.String(10))  # cattle, goat, both
    category = db.Column(db.String(50))  # respiratory, parasitic, etc.
    common_name = db.Column(db.String(100))
    scientific_name = db.Column(db.String(100))
    
    # Symptoms
    primary_symptoms = db.Column(db.Text)  # JSON list
    secondary_symptoms = db.Column(db.Text)  # JSON list
    incubation_period = db.Column(db.String(50))
    
    # Treatment
    recommended_treatments = db.Column(db.Text)  # JSON list
    prevention_measures = db.Column(db.Text)
    
    # Impact
    mortality_rate = db.Column(db.Float)
    economic_impact = db.Column(db.String(50))  # low, medium, high
    zoonotic = db.Column(db.Boolean, default=False)  # Can spread to humans
    
    created_at = db.Column(db.DateTime, default=get_malawi_time)
    updated_at = db.Column(db.DateTime, default=get_malawi_time, onupdate=get_malawi_time)

class BreedingRecord(db.Model):
    __tablename__ = 'breeding_record'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    animal_type = db.Column(db.String(10))  # cattle or goat
    animal_id = db.Column(db.String(50))
    
    # Breeding details
    breeding_date = db.Column(db.Date)
    sire_id = db.Column(db.String(50))
    dam_id = db.Column(db.String(50))
    breeding_method = db.Column(db.String(50))  # natural, AI
    
    # Pregnancy
    pregnancy_confirmed = db.Column(db.Boolean, default=False)
    confirmation_date = db.Column(db.Date)
    expected_calving_kidding_date = db.Column(db.Date)
    
    # Outcome
    actual_calving_kidding_date = db.Column(db.Date)
    number_of_offspring = db.Column(db.Integer)
    offspring_health = db.Column(db.String(50))
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=get_malawi_time)

# Other models remain the same as before...
class SystemLog(db.Model):
    __tablename__ = 'system_log'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=get_malawi_time, index=True)
    level = db.Column(db.String(20))  # info, warning, error, critical, debug
    component = db.Column(db.String(50))  # web, api, db, model, auth, notification
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45))
    message = db.Column(db.Text)
    details = db.Column(db.Text)  # JSON string for additional details

class PerformanceMetric(db.Model):
    __tablename__ = 'performance_metric'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_date = db.Column(db.Date, default=date.today, index=True)
    metric_type = db.Column(db.String(50))  # uptime, response_time, error_rate, cpu_usage, etc.
    value = db.Column(db.Float)
    target_value = db.Column(db.Float)
    unit = db.Column(db.String(20))
    recorded_at = db.Column(db.DateTime, default=get_malawi_time)

class ModelVersion(db.Model):
    __tablename__ = 'model_version'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20))  # training, staging, production, archived
    accuracy = db.Column(db.Float)
    training_data_size = db.Column(db.Integer)
    training_date = db.Column(db.Date)
    deployment_date = db.Column(db.Date, nullable=True)
    algorithm = db.Column(db.String(50))
    hyperparameters = db.Column(db.Text)  # JSON string
    performance_metrics = db.Column(db.Text)  # JSON string
    animal_types = db.Column(db.String(50))  # cattle, goat, both
    created_at = db.Column(db.DateTime, default=get_malawi_time)

class Report(db.Model):
    __tablename__ = 'report'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(20), unique=True, nullable=False)  # Format: REP-YYYY-NNN
    report_type = db.Column(db.String(50))  # performance, breeding, health, mortality, production
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    generated_at = db.Column(db.DateTime, default=get_malawi_time)
    file_path = db.Column(db.String(200))
    file_size = db.Column(db.Integer)
    data_points = db.Column(db.Text)  # JSON string of included data
    is_scheduled = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.String(20))  # daily, weekly, monthly

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_type = db.Column(db.String(50))  # prediction, treatment, mortality, breeding, system_alert
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    priority = db.Column(db.String(20))  # low, medium, high, critical
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_malawi_time)
    action_url = db.Column(db.String(200))
    related_id = db.Column(db.Integer)  # ID of related entity

class Configuration(db.Model):
    __tablename__ = 'configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))  # general, notification, security, api, database
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    data_type = db.Column(db.String(20))  # string, integer, float, boolean, json
    description = db.Column(db.Text)
    last_modified = db.Column(db.DateTime, default=get_malawi_time, onupdate=get_malawi_time)
    modified_by = db.Column(db.Integer, db.ForeignKey('user.id'))
