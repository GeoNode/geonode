# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_to_26'),
    ]

    operations = [
        migrations.CreateModel(
            name='QGISServerLayer',
            fields=[
                ('layer', models.OneToOneField(primary_key=True, serialize=False, to='layers.Layer')),
                ('base_layer_path', models.CharField(help_text=b'Location of the base layer.', max_length=100, verbose_name=b'Base Layer Path')),
            ],
        ),
    ]
