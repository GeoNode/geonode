# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_auto_20161019_1453'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcebase',
            name='a_date_created',
        ),
    ]
