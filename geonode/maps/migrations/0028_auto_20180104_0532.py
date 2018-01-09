# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0027_maplayerstyle'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='maplayerstyle',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='maplayerstyle',
            name='layer',
        ),
        migrations.RemoveField(
            model_name='maplayerstyle',
            name='map',
        ),
        migrations.RemoveField(
            model_name='maplayerstyle',
            name='modified_by',
        ),
        migrations.DeleteModel(
            name='MapLayerStyle',
        ),
    ]
