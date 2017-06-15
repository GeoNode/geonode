# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '24_to_26'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcebase',
            name='tkeywords',
            field=models.ManyToManyField(help_text='formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject (space or comma-separated', to='base.ThesaurusKeyword', blank=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
        ),
    ]
