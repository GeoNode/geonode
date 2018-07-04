# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wm_extra', '0002_endpoint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layerstats',
            name='layer',
            field=models.OneToOneField(to='layers.Layer'),
        ),
        migrations.AlterField(
            model_name='mapstats',
            name='map',
            field=models.OneToOneField(to='maps.Map'),
        ),
    ]
