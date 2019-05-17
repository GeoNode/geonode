# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields

from geonode.contrib.risks import models as risks_models

class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0035_auto_20170330_0637'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalData',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=255)),
                ('data', jsonfield.fields.JSONField(default={})),
                ('risk_analysis', models.ForeignKey(to='risks.RiskAnalysis')),
            ],
        ),
        migrations.CreateModel(
            name='RiskApp',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64, choices=[(b'data_extraction', b'Data Extraction'), (b'cost_benefit_analysis', b'Cost Benefit Analysis')])),
            ],
        ),
        migrations.RunPython(risks_models.create_risks_apps, risks_models.uncreate_risks_apps),
        migrations.AddField(
            model_name='analysistype',
            name='app',
            field=models.ForeignKey(default=risks_models.get_risk_app_default, to='risks.RiskApp'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='hazardtype',
            name='app',
            field=models.ForeignKey(default=risks_models.get_risk_app_default, to='risks.RiskApp'),
            preserve_default=False,
        ),
    ]
