# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gazetteer', '0002_gazetteerattribute'),
    ]

    operations = [
        migrations.AddField(
            model_name='gazetteerattribute',
            name='date_format',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='gazetteerattribute',
            name='is_end_date',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='gazetteerattribute',
            name='is_start_date',
            field=models.BooleanField(default=False),
        ),
    ]
