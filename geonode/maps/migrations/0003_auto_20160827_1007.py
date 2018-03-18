# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0002_wmsserver'),
    ]

    operations = [
        migrations.AddField(
            model_name='wmsserver',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 27, 10, 6, 48, 769904), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wmsserver',
            name='date_updated',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 27, 10, 7, 51, 74619), auto_now=True),
            preserve_default=False,
        ),
    ]
