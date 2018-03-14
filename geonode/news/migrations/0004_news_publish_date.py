# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_auto_20161115_1917'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='publish_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 1, 26, 19, 26, 26, 584049)),
            preserve_default=False,
        ),
    ]
