# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0002_initial_step2'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('import_id', models.BigIntegerField(null=True)),
                ('state', models.CharField(max_length=16)),
                ('date', models.DateTimeField(default=datetime.datetime.now, verbose_name=b'date')),
                ('upload_dir', models.CharField(max_length=100, null=True)),
                ('name', models.CharField(max_length=64, null=True)),
                ('complete', models.BooleanField(default=False)),
                ('session', models.TextField(null=True)),
                ('metadata', models.TextField(null=True)),
                ('mosaic_time_regex', models.CharField(max_length=128, null=True)),
                ('mosaic_time_value', models.CharField(max_length=128, null=True)),
                ('mosaic_elev_regex', models.CharField(max_length=128, null=True)),
                ('mosaic_elev_value', models.CharField(max_length=128, null=True)),
                ('layer', models.ForeignKey(to='layers.Layer', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='UploadFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to=b'uploads')),
                ('slug', models.SlugField(blank=True)),
                ('upload', models.ForeignKey(blank=True, to='upload.Upload', null=True)),
            ],
        ),
    ]
