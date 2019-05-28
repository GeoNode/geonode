# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0014_notifications_emails'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationcheck',
            name='grace_period',
            field=models.DurationField(default=datetime.timedelta(0, 600), help_text=b'Minimum time between subsequent notifications', choices=[(datetime.timedelta(0, 60), b'1 minute'), (datetime.timedelta(0, 300), b'5 minutes'), (datetime.timedelta(0, 600), b'10 minutes'), (datetime.timedelta(0, 1800), b'30 minutes'), (datetime.timedelta(0, 3600), b'1 hour')]),
        ),
        migrations.AddField(
            model_name='notificationcheck',
            name='last_send',
            field=models.DateTimeField(help_text=b'Marker of last delivery', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='notificationmetricdefinition',
            name='metric',
            field=models.ForeignKey(related_name='notification_checks', to='monitoring.Metric'),
        ),
    ]
