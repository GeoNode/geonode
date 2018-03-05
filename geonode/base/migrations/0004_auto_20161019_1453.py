# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20160817_0506'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='a_date_created',
            field=models.DateTimeField(default=datetime.datetime(2016, 10, 19, 14, 53, 5, 984318), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='title',
            field=models.CharField(help_text='name by which the cited resource is known', max_length=255, verbose_name='* Title'),
        ),
    ]
