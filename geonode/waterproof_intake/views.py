"""
Views for the ``Waterproof intake`` application.

"""

import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from .models import ValuesTime, City, ProcessEfficiencies, Intake, DemandParameters, WaterExtraction, ElementSystem, ValuesTime, CostFunctionsProcess, Polygon, Basins, ElementConnections
from geonode.waterproof_nbs_ca.models import Countries, Region, Currency
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.core import serializers
from django.http import JsonResponse
from . import forms
from types import SimpleNamespace
import simplejson as json
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import OGRGeometry
import datetime
logger = logging.getLogger(__name__)

"""
Create Waterproof intake

Attributes
----------
request: Request
"""


def create(request):
    logger.debug(request.method)
    # POST submit FORM
    if request.method == 'POST':
        form = forms.IntakeForm(request.POST)
        if form.is_valid():
            intake = form.save(commit=False)
            xmlGraph = request.POST.get('xmlGraph')
            # True | False
            isFile = request.POST.get('isFile')
            # GeoJSON | SHP
            typeDelimitFile = request.POST.get('typeDelimit')
            basinId = request.POST.get('basinId')
            interpolationString = request.POST.get('waterExtraction')
            interpolation = json.loads(interpolationString)
            delimitAreaString = request.POST.get('delimitArea')
            intakeAreaString = request.POST.get('intakeAreaPolygon')
            pointIntakeString = request.POST.get('pointIntake')
            graphElementsString = request.POST.get('graphElements')
            connectionsElementString = request.POST.get('graphConnections')
            graphElements = json.loads(graphElementsString)
            connectionsElements = json.loads(connectionsElementString)
            if (isFile == 'true'):
                # Validate file's extension
                if (typeDelimitFile == 'geojson'):
                    delimitAreaJson = json.loads(delimitAreaString)
                    print(delimitAreaJson)
                    for feature in delimitAreaJson['features']:
                        delimitAreaGeom = GEOSGeometry(str(feature['geometry']))
                    print('Delimitation file: geojson')
                # Shapefile
                else:
                    delimitAreaJson = json.loads(delimitAreaString)
                    for feature in delimitAreaJson['features']:
                        delimitAreaGeom = GEOSGeometry(str(feature['geometry']))
                    print('Delimitation file: shp')
            # Manually delimit
            else:
                delimitAreaJson = json.loads(delimitAreaString)
                delimitAreaGeom = GEOSGeometry(str(delimitAreaJson['geometry']))

            intakeGeomJson = json.loads(intakeAreaString)
            pointIntakeJson = json.loads(pointIntakeString)
            # Get intake original area
            for feature in intakeGeomJson['features']:
                intakeGeom = GEOSGeometry(str(feature['geometry']))
            # Get the intake point geom
            pointIntakeGeom = GEOSGeometry(str(pointIntakeJson['geometry']))

            if (intakeGeom.equals(delimitAreaGeom)):
                delimitation_type = 'CATCHMENT'
            else:
                delimitation_type = 'MANUAL'

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
            intake.xml_graph = xmlGraph
            intake.city = City.objects.get(id=1)
            intake.demand_parameters = demand_parameters
            intake.creation_date = datetime.datetime.now()
            intake.updated_date = datetime.datetime.now()
            intake.added_by = request.user
            intake.save()
            intakeCreated = Intake.objects.get(id=intake.pk)
            print("Basin Id:"+basinId)
            print("Delimitation type:"+delimitation_type)
            basin = Basins.objects.get(id=basinId)
            intakePolygon = Polygon.objects.create(
                area=0,
                geom=delimitAreaGeom,
                geomIntake=intakeGeom,
                geomPoint=pointIntakeGeom,
                delimitation_date=datetime.datetime.now(),
                delimitation_type=delimitation_type,
                basin=basin,
                intake=intakeCreated
            )
            elementsCreated = []
            # Save all graph elements
            for element in graphElements:
                if ('external' in element):
                    # Regular element
                    if (element['external'] == 'false'):
                        parameter = json.loads(element['resultdb'])
                        element_system = ElementSystem.objects.create(
                            graphId=element['id'],
                            name=element['name'],
                            normalized_category=parameter[0]['fields']['normalized_category'],
                            transported_water=parameter[0]['fields']['maximal_transp_water_perc'],
                            sediment=parameter[0]['fields']['maximal_sediment_perc'],
                            nitrogen=parameter[0]['fields']['maximal_nitrogen_perc'],
                            phosphorus=parameter[0]['fields']['maximal_phosphorus_perc'],
                            is_external=False,
                            intake=intakeCreated
                        )
                        elementC = {}
                        elementC['pk'] = element_system.pk
                        elementC['xmlId'] = element_system.graphId
                        elementsCreated.append(elementC)
                    # External element
                    else:
                        parameter = json.loads(element['resultdb'])
                        if (len(parameter) > 0):
                            element_system = ElementSystem.objects.create(
                                graphId=element['id'],
                                name=element['name'],
                                normalized_category=parameter[0]['fields']['normalized_category'],
                                transported_water=parameter[0]['fields']['maximal_transp_water_perc'],
                                sediment=parameter[0]['fields']['maximal_sediment_perc'],
                                nitrogen=parameter[0]['fields']['maximal_nitrogen_perc'],
                                phosphorus=parameter[0]['fields']['maximal_phosphorus_perc'],
                                is_external=True,
                                intake=intakeCreated
                            )
                            elementC = {}
                            elementC['pk'] = element_system.pk
                            elementC['xmlId'] = element_system.graphId
                            elementsCreated.append(elementC)
                        else:
                            element_system = ElementSystem.objects.create(
                                graphId=element['id'],
                                name=element['name'],
                                transported_water=0,
                                sediment=0,
                                nitrogen=0,
                                phosphorus=0,
                                is_external=True,
                                intake=intakeCreated
                            )
                            elementC = {}
                            elementC['pk'] = element_system.pk
                            elementC['xmlId'] = element_system.graphId
                            elementsCreated.append(elementC)
                        external_info = json.loads(element['externaldata'])
                        elementCreated = ElementSystem.objects.get(id=element_system.pk)
                        for external in external_info:
                            external_input = ValuesTime.objects.create(
                                year=external['year'],
                                water_volume=external['water'],
                                sediment=external['sediment'],
                                nitrogen=external['nitrogen'],
                                phosphorus=external['phosphorus'],
                                element=elementCreated
                            )
                # Connections
                else:
                    parameter = json.loads(element['resultdb'])
                    if (len(parameter) > 0):
                        element_system = ElementSystem.objects.create(
                            graphId=element['id'],
                            name=element['name'],
                            normalized_category=parameter[0]['fields']['normalized_category'],
                            transported_water=parameter[0]['fields']['maximal_transp_water_perc'],
                            sediment=parameter[0]['fields']['maximal_sediment_perc'],
                            nitrogen=parameter[0]['fields']['maximal_nitrogen_perc'],
                            phosphorus=parameter[0]['fields']['maximal_phosphorus_perc'],
                            is_external=False,
                            intake=intakeCreated
                        )
                        elementC = {}
                        elementC['pk'] = element_system.pk
                        elementC['xmlId'] = element_system.graphId
                        elementsCreated.append(elementC)
            # Once all elements created, save the connections
            for con in connectionsElements:
                source = next((item for item in elementsCreated if item["xmlId"] == con['source']), None)
                target = next((item for item in elementsCreated if item["xmlId"] == con['target']), None)
                sourceElement = ElementSystem.objects.get(id=source['pk'])
                targetElement = ElementSystem.objects.get(id=target['pk'])
                ElementConnections.objects.create(
                    source=sourceElement,
                    target=targetElement
                )
            messages.success(request, ("Water Intake created."))
            return render(request, 'waterproof_intake/intake_list.html')
        else:
            messages.error(request, ("Water Intake not created."))
            return render(request, 'waterproof_intake/intake_form.html', context={"form": form, "serverApi": settings.WATERPROOF_API_SERVER})
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

            if (request.user.professional_role == 'COPART'):
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
        
            if (request.user.professional_role == 'SCADM'):
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
        
            if (request.user.professional_role == 'MCOMC'):
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
        
            if (request.user.professional_role == 'CITIZN'):
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

            if (request.user.professional_role == 'REPECS'):
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

            if (request.user.professional_role == 'OTHER'):
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


def editIntake(request, idx):
    if not request.user.is_authenticated:
        return render(request, 'waterproof_intake/intake_login_error.html')
    else:
        if request.method == 'GET':
            countries = Countries.objects.all()
            currencies = Currency.objects.all()
            filterIntake = Intake.objects.get(id=idx)
            filterExternal = ElementSystem.objects.filter(intake=filterIntake.pk, is_external=True)
            extInputs = []

            for element in filterExternal:
                filterExtraction = ValuesTime.objects.filter(element=element.pk)
                extractionElements = []
                for extraction in filterExtraction:
                    extractionObject = {
                        'year': extraction.year,
                        'waterVol': extraction.water_volume,
                        'sediment': extraction.sediment,
                        'nitrogen': extraction.nitrogen,
                        'phosphorus': extraction.phosphorus
                    }
                    extractionElements.append(extractionObject)
                external = {
                    'name': element.name,
                    'xmlId': element.graphId,
                    'waterExtraction': extractionElements
                }
                #external['waterExtraction'] = extractionElements
                extInputs.append(external)
            intakeExtInputs = json.dumps(extInputs)
            city = City.objects.all()
            form = forms.IntakeForm()
            return render(
                request, 'waterproof_intake/intake_edit.html',
                {
                    'intake': filterIntake,
                    'countries': countries,
                    'city': city,
                    'externalInputs': intakeExtInputs,
                    "serverApi": settings.WATERPROOF_API_SERVER
                }
            )
        else:
            print("Proceso de guardado")


"""
Load process by category

Attributes
----------
cagegory: string Category
"""


def loadProcessEfficiency(request, category):
    process = ProcessEfficiencies.objects.filter(normalized_category=category)
    process_serialized = serializers.serialize('json', process)
    return JsonResponse(process_serialized, safe=False)


"""
Load Cost function by category

Attributes
----------
cagegory: string Category
"""


def loadCostFunctionsProcess(request, symbol):
    function = CostFunctionsProcess.objects.filter(symbol=symbol)
    function_serialized = serializers.serialize('json', function)
    return JsonResponse(function_serialized, safe=False)


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
    print("Is file delimitation?:"+isFile)
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
