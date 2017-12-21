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

