from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0027_auto_20170801_1228'),
    ]

    try:
        from django.db.migrations.recorder import MigrationRecorder
        is_fake = MigrationRecorder.Migration.objects.filter(app='layers', name='0028_auto_20171218_0249')
        is_fake_migration = is_fake.exists()
    except Exception:
        is_fake_migration = False

    if is_fake_migration:
        is_fake.update(app='datasets')
    else:
        operations = [
            migrations.AlterField(
                model_name='Dataset',
                name='default_style',
                field=models.ForeignKey(related_name='layer_default_style', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='datasets.Style', null=True),
            ),
        ]
