# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='keywords',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True,
                                                  help_text='commonly used word(s) or formalised word(s)'
                                                            'or phrase(s) used to describe the subject'
                                                            ' (space or comma-separated',
                                                            verbose_name='keywords'),
        ),
    ]
