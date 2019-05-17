# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0045_auto_20170411_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysisdymensioninfoassociation',
            name='layer_reference_attribute',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
    ]
