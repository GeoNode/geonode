# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0028_resourcebase_is_approved'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcebase',
            name='is_approved',
        ),
    ]
