# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_monitoring_init'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='service',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='service',
            name='check_interval',
            field=models.DurationField(default=datetime.timedelta(0, 60)),
        ),
        migrations.AddField(
            model_name='service',
            name='last_check',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='service',
            name='notes',
            field=models.TextField(null=True, blank=True),
        ),
    ]
