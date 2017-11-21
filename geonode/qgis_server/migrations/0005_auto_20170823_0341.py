# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qgis_server', '0004_auto_20170805_0223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qgisserverlayer',
            name='default_style',
            field=models.ForeignKey(related_name='layer_default_style', on_delete=django.db.models.deletion.SET_NULL, default=None, to='qgis_server.QGISServerStyle', null=True),
        ),
    ]
