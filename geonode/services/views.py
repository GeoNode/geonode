# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import urllib
import uuid
import logging
import re
from urlparse import urlsplit, urlunsplit
import urlparse

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext, loader
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.db.models import signals
try:
    # Django >= 1.7
    import json
except ImportError:
    # Django <= 1.6 backwards compatibility
    from django.utils import simplejson as json
from django.shortcuts import get_object_or_404

from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.tms import TileMapService
from owslib.csw import CatalogueServiceWeb

from arcrest import Folder as ArcFolder, MapService as ArcMapService

from geoserver.catalog import Catalog

from geonode.services.models import Service, Layer, ServiceLayer, WebServiceHarvestLayersJob
from geonode.security.views import _perms_info_json
from geonode.utils import bbox_to_wkt
from geonode.services.forms import CreateServiceForm, ServiceForm
from geonode.utils import mercator_to_llbbox
from geonode.layers.utils import create_thumbnail
from geonode.geoserver.helpers import set_attributes_from_geoserver
from geonode.base.models import Link
from geonode.base.models import resourcebase_post_save
from geonode.catalogue.models import catalogue_post_save


logger = logging.getLogger("geonode.core.layers.views")

_user = settings.OGC_SERVER['default']['USER']
_password = settings.OGC_SERVER['default']['PASSWORD']

OGP_ABSTRACT = _("""
The Open Geoportal is a consortium comprised of contributions of several universities and organizations to help
facilitate the discovery and acquisition of geospatial data across many organizations and platforms. Current partners
include: Harvard, MIT, MassGIS, Princeton, Columbia, Stanford, UC Berkeley, UCLA, Yale, and UConn. Built on open source
technology, The Open Geoportal provides organizations the opportunity to share thousands of geospatial data layers,
maps, metadata, and development resources through a single common interface.
""")


@login_required
def services(request):
    """
    This view shows the list of all registered services
    """
    services = Service.objects.all()
    return render_to_response("services/service_list.html", RequestContext(request, {
        'services': services,
    }))


@login_required
def register_service(request):
    """
    This view is used for manually registering a new service, with only URL as a
    parameter.
    """

    if request.method == "GET":
        service_form = CreateServiceForm()
        return render_to_response('services/service_register.html',
                                  RequestContext(request, {
                                      'create_service_form': service_form
                                  }))

    elif request.method == 'POST':
        # Register a new Service
        service_form = CreateServiceForm(request.POST)
        if service_form.is_valid():
            url = _clean_url(service_form.cleaned_data['url'])

        # method = request.POST.get('method')
        # type = request.POST.get('type')
        # name = slugify(request.POST.get('name'))
            name = service_form.cleaned_data['name']
            type = service_form.cleaned_data["type"]
            server = None
            if type == "AUTO":
                type, server = _verify_service_type(url)

            if type is None:
                return HttpResponse('Could not determine server type', status=400)

            if "user" in request.POST and "password" in request.POST:
                user = request.POST.get('user')
                password = request.POST.get('password')
            else:
                user = None
                password = None

            if type in ["WMS", "OWS"]:
                return _process_wms_service(url, name, type, user, password, wms=server, owner=request.user)
            elif type == "REST":
                return _register_arcgis_url(url, name, user, password, owner=request.user)
            elif type == "CSW":
                return _register_harvested_service(url, name, user, password, owner=request.user)
            elif type == "OGP":
                return _register_ogp_service(url, owner=request.user)
            else:
                return HttpResponse('Not Implemented (Yet)', status=501)
    elif request.method == 'PUT':
        # Update a previously registered Service
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif request.method == 'DELETE':
        # Delete a previously registered Service
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Request', status=400)


def register_service_by_type(request):
    """
    Register a service based on a specified type
    """
    url = request.POST.get("url")
    type = request.POST.get("type")

    url = _clean_url(url)

    services = Service.objects.filter(base_url=url)

    if services.count() > 0:
        return

    type, server = _verify_service_type(url, type)

    if type == "WMS" or type == "OWS":
        return _process_wms_service(url, type, None, None, wms=server)
    elif type == "REST":
        return _register_arcgis_url(url, None, None, None)


def _is_unique(url):
    """
    Determine if a service is already registered based on matching url
    """
    return Service.objects.filter(base_url=url).count() == 0


def _clean_url(base_url):
    """
    Remove all parameters from a URL
    """
    urlprop = urlsplit(base_url)
    url = urlunsplit(
        (urlprop.scheme, urlprop.netloc, urlprop.path, None, None))
    # hack, we make sure to append the map parameter for MapServer endpoints
    # that are exposing it
    if 'map' in urlparse.parse_qs(urlprop.query):
        map_param = urllib.urlencode({'map': urlparse.parse_qs(urlprop.query)['map'][0]})
        url = '%s?%s' % (url, map_param)
    return url


def _get_valid_name(proposed_name):
    """
    Return a unique slug name for a service
    """
    slug_name = slugify(proposed_name)
    name = slug_name
    if len(slug_name) > 40:
        name = slug_name[:40]
    existing_service = Service.objects.filter(name=name)
    iter = 1
    while existing_service.count() > 0:
        name = slug_name + str(iter)
        existing_service = Service.objects.filter(name=name)
        iter += 1
    return name


def _verify_service_type(base_url, service_type=None):
    """
    Try to determine service type by process of elimination
    """
    logger.info("Checking the url: " + base_url)
    if service_type in ['WMS', 'OWS', None]:
        try:
            service = WebMapService(base_url)
        except:
            pass
        else:
            return ['WMS', service]

    if service_type in ['WFS', 'OWS', None]:
        try:
            servicewfs = WebFeatureService(base_url)
        except:
            pass
        else:
            return ['WFS', servicewfs]

    if service_type in ['TMS', None]:
        try:
            service = TileMapService(base_url)
        except:
            pass
        else:
            return ['TMS', service]

    if service_type in ['REST', None]:
        try:
            service = ArcFolder(base_url)
        except:
            pass
        else:
            try:
                service.services
                return ['REST', service]
            except ValueError:
                service = CatalogueServiceWeb(base_url)

    if service_type in ['CSW', None]:
        try:
            service = CatalogueServiceWeb(base_url)
        except Exception, e:
            logger.exception(e)
            raise
        else:
            return ['CSW', service]

    if service_type in ['OGP', None]:
        # Just use a specific OGP URL for now
        if base_url == settings.OGP_URL:
            return ["OGP", None]

    return [None, None]


def _process_wms_service(url, name, type, username, password, wms=None, owner=None, parent=None):
    """
    Create a new WMS/OWS service, cascade it if necessary (i.e. if Web Mercator not available)
    """
    if wms is None:
        wms = WebMapService(url)
    try:
        base_url = _clean_url(
            wms.getOperationByName('GetMap').methods['Get']['url'])

        if base_url and base_url != url:
            url = base_url
            wms = WebMapService(base_url)
    except:
        logger.info(
            "Could not retrieve GetMap url, using originally supplied URL %s" % url)
        pass
    try:
        service = Service.objects.get(base_url=url)
        return_dict = [{'status': 'ok',
                        'msg': _("This is an existing service"),
                        'service_id': service.pk,
                        'service_name': service.name,
                        'service_title': service.title
                        }]
        return HttpResponse(json.dumps(return_dict),
                            content_type='application/json',
                            status=200)
    except:
        pass

    title = wms.identification.title
    if not name:
        if title:
            name = _get_valid_name(title)
        else:
            name = _get_valid_name(urlsplit(url).netloc)
    try:
        supported_crs = ','.join(wms.contents.itervalues().next().crsOptions)
    except:
        supported_crs = None
    if supported_crs and re.search('EPSG:900913|EPSG:3857|EPSG:102100|EPSG:102113', supported_crs):
        return _register_indexed_service(type, url, name, username, password, wms=wms, owner=owner, parent=parent)
    else:
        return _register_cascaded_service(url, type, name, username, password, wms=wms, owner=owner, parent=parent)


def _register_cascaded_service(url, type, name, username, password, wms=None, owner=None, parent=None):
    """
    Register a service as cascading WMS
    """

    try:
        service = Service.objects.get(base_url=url)
        return_dict = {}
        return_dict['service_id'] = service.pk
        return_dict['msg'] = "This is an existing Service"
        return HttpResponse(json.dumps(return_dict),
                            content_type='application/json',
                            status=200)
    except:
        # TODO: Handle this error properly
        pass

    if wms is None:
        wms = WebMapService(url)
    # TODO: Make sure we are parsing all service level metadata
    # TODO: Handle for setting ServiceProfiletRole
    service = Service.objects.create(base_url=url,
                                     type=type,
                                     method='C',
                                     name=name,
                                     version=wms.identification.version,
                                     title=wms.identification.title,
                                     abstract=wms.identification.abstract,
                                     online_resource=wms.provider.url,
                                     owner=owner,
                                     parent=parent)
    service.keywords = ','.join(wms.identification.keywords)
    service.save()
    service.set_default_permissions()
    if type in ['WMS', 'OWS']:
        # Register the Service with GeoServer to be cascaded
        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest",
                      _user, _password)
        cascade_ws = cat.get_workspace(name)
        if cascade_ws is None:
            cascade_ws = cat.create_workspace(
                name, "http://geonode.org/" + name)

        # TODO: Make sure there isn't an existing store with that name, and
        # deal with it if there is

        try:
            cascade_store = cat.get_store(name, cascade_ws)
        except:
            cascade_store = cat.create_wmsstore(
                name, cascade_ws, username, password)
            cascade_store.capabilitiesURL = url
            cascade_store.type = "WMS"
            cat.save(cascade_store)
        available_resources = cascade_store.get_resources(available=True)

    elif type == 'WFS':
        # Register the Service with GeoServer to be cascaded
        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest",
                      _user, _password)
        # Can we always assume that it is geonode?
        cascade_ws = cat.get_workspace(settings.CASCADE_WORKSPACE)
        if cascade_ws is None:
            cascade_ws = cat.create_workspace(
                settings.CASCADE_WORKSPACE, "http://geonode.org/cascade")

        try:
            wfs_ds = cat.get_store(name, cascade_ws)
        except:
            wfs_ds = cat.create_datastore(name, cascade_ws)
            connection_params = {
                "WFSDataStoreFactory:MAXFEATURES": "0",
                "WFSDataStoreFactory:TRY_GZIP": "true",
                "WFSDataStoreFactory:PROTOCOL": "false",
                "WFSDataStoreFactory:LENIENT": "true",
                "WFSDataStoreFactory:TIMEOUT": "3000",
                "WFSDataStoreFactory:BUFFER_SIZE": "10",
                "WFSDataStoreFactory:ENCODING": "UTF-8",
                "WFSDataStoreFactory:WFS_STRATEGY": "nonstrict",
                "WFSDataStoreFactory:GET_CAPABILITIES_URL": url,
            }
            if username and password:
                connection_params["WFSDataStoreFactory:USERNAME"] = username
                connection_params["WFSDataStoreFactory:PASSWORD"] = password

            wfs_ds.connection_parameters = connection_params
            cat.save(wfs_ds)
        available_resources = wfs_ds.get_resources(available=True)

        # Save the Service record
        service, created = Service.objects.get_or_create(type=type,
                                                         method='C',
                                                         base_url=url,
                                                         name=name,
                                                         owner=owner)
        service.save()
        service.set_default_permissions()
    elif type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' +
            'Only Cascaded WMS, WFS and WCS supported',
            content_type="text/plain",
            status=400)

    message = "Service %s registered" % service.name
    return_dict = [{'status': 'ok',
                    'msg': message,
                    'service_id': service.pk,
                    'service_name': service.name,
                    'service_title': service.title,
                    'available_layers': available_resources
                    }]

    if settings.USE_QUEUE:
        # Create a layer import job
        WebServiceHarvestLayersJob.objects.get_or_create(service=service)
    else:
        _register_cascaded_layers(service)
    return HttpResponse(json.dumps(return_dict),
                        content_type='application/json',
                        status=200)


def _register_cascaded_layers(service, owner=None):
    """
    Register layers for a cascading WMS
    """
    if service.type == 'WMS' or service.type == "OWS":
        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest",
                      _user, _password)
        # Can we always assume that it is geonode?
        # Should cascading layers have a separate workspace?
        cascade_ws = cat.get_workspace(service.name)
        if cascade_ws is None:
            cascade_ws = cat.create_workspace(service.name, 'cascade')
        try:
            store = cat.get_store(service.name, cascade_ws)
        except Exception:
            store = cat.create_wmsstore(service.name, cascade_ws)
            cat.save(store)
        wms = WebMapService(service.base_url)
        layers = list(wms.contents)
        count = 0
        for layer in layers:
            lyr = cat.get_resource(layer, store, cascade_ws)
            if lyr is None:
                if service.type in ["WMS", "OWS"]:
                    resource = cat.create_wmslayer(cascade_ws, store, layer)
                elif service.type == "WFS":
                    resource = cat.create_wfslayer(cascade_ws, store, layer)

                if resource:
                    bbox = resource.latlon_bbox
                    cascaded_layer, created = Layer.objects.get_or_create(
                        typename="%s:%s" % (cascade_ws.name, resource.name),
                        defaults={
                            "name": resource.name,
                            "workspace": cascade_ws.name,
                            "store": store.name,
                            "storeType": store.resource_type,
                            "title": resource.title or 'No title provided',
                            "abstract": resource.abstract or 'No abstract provided',
                            "owner": None,
                            "uuid": str(uuid.uuid4()),
                            "bbox_x0": bbox[0],
                            "bbox_x1": bbox[1],
                            "bbox_y0": bbox[2],
                            "bbox_y1": bbox[3],
                        })

                    if created:
                        cascaded_layer.save()
                        if cascaded_layer is not None and cascaded_layer.bbox is None:
                            cascaded_layer._populate_from_gs(
                                gs_resource=resource)
                        cascaded_layer.set_default_permissions()

                        service_layer, created = ServiceLayer.objects.get_or_create(
                            service=service,
                            typename=cascaded_layer.name
                        )
                        service_layer.layer = cascaded_layer
                        service_layer.title = cascaded_layer.title,
                        service_layer.description = cascaded_layer.abstract,
                        service_layer.styles = cascaded_layer.styles
                        service_layer.save()

                        count += 1
                    else:
                        logger.error(
                            "Resource %s from store %s could not be saved as layer" % (layer, store.name))
        message = "%d Layers Registered" % count
        return_dict = {'status': 'ok', 'msg': message}
        return HttpResponse(json.dumps(return_dict),
                            content_type='application/json',
                            status=200)
    elif service.type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Service Type', status=400)


def _register_indexed_service(type, url, name, username, password, verbosity=False, wms=None, owner=None, parent=None):
    """
    Register a service - WMS or OWS currently supported
    """
    if type in ['WMS', "OWS", "HGL"]:
        # TODO: Handle for errors from owslib
        if wms is None:
            wms = WebMapService(url)
        # TODO: Make sure we are parsing all service level metadata
        # TODO: Handle for setting ServiceProfileRole

        try:
            service = Service.objects.get(base_url=url)
            return_dict = {}
            return_dict['service_id'] = service.pk
            return_dict['msg'] = "This is an existing Service"
            return HttpResponse(json.dumps(return_dict),
                                content_type='application/json',
                                status=200)
        except:
            pass

        service = Service.objects.create(base_url=url,
                                         type=type,
                                         method='I',
                                         name=name,
                                         version=wms.identification.version,
                                         title=wms.identification.title or name,
                                         abstract=wms.identification.abstract or _(
                                             "Not provided"),
                                         online_resource=wms.provider.url,
                                         owner=owner,
                                         parent=parent)

        service.keywords = ','.join(wms.identification.keywords)
        service.save()
        service.set_default_permissions()

        available_resources = []
        for layer in list(wms.contents):
            available_resources.append([wms[layer].name, wms[layer].title])
        if settings.USE_QUEUE:
            # Create a layer import job
            WebServiceHarvestLayersJob.objects.get_or_create(service=service)
        else:
            _register_indexed_layers(service, wms=wms)

        message = "Service %s registered" % service.name
        return_dict = [{'status': 'ok',
                        'msg': message,
                        'service_id': service.pk,
                        'service_name': service.name,
                        'service_title': service.title,
                        'available_layers': available_resources
                        }]
        return HttpResponse(json.dumps(return_dict),
                            content_type='application/json',
                            status=200)
    elif type == 'WFS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' +
            'Only Indexed WMS, WFS and WCS supported',
            content_type="text/plain",
            status=400)


def _register_indexed_layers(service, wms=None, verbosity=False):
    """
    Register layers for an indexed service (only WMS/OWS currently supported)
    """
    logger.info("Registering layers for %s" % service.base_url)
    if re.match("WMS|OWS", service.type):
        wms = wms or WebMapService(service.base_url)
        count = 0
        for layer in list(wms.contents):
            wms_layer = wms[layer]
            if wms_layer is None or wms_layer.name is None:
                continue
            logger.info("Registering layer %s" % wms_layer.name)
            if verbosity:
                print "Importing layer %s" % layer
            layer_uuid = str(uuid.uuid1())
            try:
                keywords = map(lambda x: x[:100], wms_layer.keywords)
            except:
                keywords = []
            if not wms_layer.abstract:
                abstract = ""
            else:
                abstract = wms_layer.abstract

            srid = None
            # Some ArcGIS WMSServers indicate they support 900913 but really
            # don't
            if 'EPSG:900913' in wms_layer.crsOptions and "MapServer/WmsServer" not in service.base_url:
                srid = 'EPSG:900913'
            elif len(wms_layer.crsOptions) > 0:
                matches = re.findall(
                    'EPSG\:(3857|102100|102113)', ' '.join(wms_layer.crsOptions))
                if matches:
                    srid = 'EPSG:%s' % matches[0]
            if srid is None:
                message = "%d Incompatible projection - try setting the service as cascaded" % count
                return_dict = {'status': 'ok', 'msg': message}
                return HttpResponse(json.dumps(return_dict),
                                    content_type='application/json',
                                    status=200)

            bbox = list(
                wms_layer.boundingBoxWGS84 or (-179.0, -89.0, 179.0, 89.0))

            # Need to check if layer already exists??
            existing_layer = None
            for layer in Layer.objects.filter(typename=wms_layer.name):
                if layer.service == service:
                    existing_layer = layer

            if not existing_layer:
                signals.post_save.disconnect(resourcebase_post_save, sender=Layer)
                signals.post_save.disconnect(catalogue_post_save, sender=Layer)
                saved_layer = Layer.objects.create(
                    typename=wms_layer.name,
                    name=wms_layer.name,
                    store=service.name,  # ??
                    storeType="remoteStore",
                    workspace="remoteWorkspace",
                    title=wms_layer.title or wms_layer.name,
                    abstract=abstract or _("Not provided"),
                    uuid=layer_uuid,
                    owner=None,
                    srid=srid,
                    bbox_x0=bbox[0],
                    bbox_x1=bbox[2],
                    bbox_y0=bbox[1],
                    bbox_y1=bbox[3]
                )

                saved_layer.set_default_permissions()
                saved_layer.keywords.add(*keywords)

                service_layer, created = ServiceLayer.objects.get_or_create(
                    typename=wms_layer.name,
                    service=service
                )
                service_layer.layer = saved_layer
                service_layer.title = wms_layer.title
                service_layer.description = wms_layer.abstract
                service_layer.styles = wms_layer.styles
                service_layer.save()

                resourcebase_post_save(saved_layer, Layer)
                catalogue_post_save(saved_layer, Layer)
                set_attributes_from_geoserver(saved_layer)

                signals.post_save.connect(resourcebase_post_save, sender=Layer)
                signals.post_save.connect(catalogue_post_save, sender=Layer)
            count += 1
        message = "%d Layers Registered" % count
        return_dict = {'status': 'ok', 'msg': message}
        return HttpResponse(json.dumps(return_dict),
                            content_type='application/json',
                            status=200)
    elif service.type == 'WFS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif service.type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Service Type', status=400)


def _register_harvested_service(url, name, username, password, csw=None, owner=None):
    """
    Register a CSW service, then step through results (or queue for asynchronous harvesting)
    """
    try:
        service = Service.objects.get(base_url=url)
        return_dict = [{
            'status': 'ok',
            'service_id': service.pk,
            'service_name': service.name,
            'service_title': service.title,
            'msg': 'This is an existing Service'
        }]
        return HttpResponse(json.dumps(return_dict),
                            content_type='application/json',
                            status=200)
    except:
        pass

    if csw is None:
        csw = CatalogueServiceWeb(url)

    service = Service.objects.create(base_url=url,
                                     type='CSW',
                                     method='H',
                                     name=_get_valid_name(
                                         csw.identification.title or url) if not name else name,
                                     title=csw.identification.title,
                                     version=csw.identification.version,
                                     abstract=csw.identification.abstract or _("Not provided"),
                                     owner=owner)

    service.keywords = ','.join(csw.identification.keywords)
    service.save
    service.set_default_permissions()

    message = "Service %s registered" % service.name
    return_dict = [{'status': 'ok',
                    'msg': message,
                    'service_id': service.pk,
                    'service_name': service.name,
                    'service_title': service.title
                    }]

    if settings.USE_QUEUE:
        # Create a layer import job
        WebServiceHarvestLayersJob.objects.get_or_create(service=service)
    else:
        _harvest_csw(service)

    return HttpResponse(json.dumps(return_dict),
                        content_type='application/json',
                        status=200)


def _harvest_csw(csw, maxrecords=10, totalrecords=float('inf')):
    """
    Step through CSW results, and if one seems to be a WMS or Arc REST service then register it
    """
    stop = 0
    flag = 0

    src = CatalogueServiceWeb(csw.base_url)

    while stop == 0:
        if flag == 0:  # first run, start from 0
            startposition = 0
        else:  # subsequent run, startposition is now paged
            startposition = src.results['nextrecord']

        src.getrecords(
            esn='summary', startposition=startposition, maxrecords=maxrecords)

        max = min(src.results['matches'], totalrecords)

        if src.results['nextrecord'] == 0 \
                or src.results['returned'] == 0 \
                or src.results['nextrecord'] > max:  # end the loop, exhausted all records or max records to process
            stop = 1
            break

        # harvest each record to destination CSW
        for record in list(src.records):
            record = src.records[record]
            known_types = {}
            for ref in record.references:
                if ref["scheme"] == "OGC:WMS" or \
                        "service=wms&request=getcapabilities" in urllib.unquote(ref["url"]).lower():
                    print "WMS:%s" % ref["url"]
                    known_types["WMS"] = ref["url"]
                if ref["scheme"] == "OGC:WFS" or \
                        "service=wfs&request=getcapabilities" in urllib.unquote(ref["url"]).lower():
                    print "WFS:%s" % ref["url"]
                    known_types["WFS"] = ref["url"]
                if ref["scheme"] == "ESRI":
                    print "ESRI:%s" % ref["url"]
                    known_types["REST"] = ref["url"]

            if "WMS" in known_types:
                type = "OWS" if "WFS" in known_types else "WMS"
                try:
                    _process_wms_service(
                        known_types["WMS"], type, None, None, parent=csw)
                except Exception, e:
                    logger.error("Error registering %s:%s" %
                                 (known_types["WMS"], str(e)))
            elif "REST" in known_types:
                try:
                    _register_arcgis_url(ref["url"], None, None, None, parent=csw)
                except Exception, e:
                    logger.error("Error registering %s:%s" %
                                 (known_types["REST"], str(e)))

        flag = 1
        stop = 0


def _register_arcgis_url(url, name, username, password, owner=None, parent=None):
    """
    Register an ArcGIS REST service URL
    """
    # http://maps1.arcgisonline.com/ArcGIS/rest/services
    baseurl = _clean_url(url)
    logger.info("Fetching the ESRI url " + url)
    if re.search("\/MapServer\/*(f=json)*", baseurl):
        # This is a MapService
        try:
            arcserver = ArcMapService(baseurl)
        except Exception, e:
            logger.exception(e)
        if isinstance(arcserver, ArcMapService) and arcserver.spatialReference.wkid in [
                102100, 102113, 3785, 3857, 900913]:
            return_json = [_process_arcgis_service(arcserver, name, owner=owner, parent=parent)]
        else:
            return_json = [{'msg':  _("Could not find any layers in a compatible projection.")}]

    else:
        # This is a Folder
        arcserver = ArcFolder(baseurl)
        return_json = _process_arcgis_folder(
            arcserver, name, services=[], owner=owner, parent=parent)

    return HttpResponse(json.dumps(return_json),
                        content_type='application/json',
                        status=200)


def _register_arcgis_layers(service, arc=None):
    """
    Register layers from an ArcGIS REST service
    """
    arc = arc or ArcMapService(service.base_url)
    logger.info("Registering layers for %s" % service.base_url)
    for layer in arc.layers:
        valid_name = slugify(layer.name)
        count = 0
        layer_uuid = str(uuid.uuid1())
        bbox = [layer.extent.xmin, layer.extent.ymin,
                layer.extent.xmax, layer.extent.ymax]
        typename = layer.id

        existing_layer = None
        logger.info("Registering layer  %s" % layer.name)
        try:
            for layer in Layer.objects.filter(typename=typename):
                if layer.service == service:
                    existing_layer = layer
        except Layer.DoesNotExist:
            pass

        llbbox = mercator_to_llbbox(bbox)

        if existing_layer is None:

            signals.post_save.disconnect(resourcebase_post_save, sender=Layer)
            signals.post_save.disconnect(catalogue_post_save, sender=Layer)

            # Need to check if layer already exists??
            logger.info("Importing layer  %s" % layer.name)
            saved_layer = Layer.objects.create(
                typename=typename,
                name=valid_name,
                store=service.name,  # ??
                storeType="remoteStore",
                workspace="remoteWorkspace",
                title=layer.name,
                abstract=layer._json_struct[
                    'description'] or _("Not provided"),
                uuid=layer_uuid,
                owner=None,
                srid="EPSG:%s" % layer.extent.spatialReference.wkid,
                bbox_x0=llbbox[0],
                bbox_x1=llbbox[2],
                bbox_y0=llbbox[1],
                bbox_y1=llbbox[3],
            )

            saved_layer.set_default_permissions()
            saved_layer.save()

            service_layer, created = ServiceLayer.objects.get_or_create(
                service=service,
                typename=layer.id
            )
            service_layer.layer = saved_layer
            service_layer.title = layer.name,
            service_layer.description = saved_layer.abstract,
            service_layer.styles = None
            service_layer.save()

            resourcebase_post_save(saved_layer, Layer)
            catalogue_post_save(saved_layer, Layer)

            signals.post_save.connect(resourcebase_post_save, sender=Layer)
            signals.post_save.connect(catalogue_post_save, sender=Layer)

            create_arcgis_links(saved_layer)

        count += 1
    message = "%d Layers Registered" % count
    return_dict = {'status': 'ok', 'msg': message}
    return return_dict


def _process_arcgis_service(arcserver, name, owner=None, parent=None):
    """
    Create a Service model instance for an ArcGIS REST service
    """
    arc_url = _clean_url(arcserver.url)
    services = Service.objects.filter(base_url=arc_url)

    if services.count() > 0:
        service = services[0]
        return_dict = [{
            'status': 'ok',
            'service_id': service.pk,
            'service_name': service.name,
            'service_title': service.title,
            'msg': 'This is an existing Service'
        }]
        return return_dict

    name = _get_valid_name(arcserver.mapName or arc_url) if not name else name
    service = Service.objects.create(base_url=arc_url, name=name,
                                     type='REST',
                                     method='I',
                                     title=arcserver.mapName,
                                     abstract=arcserver.serviceDescription,
                                     online_resource=arc_url,
                                     owner=owner,
                                     parent=parent)

    service.set_default_permissions()

    available_resources = []
    for layer in list(arcserver.layers):
        available_resources.append([layer.id, layer.name])

    if settings.USE_QUEUE:
        # Create a layer import job
        WebServiceHarvestLayersJob.objects.get_or_create(service=service)
    else:
        _register_arcgis_layers(service, arc=arcserver)

    message = "Service %s registered" % service.name
    return_dict = {'status': 'ok',
                   'msg': message,
                   'service_id': service.pk,
                   'service_name': service.name,
                   'service_title': service.title,
                   'available_layers': available_resources
                   }
    return return_dict


def _process_arcgis_folder(folder, name, services=None, owner=None, parent=None):
    """
    Iterate through folders and services in an ArcGIS REST service folder
    """
    if services is None:
        services = []
    for service in folder.services:
        return_dict = {}
        if not isinstance(service, ArcMapService):
            return_dict[
                'msg'] = 'Service could not be identified as an ArcMapService, URL: %s' % service.url
            logger.debug(return_dict['msg'])
        else:
            try:
                if service.spatialReference.wkid in [102100, 102113, 3785, 3857, 900913]:
                    return_dict = _process_arcgis_service(
                        service, name, owner, parent=parent)
                else:
                    return_dict['msg'] = _("Could not find any layers in a compatible projection: \
                    The spatial id was: %(srs)s and the url %(url)s" % {'srs': service.spatialReference.wkid,
                                                                        'url': service.url})
                    logger.debug(return_dict['msg'])
            except Exception as e:
                logger.exception('Error uploading from the service: ' + service.url + ' ' + str(e))

        services.append(return_dict)

    for subfolder in folder.folders:
        _process_arcgis_folder(subfolder, name, services, owner)
    return services


def _register_ogp_service(url, owner=None):
    """
    Register OpenGeoPortal as a service
    """
    services = Service.objects.filter(base_url=url)

    if services.count() > 0:
        service = services[0]
        return_dict = [{
            'status': 'ok',
            'service_id': service.pk,
            'service_name': service.name,
            'service_title': service.title,
            'msg': 'This is an existing Service'
        }]
        return return_dict

    service = Service.objects.create(base_url=url,
                                     type="OGP",
                                     method='H',
                                     name="OpenGeoPortal",
                                     title="OpenGeoPortal",
                                     abstract=OGP_ABSTRACT,
                                     owner=owner)

    service.set_default_permissions()
    if settings.USE_QUEUE:
        # Create a layer import job
        WebServiceHarvestLayersJob.objects.get_or_create(service=service)
    else:
        _harvest_ogp_layers(service, owner=owner)

    message = "Service %s registered" % service.name
    return_dict = [{'status': 'ok',
                    'msg': message,
                    'service_id': service.pk,
                    'service_name': service.name,
                    'service_title': service.title
                    }]
    return HttpResponse(json.dumps(return_dict),
                        content_type='application/json',
                        status=200)


def _harvest_ogp_layers(service, maxrecords=10, start=0, totalrecords=float('inf'), owner=None,  institution=None):
    """
    Query OpenGeoPortal's solr instance for layers.
    """
    query = "?q=_val_:%22sum(sum(product(9.0,map(sum(map(MinX,-180.0,180,1,0)," + \
            "map(MaxX,-180.0,180.0,1,0),map(MinY,-90.0,90.0,1,0),map(MaxY,-90.0,90.0,1,0)),4,4,1,0))),0,0)%22" + \
            "&debugQuery=false&&fq={!frange+l%3D1+u%3D10}product(2.0,map(sum(map(sub(abs(sub(0,CenterX))," + \
            "sum(171.03515625,HalfWidth)),0,400000,1,0),map(sub(abs(sub(0,CenterY)),sum(75.84516854027,HalfHeight))" + \
            ",0,400000,1,0)),0,0,1,0))&wt=json&fl=Name,CollectionId,Institution,Access,DataType,Availability," + \
            "LayerDisplayName,Publisher,GeoReferenced,Originator,Location,MinX,MaxX,MinY,MaxY,ContentDate,LayerId," + \
            "score,WorkspaceName,SrsProjectionCode&sort=score+desc&fq=DataType%3APoint+OR+DataType%3ALine+OR+" + \
            "DataType%3APolygon+OR+DataType%3ARaster+OR+DataType%3APaper+Map&fq=Access:Public"
    if institution:
        query += "&fq=%s" % urllib.urlencode(institution)
    fullurl = service.base_url + query + \
        ("&rows=%d&start=%d" % (maxrecords, start))
    response = urllib.urlopen(fullurl).read()
    json_response = json.loads(response)
    process_ogp_results(service, json_response)

    max = min(json_response["response"]["numFound"], totalrecords)

    while start < max:
        start = start + maxrecords
        _harvest_ogp_layers(
            service, maxrecords, start, totalrecords=totalrecords, owner=owner, institution=institution)


def process_ogp_results(ogp, result_json, owner=None):
    """
    Create WMS services and layers from OGP results
    """
    for doc in result_json["response"]["docs"]:
        try:
            locations = json.loads(doc["Location"])
        except:
            continue
        if "tilecache" in locations:
            service_url = locations["tilecache"][0]
            service_type = "WMS"
        elif "wms" in locations:
            service_url = locations["wms"][0]
            if "wfs" in locations:
                service_type = "OWS"
            else:
                service_type = "WMS"
        else:
            pass

        """
        Harvard Geospatial Library is a special case, requires an activation request
        to prepare the layer before WMS requests can be successful.

        """
        if doc["Institution"] == "Harvard":
            service_type = "HGL"

        service = None
        try:
            service = Service.objects.get(base_url=service_url)
        except Service.DoesNotExist:
            if service_type in ["WMS", "OWS", "HGL"]:
                try:
                    response = _process_wms_service(
                        service_url, service_type, None, None, parent=ogp)
                    r_json = json.loads(response.content)
                    service = Service.objects.get(id=r_json[0]["service_id"])
                except Exception, e:
                    print str(e)

        if service:
            typename = doc["Name"]
            if service_type == "HGL":
                typename = typename.replace("SDE.", "")
            elif doc["WorkspaceName"]:
                typename = doc["WorkspaceName"] + ":" + typename

            bbox = (
                float(doc['MinX']),
                float(doc['MinY']),
                float(doc['MaxX']),
                float(doc['MaxY']),
            )

            layer_uuid = str(uuid.uuid1())
            saved_layer, created = Layer.objects.get_or_create(typename=typename,
                                                               defaults=dict(
                                                                   name=doc["Name"],
                                                                   uuid=layer_uuid,
                                                                   store=service.name,
                                                                   storeType="remoteStore",
                                                                   workspace=doc["WorkspaceName"],
                                                                   title=doc["LayerDisplayName"],
                                                                   owner=None,
                                                                   # Assumption
                                                                   srid="EPSG:900913",
                                                                   bbox=list(bbox),
                                                                   geographic_bounding_box=bbox_to_wkt(
                                                                       str(bbox[0]), str(bbox[1]),
                                                                       str(bbox[2]), str(bbox[3]), srid="EPSG:4326")
                                                               )
                                                               )
            saved_layer.set_default_permissions()
            saved_layer.save()
            service_layer, created = ServiceLayer.objects.get_or_create(service=service, typename=typename,
                                                                        defaults=dict(
                                                                            title=doc[
                                                                                "LayerDisplayName"]
                                                                        )
                                                                        )
            if service_layer.layer is None:
                service_layer.layer = saved_layer
                service_layer.save()


def service_detail(request, service_id):
    '''
    This view shows the details of a service
    '''
    service = get_object_or_404(Service, pk=service_id)
    layer_list = [sl.layer for sl in service.servicelayer_set.all()]
    service_list = service.service_set.all()
    # Show 25 services per page
    service_paginator = Paginator(service_list, 25)
    layer_paginator = Paginator(layer_list, 25)  # Show 25 services per page

    page = request.GET.get('page')
    try:
        layers = layer_paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        layers = layer_paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        layers = layer_paginator.page(layer_paginator.num_pages)

    try:
        services = service_paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        services = service_paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        services = service_paginator.page(service_paginator.num_pages)

    return render_to_response("services/service_detail.html", RequestContext(request, {
        'service': service,
        'layers': layers,
        'services': services,
        'permissions_json': _perms_info_json(service)
    }))


@login_required
def edit_service(request, service_id):
    """
    Edit an existing Service
    """
    service_obj = get_object_or_404(Service, pk=service_id)

    if request.method == "POST":
        service_form = ServiceForm(
            request.POST, instance=service_obj, prefix="service")
        if service_form.is_valid():
            service_obj = service_form.save(commit=False)
            service_obj.keywords.clear()
            service_obj.keywords.add(*service_form.cleaned_data['keywords'])
            service_obj.save()

            return HttpResponseRedirect(service_obj.get_absolute_url())
    else:
        service_form = ServiceForm(instance=service_obj, prefix="service")

    return render_to_response("services/service_edit.html", RequestContext(request, {
        "service": service_obj,
        "service_form": service_form
    }))


def update_layers(service):
    """
    Import/update layers for an existing service
    """
    if service.method == "C":
        _register_cascaded_layers(service)
    elif service.type in ["WMS", "OWS"]:
        _register_indexed_layers(service)
    elif service.type == "REST":
        _register_arcgis_layers(service)
    elif service.type == "CSW":
        _harvest_csw(service)
    elif service.type == "OGP":
        _harvest_ogp_layers(service, 25)


@login_required
def remove_service(request, service_id):
    """
    Delete a service, and its constituent layers.
    """
    service_obj = get_object_or_404(Service, pk=service_id)

    if not request.user.has_perm('maps.delete_service', obj=service_obj):
        return HttpResponse(loader.render_to_string('401.html',
                                                    RequestContext(request, {
                                                        'error_message':
                                                        _("You are not permitted to remove this service.")
                                                    })), status=401)

    if request.method == 'GET':
        return render_to_response("services/service_remove.html", RequestContext(request, {
            "service": service_obj
        }))
    elif request.method == 'POST':
        # Retrieve this service's workspace from the GeoServer catalog.
        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest",
                      _user, _password)
        workspace = cat.get_workspace(service_obj.name)

        # Delete nested workspace structure from GeoServer for this service.
        if workspace:
            for store in cat.get_stores(workspace):
                for resource in cat.get_resources(store):
                    for layer in cat.get_layers(resource):
                        cat.delete(layer)
                    cat.delete(resource)
                cat.delete(store)
            cat.delete(workspace)

        # Delete service from GeoNode.
        service_obj.delete()
        return HttpResponseRedirect(reverse("services"))


@login_required
def ajax_service_permissions(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if not request.user.has_perm("maps.change_service_permissions", obj=service):
        return HttpResponse(
            'You are not allowed to change permissions for this service',
            status=401,
            content_type='text/plain'
        )

    if not request.method == 'POST':
        return HttpResponse(
            'You must use POST for editing service permissions',
            status=405,
            content_type='text/plain'
        )

    spec = json.loads(request.body)
    service.set_permissions(spec)

    return HttpResponse(
        "Permissions updated",
        status=200,
        content_type='text/plain')


def create_arcgis_links(instance):
    kmz_link = instance.ows_url + '?f=kmz'

    Link.objects.get_or_create(resource=instance.get_self_resource(),
                               url=kmz_link,
                               defaults=dict(
        extension='kml',
        name="View in Google Earth",
        mime='text/xml',
        link_type='data',
    )
    )

    # Create legend.
    legend_url = instance.ows_url + 'legend?f=json'

    Link.objects.get_or_create(resource=instance.get_self_resource(),
                               url=legend_url,
                               defaults=dict(
        extension='json',
        name=_('Legend'),
        url=legend_url,
        mime='application/json',
        link_type='json',
    )
    )

    # Create thumbnails.
    bbox = urllib.pathname2url('%s,%s,%s,%s' % (instance.bbox_x0, instance.bbox_y0, instance.bbox_x1, instance.bbox_y1))

    thumbnail_remote_url = instance.ows_url + 'export?LAYERS=show%3A' + str(instance.typename) + \
        '&TRANSPARENT=true&FORMAT=png&BBOX=' + bbox + '&SIZE=200%2C150&F=image&BBOXSR=4326&IMAGESR=3857'
    create_thumbnail(instance, thumbnail_remote_url)
