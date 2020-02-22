# -*- coding: utf-8 -*-

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
            field=models.DurationField(default=datetime.timedelta(0, 600), help_text='Minimum time between subsequent notifications', choices=[(datetime.timedelta(0, 60),'1 minute'), (datetime.timedelta(0, 300),'5 minutes'), (datetime.timedelta(0, 600),'10 minutes'), (datetime.timedelta(0, 1800),'30 minutes'), (datetime.timedelta(0, 3600),'1 hour')]),
        ),
        migrations.AddField(
            model_name='notificationcheck',
            name='last_send',
            field=models.DateTimeField(help_text='Marker of last delivery', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='notificationmetricdefinition',
            name='metric',
            field=models.ForeignKey(related_name='notification_checks',
                                    to='monitoring.Metric', on_delete=models.CASCADE),
        ),
    ]
