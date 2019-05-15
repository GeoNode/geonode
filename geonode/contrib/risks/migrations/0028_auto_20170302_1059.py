# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0027_increased_filefield_name_limit'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='riskanalysiscreate',
            options={'ordering': ['descriptor_file'], 'verbose_name': 'Risks Analysis: Create new through a .ini                         descriptor file', 'verbose_name_plural': 'Risks Analysis: Create new through a .ini                                descriptor file'},
        ),
        migrations.AlterModelOptions(
            name='riskanalysisimportmetadata',
            options={'ordering': ['region', 'riskanalysis'], 'verbose_name': 'Risks Analysis: Import or Update Risk Metadata from                         XLSX file', 'verbose_name_plural': 'Risks Analysis: Import or Update Risk Metadata                                from XLSX file'},
        ),
        migrations.AlterField(
            model_name='riskanalysisdymensioninfoassociation',
            name='dymensioninfo',
            field=models.ForeignKey(related_name='riskanalysis_associacion', to='risks.DymensionInfo'),
        ),
        migrations.AlterField(
            model_name='riskanalysisdymensioninfoassociation',
            name='riskanalysis',
            field=models.ForeignKey(related_name='dymensioninfo_associacion', to='risks.RiskAnalysis'),
        ),
    ]
