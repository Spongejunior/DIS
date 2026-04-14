from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, FloatField, DateField, DateTimeField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User
import json

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Login As', choices=[
        ('', 'Select Role'),
        ('farmer', 'Farmer'),
        ('veterinarian', 'Veterinarian'),
        ('organization_admin', 'Organization Admin'),
        ('system_admin', 'System Admin')
    ], validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[Optional()])
    phone = StringField('Phone Number', validators=[Optional()])
    role = SelectField('User Role', choices=[
        ('', 'Select Role'),
        ('farmer', 'Farmer'),
        ('veterinarian', 'Veterinarian')
    ], validators=[DataRequired()])
    location = TextAreaField('Location/Farm Address', validators=[Optional()])
    
    # Farm specific for farmers
    farm_name = StringField('Farm Name', validators=[Optional()])
    farm_size = StringField('Farm Size (acres)', validators=[Optional()])
    animal_types = SelectField('Primary Animal Types', choices=[
        ('', 'Select Animals'),
        ('cattle', 'Cattle Only'),
        ('goat', 'Goats Only'),
        ('cattle,goat', 'Both Cattle and Goats')
    ], validators=[Optional()])
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class SymptomForm(FlaskForm):
    # Animal Information
    animal_id = StringField('Animal ID/Tag Number', validators=[DataRequired()])
    animal_name = StringField('Animal Name (Optional)', validators=[Optional()])
    animal_type = SelectField('Animal Type', choices=[
        ('', 'Select Type'),
        ('cattle', 'Cattle'),
        ('goat', 'Goat')
    ], validators=[DataRequired()])
    animal_age = IntegerField('Age (months)', validators=[Optional(), NumberRange(min=0)])
    animal_weight = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=0)])
    animal_breed = StringField('Breed', validators=[Optional()])
    
    # Cattle/Goat specific
    is_dairy = BooleanField('Dairy Animal')
    lactation_stage = SelectField('Lactation Stage (if dairy)', choices=[
        ('', 'Select Stage'),
        ('early', 'Early (0-100 days)'),
        ('mid', 'Mid (100-200 days)'),
        ('late', 'Late (200+ days)'),
        ('dry', 'Dry Period')
    ], validators=[Optional()])
    
    # Vital Signs
    appetite = SelectField('Appetite', choices=[
        ('', 'Select'),
        ('normal', 'Normal'),
        ('reduced', 'Reduced'),
        ('none', 'No Appetite'),
        ('increased', 'Increased')
    ], validators=[DataRequired()])
    temperature = FloatField('Body Temperature (°C)', validators=[DataRequired(), NumberRange(min=35, max=45)])
    heart_rate = IntegerField('Heart Rate (beats/minute)', validators=[Optional(), NumberRange(min=30, max=150)])
    respiration_rate = IntegerField('Respiration Rate (breaths/minute)', validators=[Optional(), NumberRange(min=10, max=100)])
    
    # Rumen/Reticulum (for ruminants)
    rumen_movement = SelectField('Rumen Movement', choices=[
        ('normal', 'Normal (1-2 contractions/minute)'),
        ('reduced', 'Reduced'),
        ('absent', 'Absent'),
        ('increased', 'Increased')
    ], validators=[Optional()])
    
    # Digestive System
    stool_consistency = SelectField('Stool Consistency', choices=[
        ('normal', 'Normal'),
        ('loose', 'Loose'),
        ('watery', 'Watery Diarrhea'),
        ('firm', 'Firm/Hard'),
        ('bloody', 'Bloody')
    ], validators=[Optional()])
    
    # Production (for dairy)
    milk_production = SelectField('Milk Production (if dairy)', choices=[
        ('normal', 'Normal'),
        ('reduced', 'Reduced'),
        ('stopped', 'Stopped'),
        ('abnormal', 'Abnormal (clots, blood)')
    ], validators=[Optional()])
    
    # Common Symptoms for Cattle/Goats
    additional_symptoms = TextAreaField('Additional Observations', validators=[Optional()])
    
    # Environmental Factors
    feed_type = StringField('Current Feed Type', validators=[Optional()])
    feed_changes = TextAreaField('Recent Feed Changes', validators=[Optional()])
    housing_conditions = SelectField('Housing Conditions', choices=[
        ('good', 'Good (clean, dry, ventilated)'),
        ('fair', 'Fair'),
        ('poor', 'Poor (dirty, damp, crowded)')
    ], validators=[Optional()])
    recent_treatments = TextAreaField('Recent Treatments/Medications', validators=[Optional()])
    
    # Other Animals
    similar_cases = IntegerField('Number of Other Animals Showing Similar Symptoms', validators=[Optional(), NumberRange(min=0)])
    
    submit = SubmitField('Submit for Disease Prediction')

class CattleSymptomForm(SymptomForm):
    # Cattle specific symptoms
    lameness = SelectField('Lameness', choices=[
        ('none', 'None'),
        ('mild', 'Mild'),
        ('severe', 'Severe')
    ], validators=[Optional()])
    
    mastitis_signs = BooleanField('Signs of Mastitis')
    bloat = BooleanField('Signs of Bloat')
    foot_rot = BooleanField('Signs of Foot Rot')

class GoatSymptomForm(SymptomForm):
    # Goat specific symptoms
    coccidiosis_signs = BooleanField('Signs of Coccidiosis (bloody diarrhea)')
    caseous_lymphadenitis = BooleanField('Swollen Lymph Nodes')
    caprine_arthritis = BooleanField('Joint Swelling/Arthritis')

class TreatmentForm(FlaskForm):
    # Treatment selection
    medication = StringField('Medication Name', validators=[DataRequired()])
    medication_type = SelectField('Medication Type', choices=[
        ('antibiotic', 'Antibiotic'),
        ('antiparasitic', 'Antiparasitic'),
        ('anti-inflammatory', 'Anti-inflammatory'),
        ('vitamin', 'Vitamin/Supplement'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    # Dosage calculation
    weight_based = BooleanField('Calculate dosage by weight')
    animal_weight = FloatField('Animal Weight (kg)', validators=[Optional(), NumberRange(min=0)])
    dosage_per_kg = FloatField('Dosage per kg (mg/kg)', validators=[Optional(), NumberRange(min=0)])
    total_dosage = StringField('Total Dosage', validators=[Optional()])
    
    # Administration
    frequency = SelectField('Frequency', choices=[
        ('once_daily', 'Once daily'),
        ('twice_daily', 'Twice daily'),
        ('three_times_daily', 'Three times daily'),
        ('every_other_day', 'Every other day'),
        ('weekly', 'Weekly'),
        ('single_dose', 'Single dose')
    ], validators=[DataRequired()])
    duration = IntegerField('Duration (days)', validators=[DataRequired(), NumberRange(min=1)])
    route = SelectField('Route of Administration', choices=[
        ('oral', 'Oral (feed/water)'),
        ('injection', 'Injection'),
        ('intramammary', 'Intramammary (for mastitis)'),
        ('topical', 'Topical'),
        ('inhalation', 'Inhalation')
    ], validators=[DataRequired()])
    
    # Withdrawal periods (important for food safety)
    milk_withdrawal_days = IntegerField('Milk Withdrawal Period (days)', validators=[Optional(), NumberRange(min=0)])
    meat_withdrawal_days = IntegerField('Meat Withdrawal Period (days)', validators=[Optional(), NumberRange(min=0)])
    
    # Supportive care
    supportive_care = TextAreaField('Supportive Care Instructions', validators=[Optional()])
    diet_recommendations = TextAreaField('Diet Recommendations', validators=[Optional()])
    isolation_required = BooleanField('Isolate Animal')
    
    # Follow-up
    follow_up_required = BooleanField('Schedule Follow-up Examination')
    follow_up_date = DateField('Follow-up Date', validators=[Optional()])
    
    submit = SubmitField('Save Treatment Plan')

class MortalityReportForm(FlaskForm):
    animal_type = SelectField('Animal Type', choices=[
        ('cattle', 'Cattle'),
        ('goat', 'Goat')
    ], validators=[DataRequired()])
    animal_id = StringField('Animal ID/Tag Number', validators=[DataRequired()])
    animal_name = StringField('Animal Name', validators=[Optional()])
    breed = StringField('Breed', validators=[Optional()])
    age = IntegerField('Age (months)', validators=[Optional(), NumberRange(min=0)])
    
    # Mortality details
    date_of_death = DateField('Date of Death', validators=[DataRequired()])
    time_of_death = StringField('Approximate Time of Death', validators=[Optional()])
    
    # Cause of death (cattle/goat specific)
    suspected_cause = SelectField('Suspected Cause of Death', choices=[
        ('', 'Select Cause'),
        ('respiratory', 'Respiratory Disease'),
        ('digestive', 'Digestive Problem'),
        ('parasitic', 'Parasitic Infection'),
        ('metabolic', 'Metabolic Disorder'),
        ('nutritional', 'Nutritional Deficiency'),
        ('trauma', 'Trauma/Injury'),
        ('poisoning', 'Poisoning'),
        ('dystocia', 'Dystocia (Birthing Problem)'),
        ('unknown', 'Unknown'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    # For dairy animals
    was_dairy = BooleanField('Was this a dairy animal?')
    last_milk_production = StringField('Last Milk Production', validators=[Optional()])
    
    # Symptoms before death
    symptoms_before_death = TextAreaField('Symptoms Observed Before Death', validators=[Optional()])
    
    # Treatment history
    treatment_provided = SelectField('Treatment Provided Before Death', choices=[
        ('none', 'None'),
        ('basic', 'Basic Treatment'),
        ('full', 'Full Treatment'),
        ('emergency', 'Emergency Treatment')
    ], validators=[DataRequired()])
    
    # Prediction
    was_predicted = SelectField('Was this predicted by AI?', choices=[
        ('no', 'No'),
        ('yes_high', 'Yes - High Confidence'),
        ('yes_medium', 'Yes - Medium Confidence'),
        ('yes_low', 'Yes - Low Confidence')
    ], validators=[DataRequired()])
    
    # Investigation
    requires_investigation = BooleanField('This case requires further investigation')
    lab_samples_taken = BooleanField('Lab Samples Taken')
    lab_results = TextAreaField('Lab Results (if available)', validators=[Optional()])
    
    additional_notes = TextAreaField('Additional Notes', validators=[Optional()])
    
    submit = SubmitField('Submit Mortality Report')

class BreedingRecordForm(FlaskForm):
    animal_type = SelectField('Animal Type', choices=[
        ('cattle', 'Cattle'),
        ('goat', 'Goat')
    ], validators=[DataRequired()])
    animal_id = StringField('Animal ID', validators=[DataRequired()])
    
    # Breeding details
    breeding_date = DateField('Breeding Date', validators=[DataRequired()])
    sire_id = StringField('Sire (Father) ID', validators=[Optional()])
    dam_id = StringField('Dam (Mother) ID', validators=[Optional()])
    breeding_method = SelectField('Breeding Method', choices=[
        ('natural', 'Natural Mating'),
        ('ai', 'Artificial Insemination'),
        ('embryo', 'Embryo Transfer')
    ], validators=[DataRequired()])
    
    # AI specific
    ai_technician = StringField('AI Technician (if AI)', validators=[Optional()])
    semen_code = StringField('Semen Code (if AI)', validators=[Optional()])
    
    # Pregnancy
    pregnancy_check_date = DateField('Pregnancy Check Date', validators=[Optional()])
    pregnancy_confirmed = BooleanField('Pregnancy Confirmed')
    expected_calving_kidding_date = DateField('Expected Calving/Kidding Date', validators=[Optional()])
    
    submit = SubmitField('Save Breeding Record')

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[Optional()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional()])
    
    # Farm information
    farm_name = StringField('Farm Name', validators=[Optional()])
    location = TextAreaField('Farm Address/Location', validators=[Optional()])
    farm_size = StringField('Farm Size (acres)', validators=[Optional()])
    
    # Animal information
    animal_types = SelectField('Primary Animal Types', choices=[
        ('cattle', 'Cattle Only'),
        ('goat', 'Goats Only'),
        ('cattle,goat', 'Both Cattle and Goats')
    ], validators=[Optional()])
    
    # Production focus
    production_focus = SelectField('Production Focus', choices=[
        ('dairy', 'Dairy'),
        ('meat', 'Meat'),
        ('dual', 'Dual Purpose'),
        ('breeding', 'Breeding Stock')
    ], validators=[Optional()])
    
    submit = SubmitField('Save Changes')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    
    submit = SubmitField('Update Password')

class ConfigurationForm(FlaskForm):
    system_name = StringField('System Name', validators=[DataRequired()])
    default_language = SelectField('Default Language', choices=[
        ('english', 'English'),
        ('spanish', 'Spanish'),
        ('french', 'French')
    ])
    
    # Cattle/Goat specific settings
    default_animal_type = SelectField('Default Animal Type', choices=[
        ('cattle', 'Cattle'),
        ('goat', 'Goat')
    ])
    temperature_unit = SelectField('Temperature Unit', choices=[
        ('celsius', 'Celsius'),
        ('fahrenheit', 'Fahrenheit')
    ])
    weight_unit = SelectField('Weight Unit', choices=[
        ('kg', 'Kilograms'),
        ('lbs', 'Pounds')
    ])
    
    # Prediction settings
    prediction_timeout = IntegerField('Prediction Timeout (seconds)', validators=[NumberRange(min=10, max=120)])
    max_predictions_per_day = IntegerField('Max Predictions Per Day', validators=[Optional(), NumberRange(min=1)])
    min_confidence_threshold = FloatField('Minimum Confidence Threshold', validators=[NumberRange(min=0.5, max=1.0)])
    
    # Notification settings
    notify_high_confidence = BooleanField('Notify on High Confidence Predictions (>90%)')
    notify_outbreak = BooleanField('Notify on Potential Outbreaks')
    
    submit = SubmitField('Save Settings')

class ReportGenerationForm(FlaskForm):
    report_name = StringField('Report Name', validators=[DataRequired()])
    report_type = SelectField('Report Type', choices=[
        ('health', 'Health Summary'),
        ('breeding', 'Breeding Report'),
        ('mortality', 'Mortality Analysis'),
        ('production', 'Production Report'),
        ('financial', 'Financial Summary'),
        ('custom', 'Custom Report')
    ], validators=[DataRequired()])
    
    # Animal type filter
    animal_type = SelectField('Animal Type', choices=[
        ('all', 'All Animals'),
        ('cattle', 'Cattle Only'),
        ('goat', 'Goats Only')
    ], validators=[DataRequired()])
    
    # Date range
    period_start = DateField('Start Date', validators=[DataRequired()])
    period_end = DateField('End Date', validators=[DataRequired()])
    
    # Output format
    output_format = SelectField('Output Format', choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV')
    ], validators=[DataRequired()])
    
    # Schedule
    schedule_frequency = SelectField('Schedule Report', choices=[
        ('once', 'Generate once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ])
    
    submit = SubmitField('Generate Report')
