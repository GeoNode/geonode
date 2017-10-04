# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '24_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='map',
            name='abstract_en',
            field=models.TextField(default=b'Abstract is very important! You are requested to update it now.', help_text='brief narrative summary of the content of the resource(s)', null=True, verbose_name='abstract', blank=True),
        ),
        migrations.AlterField(
            model_name='map',
            name='title_en',
            field=models.CharField(help_text='name by which the cited resource is known', max_length=255, null=True, verbose_name='* Title'),
        ),
    ]
