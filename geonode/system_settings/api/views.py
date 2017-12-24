from django.views.generic.base import TemplateView

from geonode.layers.models import Layer
from geonode.layers.views import _resolve_layer
from geonode.class_factory import ClassFactory
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
import json
from geonode.system_settings.system_settings_enum import SystemSettingsEnum
from geonode.layers.models import Layer
from geonode.system_settings.models import SystemSettings
from rest_framework.generics import ListAPIView
from .serializers import SystemSettingsSerializer
from geonode.system_settings.models import SystemSettings
from geonode.base.models import ResourceBase
from geonode.db_connections import Database


class SystemSettingsSaveAPIView(APIView):

    # permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        data = request.data
        settings_code = data.get('settings_code', None)
        if not settings_code:
            raise Exception('Settings code must be provided')

        try:
            system_settings = SystemSettings.objects.get(settings_code=settings_code)
        except SystemSettings.DoesNotExist:
            system_settings = SystemSettings(settings_code=settings_code, created_by=request.user)

        model_instance = SystemSettingsEnum.CONTENT_TYPES.get(settings_code, None)

        if model_instance:
            uuid = str(data.get('uuid', str()))
            resource_base_obj = ResourceBase.objects.get(uuid=uuid)
            system_settings.content_object = model_instance.objects.get(id=resource_base_obj.id)
        else:
            system_settings.value = data.get('value', str())

        system_settings.modified_by = request.user

        system_settings.save()

        return Response(status=status.HTTP_200_OK)


class SystemSettingsAPIView(ListAPIView):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer


class MissingAttributeAPIView(APIView):

    def get(self, request, format=None, uuid=None):

        # import pdb;pdb.set_trace()

        data = dict()
        address_fields = ['post_code', 'road_no', 'house_no']

        resource_base = ResourceBase.objects.get(uuid=str(uuid))
        layer = Layer.objects.get(id=resource_base.id)
        db = Database(db_name=layer.store)
        table_schema = db.get_table_schema_info(table_name=str(layer.name))

        columns_name = list()
        for column in table_schema:
            columns_name.append(str(column.column_name).lower())

        missing_list = list()
        for add_field in address_fields:
            if add_field not in columns_name:
                missing_list.append(add_field)

        if len(missing_list) == 0:
            data['status'] = "valid"
        else:
            data['status'] = "invalid"

        data['columns'] = missing_list
        # data = json.dumps(data)
        # import pdb;pdb.set_trace()

        return JsonResponse(data)

