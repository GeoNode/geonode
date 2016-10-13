# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0002_initial_step2'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='layer',
            options={'verbose_name_plural': 'StoryLayers', 'permissions': (('change_layer_data', 'Can edit layer data'), ('change_layer_style', 'Can change layer style'))},
        ),
        migrations.AlterField(
            model_name='layerfile',
            name='file',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/uploaded/'), max_length=255, upload_to=b'layers'),
        ),
    ]
