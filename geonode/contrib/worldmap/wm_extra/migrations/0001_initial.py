# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '24_initial'),
        ('maps', '24_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LayerStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('visits', models.IntegerField(default=0, verbose_name='Visits')),
                ('uniques', models.IntegerField(default=0, verbose_name='Unique Visitors')),
                ('downloads', models.IntegerField(default=0, verbose_name='Downloads')),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('layer', models.ForeignKey(to='layers.Layer', unique=True)),
            ],
            options={
                'verbose_name_plural': 'Layer stats',
            },
        ),
        migrations.CreateModel(
            name='MapStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('visits', models.IntegerField(default=0, verbose_name='Visits')),
                ('uniques', models.IntegerField(default=0, verbose_name='Unique Visitors')),
                ('last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('map', models.ForeignKey(to='maps.Map', unique=True)),
            ],
            options={
                'verbose_name_plural': 'Map stats',
            },
        ),
    ]
