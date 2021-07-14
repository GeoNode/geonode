from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0030_auto_20171212_0518'),
        ('datasets', '0028_auto_20171218_0249'),
    ]
    try:
        from django.db.migrations.recorder import MigrationRecorder
        is_fake = MigrationRecorder.Migration.objects.filter(app='layers', name='0029_layer_service')
        is_fake_migration = is_fake.exists()
    except Exception:
        is_fake_migration = False

    if is_fake_migration:
        is_fake.update(app='datasets')
    else:
        operations = [
            migrations.AddField(
                model_name='Dataset',
                name='service',
                field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='services.Service', null=True),
            ),
        ]
