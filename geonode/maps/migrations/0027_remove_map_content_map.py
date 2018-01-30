# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0026_map_content_map'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='map',
            name='content_map',
        ),
    ]
