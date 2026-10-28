"""Forms (validation) for the pages.

The Next.js frontend renders each form from the JSON description built in
core/bridge.py, so field names, labels, choices and error messages here are
what the user sees.
"""
import hmac
import secrets

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .locations import ALL_SECTIONS, EPA_NAMES, section_belongs_to_epa
from .models import User

CSRF_SESSION_KEY = '_csrf_token'

NOT_A_CHOICE = _('Not a valid choice.')
NOT_AN_INTEGER = _('Not a valid integer value.')
NOT_A_FLOAT = _('Not a valid float value.')
NOT_A_DATE = _('Not a valid date value.')


def csrf_token(request):
    """The session's form token, created on first use."""
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_hex(20)
        request.session[CSRF_SESSION_KEY] = token
    return token


class DateInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, attrs=None):
        super().__init__(attrs, format='%Y-%m-%d')


# Field helpers: keyword arguments are passed through to the Django field.

def text(label, required=None, **kwargs):
    error_messages = {'required': required} if required else {}
    error_messages.update(kwargs.pop('error_messages', {}))
    return forms.CharField(label=label, required=bool(required), error_messages=error_messages,
                           widget=kwargs.pop('widget', forms.TextInput), **kwargs)


def password_field(label, required, **kwargs):
    return text(label, required, strip=False, widget=forms.PasswordInput, **kwargs)


def textarea(label):
    return forms.CharField(label=label, required=False, widget=forms.Textarea)


def email_field(label, required):
    return forms.EmailField(label=label, widget=forms.TextInput, max_length=None, error_messages={
        'required': required, 'invalid': _('Please enter a valid email address.')})


class StrictChoiceField(forms.ChoiceField):
    """A select that must hold one of its choices, but is not marked required."""

    def validate(self, value):
        if value in self.empty_values:
            raise forms.ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
        super().validate(value)


def select(label, choices, required=None, strict=False):
    error_messages = {'invalid_choice': NOT_A_CHOICE}
    if required:
        error_messages['required'] = required
    field_class = StrictChoiceField if strict else forms.ChoiceField
    return field_class(label=label, choices=choices, required=bool(required), error_messages=error_messages)


class RequiredNumberMixin:
    """A required number that is 0 or not a number gets the "required" message."""

    def to_python(self, value):
        try:
            return super().to_python(value)
        except forms.ValidationError:
            if self.required:
                raise forms.ValidationError(self.error_messages['required'], code='required')
            raise

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'], code='required')
        super().validate(value)


class IntegerField(RequiredNumberMixin, forms.IntegerField):
    pass


class FloatField(RequiredNumberMixin, forms.FloatField):
    pass


def integer(label, required=None, min_value=None, min_message=None, **kwargs):
    error_messages = {'invalid': NOT_AN_INTEGER}
    if required:
        error_messages['required'] = required
    if min_message:
        error_messages['min_value'] = min_message
    return IntegerField(label=label, required=bool(required), min_value=min_value,
                        error_messages=error_messages, **kwargs)


def decimal(label, required=None, min_value=None, max_value=None, range_message=None):
    error_messages = {'invalid': NOT_A_FLOAT}
    if required:
        error_messages['required'] = required
    if range_message:
        error_messages['min_value'] = error_messages['max_value'] = range_message
    return FloatField(label=label, required=bool(required), min_value=min_value, max_value=max_value,
                      widget=forms.TextInput, error_messages=error_messages)


def date_field(label, required=None):
    error_messages = {'invalid': NOT_A_DATE}
    if required:
        error_messages['required'] = required
    return forms.DateField(label=label, required=bool(required), widget=DateInput,
                           input_formats=['%Y-%m-%d'], error_messages=error_messages)


def checkbox(label):
    return forms.BooleanField(label=label, required=False)


def is_checkbox(field):
    return isinstance(field.widget, forms.CheckboxInput)


class PageForm(forms.Form):
    """A form posted by a page, with a csrf_token field like Flask-WTF's.

    ``PageForm(request)`` binds to the POST data on a POST request. With
    ``instance``, fields start from that object's values. On a POST, a field
    the page did not send keeps the object's value (as WTForms did): a
    required field is checked with that value, an optional one is not checked.
    """
    submit_label = _('Submit')

    csrf_token = forms.CharField(label=_('CSRF Token'), required=False, widget=forms.HiddenInput)

    def __init__(self, request, instance=None):
        self.request = request
        initial = {}
        if instance is not None:
            for name, field in self.base_fields.items():
                value = getattr(instance, name, None)
                if value is not None and isinstance(field, forms.IntegerField):
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        value = None
                if value is not None:
                    initial[name] = value

        data = None
        self.posted = set()
        if request.method == 'POST':
            data = request.POST.copy()
            self.posted = set(data.keys())
            for name, value in initial.items():
                field = self.base_fields[name]
                if name not in data and field.required and not is_checkbox(field):
                    data[name] = value
        super().__init__(data, initial=initial, auto_id='%s')

    def validate_on_submit(self):
        return self.is_bound and self.is_valid()

    def clean(self):
        cleaned_data = super().clean()
        if self.is_bound and getattr(settings, 'CSRF_FORMS_ENABLED', True):
            submitted = self.data.get('csrf_token') or ''
            expected = self.request.session.get(CSRF_SESSION_KEY) or ''
            if not submitted:
                self.add_error('csrf_token', _('The CSRF token is missing.'))
            elif not expected or not hmac.compare_digest(submitted, expected):
                self.add_error('csrf_token', _('The CSRF token is invalid.'))
        return cleaned_data

    def check_match(self, name, other, message):
        """``EqualTo``: compare what was typed, once ``name`` itself has passed."""
        if name in self.cleaned_data and self.data.get(name) != self.data.get(other):
            self.add_error(name, message)

    def value(self, name):
        """The submitted value; a field the page did not send keeps the saved
        value (None when there is none)."""
        field = self.fields[name]
        if self.is_bound and name not in self.posted and not is_checkbox(field):
            return self.initial.get(name)
        return self.cleaned_data.get(name)


class LoginForm(PageForm):
    submit_label = _('Login')
    username = text(_('Username'), _('Username is required.'))
    password = password_field(_('Password'), _('Password is required.'))
    remember = checkbox(_('Remember Me'))


class ForgotPasswordForm(PageForm):
    submit_label = _('Send Reset Link')
    identity = text(_('Username or Email'), _('Username or email is required.'), min_length=3, max_length=120)


class ResetPasswordForm(PageForm):
    submit_label = _('Reset Password')
    new_password = password_field(_('New Password'), _('New password is required.'), min_length=6,
                            error_messages={'min_length': _('Password must be at least 6 characters long.')})
    confirm_new_password = password_field(_('Confirm New Password'), _('Please confirm your new password.'))

    def clean(self):
        cleaned_data = super().clean()
        self.check_match('confirm_new_password', 'new_password', _('Passwords must match.'))
        return cleaned_data


class RegistrationForm(PageForm):
    submit_label = _('Register')
    full_name = text(_('Full Name'), _('Full name is required.'))
    email = email_field(_('Email'), _('Email is required.'))
    username = text(_('Username'), _('Username is required.'), min_length=3, max_length=80, error_messages={
        'min_length': _('Username must be between 3 and 80 characters.'),
        'max_length': _('Username must be between 3 and 80 characters.'),
    })
    password = password_field(_('Password'), _('Password is required.'), min_length=6,
                        error_messages={'min_length': _('Password must be at least 6 characters long.')})
    confirm_password = password_field(_('Confirm Password'), _('Please confirm your password.'))
    phone = text(_('Phone Number'))
    role = select(_('User Role'), [
        ('', _('Select Role')),
        ('farmer', _('Farmer')),
        ('veterinarian', _('Veterinarian')),
    ], _('Please select a role.'))
    # EPA (Extension Planning Area): drives farmer<->veterinarian assignment.
    location = select(_('EPA (Mzimba North)'), [('', _('Select EPA in Mzimba North'))] + [
        (epa, epa) for epa in EPA_NAMES], _('Please select your EPA.'))
    # Section within the chosen EPA.
    specific_location = select(_('Section'), [('', _('Select Section'))] + [
        (section, section) for section in ALL_SECTIONS])

    # Farm details for farmers
    farm_name = text(_('Farm Name'))
    animal_types = select(_('Primary Animal Types'), [
        ('', _('Select Animals')),
        ('cattle', _('Cattle Only')),
        ('goat', _('Goats Only')),
        ('cattle,goat', _('Both Cattle and Goats')),
    ])
    production_focus = select(_('Production Focus'), [
        ('', _('Select Focus')),
        ('dairy', _('Dairy')),
        ('meat', _('Meat')),
        ('dual', _('Dual Purpose')),
        ('breeding', _('Breeding Stock')),
    ])

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('Username already exists.'))
        return username

    def clean_email(self):
        value = self.cleaned_data['email']
        if User.objects.filter(email=value).exists():
            raise forms.ValidationError(_('Email already registered.'))
        return value

    def clean(self):
        cleaned_data = super().clean()
        self.check_match('confirm_password', 'password', _('Passwords must match.'))
        section = cleaned_data.get('specific_location')
        if section and not section_belongs_to_epa(section, self.data.get('location')):
            self.add_error('specific_location', _('Please select a section in your EPA.'))
        return cleaned_data


class SymptomForm(PageForm):
    submit_label = _('Submit for Disease Prediction')
    animal_type = select(_('Specie'), [
        ('', _('Select Specie')),
        ('cattle', _('Cattle')),
        ('goat', _('Goat')),
    ], _('Please select a specie.'))
    animal_sex = select(_('Sex'), [
        ('female', _('Female')),
        ('male', _('Male')),
    ], _('Please select the animal sex.'))
    animal_age = integer(_('Age (months)'), min_value=0, min_message=_('Age cannot be negative.'))
    animal_weight = decimal(_('Weight (kg)'), min_value=0, range_message=_('Weight cannot be negative.'))

    is_dairy = checkbox(_('Dairy Animal'))
    lactation_stage = select(_('Lactation Stage (if dairy)'), [
        ('', _('Select Stage')),
        ('early', _('Early (0-100 days)')),
        ('mid', _('Mid (100-200 days)')),
        ('late', _('Late (200+ days)')),
        ('dry', _('Dry Period')),
    ])

    temperature = decimal(_('Body Temperature (°C)'), _('Body temperature is required.'), min_value=1, max_value=100,
                          range_message=_('Temperature must be between 1 and 100 °C.'))

    stool_consistency = select(_('Stool Consistency'), [
        ('normal', _('Normal')),
        ('loose', _('Loose')),
        ('watery', _('Watery Diarrhea')),
        ('firm', _('Firm/Hard')),
        ('bloody', _('Bloody')),
    ])
    milk_production = select(_('Milk Production (if dairy)'), [
        ('normal', _('Normal')),
        ('reduced', _('Reduced')),
        ('stopped', _('Stopped')),
        ('abnormal', _('Abnormal (clots, blood)')),
    ])

    feed_type = text(_('Current Feed Type'))
    feed_changes = textarea(_('Recent Feed Changes'))
    housing_conditions = select(_('Housing Conditions'), [
        ('good', _('Good (clean, dry, ventilated)')),
        ('fair', _('Fair')),
        ('poor', _('Poor (dirty, damp, crowded)')),
    ])
    recent_treatments = textarea(_('Recent Treatments/Medications'))

    similar_cases = integer(_('Number of Other Animals Showing Similar Symptoms'), min_value=0,
                            min_message=_('Number cannot be negative.'))

    appetite = select(_('Appetite'), [
        ('normal', _('Normal')),
        ('reduced', _('Reduced')),
        ('none', _('None')),
        ('increased', _('Increased')),
    ])
    rumen_movement = select(_('Rumen Movement'), [
        ('normal', _('Normal')),
        ('reduced', _('Reduced')),
        ('absent', _('Absent')),
    ])
    animal_breed = text(_('Breed'))


class TreatmentForm(PageForm):
    submit_label = _('Save Treatment Plan')
    medication = text(_('Medication Name'), _('Medication name is required.'))
    medication_type = select(_('Medication Type'), [
        ('antibiotic', _('Antibiotic')),
        ('antiparasitic', _('Antiparasitic')),
        ('anti-inflammatory', _('Anti-inflammatory')),
        ('vitamin', _('Vitamin/Supplement')),
        ('other', _('Other')),
    ], _('Please select a medication type.'))

    weight_based = checkbox(_('Calculate dosage by weight'))
    animal_weight = decimal(_('Animal Weight (kg)'), min_value=0, range_message=_('Weight cannot be negative.'))
    dosage_per_kg = decimal(_('Dosage per kg (mg/kg)'), min_value=0, range_message=_('Dosage cannot be negative.'))
    dosage = text(_('Total Dosage'))

    frequency = select(_('Frequency'), [
        ('once_daily', _('Once daily')),
        ('twice_daily', _('Twice daily')),
        ('three_times_daily', _('Three times daily')),
        ('every_other_day', _('Every other day')),
        ('weekly', _('Weekly')),
        ('single_dose', _('Single dose')),
    ], _('Please select a frequency.'))
    duration = integer(_('Duration (days)'), _('Duration is required.'), min_value=1,
                       min_message=_('Duration must be at least 1 day.'))
    route = select(_('Route of Administration'), [
        ('oral', _('Oral (feed/water)')),
        ('injection', _('Injection')),
        ('intramammary', _('Intramammary (for mastitis)')),
        ('topical', _('Topical')),
        ('inhalation', _('Inhalation')),
    ], _('Please select a route of administration.'))

    # Withdrawal periods (food safety)
    milk_withdrawal_days = integer(_('Milk Withdrawal Period (days)'), min_value=0,
                                   min_message=_('Days cannot be negative.'))
    meat_withdrawal_days = integer(_('Meat Withdrawal Period (days)'), min_value=0,
                                   min_message=_('Days cannot be negative.'))

    supportive_care = textarea(_('Supportive Care Instructions'))
    diet_recommendations = textarea(_('Diet Recommendations'))
    isolation_required = checkbox(_('Isolate Animal'))

    follow_up_required = checkbox(_('Schedule Follow-up Examination'))
    follow_up_date = date_field(_('Follow-up Date'))


class NewTreatmentForm(TreatmentForm):
    """A treatment plan from the treatments page, for a case the vet picks."""
    case = select(_('Case'), [], _('Please select a case.'))

    def __init__(self, request, cases):
        super().__init__(request)
        self.fields['case'].choices = [('', _('Select a case'))] + list(cases)


class MortalityReportForm(PageForm):
    submit_label = _('Submit Mortality Report')
    farmer = select(_('Farmer'), [], _('Please select the farmer who owned the animal.'))
    animal_type = select(_('Animal Type'), [
        ('cattle', _('Cattle')),
        ('goat', _('Goat')),
    ], _('Please select an animal type.'))
    age = integer(_('Age (months)'), min_value=0, min_message=_('Age cannot be negative.'))

    date_of_death = date_field(_('Date of Death'), _('Date of death is required.'))
    time_of_death = text(_('Approximate Time of Death'))

    suspected_cause = select(_('Suspected Cause of Death'), [
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
        ('other', _('Other')),
    ], _('Please select a suspected cause.'))

    was_dairy = checkbox(_('Was this a dairy animal?'))
    last_milk_production = text(_('Last Milk Production'))
    symptoms_before_death = textarea(_('Symptoms Observed Before Death'))

    treatment_provided = select(_('Treatment Provided Before Death'), [
        ('none', _('None')),
        ('basic', _('Basic Treatment')),
        ('full', _('Full Treatment')),
        ('emergency', _('Emergency Treatment')),
    ], _('Please select treatment provided.'))
    was_predicted = select(_('Was this predicted by AI?'), [
        ('no', _('No')),
        ('yes_high', _('Yes - High Confidence')),
        ('yes_medium', _('Yes - Medium Confidence')),
        ('yes_low', _('Yes - Low Confidence')),
    ], _('Please indicate if this was predicted by AI.'))

    requires_investigation = checkbox(_('This case requires further investigation'))
    lab_samples_taken = checkbox(_('Lab Samples Taken'))
    lab_results = textarea(_('Lab Results (if available)'))
    additional_notes = textarea(_('Additional Notes'))

    def __init__(self, request, farmers):
        super().__init__(request)
        self.fields['farmer'].choices = [('', _('Select farmer'))] + list(farmers)


class ProfileForm(PageForm):
    submit_label = _('Save Changes')
    full_name = text(_('Full Name'))
    email = email_field(_('Email'), _('Email is required.'))
    phone = text(_('Phone Number'))

    farm_name = text(_('Farm Name'))
    # EPA (Mzimba North): drives automatic farmer<->veterinarian assignment.
    location = select(_('EPA (Mzimba North)'), [('', _('Select EPA'))] + [(epa, epa) for epa in EPA_NAMES])
    specific_location = text(_('Village'))

    animal_types = select(_('Primary Animal Types'), [
        ('cattle', _('Cattle Only')),
        ('goat', _('Goats Only')),
        ('cattle,goat', _('Both Cattle and Goats')),
    ])
    production_focus = select(_('Production Focus'), [
        ('dairy', _('Dairy')),
        ('meat', _('Meat')),
        ('dual', _('Dual Purpose')),
        ('breeding', _('Breeding Stock')),
    ])


class ReportGenerationForm(PageForm):
    submit_label = _('Generate Report')
    report_name = text(_('Report Name'), _('Report name is required.'))
    report_type = select(_('Report Type'), [
        ('health', _('Health Summary')),
        ('breeding', _('Breeding Report')),
        ('mortality', _('Mortality Analysis')),
        ('production', _('Production Report')),
        ('financial', _('Financial Summary')),
        ('custom', _('Custom Report')),
    ], _('Please select a report type.'))
    animal_type = select(_('Animal Type'), [
        ('all', _('All Animals')),
        ('cattle', _('Cattle Only')),
        ('goat', _('Goats Only')),
    ], _('Please select an animal type.'))
    period_start = date_field(_('Start Date'), _('Start date is required.'))
    period_end = date_field(_('End Date'), _('End date is required.'))
    output_format = select(_('Output Format'), [
        ('pdf', 'PDF'),
        ('excel', _('Excel')),
        ('csv', 'CSV'),
    ], _('Please select an output format.'))
    schedule_frequency = select(_('Schedule Report'), [
        ('once', _('Generate once')),
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
    ], strict=True)
