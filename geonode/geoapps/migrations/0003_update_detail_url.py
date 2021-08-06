from django.db import migrations
from django.db.migrations.operations import RunPython


def update_geoapps_detail_url(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('geoapps', '0002_auto_20210615_0717'),
    ]

    operations = [
        RunPython(update_geoapps_detail_url, migrations.RunPython.noop)
    ]
