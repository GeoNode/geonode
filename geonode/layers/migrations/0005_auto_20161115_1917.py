# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0004_auto_20161104_1944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layerauditactivity',
            name='comment_body',
            field=models.TextField(help_text='Comments when auditor denied or approved layer submission', null=True, blank=True),
        ),
    ]
