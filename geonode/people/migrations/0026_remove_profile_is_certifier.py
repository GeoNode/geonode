# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0025_auto_20170924_0932'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='is_certifier',
        ),
    ]
