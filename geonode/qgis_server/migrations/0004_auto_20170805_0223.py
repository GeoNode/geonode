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


class Migration(migrations.Migration):

    dependencies = [
        ('qgis_server', '0003_auto_20170727_0509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qgisserverlayer',
            name='layer',
            field=models.OneToOneField(related_name='qgis_layer', on_delete=models.CASCADE,
                                       primary_key=True, serialize=False, to='layers.Layer'),
        ),
        migrations.AlterField(
            model_name='qgisserverstyle',
            name='name',
            field=models.CharField(max_length=255, verbose_name='style name'),
        ),
    ]
