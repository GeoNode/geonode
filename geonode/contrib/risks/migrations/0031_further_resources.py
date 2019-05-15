# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0030_risk_analysis_style'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysistypefurtherresourceassociation',
            name='analysis_type',
            field=models.ForeignKey(default=None, to='risks.AnalysisType'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='analysistypefurtherresourceassociation',
            name='resource',
            field=models.ForeignKey(related_name='analysis_type', to='risks.FurtherResource'),
        ),
        migrations.AlterField(
            model_name='dymensioninfofurtherresourceassociation',
            name='dymension_info',
            field=models.ForeignKey(related_name='further_resource', blank=True, to='risks.DymensionInfo', null=True),
        ),
        migrations.AlterField(
            model_name='dymensioninfofurtherresourceassociation',
            name='resource',
            field=models.ForeignKey(related_name='dimension_info', to='risks.FurtherResource'),
        ),
        migrations.AlterField(
            model_name='hazardsetfurtherresourceassociation',
            name='hazardset',
            field=models.ForeignKey(default=None, to='risks.HazardSet'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='hazardsetfurtherresourceassociation',
            name='resource',
            field=models.ForeignKey(related_name='hazard_set', to='risks.FurtherResource'),
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
