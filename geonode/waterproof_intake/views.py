"""
Views for the ``Waterproof intake`` application.

"""

import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from .models import ExternalInputs
from .models import City, ProcessEfficiencies, Intake
from django.core import serializers
from django.http import JsonResponse
from . import forms
import json
from django.contrib.gis.geos import Polygon, MultiPolygon, GEOSGeometry
from django.contrib.gis.gdal import OGRGeometry
logger = logging.getLogger(__name__)


def create(request):
    logger.debug(request.method)
    if request.method == 'POST':
        form = forms.IntakeForm(request.POST)
        if form.is_valid():
            intake = form.save(commit=False)
            """
            zf = zipfile.ZipFile(request.FILES['area'])
            print(zf.namelist())
            for filename in zf.namelist():
                if filename=='prevent_grass_strips_slope_gura.shp':
                    print('es el que es')
            """
            intake.save()
            messages.success(request, ("Water Intake created."))
        else:
            messages.error(request, ("Water Intake not created."))

    else:
        form = forms.IntakeForm()
    return render(request, 'waterproof_intake/intake_form.html', context={"form": form, "serverApi": settings.WATERPROOF_API_SERVER})


def listIntake(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            if (request.user.professional_role == 'ADMIN'):

                intake = Intake.objects.all()
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_intake/intake_list.html',
                    {
                        'intake': intake,
                        'city': city,
                    }
                )

            if (request.user.professional_role == 'ANAL'):
                intake = Intake.objects.all()
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_intake/intake_list.html',
                    {
                        'intake': intake,
                        'city': city,
                    }
                )
        else:
            intake = Intake.objects.all()
            city = City.objects.all()
            return render(
                request,
                'waterproof_intake/intake_list.html',
                {
                    'intake': intake,
                    'city': city,
                }
            )


"""
Load process by ID

Attributes
----------
process: string
    Process name
"""


def loadProcessEfficiency(request, name):
    process = ProcessEfficiencies.objects.filter(name=name)
    process_serialized = serializers.serialize('json', process)
    return JsonResponse(process_serialized, safe=False)


"""
Validate polygon geometry

Attributes
----------
geometry: geoJSON
    Polygon geometry
"""


def validateGeometry(request):
    geometryValidations = {
        'validPolygon': False,
        'polygonContains': False
    }
    # Polygon uploaded | polygon copied from intake
    editableGeomString = request.POST.get('editablePolygon')
    # True | False
    isFile = request.POST.get('isFile')
    # GeoJSON | SHP
    typeDelimitFile = request.POST.get('typeDelimit')
    print(isFile)
    # Validate if delimited by file or manually
    if (isFile):
        # Validate file's extension
        if (typeDelimitFile == 'geojson'):
            editableGeomJson = json.loads(editableGeomString)
            print(editableGeomJson)
            for feature in editableGeomJson['features']:
                editableGeometry = GEOSGeometry(str(feature['geometry']))
            print('geojson')
        # Shapefile
        else:
            editableGeomJson = json.loads(editableGeomString)
            for feature in editableGeomJson['features']:
                editableGeometry = GEOSGeometry(str(feature['geometry']))
            print('shp')
    # Manually delimit
    else:
        editableGeomJson = json.loads(editableGeomString)
        editableGeometry = GEOSGeometry(str(editableGeomJson['geometry']))
    
    intakeGeomString = request.POST.get('intakePolygon')
    intakeGeomJson = json.loads(intakeGeomString)

    for feature in intakeGeomJson['features']:
        intakeGeometry = GEOSGeometry(str(feature['geometry']))
    intakeGeometry.contains(editableGeometry)

    if (editableGeometry.valid):
        geometryValidations['validPolygon'] = True
    else:
        geometryValidations['validPolygon'] = False
    if (intakeGeometry.contains(editableGeometry)):
        geometryValidations['polygonContains'] = True
    else:
        geometryValidations['polygonContains'] = False

    return JsonResponse(geometryValidations, safe=False)
