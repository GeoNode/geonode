# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0015_notification_grace_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationcheck',
            name='severity',
            field=models.CharField(default=b'error', max_length=32, choices=[(b'warning', b'Warning'), (b'error', b'Error'), (b'fatal', b'Fatal')]),
        ),
    ]
