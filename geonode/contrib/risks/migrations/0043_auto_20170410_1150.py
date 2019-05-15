# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0042_risks_analysis_finalize'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='riskanalysisimportdata',
            options={'ordering': ['riskapp', 'region', 'riskanalysis'], 'verbose_name': 'Risks Analysis: Import Risk Data from XLSX file', 'verbose_name_plural': 'Risks Analysis: Import Risk Data from XLSX file'},
        ),
        migrations.AddField(
            model_name='riskanalysisimportdata',
            name='riskapp',
            field=models.ForeignKey(default=1, to='risks.RiskApp'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='additionaldata',
            name='risk_analysis',
            field=models.ForeignKey(related_name='additional_data', to='risks.RiskAnalysis'),
        ),
    ]
