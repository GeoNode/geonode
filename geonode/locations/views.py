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


class LocationView(TemplateView):

    template_name = "locations/locations.html"


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

        # import pdb;pdb.set_trace()
        return JsonResponse(layers_attributes)


class LayersAttributesSearchAPIView(APIView):

    # permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        pass
