# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_to_26'),
        ('risks', '0044_auto_20170411_0440'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysis',
            name='reference_layer',
            field=models.ForeignKey(related_name='reference_layer', blank=True, to='layers.Layer', null=True),
        ),
        migrations.AddField(
            model_name='riskanalysis',
            name='reference_style',
            field=models.ForeignKey(related_name='style_reference_layer', blank=True, to='layers.Style', null=True),
        ),
    ]
