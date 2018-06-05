# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wm_extra', '0008_extlayerattribute'),
    ]

    operations = [
        migrations.AddField(
            model_name='extmap',
            name='group_params',
            field=models.TextField(verbose_name='Layer Category Parameters', blank=True),
        ),
    ]
