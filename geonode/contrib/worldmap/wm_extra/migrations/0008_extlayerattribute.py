# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0029_layer_service'),
        ('wm_extra', '0007_action'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtLayerAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('searchable', models.BooleanField(default=False)),
                ('attribute', models.OneToOneField(to='layers.Attribute')),
            ],
        ),
    ]
