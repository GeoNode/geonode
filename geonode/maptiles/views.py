from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.db.models import Q

from geonode.services.models import Service
from geonode.layers.models import Layer
from geonode.layers.utils import is_vector, get_bbox
from geonode.utils import resolve_object, llbbox_to_mercator
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.utils import default_map_config

from geonode.security.views import _perms_info_json
from geonode.cephgeo.models import CephDataObject, DataClassification, FTPRequest, UserJurisdiction, UserTiles, TileDataClass
from geonode.cephgeo.cart_utils import *
from geonode.maptiles.utils import *
from geonode.datarequests.models import DataRequestProfile, DataRequest
from geonode.documents.models import get_related_documents
from geonode.registration.models import Province, Municipality
from geonode.base.models import ResourceBase
from geonode.groups.models import GroupProfile

import geonode.settings as settings

from pprint import pprint
from datetime import datetime, timedelta, date, time

import logging

from geonode.cephgeo.utils import get_cart_datasize
from django.utils.text import slugify
from geonode.maptiles.models import SRS
from httplib import HTTPResponse


_PERMISSION_VIEW = _("You are not permitted to view this layer")
_PERMISSION_GENERIC = _('You do not have permissions for this layer.')
# Create your views here.

logger = logging.getLogger("geonode")


def _resolve_layer(request, typename, permission='base.view_resourcebase',
                   msg=_PERMISSION_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = typename.split(":", 1)
    service = Service.objects.filter(name=service_typename[0])

    if service.count() > 0:
        return resolve_object(request,
                              Layer,
                              {'service': service[0],
                               'typename': service_typename[1] if service[0].method != "C" else typename},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)
    else:
        return resolve_object(request,
                              Layer,
                              {'typename': typename,
                               'service': None},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)

#
# This function generates the layer configuration details required for the map view.
# Returns the template with the configuration details as context
#


@login_required
def tiled_view(request, overlay=settings.TILED_SHAPEFILE, template="maptiles/maptiles_map.html", test_mode=False, jurisdiction=None):

    context_dict = {}
    context_dict["grid"] = get_layer_config(
        request, overlay, "base.view_resourcebase", _PERMISSION_VIEW)
    legend_link = ''
    if not 'localhost' in settings.BASEURL:
        legend_link = settings.OGC_SERVER['default']['PUBLIC_LOCATION'] + \
            'wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=geonode:philgrid&STYLE='
    else:
        legend_link = settings.SITEURL + \
            'geoserver/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER=geonode:philgrid&STYLE='
    try:
        context_dict["dtm_lgd"] = legend_link + settings.DTM_SLD
        context_dict["ortho_lgd"] = legend_link + settings.ORTHO_SLD
        context_dict["laz_lgd"] = legend_link + settings.LAZ_SLD
        context_dict["dsm_lgd"] = legend_link + settings.DSM_SLD
        context_dict["dtm_sld"] = settings.DTM_SLD
        context_dict["ortho_sld"] = settings.ORTHO_SLD
        context_dict["laz_sld"] = settings.LAZ_SLD
        context_dict["dsm_sld"] = settings.DSM_SLD
        context_dict["philgrid_sld"] = settings.PHILGRID_SLD
        context_dict["clear_sld"] = settings.CLEAR_SLD
    except Exception:
        context_dict["dtm"] = None
        context_dict["ortho"] = None
        context_dict["laz"] = None
        context_dict["dsm"] = None
        context_dict["philgrid_sld"] = None
        
    context_dict["geoserver_url"] = settings.OGC_SERVER['default']['PUBLIC_LOCATION']
    jurisdiction_object = None

    if jurisdiction is None:
        try:
            jurisdiction_object = UserJurisdiction.objects.get(
                user=request.user)
            jurisdiction_shapefile = jurisdiction_object.jurisdiction_shapefile
            context_dict["jurisdiction"] = get_layer_config(
                request, jurisdiction_object.jurisdiction_shapefile.typename, "base.view_resourcebase", _PERMISSION_VIEW)
            context_dict[
                "jurisdiction_name"] = jurisdiction_object.jurisdiction_shapefile.typename
            context_dict["jurisdiction_yes"] = True
        except Exception as e:
            context_dict["jurisdiction_yes"] = False
            print e

    else:
        context_dict["jurisdiction"] = get_layer_config(
            request, jurisdiction, "base.view_resourcebase", _PERMISSION_VIEW)

    context_dict["feature_municipality"] = settings.MUNICIPALITY_SHAPEFILE.split(":")[
        1]
    context_dict["feature_tiled"] = overlay.split(":")[1]
    context_dict["test_mode"] = test_mode
    context_dict["data_classes"] = DataClassification.labels.values()

    #context_dict["projections"]= SRS.labels.values()

    return render_to_response(template, RequestContext(request, context_dict))


def tiled_view2(request, overlay=settings.TILED_SHAPEFILE, template="maptiles/maptiles_map2.html", test_mode=False, jurisdiction=None):

    context_dict = {}
    context_dict["grid"] = get_layer_config(
        request, overlay, "base.view_resourcebase", _PERMISSION_VIEW)

    if jurisdiction is None:
        try:
            jurisdiction_object = UserJurisdiction.objects.get(
                user=request.user)
            jurisdiction_shapefile = jurisdiction_object.jurisdiction_shapefile
            context_dict["jurisdiction"] = get_layer_config(
                request, jurisdiction_object.jurisdiction_shapefile.typename, "base.view_resourcebase", _PERMISSION_VIEW)
            context_dict[
                "jurisdiction_name"] = jurisdiction_object.jurisdiction_shapefile.typename
            context_dict["jurisdiction_yes"] = True
        except Exception as e:
            context_dict["jurisdiction_yes"] = False
            print e
    else:
        context_dict["jurisdiction"] = get_layer_config(
            request, jurisdiction, "base.view_resourcebase", _PERMISSION_VIEW)

    context_dict["feature_municipality"] = settings.MUNICIPALITY_SHAPEFILE.split(":")[
        1]
    context_dict["feature_tiled"] = overlay.split(":")[1]
    context_dict["test_mode"] = test_mode
    context_dict["data_classes"] = DataClassification.labels.values()
    #context_dict["projections"]= SRS.labels.values()

    return render_to_response(template, RequestContext(request, context_dict))

#
# Function for processing the georefs submitted by the user
#


def process_georefs(request):
    if request.method == "POST":
        try:
            # Get georef list filtered with georefs computed upon approval of
            # registration
            georef_area = request.POST['georef_area']
            # georef_list = filter(None, georef_area.split(","))
            # #pprint("Initial georef_list:" + str(georef_list))
            # try:
            #     georef_list = clean_georefs(request.user, georef_list)
            # except ObjectDoesNotExist:
            #     messages.info(request, "Due to a recent update, your selectable tiles are still under process. We apologize for the inconvenience.")
            #     return redirect('geonode.cephgeo.views.get_cart')
            # #pprint("Filtered georef_list:" + str(georef_list))
            submitted_georef_list = filter(None, georef_area.split(","))
            georef_list = []
            jurisdiction_georefs = []

            try:
                jurisdiction_georefs = str(
                    UserTiles.objects.get(user=request.user).gridref_list)
            except ObjectDoesNotExist as e:
                pprint("No jurisdiction tiles for this user")
                raise PermissionDenied

            for georef in submitted_georef_list:
                if georef in jurisdiction_georefs:
                    georef_list.append(georef)

            pprint(georef_list)

            # Get the requested dataclasses
            data_classes = list()
            for data_class in DataClassification.labels.values():
                if request.POST.get(slugify(data_class.decode('cp1252'))):
                    data_classes.append(data_class)

            # Construct filter for excluding unselected data classes
            dataclass_filter = DataClassification.labels.keys()
            for dataclass, label in DataClassification.labels.iteritems():
                if label in data_classes:
                    dataclass_filter.remove(dataclass)

            # Initialize variables for counting empty and duplicates
            count = 0
            empty_georefs = 0
            duplicates = []

            for georef in georef_list:      # Process each georef in list

                # Build filter query to exclude unselected data classes
                filter_query = Q(name__startswith=georef)
                for filtered_class in dataclass_filter:
                    filter_query = filter_query & ~Q(data_class=filtered_class)

                # Execute query
                objects = CephDataObject.objects.filter(filter_query)
                pprint("objects found for georef:" + georef)

                # Count duplicates and empty references
                count += len(objects)
                if len(objects) > 0:
                    for ceph_obj in objects:    # Add each Ceph object to cart
                        try:
                            add_to_cart_unique(request, ceph_obj.id)
                            pprint("object " + ceph_obj.name + " added to cart")
                        except DuplicateCartItemException:  # List each duplicate object
                            duplicates.append(ceph_obj.name)
                else:
                    empty_georefs += 1

            # if len(duplicates) > 0:         # Warn on duplicates
            #    messages.warning(request, "WARNING: The following items are already in the cart and have not been added: \n{0}".format(str(duplicates)))

            if empty_georefs > 0:
                messages.error(request, "ERROR: [{0}] out of selected [{1}] georef tiles have no data! A total of [{2}] objects have been added to cart. \n".format(
                    empty_georefs, len(georef_list), (count - len(duplicates))))
            elif len(duplicates) > 0:  # Inform user of the number of processed georefs and objects
                messages.info(request, "Processed [{0}] georefs tiles. [{2}] duplicate objects found in cart have been skipped. A total of [{1}] objects have been added to cart. ".format(
                    len(georef_list), (count - len(duplicates)), len(duplicates)))
            else:  # Inform user of the number of processed georefs and objects
                messages.info(request, "Processed [{0}] georefs tiles. A total of [{1}] objects have been added to cart.".format(
                    len(georef_list), (count - len(duplicates))))

            return redirect('geonode.cephgeo.views.get_cart')

        except ValidationError:             # Redirect and inform if an invalid georef is encountered
            messages.error(request, "Invalid georefs list")
            return HttpResponseRedirect('/maptiles/')
            # return redirect('geonode.maptiles.views.tiled_view')

    else:   # Must process HTTP POST method from form
        raise Exception("HTTP method must be POST!")

#
# Validates if the total file size requested is less than the limit specified in local settings
#


@login_required
def georefs_validation(request):
    """
    Note: does not check yet if tiles to be added are unique (or are not yet included in the cart)
    """
    if request.method != 'POST':
        return HttpResponse(
            content='no data received from HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    else:
        georefs = request.POST["georefs"]
        print("[VALIDATION]")
        pprint(request.POST)
        georefs_list = filter(None, georefs.split(","))
        cart_total_size = get_cart_datasize(request)

        # Retrieve FTPRequests from the last 24 hours
        #yesterday = datetime.now() -  timedelta(days=1)
        #requests_last24h = FTPRequest.objects.filter(date_time__gt=yesterday, user=request.user)

        # Retrieve FTPRequests since midnight
        today_min = datetime.combine(date.today(), time.min)
        today_max = datetime.combine(date.today(), time.max)
        requests_today = FTPRequest.objects.filter(
            user=request.user, date_time__range=(today_min, today_max))
        #requests_today = FTPRequest.objects.filter(date_time__gt=today_min, user=request.user)
        print "PREVIOUS REQUESTS:  "
        pprint(requests_today)
        total_size = 0
        for georef in georefs_list:
            objects = CephDataObject.objects.filter(name__startswith=georef)
            for o in objects:
                total_size += o.size_in_bytes

        request_size_last24h = 0
        pprint('Total size:' + str(total_size))

        # for r in requests_last24h:
        for r in requests_today:
            request_size_last24h += r.size_in_bytes

        if total_size + cart_total_size + request_size_last24h > settings.SELECTION_LIMIT:
            return HttpResponse(
                content=json.dumps({"response": False, "total_size": total_size,
                                    "cart_size": cart_total_size, "recent_requests_size": request_size_last24h}),
                status=200,
                # mimetype='text/plain'
                content_type="application/json"
            )
        else:
            return HttpResponse(
                content=json.dumps(
                    {"response": True, "total_size": total_size, "cart_size": cart_total_size}),
                status=200,
                # mimetype='text/plain'
                content_type="application/json"
            )

#
# Function for looking up the municipalities within a province
#


@login_required
def province_lookup(request, province=""):
    if province == "":
        provinces = []
        for p in Province.objects.all():
            p.append(p.province_name)

        return HttpResponse(
            content=json.dumps({"provinces": provinces}),
            status=200,
            content_type="application/json"
        )
    else:
        provinceObject = Province.objects.get(province_name=province)
        municipalities = []
        for m in Municipality.objects.filter(province__province_name="province"):
            m.append(m.municipality_name)

        return HTTPResponse(
            content=json.dumps(
                {"province": province, "municipalities": municipalities}),
            status=200,
            content_type="application/json",
        )
#
# Function for showing the data size of a georef
#


@login_required
def georefs_datasize(request):
    if request.method != 'POST':
        return HttpResponse(
            content='no data received from HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    else:
        georefs_clicked = request.POST["georefs_clicked"]
        total_data_size_clicked = 0

        georefs_clicked_list = filter(None, georefs_clicked.split(","))

        for eachgeoref_clicked in georefs_clicked_list:
            # pprint(eachgeoref_clicked)
            clicked_objects = CephDataObject.objects.filter(
                name__startswith=eachgeoref_clicked)
            for o in clicked_objects:
                total_data_size_clicked += o.size_in_bytes
                # pprint(o.size_in_bytes)
            # pprint(total_data_size_clicked)
        return HttpResponse(
            content=json.dumps(
                {"total_data_size_clicked": total_data_size_clicked}),
            status=200,
            content_type="application/json"
        )
