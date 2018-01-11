# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0029_auto_20171114_0341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='HierarchicalKeyword',
            name='depth',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
