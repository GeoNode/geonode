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

    def post(self, request, format=None):
        data = request.data

        layer_uuid = str(data['layer_uuid'])

        resourcebase_obj = ResourceBase.objects.filter(uuid=layer_uuid).first()

        layer = Layer.objects.filter(id=resourcebase_obj.id).first()

        system_settings = SystemSettings()
        system_settings.created_by = request.user
        system_settings.settings_code = 'location'
        system_settings.value = layer.name
        system_settings.content_object = layer
        system_settings.modified_by = request.user

        # import pdb;pdb.set_trace()

        try:
            if SystemSettings.objects.filter(settings_code='location').count() == 1:
                SystemSettings.objects.filter(settings_code='location').update(value=layer.name)
            else:
                system_settings.save()
            # system_settings.objects.update_or_create(settings_code='1')
        except (AssertionError, AttributeError) as e:
            print e
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class SystemSettingsAPIView(ListAPIView):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
