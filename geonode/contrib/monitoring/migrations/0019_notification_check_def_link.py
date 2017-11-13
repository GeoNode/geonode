# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0018_notification_check_def'),
    ]

    operations = [
        migrations.AddField(
            model_name='metricnotificationcheck',
            name='definition',
            field=models.OneToOneField(related_name='metric_check', null=True, to='monitoring.NotificationMetricDefinition'),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='active',
            field=models.BooleanField(default=True, help_text=b'Is it active'),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='description',
            field=models.CharField(help_text=b'Description of the alert', max_length=255),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='severity',
            field=models.CharField(default=b'error', help_text=b'How severe would be error from this notification', max_length=32, choices=[(b'warning', b'Warning'), (b'error', b'Error'), (b'fatal', b'Fatal')]),
        ),
        migrations.AlterField(
            model_name='notificationcheck',
            name='user_threshold',
            field=jsonfield.fields.JSONField(default={}, help_text=b'Expected min/max values for user configuration'),
        ),
    ]
