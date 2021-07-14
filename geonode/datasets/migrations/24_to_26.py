from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '24_initial'),
    ]

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
