# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0033_auto_20180330_0951'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='metadata_uploaded_preserve',
            field=models.BooleanField(default=False, verbose_name='Metadata uploaded preserve'),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='thumbnail_url',
            field=models.TextField(null=True, verbose_name='Thumbnail url', blank=True),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='tkeywords',
            field=models.ManyToManyField(help_text='formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject (space or comma-separated', to='base.ThesaurusKeyword', verbose_name='keywords', blank=True),
        ),
    ]
