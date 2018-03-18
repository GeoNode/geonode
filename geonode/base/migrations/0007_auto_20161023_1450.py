# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_auto_20161023_1415'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resourcebase',
            old_name='a_current_iteration',
            new_name='current_iteration',
        ),
        migrations.RenameField(
            model_name='resourcebase',
            old_name='a_date_created',
            new_name='date_created',
        ),
        migrations.RenameField(
            model_name='resourcebase',
            old_name='a_date_updated',
            new_name='date_updated',
        ),
        migrations.RenameField(
            model_name='resourcebase',
            old_name='a_group',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='resourcebase',
            old_name='a_last_auditor',
            new_name='last_auditor',
        ),
        migrations.RenameField(
            model_name='resourcebase',
            old_name='a_status',
            new_name='status',
        ),
    ]
