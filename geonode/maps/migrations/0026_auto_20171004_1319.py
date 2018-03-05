# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0025_auto_20171004_1258'),
        ('maps', '0025_auto_20171004_1233'),
    ]

    operations = [
    ]
