# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0003_loadactivity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pinpointuseractivity',
            old_name='point',
            new_name='the_geom',
        ),
        migrations.AddField(
            model_name='loadactivity',
            name='activity_type',
            field=models.CharField(default='load', help_text='Activity Type', max_length=10, verbose_name='Activity Type', choices=[(b'share', 'share'), (b'load', 'load'), (b'download', 'download')]),
            preserve_default=False,
        ),
    ]
