from django.db import migrations
from django.db.migrations.operations import RunPython

from geonode.services.models import Service


def update_services_metadata_only(apps, schema_editor):
    Service.objects.filter(metadata_only=False).update(metadata_only=True)

class Migration(migrations.Migration):

    dependencies = [
        ('services', '0031_service_probe'),
        ('services', '0041_auto_20190404_0820'),
    ]

    operations = [
        RunPython(update_services_metadata_only, migrations.RunPython.noop)
    ]
