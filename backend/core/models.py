"""Database models.

Table and column names are the ones the Flask/SQLAlchemy version created, so
an existing database keeps working (see README: ``migrate --fake-initial``).
Times are stored as Malawi local time without a time zone.
"""
import json
from datetime import date, datetime, timedelta, timezone

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
# Password hashes are in Werkzeug's format (scrypt/pbkdf2), as the Flask
# version stored them, so existing passwords keep working.
from werkzeug.security import check_password_hash, generate_password_hash

MALAWI_TZ = timezone(timedelta(hours=2))


def malawi_now():
    """The current time in Malawi (UTC+2), as stored in the database."""
    return datetime.now(MALAWI_TZ).replace(tzinfo=None)


def as_malawi_time(value):
    """A stored time as naive Malawi time (older rows may carry an offset)."""
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(MALAWI_TZ).replace(tzinfo=None)


class UserManager(BaseUserManager):
    pass


class User(AbstractBaseUser):
    # AbstractBaseUser's fields, on the existing columns.
    password = models.CharField(max_length=256, db_column='password_hash')
    last_login = models.DateTimeField(null=True, blank=True)

    username = models.CharField(max_length=80, unique=True)
    email = models.CharField(max_length=120, unique=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20)  # farmer, veterinarian, organization_admin, system_admin
    location = models.CharField(max_length=200, null=True, blank=True)  # EPA
    specific_location = models.CharField(max_length=200, null=True, blank=True)  # section / village
    farm_name = models.CharField(max_length=100, null=True, blank=True)
    animal_types = models.CharField(max_length=200, null=True, blank=True)  # 'cattle', 'goat' or 'cattle,goat'
    production_focus = models.CharField(max_length=50, null=True, blank=True)  # dairy, meat, dual, breeding
    registration_date = models.DateTimeField(default=malawi_now, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True)
    status = models.CharField(max_length=20, default='pending')  # pending, approved, rejected
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    reset_token = models.CharField(max_length=128, null=True, blank=True)
    reset_token_expires_at = models.DateTimeField(null=True, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')  # en, chi, tum

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)
        self._password = raw_password

    def check_password(self, raw_password):
        return bool(self.password) and check_password_hash(self.password, raw_password)

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
            return [animal_type.strip() for animal_type in self.animal_types.split(',')]
        return []

    @property
    def assigned_farmers(self):
        """Farmers linked to this veterinarian."""
        return User.objects.filter(veterinarian_links__veterinarian=self).distinct().order_by('id')

    @property
    def assigned_veterinarians(self):
        """Veterinarians linked to this farmer."""
        return User.objects.filter(farmer_links__farmer=self).distinct().order_by('id')


class FarmerVeterinarian(models.Model):
    """Farmer <-> veterinarian assignment (the existing association table)."""
    pk = models.CompositePrimaryKey('farmer_id', 'veterinarian_id')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='veterinarian_links')
    veterinarian = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmer_links')
    assigned_date = models.DateTimeField(default=malawi_now, null=True, blank=True)

    class Meta:
        db_table = 'farmer_veterinarian'


class SymptomReport(models.Model):
    report_id = models.CharField(max_length=20, unique=True)  # R-YYYY-NNN
    farmer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='symptoms')
    animal_id = models.CharField(max_length=50, null=True, blank=True)
    animal_name = models.CharField(max_length=100, null=True, blank=True)
    animal_type = models.CharField(max_length=10, null=True, blank=True)  # 'cattle' or 'goat'
    animal_sex = models.CharField(max_length=10, null=True, blank=True)  # 'male' or 'female'
    animal_age = models.IntegerField(null=True, blank=True)  # months
    animal_weight = models.FloatField(null=True, blank=True)  # kg
    animal_breed = models.CharField(max_length=50, null=True, blank=True)

    appetite = models.CharField(max_length=20, null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)  # Celsius
    heart_rate = models.IntegerField(null=True, blank=True)
    respiration_rate = models.IntegerField(null=True, blank=True)
    rumen_movement = models.CharField(max_length=20, null=True, blank=True)
    stool_consistency = models.CharField(max_length=20, null=True, blank=True)
    milk_production = models.CharField(max_length=20, null=True, blank=True)
    additional_symptoms = models.TextField(null=True, blank=True)  # JSON list of symptoms

    feed_type = models.CharField(max_length=100, null=True, blank=True)
    feed_changes = models.TextField(null=True, blank=True)
    housing_conditions = models.CharField(max_length=100, null=True, blank=True)
    recent_treatments = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=20, default='pending', null=True, blank=True)  # pending, predicted, reviewed
    created_at = models.DateTimeField(default=malawi_now, null=True, blank=True)
    updated_at = models.DateTimeField(default=malawi_now, null=True, blank=True)

    is_dairy = models.BooleanField(default=False, null=True)
    lactation_stage = models.CharField(max_length=20, null=True, blank=True)
    is_dairy_goat = models.BooleanField(default=False, null=True)
    horn_status = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'symptom_report'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.updated_at = malawi_now()
        super().save(*args, **kwargs)

    def get_additional_symptoms_list(self):
        if self.additional_symptoms:
            return json.loads(self.additional_symptoms)
        return []

    @property
    def prediction(self):
        """The report's prediction (one per report in this system)."""
        return self.predictions.order_by('id').first()

    @property
    def treatment(self):
        return self.treatments.order_by('id').first()


class Prediction(models.Model):
    prediction_id = models.CharField(max_length=20, unique=True)  # PRED-YYYY-NNN
    symptom_report = models.ForeignKey(SymptomReport, on_delete=models.PROTECT, related_name='predictions')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='predictions')

    disease_name = models.CharField(max_length=100, null=True, blank=True)
    disease_category = models.CharField(max_length=50, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)  # 0.0 to 1.0
    severity = models.CharField(max_length=20, null=True, blank=True)  # mild, moderate, severe, critical
    predicted_at = models.DateTimeField(default=malawi_now, null=True, blank=True)

    # Shown to the farmer while waiting for the vet
    recommendation_text = models.TextField(null=True, blank=True)
    # JSON care plan from clinical_guidance.build_care_plan
    care_plan = models.TextField(null=True, blank=True)
    possible_diseases = models.TextField(null=True, blank=True)  # JSON list with probabilities

    reviewed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        db_column='reviewed_by', related_name='reviewed_predictions')
    review_status = models.CharField(max_length=20, default='pending', null=True, blank=True)  # pending, confirmed, modified
    review_notes = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    model_version = models.CharField(max_length=20, null=True, blank=True)
    features_used = models.TextField(null=True, blank=True)  # JSON

    class Meta:
        db_table = 'prediction'

    def get_possible_diseases(self):
        if self.possible_diseases:
            return json.loads(self.possible_diseases)
        return []

    def get_care_plan(self):
        if self.care_plan:
            return json.loads(self.care_plan)
        return None


class Treatment(models.Model):
    treatment_id = models.CharField(max_length=20, unique=True)  # T-YYYY-NNN
    symptom_report = models.ForeignKey(SymptomReport, on_delete=models.PROTECT, related_name='treatments')
    vet = models.ForeignKey(User, on_delete=models.PROTECT, related_name='treatments')

    medication = models.CharField(max_length=200, null=True, blank=True)
    medication_type = models.CharField(max_length=50, null=True, blank=True)
    dosage = models.CharField(max_length=100, null=True, blank=True)
    dosage_per_kg = models.FloatField(null=True, blank=True)
    frequency = models.CharField(max_length=50, null=True, blank=True)
    duration = models.CharField(max_length=50, null=True, blank=True)
    route = models.CharField(max_length=20, null=True, blank=True)
    withdrawal_period = models.IntegerField(null=True, blank=True)  # days

    supportive_care = models.TextField(null=True, blank=True)
    diet_recommendations = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=20, default='prescribed', null=True, blank=True)
    prescribed_at = models.DateTimeField(default=malawi_now, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    outcome = models.CharField(max_length=20, null=True, blank=True)
    effectiveness = models.FloatField(null=True, blank=True)
    follow_up_required = models.BooleanField(default=False, null=True)
    follow_up_date = models.DateField(null=True, blank=True)

    milk_withdrawal_days = models.IntegerField(null=True, blank=True)
    meat_withdrawal_days = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'treatment'


class MortalityReport(models.Model):
    report_id = models.CharField(max_length=20, unique=True)  # M-YYYY-NNN
    farmer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='farm_mortality_reports')
    vet = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='mortality_reports')

    animal_type = models.CharField(max_length=10, null=True, blank=True)
    animal_id = models.CharField(max_length=50, null=True, blank=True)
    animal_name = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)  # months
    breed = models.CharField(max_length=50, null=True, blank=True)

    date_of_death = models.DateField(null=True, blank=True)
    suspected_cause = models.CharField(max_length=100, null=True, blank=True)
    confirmed_cause = models.CharField(max_length=100, null=True, blank=True)
    symptoms_before_death = models.TextField(null=True, blank=True)

    was_dairy = models.BooleanField(default=False, null=True)
    last_milk_production = models.CharField(max_length=50, null=True, blank=True)

    requires_investigation = models.BooleanField(default=False, null=True)
    investigation_notes = models.TextField(null=True, blank=True)
    lab_results = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=malawi_now, null=True, blank=True)

    class Meta:
        db_table = 'mortality_report'


class DiseaseLibrary(models.Model):
    disease_name = models.CharField(max_length=100)
    animal_type = models.CharField(max_length=10, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    common_name = models.CharField(max_length=100, null=True, blank=True)
    scientific_name = models.CharField(max_length=100, null=True, blank=True)
    primary_symptoms = models.TextField(null=True, blank=True)
    secondary_symptoms = models.TextField(null=True, blank=True)
    incubation_period = models.CharField(max_length=50, null=True, blank=True)
    recommended_treatments = models.TextField(null=True, blank=True)
    prevention_measures = models.TextField(null=True, blank=True)
    mortality_rate = models.FloatField(null=True, blank=True)
    economic_impact = models.CharField(max_length=50, null=True, blank=True)
    zoonotic = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(default=malawi_now, null=True, blank=True)
    updated_at = models.DateTimeField(default=malawi_now, null=True, blank=True)

    class Meta:
        db_table = 'disease_library'


class BreedingRecord(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='breeding_records')
    animal_type = models.CharField(max_length=10, null=True, blank=True)
    animal_id = models.CharField(max_length=50, null=True, blank=True)
    breeding_date = models.DateField(null=True, blank=True)
    sire_id = models.CharField(max_length=50, null=True, blank=True)
    dam_id = models.CharField(max_length=50, null=True, blank=True)
    breeding_method = models.CharField(max_length=50, null=True, blank=True)
    pregnancy_confirmed = models.BooleanField(default=False, null=True)
    confirmation_date = models.DateField(null=True, blank=True)
    expected_calving_kidding_date = models.DateField(null=True, blank=True)
    actual_calving_kidding_date = models.DateField(null=True, blank=True)
    number_of_offspring = models.IntegerField(null=True, blank=True)
    offspring_health = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=malawi_now, null=True, blank=True)

    class Meta:
        db_table = 'breeding_record'


class SystemLog(models.Model):
    timestamp = models.DateTimeField(default=malawi_now, null=True, blank=True, db_index=True)
    level = models.CharField(max_length=20, null=True, blank=True)  # info, warning, error, critical
    component = models.CharField(max_length=50, null=True, blank=True)  # auth, model, notification, ...
    # A deleted user's log entries are kept without the link.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='system_logs')
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    details = models.TextField(null=True, blank=True)  # JSON

    class Meta:
        db_table = 'system_log'


class PerformanceMetric(models.Model):
    metric_date = models.DateField(default=date.today, null=True, blank=True, db_index=True)
    metric_type = models.CharField(max_length=50, null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    target_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)
    recorded_at = models.DateTimeField(default=malawi_now, null=True, blank=True)

    class Meta:
        db_table = 'performance_metric'


class ModelVersion(models.Model):
    version = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, null=True, blank=True)  # training, staging, production, archived
    accuracy = models.FloatField(null=True, blank=True)
    training_data_size = models.IntegerField(null=True, blank=True)
    training_date = models.DateField(null=True, blank=True)
    deployment_date = models.DateField(null=True, blank=True)
    algorithm = models.CharField(max_length=50, null=True, blank=True)
    hyperparameters = models.TextField(null=True, blank=True)
    performance_metrics = models.TextField(null=True, blank=True)
    animal_types = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=malawi_now, null=True, blank=True)

    class Meta:
        db_table = 'model_version'


class Report(models.Model):
    report_id = models.CharField(max_length=20, unique=True)  # REP-YYYY-NNN
    report_type = models.CharField(max_length=50, null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    generated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        db_column='generated_by', related_name='reports')
    generated_at = models.DateTimeField(default=malawi_now, null=True, blank=True)
    file_path = models.CharField(max_length=200, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    data_points = models.TextField(null=True, blank=True)
    is_scheduled = models.BooleanField(default=False, null=True)
    schedule_frequency = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'report'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=50, null=True, blank=True)  # prediction, review, treatment, alert, meeting, message
    title = models.CharField(max_length=200, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    priority = models.CharField(max_length=20, null=True, blank=True)  # low, medium, high, critical
    is_read = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(default=malawi_now, null=True, blank=True)
    action_url = models.CharField(max_length=200, null=True, blank=True)
    related_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'notification'


class Configuration(models.Model):
    category = models.CharField(max_length=50, null=True, blank=True)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(null=True, blank=True)
    data_type = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    last_modified = models.DateTimeField(default=malawi_now, null=True, blank=True)
    modified_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        db_column='modified_by', related_name='configuration_changes')

    class Meta:
        db_table = 'configuration'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.last_modified = malawi_now()
        super().save(*args, **kwargs)
