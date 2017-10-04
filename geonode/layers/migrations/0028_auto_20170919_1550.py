# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0027_auto_20170801_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='in_gazetteer',
            field=models.BooleanField(default=False, verbose_name='In Gazetteer?'),
        ),
        migrations.AddField(
            model_name='attribute',
            name='is_gaz_end_date',
            field=models.BooleanField(default=False, verbose_name='Gazetteer End Date'),
        ),
        migrations.AddField(
            model_name='attribute',
            name='is_gaz_start_date',
            field=models.BooleanField(default=False, verbose_name='Gazetteer Start Date'),
        ),
        migrations.AddField(
            model_name='layer',
            name='gazetteer_project',
            field=models.CharField(max_length=128, null=True, verbose_name='Gazetteer Project', blank=True),
        ),
        migrations.AddField(
            model_name='layer',
            name='in_gazetteer',
            field=models.BooleanField(default=False, verbose_name='In Gazetteer?'),
        ),
    ]
