from django.db import migrations, models
from django.db.models import F

def copy_typename(apps, schema_editor):
    Dataset = apps.get_model('datasets', 'dataset')
    ResourceBase = apps.get_model('base', 'resourcebase')
    for row in Dataset.objects.all():
        row.alternate = row.typename
        row.save(update_fields=['alternate'])

class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '24_to_26'),
    ]

    try:
        from django.db.migrations.recorder import MigrationRecorder
        is_fake = MigrationRecorder.Migration.objects.filter(app='layers', name='26_to_27')
        is_fake_migration = is_fake.exists()
    except Exception:
        is_fake_migration = False

    if is_fake_migration:
        is_fake.update(app='datasets')
    else:
        operations = [
            migrations.RunPython(copy_typename),
        ]
