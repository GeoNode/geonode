from django.db import migrations, models
from django.db.models import F

def copy_typename(apps, schema_editor):
    Layer = apps.get_model('layers', 'layer')
    ResourceBase = apps.get_model('base', 'resourcebase')
    for row in Layer.objects.all():
        row.alternate = row.typename
        row.save(update_fields=['alternate'])

class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_to_26'),
    ]

    operations = [
        migrations.RunPython(copy_typename, migrations.RunPython.noop),
    ]
