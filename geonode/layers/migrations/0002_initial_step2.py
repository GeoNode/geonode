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


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0001_initial'),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='service',
            field=models.ForeignKey(related_name='layer_set', blank=True, to='services.Service', null=True),
        ),
        migrations.AddField(
            model_name='layer',
            name='styles',
            field=models.ManyToManyField(related_name='LayerStyles', to='layers.Style'),
        ),
        migrations.AddField(
            model_name='layer',
            name='upload_session',
            field=models.ForeignKey(blank=True, to='layers.UploadSession', null=True),
        ),
        migrations.AddField(
            model_name='attribute',
            name='layer',
            field=models.ForeignKey(related_name='attribute_set', to='layers.Layer'),
        ),
    ]
