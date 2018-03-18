# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0037_layer_user_data_epsg'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='user_data_epsg',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
    ]
