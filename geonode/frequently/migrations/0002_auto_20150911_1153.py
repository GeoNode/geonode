# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('frequently', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='answer',
            field=ckeditor.fields.RichTextField(default='foo', verbose_name='Answer', blank=True),
            preserve_default=False,
        ),
    ]
