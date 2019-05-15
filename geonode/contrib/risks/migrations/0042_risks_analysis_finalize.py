# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0041_risks_analysis_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='riskanalysis',
            name='layer',
            field=models.ForeignKey(related_name='base_layer', null=False, to='layers.Layer'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='riskanalysisdymensioninfoassociation',
            name='layer',
        ),
        migrations.RemoveField(
            model_name='riskanalysisdymensioninfoassociation',
            name='style',
        ),
    ]
