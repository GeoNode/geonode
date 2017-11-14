# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '24_initial'),
        ('qgis_server', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QGISServerMap',
            fields=[
                ('map', models.OneToOneField(primary_key=True, serialize=False, to='maps.Map')),
            ],
        ),
    ]
