# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0035_auto_20170330_0637'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysis',
            name='unit_of_measure',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
