from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, FloatField, DateField, DateTimeField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from flask_babel import lazy_gettext as _
from models import User
import json

class LoginForm(FlaskForm):
    username = StringField(_('Username'), validators=[DataRequired(message=_('Username is required.'))])
    password = PasswordField(_('Password'), validators=[DataRequired(message=_('Password is required.'))])
    remember = BooleanField(_('Remember Me'))
    submit = SubmitField(_('Login'))

class ForgotPasswordForm(FlaskForm):
    identity = StringField(_('Username or Email'), validators=[DataRequired(message=_('Username or email is required.')), Length(min=3, max=120)])
    submit = SubmitField(_('Send Reset Link'))

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(_('New Password'), validators=[DataRequired(message=_('New password is required.')), Length(min=6, message=_('Password must be at least 6 characters long.'))])
    confirm_new_password = PasswordField(_('Confirm New Password'), validators=[DataRequired(message=_('Please confirm your new password.')), EqualTo('new_password', message=_('Passwords must match.'))])
    submit = SubmitField(_('Reset Password'))

class RegistrationForm(FlaskForm):
    full_name = StringField(_('Full Name'), validators=[DataRequired(message=_('Full name is required.'))])
    email = StringField(_('Email'), validators=[DataRequired(message=_('Email is required.')), Email(message=_('Please enter a valid email address.'))])
    username = StringField(_('Username'), validators=[DataRequired(message=_('Username is required.')), Length(min=3, max=80, message=_('Username must be between 3 and 80 characters.'))])
    password = PasswordField(_('Password'), validators=[DataRequired(message=_('Password is required.')), Length(min=6, message=_('Password must be at least 6 characters long.'))])
    confirm_password = PasswordField(_('Confirm Password'), validators=[DataRequired(message=_('Please confirm your password.')), EqualTo('password', message=_('Passwords must match.'))])
    phone = StringField(_('Phone Number'), validators=[Optional()])
    role = SelectField(_('User Role'), choices=[
        ('', _('Select Role')),
        ('farmer', _('Farmer')),
        ('veterinarian', _('Veterinarian'))
    ], validators=[DataRequired(message=_('Please select a role.'))])
    location = SelectField(_('Mzimba North'), choices=[
        ('', _('Select Blocks in Mzimba North')),
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
        
    ], validators=[DataRequired(message=_('Please select your block.'))])
    specific_location = StringField(_('Village'), validators=[Optional()])
    
    # Farm specific for farmers
    farm_name = StringField(_('Farm Name'), validators=[Optional()])
    animal_types = SelectField(_('Primary Animal Types'), choices=[
        ('', _('Select Animals')),
        ('cattle', _('Cattle Only')),
        ('goat', _('Goats Only')),
        ('cattle,goat', _('Both Cattle and Goats'))
    ], validators=[Optional()])
    production_focus = SelectField(_('Production Focus'), choices=[
        ('', _('Select Focus')),
        ('dairy', _('Dairy')),
        ('meat', _('Meat')),
        ('dual', _('Dual Purpose')),
        ('breeding', _('Breeding Stock'))
    ], validators=[Optional()])
    
    submit = SubmitField(_('Register'))
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(_('Username already exists.'))
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(_('Email already registered.'))

class SymptomForm(FlaskForm):
    # Animal Information
    animal_type = SelectField(_('Specie'), choices=[
        ('', _('Select Specie')),
        ('cattle', _('Cattle')),
        ('goat', _('Goat'))
    ], validators=[DataRequired(message=_('Please select a specie.'))])
    animal_sex = SelectField(_('Sex'), choices=[
        ('female', _('Female')),
        ('male', _('Male'))
    ], validators=[DataRequired(message=_('Please select the animal sex.'))])
    animal_age = IntegerField(_('Age (months)'), validators=[Optional(), NumberRange(min=0, message=_('Age cannot be negative.'))])
    animal_weight = FloatField(_('Weight (kg)'), validators=[Optional(), NumberRange(min=0, message=_('Weight cannot be negative.'))])
    
    # Cattle/Goat specific
    is_dairy = BooleanField(_('Dairy Animal'))
    lactation_stage = SelectField(_('Lactation Stage (if dairy)'), choices=[
        ('', _('Select Stage')),
        ('early', _('Early (0-100 days)')),
        ('mid', _('Mid (100-200 days)')),
        ('late', _('Late (200+ days)')),
        ('dry', _('Dry Period'))
    ], validators=[Optional()])
    
    # Vital Signs
    temperature = FloatField(_('Body Temperature (°C)'), validators=[DataRequired(message=_('Body temperature is required.')), NumberRange(min=1, max=100, message=_('Temperature must be between 1 and 100 °C.'))])
   
    
    # Digestive System
    stool_consistency = SelectField(_('Stool Consistency'), choices=[
        ('normal', _('Normal')),
        ('loose', _('Loose')),
        ('watery', _('Watery Diarrhea')),
        ('firm', _('Firm/Hard')),
        ('bloody', _('Bloody'))
    ], validators=[Optional()])
    
    # Production (for dairy)
    milk_production = SelectField(_('Milk Production (if dairy)'), choices=[
        ('normal', _('Normal')),
        ('reduced', _('Reduced')),
        ('stopped', _('Stopped')),
        ('abnormal', _('Abnormal (clots, blood)'))
    ], validators=[Optional()])
    
    # Environmental Factors
    feed_type = StringField(_('Current Feed Type'), validators=[Optional()])
    feed_changes = TextAreaField(_('Recent Feed Changes'), validators=[Optional()])
    housing_conditions = SelectField(_('Housing Conditions'), choices=[
        ('good', _('Good (clean, dry, ventilated)')),
        ('fair', _('Fair')),
        ('poor', _('Poor (dirty, damp, crowded)'))
    ], validators=[Optional()])
    recent_treatments = TextAreaField(_('Recent Treatments/Medications'), validators=[Optional()])
    
    # Other Animals
    similar_cases = IntegerField(_('Number of Other Animals Showing Similar Symptoms'), validators=[Optional(), NumberRange(min=0, message=_('Number cannot be negative.'))])

    # Extra fields required by app.py -> SymptomReport
    appetite = SelectField(_('Appetite'), choices=[
        ('normal', _('Normal')),
        ('reduced', _('Reduced')),
        ('none', _('None')),
        ('increased', _('Increased'))
    ], validators=[Optional()])

    rumen_movement = SelectField(_('Rumen Movement'), choices=[
        ('normal', _('Normal')),
        ('reduced', _('Reduced')),
        ('absent', _('Absent'))
    ], validators=[Optional()])

    animal_breed = StringField(_('Breed'), validators=[Optional()])

    submit = SubmitField(_('Submit for Disease Prediction'))


class CattleSymptomForm(SymptomForm):
    # Cattle specific symptoms
    lameness = SelectField(_('Lameness'), choices=[
        ('none', _('None')),
        ('mild', _('Mild')),
        ('severe', _('Severe'))
    ], validators=[Optional()])
    
    mastitis_signs = BooleanField(_('Signs of Mastitis'))
    bloat = BooleanField(_('Signs of Bloat'))
    foot_rot = BooleanField(_('Signs of Foot Rot'))

class GoatSymptomForm(SymptomForm):
    # Goat specific symptoms
    coccidiosis_signs = BooleanField(_('Signs of Coccidiosis (bloody diarrhea)'))
    caseous_lymphadenitis = BooleanField(_('Swollen Lymph Nodes'))
    caprine_arthritis = BooleanField(_('Joint Swelling/Arthritis'))

class TreatmentForm(FlaskForm):
    # Treatment selection
    medication = StringField(_('Medication Name'), validators=[DataRequired(message=_('Medication name is required.'))])
    medication_type = SelectField(_('Medication Type'), choices=[
        ('antibiotic', _('Antibiotic')),
        ('antiparasitic', _('Antiparasitic')),
        ('anti-inflammatory', _('Anti-inflammatory')),
        ('vitamin', _('Vitamin/Supplement')),
        ('other', _('Other'))
    ], validators=[DataRequired(message=_('Please select a medication type.'))])
    
    # Dosage calculation
    weight_based = BooleanField(_('Calculate dosage by weight'))
    animal_weight = FloatField(_('Animal Weight (kg)'), validators=[Optional(), NumberRange(min=0, message=_('Weight cannot be negative.'))])
    dosage_per_kg = FloatField(_('Dosage per kg (mg/kg)'), validators=[Optional(), NumberRange(min=0, message=_('Dosage cannot be negative.'))])
    dosage = StringField(_('Total Dosage'), validators=[Optional()])
    
    # Administration
    frequency = SelectField(_('Frequency'), choices=[
        ('once_daily', _('Once daily')),
        ('twice_daily', _('Twice daily')),
        ('three_times_daily', _('Three times daily')),
        ('every_other_day', _('Every other day')),
        ('weekly', _('Weekly')),
        ('single_dose', _('Single dose'))
    ], validators=[DataRequired(message=_('Please select a frequency.'))])
    duration = IntegerField(_('Duration (days)'), validators=[DataRequired(message=_('Duration is required.')), NumberRange(min=1, message=_('Duration must be at least 1 day.'))])
    route = SelectField(_('Route of Administration'), choices=[
        ('oral', _('Oral (feed/water)')),
        ('injection', _('Injection')),
        ('intramammary', _('Intramammary (for mastitis)')),
        ('topical', _('Topical')),
        ('inhalation', _('Inhalation'))
    ], validators=[DataRequired(message=_('Please select a route of administration.'))])
    
    # Withdrawal periods (important for food safety)
    milk_withdrawal_days = IntegerField(_('Milk Withdrawal Period (days)'), validators=[Optional(), NumberRange(min=0, message=_('Days cannot be negative.'))])
    meat_withdrawal_days = IntegerField(_('Meat Withdrawal Period (days)'), validators=[Optional(), NumberRange(min=0, message=_('Days cannot be negative.'))])
    
    # Supportive care
    supportive_care = TextAreaField(_('Supportive Care Instructions'), validators=[Optional()])
    diet_recommendations = TextAreaField(_('Diet Recommendations'), validators=[Optional()])
    isolation_required = BooleanField(_('Isolate Animal'))
    
    # Follow-up
    follow_up_required = BooleanField(_('Schedule Follow-up Examination'))
    follow_up_date = DateField(_('Follow-up Date'), validators=[Optional()])
    
    submit = SubmitField(_('Save Treatment Plan'))

class MortalityReportForm(FlaskForm):
    animal_type = SelectField(_('Animal Type'), choices=[
        ('cattle', _('Cattle')),
        ('goat', _('Goat'))
    ], validators=[DataRequired(message=_('Please select an animal type.'))])
    # animal_id = StringField('Animal ID/Tag Number', validators=[DataRequired()])
    # animal_name = StringField('Animal Name', validators=[Optional()])
    # breed = StringField('Breed', validators=[Optional()])
    age = IntegerField(_('Age (months)'), validators=[Optional(), NumberRange(min=0, message=_('Age cannot be negative.'))])
    
    # Mortality details
    date_of_death = DateField(_('Date of Death'), validators=[DataRequired(message=_('Date of death is required.'))])
    time_of_death = StringField(_('Approximate Time of Death'), validators=[Optional()])
    
    # Cause of death (cattle/goat specific)
    suspected_cause = SelectField(_('Suspected Cause of Death'), choices=[
        ('', _('Select Cause')),
        ('respiratory', _('Respiratory Disease')),
        ('digestive', _('Digestive Problem')),
        ('parasitic', _('Parasitic Infection')),
        ('metabolic', _('Metabolic Disorder')),
        ('nutritional', _('Nutritional Deficiency')),
        ('trauma', _('Trauma/Injury')),
        ('poisoning', _('Poisoning')),
        ('dystocia', _('Dystocia (Birthing Problem)')),
        ('unknown', _('Unknown')),
        ('other', _('Other'))
    ], validators=[DataRequired(message=_('Please select a suspected cause.'))])
    
    # For dairy animals
    was_dairy = BooleanField(_('Was this a dairy animal?'))
    last_milk_production = StringField(_('Last Milk Production'), validators=[Optional()])
    
    # Symptoms before death
    symptoms_before_death = TextAreaField(_('Symptoms Observed Before Death'), validators=[Optional()])
    
    # Treatment history
    treatment_provided = SelectField(_('Treatment Provided Before Death'), choices=[
        ('none', _('None')),
        ('basic', _('Basic Treatment')),
        ('full', _('Full Treatment')),
        ('emergency', _('Emergency Treatment'))
    ], validators=[DataRequired(message=_('Please select treatment provided.'))])
    
    # Prediction
    was_predicted = SelectField(_('Was this predicted by AI?'), choices=[
        ('no', _('No')),
        ('yes_high', _('Yes - High Confidence')),
        ('yes_medium', _('Yes - Medium Confidence')),
        ('yes_low', _('Yes - Low Confidence'))
    ], validators=[DataRequired(message=_('Please indicate if this was predicted by AI.'))])
    
    # Investigation
    requires_investigation = BooleanField(_('This case requires further investigation'))
    lab_samples_taken = BooleanField(_('Lab Samples Taken'))
    lab_results = TextAreaField(_('Lab Results (if available)'), validators=[Optional()])
    
    additional_notes = TextAreaField(_('Additional Notes'), validators=[Optional()])
    
    submit = SubmitField(_('Submit Mortality Report'))

class BreedingRecordForm(FlaskForm):
    animal_type = SelectField(_('Animal Type'), choices=[
        ('cattle', _('Cattle')),
        ('goat', _('Goat'))
    ], validators=[DataRequired(message=_('Please select an animal type.'))])
    animal_id = StringField(_('Animal ID'), validators=[DataRequired(message=_('Animal ID is required.'))])
    
    # Breeding details
    breeding_date = DateField(_('Breeding Date'), validators=[DataRequired(message=_('Breeding date is required.'))])
    sire_id = StringField(_('Sire (Father) ID'), validators=[Optional()])
    dam_id = StringField(_('Dam (Mother) ID'), validators=[Optional()])
    breeding_method = SelectField(_('Breeding Method'), choices=[
        ('natural', _('Natural Mating')),
        ('ai', _('Artificial Insemination')),
        ('embryo', _('Embryo Transfer'))
    ], validators=[DataRequired(message=_('Please select a breeding method.'))])
    
    # AI specific
    ai_technician = StringField(_('AI Technician (if AI)'), validators=[Optional()])
    semen_code = StringField(_('Semen Code (if AI)'), validators=[Optional()])
    
    # Pregnancy
    pregnancy_check_date = DateField(_('Pregnancy Check Date'), validators=[Optional()])
    pregnancy_confirmed = BooleanField(_('Pregnancy Confirmed'))
    expected_calving_kidding_date = DateField(_('Expected Calving/Kidding Date'), validators=[Optional()])
    
    submit = SubmitField(_('Save Breeding Record'))

class ProfileForm(FlaskForm):
    full_name = StringField(_('Full Name'), validators=[Optional()])
    email = StringField(_('Email'), validators=[DataRequired(message=_('Email is required.')), Email(message=_('Please enter a valid email address.'))])
    phone = StringField(_('Phone Number'), validators=[Optional()])
    
    # Farm information
    farm_name = StringField(_('Farm Name'), validators=[Optional()])
    # Block (Mzimba North) — drives automatic farmer<->veterinarian assignment.
    location = SelectField(_('Block (Mzimba North)'), choices=[
        ('', _('Select Block')),
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
    ], validators=[Optional()])
    specific_location = StringField(_('Village'), validators=[Optional()])
    
    # Animal information
    animal_types = SelectField(_('Primary Animal Types'), choices=[
        ('cattle', _('Cattle Only')),
        ('goat', _('Goats Only')),
        ('cattle,goat', _('Both Cattle and Goats'))
    ], validators=[Optional()])
    
    # Production focus
    production_focus = SelectField(_('Production Focus'), choices=[
        ('dairy', _('Dairy')),
        ('meat', _('Meat')),
        ('dual', _('Dual Purpose')),
        ('breeding', _('Breeding Stock'))
    ], validators=[Optional()])
    
    submit = SubmitField(_('Save Changes'))

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(_('Current Password'), validators=[DataRequired(message=_('Current password is required.'))])
    new_password = PasswordField(_('New Password'), validators=[DataRequired(message=_('New password is required.')), Length(min=6, message=_('Password must be at least 6 characters long.'))])
    confirm_new_password = PasswordField(_('Confirm New Password'), validators=[DataRequired(message=_('Please confirm your new password.')), EqualTo('new_password', message=_('Passwords must match.'))])
    
    submit = SubmitField(_('Update Password'))

class ConfigurationForm(FlaskForm):
    system_name = StringField(_('System Name'), validators=[DataRequired(message=_('System name is required.'))])
    default_language = SelectField(_('Default Language'), choices=[
        ('english', _('English')),
        ('spanish', _('Spanish')),
        ('french', _('French'))
    ])
    
    # Cattle/Goat specific settings
    default_animal_type = SelectField(_('Default Animal Type'), choices=[
        ('cattle', _('Cattle')),
        ('goat', _('Goat'))
    ])
    temperature_unit = SelectField(_('Temperature Unit'), choices=[
        ('celsius', _('Celsius')),
        ('fahrenheit', _('Fahrenheit'))
    ])
    weight_unit = SelectField(_('Weight Unit'), choices=[
        ('kg', _('Kilograms')),
        ('lbs', _('Pounds'))
    ])
    
    # Prediction settings
    prediction_timeout = IntegerField(_('Prediction Timeout (seconds)'), validators=[NumberRange(min=10, max=120, message=_('Timeout must be between 10 and 120 seconds.'))])
    max_predictions_per_day = IntegerField(_('Max Predictions Per Day'), validators=[Optional(), NumberRange(min=1, message=_('Must be at least 1 prediction per day.'))])
    min_confidence_threshold = FloatField(_('Minimum Confidence Threshold'), validators=[NumberRange(min=0.5, max=1.0, message=_('Threshold must be between 0.5 and 1.0.'))])
    
    # Notification settings
    notify_high_confidence = BooleanField(_('Notify on High Confidence Predictions (>90%)'))
    notify_outbreak = BooleanField(_('Notify on Potential Outbreaks'))
    
    submit = SubmitField(_('Save Settings'))

class ReportGenerationForm(FlaskForm):
    report_name = StringField(_('Report Name'), validators=[DataRequired(message=_('Report name is required.'))])
    report_type = SelectField(_('Report Type'), choices=[
        ('health', _('Health Summary')),
        ('breeding', _('Breeding Report')),
        ('mortality', _('Mortality Analysis')),
        ('production', _('Production Report')),
        ('financial', _('Financial Summary')),
        ('custom', _('Custom Report'))
    ], validators=[DataRequired(message=_('Please select a report type.'))])
    
    # Animal type filter
    animal_type = SelectField(_('Animal Type'), choices=[
        ('all', _('All Animals')),
        ('cattle', _('Cattle Only')),
        ('goat', _('Goats Only'))
    ], validators=[DataRequired(message=_('Please select an animal type.'))])
    
    # Date range
    period_start = DateField(_('Start Date'), validators=[DataRequired(message=_('Start date is required.'))])
    period_end = DateField(_('End Date'), validators=[DataRequired(message=_('End date is required.'))])
    
    # Output format
    output_format = SelectField(_('Output Format'), choices=[
        ('pdf', 'PDF'),
        ('excel', _('Excel')),
        ('csv', 'CSV')
    ], validators=[DataRequired(message=_('Please select an output format.'))])
    
    # Schedule
    schedule_frequency = SelectField(_('Schedule Report'), choices=[
        ('once', _('Generate once')),
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly'))
    ])
    
    submit = SubmitField(_('Generate Report'))
