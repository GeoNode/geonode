# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0003_auto_20161023_1446'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='abstract_en',
            field=models.TextField(default=b'Abstract is very important! You are requested to update it now.', help_text='brief narrative summary of the content of the resource(s)', null=True, verbose_name='abstract', blank=True),
        ),
    ]
