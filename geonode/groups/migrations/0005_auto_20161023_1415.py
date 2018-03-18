# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_groupprofile_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionanswer',
            name='answer',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='questionanswer',
            name='question',
            field=models.TextField(),
        ),
    ]
