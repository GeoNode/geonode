# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_to_26'),
        ('risks', '0029_risk_additional_layers'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysisdymensioninfoassociation',
            name='style',
            field=models.ForeignKey(related_name='risk_analysis', blank=True, to='layers.Style', null=True),
        ),
    ]
