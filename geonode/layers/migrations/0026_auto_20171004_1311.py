# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0025_auto_20171004_1258'),
        ('layers', '0025_auto_20171004_1231'),
    ]

    operations = [
    ]
