"""Data the Flask version set up on every start, now done once by `migrate`:

* demo accounts (password ``pass123``), approved, with vet1 in farmer1's EPA;
* stored EPA names brought in line with locations.py (renamed EPAs, section
  letter case), then farmers and vets re-linked by EPA;
* a record of the deployed prediction model.

Safe on an existing database: nothing that already exists is created twice.
"""
from datetime import date, datetime, timedelta, timezone

from django.db import migrations
from werkzeug.security import generate_password_hash

from core.locations import EPA_NAMES, EPA_SECTIONS, RENAMED_EPAS


def malawi_now():
    return datetime.now(timezone(timedelta(hours=2))).replace(tzinfo=None)


DEFAULT_USERS = [
    dict(username='sysadmin', email='sysadmin@animalhealth.com', full_name='System Administrator',
         role='system_admin', location='Headquarters'),
    dict(username='orgadmin', email='orgadmin@animalhealth.com', full_name='Organization Administrator',
         role='organization_admin', location='Headquarters'),
    dict(username='vet1', email='vet1@animalhealth.com', full_name='Dr. Sarah Smith',
         phone='+1 (555) 987-6543', role='veterinarian', location='Zombwe'),
    dict(username='farmer1', email='farmer1@example.com', full_name='John Farmer',
         phone='+1 (555) 123-4567', role='farmer', location='Zombwe', farm_name='Green Valley Farm',
         animal_types='Cattle,Goats', production_focus='dairy'),
]


def link_by_location(User, FarmerVeterinarian, user):
    """The app's auto_assign_by_location, on the migration's models."""
    location = (user.location or '').strip()
    if not location or user.status != 'approved' or user.role not in ('farmer', 'veterinarian'):
        return
    other_role = 'veterinarian' if user.role == 'farmer' else 'farmer'
    for other in User.objects.filter(role=other_role, status='approved', location=location).order_by('id'):
        farmer, vet = (user, other) if user.role == 'farmer' else (other, user)
        if not FarmerVeterinarian.objects.filter(farmer=farmer, veterinarian=vet).exists():
            FarmerVeterinarian.objects.create(farmer=farmer, veterinarian=vet, assigned_date=malawi_now())


def fix_epa_locations(User, FarmerVeterinarian):
    changed = False
    for old_name, new_name in RENAMED_EPAS.items():
        changed |= bool(User.objects.filter(location=old_name).update(location=new_name))

    for user in User.objects.filter(location__in=EPA_NAMES, specific_location__isnull=False):
        typed = (user.specific_location or '').strip()
        if not typed:
            continue
        listed = {section.lower(): section for section in EPA_SECTIONS[user.location]}
        canonical = listed.get(typed.lower())
        if canonical and canonical != user.specific_location:
            user.specific_location = canonical
            user.save(update_fields=['specific_location'])
            changed = True

    if changed:
        for user in User.objects.filter(role__in=['farmer', 'veterinarian'], status='approved'):
            link_by_location(User, FarmerVeterinarian, user)


def create_default_users(User, FarmerVeterinarian):
    for details in DEFAULT_USERS:
        user = User.objects.filter(username=details['username']).first()
        if user is None:
            user = User(password=generate_password_hash('pass123'), registration_date=malawi_now(), **details)
        user.status = 'approved'
        user.approved_at = user.approved_at or malawi_now()
        user.rejected_at = None
        user.save()

    # Keep the sample vet in the sample farmer's EPA so they are linked.
    vet = User.objects.filter(username='vet1').first()
    farmer = User.objects.filter(username='farmer1').first()
    if vet and farmer:
        if vet.location != farmer.location:
            vet.location = farmer.location
            vet.save(update_fields=['location'])
        link_by_location(User, FarmerVeterinarian, vet)


def record_model_version(ModelVersion):
    if not ModelVersion.objects.filter(version='v1.0').exists():
        ModelVersion.objects.create(
            version='v1.0',
            status='production',
            accuracy=0.997,
            training_data_size=5130,
            training_date=date(2026, 5, 24),
            deployment_date=date(2026, 6, 25),
            algorithm='StackingClassifier',
            animal_types='cattle,goat',
            created_at=malawi_now(),
        )


def seed(apps, schema_editor):
    User = apps.get_model('core', 'User')
    FarmerVeterinarian = apps.get_model('core', 'FarmerVeterinarian')
    ModelVersion = apps.get_model('core', 'ModelVersion')

    # Rows from the Flask days may have these empty.
    User.objects.filter(status__isnull=True).update(status='approved')
    User.objects.filter(preferred_language__isnull=True).update(preferred_language='en')

    fix_epa_locations(User, FarmerVeterinarian)
    create_default_users(User, FarmerVeterinarian)
    record_model_version(ModelVersion)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
