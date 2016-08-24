# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0002_auto_20160821_1919'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='keywords',
            field= taggit.managers.TaggableManager(
            to='taggit.Tag',
            through='taggit.TaggedItem',
            blank=True,
            help_text='commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject             (space or comma-separated',
            verbose_name='keywords'),
        ),
    ]
