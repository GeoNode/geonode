# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('wm_extra', '0006_auto_20180112_1338'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action_type', models.CharField(max_length=25, choices=[[b'layer_delete', b'Layer Deleted'], [b'layer_create', b'Layer Created'], [b'layer_upload', b'Layer Uploaded'], [b'map_delete', b'Map Deleted'], [b'map_create', b'Map Created']])),
                ('description', models.CharField(max_length=255, db_index=True)),
                ('args', models.CharField(max_length=255, db_index=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
            ],
        ),
    ]
