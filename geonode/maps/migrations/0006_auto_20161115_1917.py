# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0005_auto_20161104_1945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapauditactivity',
            name='comment_body',
            field=models.TextField(help_text='Comments when auditor denied or approved layer submission', null=True, blank=True),
        ),
    ]
