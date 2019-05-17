# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models



def get_default_app():
    from geonode.contrib.risks.models import RiskApp
    return RiskApp.objects.all().first().id
    
class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0043_auto_20170410_1150'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='riskanalysisimportmetadata',
            options={'ordering': ['riskapp', 'region', 'riskanalysis'], 'verbose_name': 'Risks Analysis: Import or Update Risk Metadata from                         XLSX file', 'verbose_name_plural': 'Risks Analysis: Import or Update Risk Metadata                                from XLSX file'},
        ),
        migrations.AddField(
            model_name='riskanalysisimportmetadata',
            name='riskapp',
            field=models.ForeignKey(default=get_default_app, to='risks.RiskApp'),
            preserve_default=False,
        ),
    ]
