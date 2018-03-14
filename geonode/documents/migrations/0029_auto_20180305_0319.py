# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0033_auto_20180305_0319'),
        ('documents', '0028_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='layers',
            field=models.ManyToManyField(to='layers.Layer', null=True, through='documents.DocumentLayers', blank=True),
        ),
    ]
