# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0002_monitoring_active_objects'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='url',
            field=models.URLField(default=True, null=True, blank=True),
        ),
    ]
