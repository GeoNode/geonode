from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_monitoring_init'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='metricvalue',
            unique_together={('valid_from', 'valid_to', 'service', 'service_metric', 'resource', 'label')},
        ),
    ]
