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


class LayersAttributesAPIView(APIView):

    # permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        # context['latest_articles'] = Article.objects.all()[:5]

        layers = Layer.objects.values('name')

        layers_attributes = dict()

        for layer_name in layers:
            cursor = connection.cursor()
            try:

                cursor.execute("select column_name from INFORMATION_SCHEMA.COLUMNS where table_name =  %s",
                               [layer_name['name']])
                result = cursor.fetchall()
                result = [str(r[0]) for r in result]
                layers_attributes[str(layer_name['name'])] = result

            finally:
                cursor.close()

        # context['layers'] = layers
        # context['layers_attributes'] = layers_attributes

        saved_layer = SystemSettings.objects.filter(settings_code='1').first()

        layers_attributes['saved_layer'] = str(saved_layer.value)

        # import pdb;pdb.set_trace()
        return JsonResponse(layers_attributes)


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
