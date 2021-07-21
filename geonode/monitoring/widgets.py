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


from django.forms.widgets import Textarea
from django.core.exceptions import ValidationError
from django.core import validators

MULTI_EMAIL_FIELD_EMPTY_VALUES = validators.EMPTY_VALUES + ('[]', )


class MultiEmailWidget(Textarea):

    is_hidden = False

    def prep_value(self, value):
        """ Prepare value before effectively render widget """
        if value in MULTI_EMAIL_FIELD_EMPTY_VALUES:
            return ""
        elif isinstance(value, str):
            return value
        elif isinstance(value, list):
            return "\n".join(value)
        raise ValidationError('Invalid format.')

    def render(self, name, value, attrs=None, renderer=None):
        value = self.prep_value(value)
        return super().render(name, value, attrs, renderer)
