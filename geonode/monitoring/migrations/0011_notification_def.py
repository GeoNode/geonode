from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0010_metric_unit'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationMetricDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('use_service', models.BooleanField(default=False)),
                ('use_resource', models.BooleanField(default=False)),
                ('use_label', models.BooleanField(default=False)),
                ('use_ows_service', models.BooleanField(default=False)),
                ('field_option', models.CharField(default='min_value', max_length=32, choices=[('min_value','Value must be above'), ('max_value','Value must be below'), ('max_timeout','Last update must not be older than')])),
            ],
        ),
        migrations.AlterField(
            model_name='metric',
            name='unit',
            field=models.CharField(blank=True, max_length=255, null=True, choices=[('B','Bytes'), ('KB','Kilobytes'), ('MB','Megabytes'), ('GB','Gigabytes'), ('B/s','Bytes per second'), ('KB/s','Kilobytes per second'), ('MB/s','Megabytes per second'), ('GB/s','Gigabytes per second'), ('s','Seconds'), ('Rate','Rate'), ('%','Percentage'), ('Count','Count')]),
        ),
        migrations.AlterField(
            model_name='metricnotificationcheck',
            name='user',
            field=models.ForeignKey(related_name='monitoring_checks',
                                    to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='metric',
            field=models.ForeignKey(related_name='+', to='monitoring.Metric', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='notification_check',
            field=models.ForeignKey(related_name='definitions',
                                    to='monitoring.NotificationCheck', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='notificationcheck',
            name='metrics',
            field=models.ManyToManyField(related_name='_notificationcheck_metrics_+', through='monitoring.NotificationMetricDefinition', to='monitoring.Metric'),
        ),
    ]
