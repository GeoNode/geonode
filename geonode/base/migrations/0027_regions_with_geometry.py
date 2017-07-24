# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('base', '26_to_27'),
    ]

    operations = [
        migrations.AddField(
            model_name='region',
            name='envelope',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326, null=True),
        ),
        migrations.AddField(
            model_name='region',
            name='geom',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326, null=True),
        ),
    ]
