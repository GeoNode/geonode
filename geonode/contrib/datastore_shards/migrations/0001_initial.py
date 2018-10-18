# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Database',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(verbose_name='Database Shard Name')),
                ('layers_count', models.IntegerField(default=0, verbose_name='Layers Count')),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('strategy_type', models.IntegerField(choices=[(0, b'yearly'), (1, b'monthly'), (2, b'layercount')])),
            ],
            options={
                'verbose_name_plural': 'Shard Databases',
            },
        ),
    ]
