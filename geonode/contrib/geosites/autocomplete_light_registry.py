# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2019 OSGeo
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

from autocomplete_light.registry import register

from geonode.base.autocomplete_light_registry import ResourceBaseAutocomplete
from geonode.documents.autocomplete_light_registry import DocumentAutocomplete
from geonode.documents.models import Document
from geonode.layers.autocomplete_light_registry import LayerAutocomplete
from geonode.layers.models import Layer
from geonode.maps.autocomplete_light_registry import MapAutocomplete
from geonode.maps.models import Map
from .utils import resources_for_site


# This class MUST have the same name as Geonode class, otherwise templates and javascript code MUST be overridden
class ResourceBaseAutocomplete(ResourceBaseAutocomplete):

    def choices_for_request(self):
        self.choices = self.choices.filter(id__in=resources_for_site())
        return super(ResourceBaseAutocomplete, self).choices_for_request()


class DocumentAutocomplete(DocumentAutocomplete):
    def choices_for_request(self):
        self.choices = Document.objects.filter(id__in=resources_for_site())
        return super(DocumentAutocomplete, self).choices_for_request()


class LayerAutocomplete(LayerAutocomplete):
    def choices_for_request(self):
        self.choices = Layer.objects.filter(id__in=resources_for_site())
        return super(LayerAutocomplete, self).choices_for_request()


class MapAutocomplete(MapAutocomplete):
    def choices_for_request(self):
        self.choices = Map.objects.filter(id__in=resources_for_site())
        return super(MapAutocomplete, self).choices_for_request()


register(ResourceBaseAutocomplete,
         search_fields=['title'],
         order_by=['title'],
         limit_choices=100,
         autocomplete_js_attributes={'placeholder': 'Resource name..', }, )

register(
    Document,
    DocumentAutocomplete,
    search_fields=['title'],
    order_by=['title'],
    limit_choices=100,
    autocomplete_js_attributes={
        'placeholder': 'Document name..',
    },
)

register(
    Layer,
    LayerAutocomplete,
    search_fields=[
        'title',
        '^alternate'],
    order_by=['title'],
    limit_choices=100,
    autocomplete_js_attributes={
        'placeholder': 'Layer name..',
    },
)

register(
    Map,
    MapAutocomplete,
    search_fields=['title'],
    order_by=['title'],
    limit_choices=100,
    autocomplete_js_attributes={
        'placeholder': 'Map name..',
    },
)
