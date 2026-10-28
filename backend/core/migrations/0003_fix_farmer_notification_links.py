"""Farmers' treatment and diagnosis notifications used to link to vet-only
pages (which sent the farmer to "You do not have permission"). Point them at
the farmer's predictions page."""
from django.db import migrations

VET_PAGES = ['/veterinarian/treatments', '/veterinarian/predictions']


def fix_links(apps, schema_editor):
    Notification = apps.get_model('core', 'Notification')
    Notification.objects.filter(user__role='farmer', action_url__in=VET_PAGES).update(
        action_url='/farmer/predictions')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seed_data'),
    ]

    operations = [
        migrations.RunPython(fix_links, migrations.RunPython.noop),
    ]
