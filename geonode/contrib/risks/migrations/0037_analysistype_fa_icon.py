# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0036_riskanalysis_unit_of_measure'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysistype',
            name='fa_icon',
            field=models.CharField(max_length=30, null=True, blank=True),
        ),
    ]
