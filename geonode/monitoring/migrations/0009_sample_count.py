from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0008_monitoring_notifications_check'),
    ]

    operations = [
        migrations.AddField(
            model_name='metricvalue',
            name='samples_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
