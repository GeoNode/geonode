# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wm_extra', '0003_auto_20171019_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layerstats',
            name='layer',
            field=models.OneToOneField(related_name='layer_stats', to='layers.Layer'),
        ),
        migrations.AlterField(
            model_name='mapstats',
            name='map',
            field=models.OneToOneField(related_name='map_stats', to='maps.Map'),
        ),
    ]
