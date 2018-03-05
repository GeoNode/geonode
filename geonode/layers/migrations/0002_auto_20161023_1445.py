# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='title_en',
            field=models.CharField(help_text='name by which the cited resource is known', max_length=255, null=True, verbose_name='* Title'),
        ),
        migrations.AddField(
            model_name='layer',
            name='user_data_epsg',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
    ]
