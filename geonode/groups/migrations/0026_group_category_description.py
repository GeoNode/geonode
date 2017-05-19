# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0025_group_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupcategory',
            name='description',
            field=models.TextField(default=None, null=True, blank=True),
        ),
    ]
