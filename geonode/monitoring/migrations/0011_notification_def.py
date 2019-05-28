# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
                ('field_option', models.CharField(default=b'min_value', max_length=32, choices=[(b'min_value', b'Value must be above'), (b'max_value', b'Value must be below'), (b'max_timeout', b'Last update must not be older than')])),
            ],
        ),
        migrations.AlterField(
            model_name='metric',
            name='unit',
            field=models.CharField(blank=True, max_length=255, null=True, choices=[(b'B', b'Bytes'), (b'KB', b'Kilobytes'), (b'MB', b'Megabytes'), (b'GB', b'Gigabytes'), (b'B/s', b'Bytes per second'), (b'KB/s', b'Kilobytes per second'), (b'MB/s', b'Megabytes per second'), (b'GB/s', b'Gigabytes per second'), (b's', b'Seconds'), (b'Rate', b'Rate'), (b'%', b'Percentage'), (b'Count', b'Count')]),
        ),
        migrations.AlterField(
            model_name='metricnotificationcheck',
            name='user',
            field=models.ForeignKey(related_name='monitoring_checks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='metric',
            field=models.ForeignKey(related_name='+', to='monitoring.Metric'),
        ),
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='notification_check',
            field=models.ForeignKey(related_name='definitions', to='monitoring.NotificationCheck'),
        ),
        migrations.AddField(
            model_name='notificationcheck',
            name='metrics',
            field=models.ManyToManyField(related_name='_notificationcheck_metrics_+', through='monitoring.NotificationMetricDefinition', to='monitoring.Metric'),
        ),
    ]
