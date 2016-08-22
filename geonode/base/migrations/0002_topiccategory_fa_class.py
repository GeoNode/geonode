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

import json
import os

from django.db import migrations, models


class Migration(migrations.Migration):

    DEFAULT_FA_CLASS = b"fa-times"
    SQL_UPDATE = "UPDATE base_topiccategory SET fa_class=%s WHERE identifier=%s AND fa_class='" \
                 + DEFAULT_FA_CLASS + "';"

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='topiccategory',
            name='fa_class',
            field=models.CharField(default=DEFAULT_FA_CLASS, max_length=64),
        )
    ]

    current = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.abspath(os.path.join(current, os.pardir))
    fixture = os.path.join(parent, 'fixtures/initial_data.json')
    # geonode/base/fixtures/initial_data.json

    with open(fixture) as data_file:
        data = json.load(data_file)

        for record in data:
            if(record['model'] == "base.topiccategory"):
                fields = record['fields']
                id = fields['identifier']
                fa = fields['fa_class']

                if(fa == DEFAULT_FA_CLASS):
                    raise ValueError('Default fa_class should not be used for any '
                                     'specific TopicCategory (class={} cat={})'.format(fa, id))

                operations.append(migrations.RunSQL([(SQL_UPDATE, [fa, id])]),)
