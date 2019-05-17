# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def migrate_layers(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    #RA = apps.get_model('risks', 'RiskAnalysis')
    DIRA = apps.get_model('risks', 'RiskAnalysisDymensionInfoAssociation')
    for d in DIRA.objects.all():

        d.riskanalysis.layer = d.layer
        d.riskanalysis.style = d.style
        d.riskanalysis.save()

def unmigrate_layers(apps, schema_editor):
    if schema_editor.connection.alias != 'default':
        return
    RA = apps.get_model('risks', 'RiskAnalysis')
    #DIRA = apps.get_model('risks', 'RiskAnalysisDymensionInfoAssociation')
    for d in RA.objects.all():
        d.dymensioninfo_associacion.layer = d.layer
        d.dymensioninfo_associacion.style = d.style
        d.dymensioninfo_associacion.save()


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0040_risk_analysis_layer'),
    ]

    operations = [
        migrations.RunPython(migrate_layers, unmigrate_layers),
    ]
