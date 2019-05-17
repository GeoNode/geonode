# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models



class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_to_26'),
        ('risks', '0039_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysis',
            name='layer',
            field=models.ForeignKey(related_name='base_layer', blank=True, null=True, default=None, to='layers.Layer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='riskanalysis',
            name='style',
            field=models.ForeignKey(related_name='style_layer', blank=True, to='layers.Style', null=True)
        ),


    ]
