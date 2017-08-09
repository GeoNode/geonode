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
import os

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def _extension_validator(value):
    __, ext = os.path.splitext(value.name)
    if not ext == '.qml':
        raise ValidationError('Only accept QML file.')


class QGISLayerStyleUploadForm(forms.Form):

    alphanumeric = RegexValidator(
        r'^[0-9a-zA-Z_]*$',
        'Only alphanumeric and underscore characters are allowed.')

    name = forms.CharField(
        label='Name', required=True,
        help_text='Name identifier for style',
        validators=[alphanumeric])
    title = forms.CharField(
        label='Title', required=True,
        help_text='Human friendly title for style')
    qml = forms.FileField(
        label='QML',
        help_text='QGIS Style file (QML)',
        validators=[_extension_validator])
