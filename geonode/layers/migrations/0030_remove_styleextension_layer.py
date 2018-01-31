# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0029_auto_20171220_0040'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='styleextension',
            name='layer',
        ),
    ]
