from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Concat
from django.db.migrations.operations import RunPython

from geonode.geoapps.models import GeoApp


def update_geoapps_detail_url(apps, schema_editor):
    GeoApp.objects.update(detail_url=Concat(Value('/apps/'), 'id'))


class Migration(migrations.Migration):

    dependencies = [
        ('geoapps', '0002_auto_20210615_0717'),
    ]

    operations = [
        RunPython(update_geoapps_detail_url)
    ]
