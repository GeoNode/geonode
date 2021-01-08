"""
Views for the ``Waterproof intake`` application.

"""

import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from .models import ExternalInputs, City, ProcessEfficiencies, Intake, DemandParameters, WaterExtraction, ElementSystem, ExternalInputs
from geonode.waterproof_nbs_ca.models import Countries, Region
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.core import serializers
from django.http import JsonResponse
from . import forms
import json
from django.contrib.gis.geos import Polygon, MultiPolygon, GEOSGeometry
from django.contrib.gis.gdal import OGRGeometry
import datetime
logger = logging.getLogger(__name__)


def create(request):
    logger.debug(request.method)
    if request.method == 'POST':
        form = forms.IntakeForm(request.POST)
        if form.is_valid():
            intake = form.save(commit=False)
            xmlGraph = request.POST.get('xmlGraph')
            # True | False
            isFile = request.POST.get('isFile')
            # GeoJSON | SHP
            typeDelimitFile = request.POST.get('typeDelimit')
            interpolationString = request.POST.get('waterExtraction')
            interpolation = json.loads(interpolationString)
            intakeAreaString = request.POST.get('areaGeometry')
            graphElementsString = request.POST.get('graphElements')
            print(graphElementsString)
            graphElements = json.loads(graphElementsString)
            if (isFile == 'true'):
                # Validate file's extension
                if (typeDelimitFile == 'geojson'):
                    intakeAreaJson = json.loads(intakeAreaString)
                    print(intakeAreaJson)
                    for feature in intakeAreaJson['features']:
                        intakeAreaGeom = GEOSGeometry(str(feature['geometry']))
                    print('geojson')
                # Shapefile
                else:
                    intakeAreaJson = json.loads(intakeAreaString)
                    for feature in intakeAreaJson['features']:
                        intakeAreaGeom = GEOSGeometry(str(feature['geometry']))
                    print('shp')
            # Manually delimit
            else:
                intakeAreaJson = json.loads(intakeAreaString)
                intakeAreaGeom = GEOSGeometry(str(intakeAreaJson['geometry']))

            demand_parameters = DemandParameters.objects.create(
                interpolation_type=interpolation['typeInterpolation'],
                initial_extraction=interpolation['initialValue'],
                ending_extraction=interpolation['finalValue'],
                years_number=interpolation['yearCount'],
                is_manual=True,
            )

            for extraction in interpolation['yearValues']:
                water_extraction = WaterExtraction.objects.create(
                    year=extraction['year'],
                    value=extraction['value'],
                    demand=demand_parameters
                )
            intake.area = intakeAreaGeom
            intake.xml_graph = xmlGraph
            intake.city=City.objects.get(id=1)
            intake.demand_parameters = demand_parameters
            intake.creation_date = datetime.datetime.now()
            intake.updated_date = datetime.datetime.now()
            intake.added_by = request.user
            intake.save()
            intakeCreated = Intake.objects.get(id=intake.pk)

            for element in graphElements:
                # River element has diferent parameters
                if (element['id'] == '2'):
                    print('River element')
                #
                else:
                    parameter = json.loads(element['resultdb'])
                    element_system = ElementSystem.objects.create(
                        name=element['name'],
                        normalized_category=parameter[0]['fields']['normalized_category'],
                        origin=1,
                        destination=2,
                        sediment=parameter[0]['fields']['maximal_sediment_perc'],
                        nitrogen=parameter[0]['fields']['maximal_nitrogen_perc'],
                        phosphorus=parameter[0]['fields']['maximal_phosphorus_perc'],
                        intake=intakeCreated
                    )
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
                userCountry = Countries.objects.get(code=request.user.country)
                region = Region.objects.get(id=userCountry.region_id)
                intake = Intake.objects.all()
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_intake/intake_list.html',
                    {
                        'intakeList': intake,
                        'city': city,
                        'userCountry': userCountry,
                        'region': region
                    }
                )

            if (request.user.professional_role == 'ANALYS'):
                intake = Intake.objects.all()
                userCountry = Countries.objects.get(code=request.user.country)
                region = Region.objects.get(id=userCountry.region_id)
                city = City.objects.all()
                return render(
                    request,
                    'waterproof_intake/intake_list.html',
                    {
                        'intakeList': intake,
                        'city': city,
                        'userCountry': userCountry,
                        'region': region
                    }
                )
        else:
            intake = Intake.objects.all()
            userCountry = Countries.objects.get(code='COL')
            region = Region.objects.get(id=userCountry.region_id)
            city = City.objects.all()
            return render(
                request,
                'waterproof_intake/intake_list.html',
                {
                    'intakeList': intake,
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


def loadProcessEfficiency(request, category):
    process = ProcessEfficiencies.objects.filter(normalized_category=category)
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
    if (isFile == 'true'):
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
