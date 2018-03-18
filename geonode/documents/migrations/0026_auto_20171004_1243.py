# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '24_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0025_auto_20171004_1233'),
    ]

    operations = [
    ]
