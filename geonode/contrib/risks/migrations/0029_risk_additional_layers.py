# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_to_26'),
        ('risks', '0028_auto_20170302_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysis',
            name='additional_layers',
            field=models.ManyToManyField(to='layers.Layer'),
        ),
    ]
