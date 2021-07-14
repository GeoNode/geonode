from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '24_initial'),
    ]

    try:
        from django.db.migrations.recorder import MigrationRecorder
        is_fake = MigrationRecorder.Migration.objects.filter(app='layers', name='24_to_26')
        is_fake_migration = is_fake.exists()
    except Exception:
        is_fake_migration = False

    if is_fake_migration:
        is_fake.update(app='datasets')
    else:
        operations = [
            migrations.AddField(
                model_name='Dataset',
                name='elevation_regex',
                field=models.CharField(max_length=128, null=True, blank=True),
            ),
            migrations.AddField(
                model_name='Dataset',
                name='has_elevation',
                field=models.BooleanField(default=False),
            ),
            migrations.AddField(
                model_name='Dataset',
                name='has_time',
                field=models.BooleanField(default=False),
            ),
            migrations.AddField(
                model_name='Dataset',
                name='is_mosaic',
                field=models.BooleanField(default=False),
            ),
            migrations.AddField(
                model_name='Dataset',
                name='time_regex',
                field=models.CharField(blank=True, max_length=128, null=True, choices=[('[0-9]{8}', 'YYYYMMDD'), ('[0-9]{8}T[0-9]{6}', "YYYYMMDD'T'hhmmss"), ('[0-9]{8}T[0-9]{6}Z', "YYYYMMDD'T'hhmmss'Z'")]),
            ),
        ]
