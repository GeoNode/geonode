# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qgis_server', '0003_auto_20170727_0509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qgisserverlayer',
            name='layer',
            field=models.OneToOneField(related_name='qgis_layer', primary_key=True, serialize=False, to='layers.Layer'),
        ),
        migrations.AlterField(
            model_name='qgisserverstyle',
            name='name',
            field=models.CharField(max_length=255, verbose_name='style name'),
        ),
    ]
