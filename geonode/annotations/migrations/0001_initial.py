# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0003_map_viewer_playbackmode'),
    ]

    operations = [
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField()),
                ('content', models.TextField(null=True, blank=True)),
                ('media', models.TextField(null=True, blank=True)),
                ('the_geom', models.TextField(null=True, blank=True)),
                ('start_time', models.BigIntegerField(null=True, blank=True)),
                ('end_time', models.BigIntegerField(null=True, blank=True)),
                ('in_timeline', models.BooleanField(default=False)),
                ('in_map', models.BooleanField(default=False)),
                ('appearance', models.TextField(null=True, blank=True)),
                ('map', models.ForeignKey(to='maps.Map')),
            ],
        ),
    ]
