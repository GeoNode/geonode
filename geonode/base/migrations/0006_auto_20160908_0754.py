# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_auto_20160825_0400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='keywords',
            field=taggit.managers.TaggableManager(to='base.HierarchicalKeyword', through='base.TaggedContentItem', blank=True, help_text='commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject (space or comma-separated', verbose_name='keywords'),
        ),
    ]
