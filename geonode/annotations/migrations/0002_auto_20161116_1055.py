# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='auto_show',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='annotation',
            name='pause_playback',
            field=models.BooleanField(default=False),
        ),
    ]
