# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_new_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='caveat',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='classification',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='provenance',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='service_refs',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='servicelayer',
            name='srid',
            field=models.CharField(default=b'EPSG:4326', max_length=255),
        ),
    ]
