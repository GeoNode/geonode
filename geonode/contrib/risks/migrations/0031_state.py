# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0030_risk_analysis_style'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysis',
            name='state',
            field=models.CharField(default=b'ready', max_length=64, choices=[(b'queued', b'Queued'), (b'processing', b'Processing'), (b'ready', b'Ready'), (b'error', b'Error')]),
        ),
        migrations.AlterField(
            model_name='riskanalysis',
            name='additional_layers',
            field=models.ManyToManyField(to='layers.Layer', blank=True),
        ),
        migrations.AlterField(
            model_name='riskanalysisdymensioninfoassociation',
            name='style',
            field=models.ForeignKey(related_name='style_layer', blank=True, to='layers.Style', null=True),
        ),
    ]
