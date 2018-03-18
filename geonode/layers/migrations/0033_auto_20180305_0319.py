# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0032_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='layerstyles',
            name='layer',
        ),
        migrations.RemoveField(
            model_name='layerstyles',
            name='style',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='service',
        ),
        migrations.AlterField(
            model_name='layer',
            name='styles',
            field=models.ManyToManyField(related_name='layer_styles', to='layers.Style'),
        ),
        migrations.AlterField(
            model_name='layerfile',
            name='file',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/uploaded/'), max_length=255, upload_to=b'layers'),
        ),
        migrations.DeleteModel(
            name='LayerStyles',
        ),
    ]
