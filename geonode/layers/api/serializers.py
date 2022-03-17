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
from rest_framework import serializers

from urllib.parse import urlparse

from django.conf import settings

from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField, DynamicComputedField

from geonode.layers.models import Dataset, Style, Attribute
from geonode.base.api.serializers import ResourceBaseSerializer

import logging

logger = logging.getLogger(__name__)


class StyleSerializer(DynamicModelSerializer):

    class Meta:
        model = Style
        name = 'style'
        fields = (
            'pk', 'name', 'workspace', 'sld_title', 'sld_url'
        )

    name = serializers.CharField(read_only=True)
    workspace = serializers.CharField(read_only=True)
    sld_url = serializers.SerializerMethodField()

    def get_sld_url(self, instance):
        if bool(urlparse(instance.sld_url).netloc):
            return instance.sld_url.replace(
                settings.OGC_SERVER['default']['LOCATION'],
                settings.OGC_SERVER['default']['PUBLIC_LOCATION']
            )
        return instance.sld_url


class AttributeSerializer(DynamicModelSerializer):

    class Meta:
        model = Attribute
        name = 'attribute'
        fields = (
            'pk', 'attribute', 'description',
            'attribute_label', 'attribute_type', 'visible',
            'display_order', 'featureinfo_type',
            'count', 'min', 'max', 'average', 'median', 'stddev', 'sum',
            'unique_values', 'last_stats_updated'
        )

    attribute = serializers.CharField(read_only=True)


class FeatureInfoTemplateField(DynamicComputedField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        if instance.use_featureinfo_custom_template and instance.featureinfo_custom_template:
            return instance.featureinfo_custom_template
        else:
            _attributes = instance.attributes.filter(visible=True).order_by('display_order')
            if _attributes.exists():
                _template = '<div>'
                for _field in _attributes:
                    _label = _field.attribute_label or _field.attribute
                    _template += '<div class="row">'
                    if _field.featureinfo_type == Attribute.TYPE_HREF:
                        _template += '<div class="col-xs-6" style="font-weight: bold; word-wrap: break-word;">%s:</div> \
                            <div class="col-xs-6" style="word-wrap: break-word;"><a href="${properties.%s}" target="_new">${properties.%s}</a></div>' % \
                            (_label, _field, _field)
                    elif _field.featureinfo_type == Attribute.TYPE_IMAGE:
                        _template += '<div class="col-xs-12" align="center" style="font-weight: bold; word-wrap: break-word;"> \
                            <a href="${properties.%s}" target="_new"><img width="100%%" height="auto" src="${properties.%s}" title="%s" alt="%s"/></a></div>' % \
                            (_field.attribute, _field.attribute, _label, _label)
                    elif _field.featureinfo_type in (
                            Attribute.TYPE_VIDEO_3GP, Attribute.TYPE_VIDEO_FLV, Attribute.TYPE_VIDEO_MP4,
                            Attribute.TYPE_VIDEO_OGG, Attribute.TYPE_VIDEO_WEBM, Attribute.TYPE_VIDEO_YOUTUBE):
                        if 'youtube' in _field.featureinfo_type:
                            _template += '<div class="col-xs-12" align="center" style="font-weight: bold; word-wrap: break-word;"> \
                                <iframe src="${properties.%s}" width="100%%" height="360" frameborder="0" allowfullscreen></iframe></div>' % \
                                (_field.attribute)
                        else:
                            _type = f"video/{_field.featureinfo_type[11:]}"
                            _template += '<div class="col-xs-12" align="center" style="font-weight: bold; word-wrap: break-word;"> \
                                <video width="100%%" height="360" controls><source src="${properties.%s}" type="%s">Your browser does not support the video tag.</video></div>' % \
                                (_field.attribute, _type)
                    elif _field.featureinfo_type == Attribute.TYPE_AUDIO:
                        _template += '<div class="col-xs-12" align="center" style="font-weight: bold; word-wrap: break-word;"> \
                            <audio controls><source src="${properties.%s}" type="audio/mpeg">Your browser does not support the audio element.</audio></div>' % \
                            (_field.attribute)
                    elif _field.featureinfo_type == Attribute.TYPE_IFRAME:
                        _template += '<div class="col-xs-12" align="center" style="font-weight: bold; word-wrap: break-word;"> \
                            <iframe src="/proxy/?url=${properties.%s}" width="100%%" height="360" frameborder="0" allowfullscreen></iframe></div>' % \
                            (_field.attribute)
                    elif _field.featureinfo_type == Attribute.TYPE_PROPERTY:
                        _template += '<div class="col-xs-6" style="font-weight: bold; word-wrap: break-word;">%s:</div> \
                            <div class="col-xs-6" style="word-wrap: break-word;">${properties.%s}</div>' % \
                            (_label, _field.attribute)
                    _template += '</div>'
                _template += '</div>'
                return _template
            return None


class DatasetSerializer(ResourceBaseSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    class Meta:
        model = Dataset
        name = 'dataset'
        view_name = 'datasets-list'
        fields = (
            'pk', 'uuid', 'name', 'workspace', 'store', 'subtype', 'charset',
            'is_mosaic', 'has_time', 'has_elevation', 'time_regex', 'elevation_regex',
            'featureinfo_custom_template', 'ows_url', 'ptype', 'default_style', 'styles', 'attribute_set'
        )

    name = serializers.CharField(read_only=True)
    workspace = serializers.CharField(read_only=True)
    store = serializers.CharField(read_only=True)
    charset = serializers.CharField(read_only=True)

    default_style = DynamicRelationField(StyleSerializer, embed=True, many=False, read_only=True)
    styles = DynamicRelationField(StyleSerializer, embed=True, many=True, read_only=True)

    attribute_set = DynamicRelationField(AttributeSerializer, embed=True, many=True, read_only=True)

    featureinfo_custom_template = FeatureInfoTemplateField()


class DatasetListSerializer(DatasetSerializer):
    class Meta(DatasetSerializer.Meta):
        fields = (
            'pk', 'uuid', 'name', 'workspace', 'store', 'subtype', 'charset',
            'is_mosaic', 'has_time', 'has_elevation', 'time_regex', 'elevation_regex',
            'featureinfo_custom_template', 'ptype', 'default_style', 'styles'
        )

    featureinfo_custom_template = FeatureInfoTemplateField()


class DatasetReplaceAppendSerializer(serializers.Serializer):
    class Meta:
        fields = (
            "base_file", "dbf_file", "shx_file", "prj_file", "xml_file",
            "sld_file", "store_spatial_files"
        )

    base_file = serializers.CharField()
    dbf_file = serializers.CharField(required=False)
    shx_file = serializers.CharField(required=False)
    prj_file = serializers.CharField(required=False)
    xml_file = serializers.CharField(required=False)
    sld_file = serializers.CharField(required=False)
    store_spatial_files = serializers.BooleanField(required=False, default=True)
