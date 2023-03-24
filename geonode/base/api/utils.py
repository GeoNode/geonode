#########################################################################
#
# Copyright (C) 2020 OSGeo
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

import json


def to_internal_value(serializer, data):
    """DynamicModelSerializer return dict objects based on the fields set in their
        serializers. Somehow in the validation process objects are instantiated based on
        their id in the database. This function translates the dicts of field values into
        a Queryset object, so that validation of this objects works properly

    Args:
        serializer BaseSerializer: serializer related to the data
        data (dict): data thats used to identify object from database

    Returns:
        _type_: _description_
    """
    if isinstance(data, str):
        data = json.loads(data)

    if hasattr(serializer, "many") and serializer.many is True:
        return [serializer.get_model().objects.get(**d) for d in data]
    return serializer.get_model().objects.get(**data)
