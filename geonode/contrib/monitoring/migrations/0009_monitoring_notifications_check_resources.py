# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0008_notificationcheck'),
    ]

    operations = [
        migrations.AddField(
            model_name='metricnotificationcheck',
            name='label',
            field=models.ForeignKey(blank=True, to='monitoring.MetricLabel', null=True),
        ),
        migrations.AddField(
            model_name='metricnotificationcheck',
            name='ows_service',
            field=models.ForeignKey(blank=True, to='monitoring.OWSService', null=True),
        ),
        migrations.AddField(
            model_name='metricnotificationcheck',
            name='resource',
            field=models.ForeignKey(blank=True, to='monitoring.MonitoredResource', null=True),
        ),
    ]
