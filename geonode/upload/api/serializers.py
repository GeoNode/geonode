# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields.fields import DynamicRelationField, DynamicComputedField

from geonode.upload.models import Upload, UploadFile
from geonode.layers.api.serializers import LayerSerializer
from geonode.base.api.serializers import BaseDynamicModelSerializer

import logging

logger = logging.getLogger(__name__)


class UploadFileSerializer(DynamicModelSerializer):

    class Meta:
        model = UploadFile
        name = 'upload_file'
        fields = (
            'pk', 'name', 'slug', 'base', 'file'
        )

    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)


class SessionSerializer(serializers.Field):

    @classmethod
    def _decode_target(cls, obj):
        if obj:
            return {
                'name': getattr(obj, 'name', None),
                'type': getattr(obj, 'type', None),
                'enabled': getattr(obj, 'enabled', None)
            }
        return obj

    @classmethod
    def _decode_data(cls, obj):
        if obj:
            return {
                'type': getattr(obj, 'type', None),
                'format': getattr(obj, 'format', None),
                'charset': getattr(obj, 'charset', None),
                'charsetEncoding': getattr(obj, 'charsetEncoding', None),
                'location': getattr(obj, 'location', None),
                'file': getattr(obj, 'file', None),
                'files': getattr(obj, 'files', None),
                'username': getattr(obj, 'username', None)
            }
        return obj

    @classmethod
    def _decode_layer(cls, obj):
        if obj:
            return {
                'name': getattr(obj, 'name', None),
                'href': getattr(obj, 'href', None),
                'originalName': getattr(obj, 'originalName', None),
                'nativeName': getattr(obj, 'nativeName', None),
                'srs': getattr(obj, 'srs', None),
                'attributes': SessionSerializer._decode_layer_attributes(
                    getattr(obj, 'attributes', None)),
                'bbox': SessionSerializer._decode_layer_bbox(
                    getattr(obj, 'bbox', None))
            }
        return obj

    @classmethod
    def _decode_layer_attributes(cls, objs):
        if objs:
            _a = []
            for obj in objs:
                _a.append({
                    'name': getattr(obj, 'name', None),
                    'binding': getattr(obj, 'binding', None)
                })
            return _a
        return objs

    @classmethod
    def _decode_layer_bbox(cls, obj):
        if obj:
            return {
                'minx': getattr(obj, 'minx', None),
                'miny': getattr(obj, 'miny', None),
                'maxx': getattr(obj, 'maxx', None),
                'maxy': getattr(obj, 'maxy', None),
                'crs': getattr(obj, 'crs', None),
            }
        return obj

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        if value:
            _s = {
                'name': value.name,
                'charset': value.charset,
                'permissions': value.permissions,
                'time_transforms': value.time_transforms,
                'update_mode': value.update_mode,
                'time': value.time,
                'layer_title': value.layer_title,
                'layer_abstract': value.layer_abstract,
                'completed_step': value.completed_step,
                'error_msg': value.error_msg,
                'upload_type': value.upload_type,
                'time_info': value.time_info,
                'mosaic': value.mosaic,
                'append_to_mosaic_opts': value.append_to_mosaic_opts,
                'append_to_mosaic_name': value.append_to_mosaic_name,
                'mosaic_time_regex': value.mosaic_time_regex,
                'mosaic_time_value': value.mosaic_time_value,
            }
            if getattr(value, 'import_session'):
                _import_session = value.import_session
                _s['import_session'] = {
                    'id': _import_session.id,
                    'href': _import_session.href,
                    'state': _import_session.state,
                    'archive': _import_session.archive,
                    'targetWorkspace': SessionSerializer._decode_target(
                        getattr(_import_session, 'targetWorkspace', None)),
                    'targetStore': SessionSerializer._decode_target(
                        getattr(_import_session, 'targetStore', None)),
                    'tasks': []
                }
                for _task in _import_session.tasks:
                    _s['import_session']['tasks'].append(
                        {
                            'id': _task.id,
                            'href': _task.href,
                            'state': _task.state,
                            'progress': getattr(_task, 'progress', None),
                            'updateMode': getattr(_task, 'updateMode', None),
                            'data': SessionSerializer._decode_data(
                                getattr(_task, 'data', None)),
                            'target': SessionSerializer._decode_target(
                                getattr(_task, 'target', None)),
                            'layer': SessionSerializer._decode_layer(
                                getattr(_task, 'layer', None))
                        }
                    )
            return _s


class ProgressField(DynamicComputedField):

    def get_attribute(self, instance):
        return instance.progress


class ProgressUrlField(DynamicComputedField):

    def __init__(self, type, **kwargs):
        self.type = type
        super(ProgressUrlField, self).__init__(**kwargs)

    def get_attribute(self, instance):
        try:
            func = getattr(instance, f"get_{self.type}_url")
            return func()
        except AttributeError as e:
            logger.exception(e)
            return None


class UploadSerializer(BaseDynamicModelSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(UploadSerializer, self).__init__(*args, **kwargs)

        if 'request' in self.context and \
                self.context['request'].query_params.get('full'):
            self.fields['layer'] = DynamicRelationField(
                LayerSerializer,
                embed=True,
                many=False,
                read_only=True)
            self.fields['session'] = SessionSerializer(
                source='get_session',
                read_only=True)

    class Meta:
        model = Upload
        name = 'upload'
        view_name = 'uploads-list'
        fields = (
            'id', 'name', 'date', 'create_date', 'user',
            'state', 'progress', 'complete', 'import_id',
            'uploadfile_set', 'resume_url', 'delete_url', 'import_url', 'detail_url'
        )

    progress = ProgressField(read_only=True)
    resume_url = ProgressUrlField('resume', read_only=True)
    delete_url = ProgressUrlField('delete', read_only=True)
    import_url = ProgressUrlField('import', read_only=True)
    detail_url = ProgressUrlField('detail', read_only=True)
    uploadfile_set = DynamicRelationField(UploadFileSerializer, embed=True, many=True, read_only=True)
