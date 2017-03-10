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

from geonode.layers.models import Style, Attribute, Layer
import notification
from django.utils.translation import ugettext as _


styles = [{"name": "test_style_1",
           "sld_url": "http://localhost:8080/geoserver/rest/styles/test_style.sld",
           "sld_body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><sld:StyledLayerDescriptor \
            xmlns=\"http://www.opengis.net/sld\" xmlns:sld=\"http://www.opengis.net/sld\" \
            xmlns:ogc=\"http://www.opengis.net/ogc\" xmlns:gml=\"http://www.opengis.net/gml\" \
            version=\"1.0.0\"><sld:NamedLayer><sld:Name>test_style_1</sld:Name><sld:UserStyle>\
            <sld:Name>test_style_1</sld:Name><sld:Title/><sld:FeatureTypeStyle><sld:Name>name</sld:Name>\
            <sld:Rule><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name=\"fill\">#888800</sld:CssParameter>\
            </sld:Fill><sld:Stroke><sld:CssParameter name=\"stroke\">#ffffbb</sld:CssParameter>\
            <sld:CssParameter name=\"stroke-width\">0.7</sld:CssParameter></sld:Stroke>\
            </sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle>\
            </sld:NamedLayer></sld:StyledLayerDescriptor>",
           },
          {"name": "test_style_2",
           "sld_url": "http://localhost:8080/geoserver/rest/styles/test_style.sld",
           "sld_body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><sld:StyledLayerDescriptor \
           xmlns=\"http://www.opengis.net/sld\" xmlns:sld=\"http://www.opengis.net/sld\" \
           xmlns:ogc=\"http://www.opengis.net/ogc\" xmlns:gml=\"http://www.opengis.net/gml\" \
           version=\"1.0.0\"><sld:NamedLayer><sld:Name>test_style_2</sld:Name><sld:UserStyle>\
           <sld:Name>test_style_2</sld:Name><sld:Title/><sld:FeatureTypeStyle><sld:Name>name</sld:Name>\
           <sld:Rule><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name=\"fill\">#888800</sld:CssParameter>\
           </sld:Fill><sld:Stroke><sld:CssParameter name=\"stroke\">#ffffbb</sld:CssParameter>\
           <sld:CssParameter name=\"stroke-width\">0.7</sld:CssParameter></sld:Stroke></sld:PolygonSymbolizer>\
           </sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>",
           },
          {"name": "test_style_3",
           "sld_url": "http://localhost:8080/geoserver/rest/styles/test_style.sld",
           "sld_body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><sld:StyledLayerDescriptor \
           xmlns=\"http://www.opengis.net/sld\" xmlns:sld=\"http://www.opengis.net/sld\" \
           xmlns:ogc=\"http://www.opengis.net/ogc\" xmlns:gml=\"http://www.opengis.net/gml\" \
           version=\"1.0.0\"><sld:NamedLayer><sld:Name>test_style_3</sld:Name><sld:UserStyle>\
           <sld:Name>test_style_3</sld:Name><sld:Title/><sld:FeatureTypeStyle><sld:Name>name</sld:Name>\
           <sld:Rule><sld:PolygonSymbolizer><sld:Fill><sld:CssParameter name=\"fill\">#888800</sld:CssParameter>\
           </sld:Fill><sld:Stroke><sld:CssParameter name=\"stroke\">#ffffbb</sld:CssParameter><sld:CssParameter \
           name=\"stroke-width\">0.7</sld:CssParameter></sld:Stroke></sld:PolygonSymbolizer></sld:Rule>\
           </sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>",
           },
          {"name": "Evaluación",
           "sld_url": "http://localhost:8080/geoserver/rest/styles/test_style.sld",
           "sld_body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><sld:StyledLayerDescriptor \
           xmlns=\"http://www.opengis.net/sld\" xmlns:sld=\"http://www.opengis.net/sld\" \
           xmlns:ogc=\"http://www.opengis.net/ogc\" xmlns:gml=\"http://www.opengis.net/gml\" version=\"1.0.0\">\
           <sld:NamedLayer><sld:Name>test_style_3</sld:Name><sld:UserStyle><sld:Name>test_style_3</sld:Name>\
           <sld:Title/><sld:FeatureTypeStyle><sld:Name>name</sld:Name><sld:Rule><sld:PolygonSymbolizer><sld:Fill>\
           <sld:CssParameter name=\"fill\">#888800</sld:CssParameter></sld:Fill><sld:Stroke><sld:CssParameter \
           name=\"stroke\">#ffffbb</sld:CssParameter><sld:CssParameter name=\"stroke-width\">0.7</sld:CssParameter>\
           </sld:Stroke></sld:PolygonSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer>\
           </sld:StyledLayerDescriptor>",
           }]

attributes = [
    {
        "attribute": u'N\xfamero_De_M\xe9dicos',
        "attribute_label": u'N\xfamero_De_M\xe9dicos',
        "attribute_type": "xsd:string",
        "visible": True,
        "display_order": 4
    },
    {
        "attribute": "the_geom",
        "attribute_label": "Shape",
        "attribute_type": "gml:Geometry",
        "visible": False,
        "display_order": 3
    },
    {
        "attribute": "description",
        "attribute_label": "Description",
        "attribute_type": "xsd:string",
        "visible": True,
        "display_order": 2
    },
    {
        "attribute": "place_name",
        "attribute_label": "Place Name",
        "attribute_type": "xsd:string",
        "visible": True,
        "display_order": 1
    }
]


def create_layer_data():
    layer = Layer.objects.get(pk=1)
    for style in styles:
        new_style = Style.objects.create(
            name=style['name'],
            sld_url=style['sld_url'],
            sld_body=style['sld_body'])
        layer.styles.add(new_style)
        layer.default_style = new_style
    layer.save()

    for attr in attributes:
        Attribute.objects.create(layer=layer,
                                 attribute=attr['attribute'],
                                 attribute_label=attr['attribute_label'],
                                 attribute_type=attr['attribute_type'],
                                 visible=attr['visible'],
                                 display_order=attr['display_order']
                                 )


def create_notifications():
    notification.models.NoticeType.create(
        "layer_created",
        _("Layer Created"),
        _("A Layer was created"))
    notification.models.NoticeType.create(
        "layer_updated",
        _("Layer Updated"),
        _("A Layer was updated"))
    notification.models.NoticeType.create(
        "layer_deleted",
        _("Layer Deleted"),
        _("A Layer was deleted"))
    notification.models.NoticeType.create(
        "layer_comment",
        _("Comment on Layer"),
        _("A layer was commented on"))
    notification.models.NoticeType.create(
        "layer_rated",
        _("Rating for Layer"),
        _("A rating was given to a layer"))
    notification.models.NoticeType.create(
        "request_download_resourcebase",
        _("Request download to an owner"),
        _("A request has been sent to the owner"))
    notification.models.NoticeType.create(
        "map_created",
        _("Map Created"),
        _("A Map was created"))
    notification.models.NoticeType.create(
        "map_updated",
        _("Map Updated"),
        _("A Map was updated"))
    notification.models.NoticeType.create(
        "map_deleted",
        _("Map Deleted"),
        _("A Map was deleted"))
    notification.models.NoticeType.create(
        "profile_created",
        _("Profile Created"),
        _("A Profile was created"))
    notification.models.NoticeType.create(
        "profile_updated",
        _("Profile Updated"),
        _("A Profile was updated"))
    notification.models.NoticeType.create(
        "profile_deleted",
        _("Profile Deleted"),
        _("A Profile was deleted"))
    notification.models.NoticeType.create(
        "document_created",
        _("Document Created"),
        _("A Document was created"))
    notification.models.NoticeType.create(
        "document_updated",
        _("Document Updated"),
        _("A Document was updated"))
    notification.models.NoticeType.create(
        "document_deleted",
        _("Document Deleted"),
        _("A Document was deleted"))
