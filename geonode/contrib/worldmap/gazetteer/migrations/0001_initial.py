# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GazetteerEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('layer_name', models.CharField(max_length=255, verbose_name='Layer Name')),
                ('layer_attribute', models.CharField(max_length=255, verbose_name='Layer Attribute')),
                ('feature_type', models.CharField(max_length=255, verbose_name='Feature Type')),
                ('feature_fid', models.BigIntegerField(verbose_name='Feature FID')),
                ('latitude', models.FloatField(verbose_name='Latitude')),
                ('longitude', models.FloatField(verbose_name='Longitude')),
                ('place_name', models.TextField(verbose_name='Place name')),
                ('start_date', models.TextField(null=True, verbose_name='Start Date', blank=True)),
                ('end_date', models.TextField(null=True, verbose_name='End Date', blank=True)),
                ('julian_start', models.IntegerField(null=True, verbose_name='Julian Date Start', blank=True)),
                ('julian_end', models.IntegerField(null=True, verbose_name='Julian Date End', blank=True)),
                ('project', models.CharField(max_length=255, null=True, verbose_name='Project', blank=True)),
                ('feature', django.contrib.gis.db.models.fields.GeometryField(srid=4326, null=True, verbose_name='Geometry', blank=True)),
                ('username', models.CharField(max_length=30, null=True, verbose_name='User Name', blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='gazetteerentry',
            unique_together=set([('layer_name', 'layer_attribute', 'feature_fid')]),
        ),
    ]
