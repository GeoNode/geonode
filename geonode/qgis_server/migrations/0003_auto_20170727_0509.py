# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qgis_server', '0002_qgisservermap'),
    ]

    operations = [
        migrations.CreateModel(
            name='QGISServerStyle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='style name')),
                ('title', models.CharField(max_length=255, null=True, blank=True)),
                ('body', models.TextField(null=True, verbose_name='style xml', blank=True)),
                ('style_url', models.CharField(max_length=1000, null=True, verbose_name='style url')),
                ('style_legend_url', models.CharField(max_length=1000, null=True, verbose_name='style legend url')),
            ],
        ),
        migrations.AddField(
            model_name='qgisserverlayer',
            name='default_style',
            field=models.ForeignKey(related_name='layer_default_style', default=None, to='qgis_server.QGISServerStyle', null=True),
        ),
        migrations.AddField(
            model_name='qgisserverlayer',
            name='styles',
            field=models.ManyToManyField(related_name='layer_styles', to='qgis_server.QGISServerStyle'),
        ),
    ]
