# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0002_auto_20161110_2003'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='last_message_view',
        ),
        migrations.AlterField(
            model_name='profile',
            name='last_notification_view',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
