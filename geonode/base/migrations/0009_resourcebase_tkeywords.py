# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_add_thesaurus_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='tkeywords',
            field=models.ManyToManyField(help_text='formalised word(s) or phrase(s) from a fixed thesaurus used to describe the subject (space or comma-separated', to='base.ThesaurusKeyword'),
        ),
    ]