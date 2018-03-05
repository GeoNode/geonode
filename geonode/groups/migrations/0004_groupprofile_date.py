# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0003_auto_20160815_0504'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupprofile',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 28, 2, 1, 54, 628276), auto_now=True),
            preserve_default=False,
        ),
    ]
