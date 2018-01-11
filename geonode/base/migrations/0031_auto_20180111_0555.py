# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0030_auto_20171215_0341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hierarchicalkeyword',
            name='depth',
            field=models.PositiveIntegerField(),
        ),
    ]
