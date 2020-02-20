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



from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qgis_server', '0004_auto_20170805_0223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qgisserverlayer',
            name='default_style',
            field=models.ForeignKey(related_name='layer_default_style', on_delete=models.SET_NULL,
                                    default=None, to='qgis_server.QGISServerStyle', null=True),
        ),
    ]
