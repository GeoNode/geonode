# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0002_add_map_chapters'),
    ]

    operations = [
        migrations.AddField(
            model_name='map',
            name='viewer_playbackmode',
            field=models.CharField(max_length=32, null=True, verbose_name='Viewer Playback', blank=True),
        ),
    ]
