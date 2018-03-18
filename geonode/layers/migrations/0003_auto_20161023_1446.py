# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0002_auto_20161023_1445'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='layer',
            name='current_iteration',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='date_updated',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='group',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='last_auditor',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='status',
        ),
    ]
