# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='elevation_regex',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='layer',
            name='has_elevation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='layer',
            name='has_time',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='layer',
            name='is_mosaic',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='layer',
            name='time_regex',
            field=models.CharField(blank=True, max_length=128, null=True, choices=[(b'[0-9]{8}', 'YYYYMMDD'), (b'[0-9]{8}T[0-9]{6}', "YYYYMMDD'T'hhmmss"), (b'[0-9]{8}T[0-9]{6}Z', "YYYYMMDD'T'hhmmss'Z'")]),
        ),
    ]
