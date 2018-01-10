# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0028_auto_20170919_1550'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='created_dttm',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 7, 8, 22, 2, 548432), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attribute',
            name='date_format',
            field=models.CharField(max_length=255, null=True, verbose_name='Date Format', blank=True),
        ),
        migrations.AddField(
            model_name='attribute',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 7, 8, 22, 8, 290244), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attribute',
            name='searchable',
            field=models.BooleanField(default=False, verbose_name='Searchable?'),
        ),
    ]
