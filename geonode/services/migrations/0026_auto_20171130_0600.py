# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0025_harvestjob'),
    ]

    operations = [
        migrations.AlterField(
            model_name='harvestjob',
            name='service',
            field=models.ForeignKey(to='services.Service'),
        ),
    ]
