# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='last_message_view',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 10, 20, 3, 37, 150921)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profile',
            name='last_notification_view',
            field=models.DateTimeField(default=datetime.datetime(2016, 11, 10, 20, 3, 43, 667110)),
            preserve_default=False,
        ),
    ]
