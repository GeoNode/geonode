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

import os
import sys
import logging
import shutil
import base64
import traceback
import uuid
import decimal
import re

from django.contrib.gis.geos import GEOSGeometry
from django.template.response import TemplateResponse
from requests import Request
from itertools import chain
from six import string_types
from owslib.wfs import WebFeatureService
from owslib.feature.schema import get_schema

from guardian.shortcuts import get_perms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _

from geonode import geoserver, qgis_server

try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.utils.html import escape
from django.template.defaultfilters import slugify
from django.forms.models import inlineformset_factory
from django.db import transaction
from django.db.models import F
from django.forms.utils import ErrorList

from geonode.tasks.deletion import delete_layer
from geonode.services.models import Service
from geonode.layers.forms import LayerForm, LayerUploadForm, NewLayerUploadForm, LayerAttributeForm
from geonode.base.forms import CategoryForm, TKeywordForm
from geonode.layers.models import Layer, Attribute, UploadSession
from geonode.base.enumerations import CHARSETS
from geonode.base.models import TopicCategory
from geonode.groups.models import GroupProfile

from geonode.utils import default_map_config, check_ogc_backend
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.layers.utils import file_upload, is_raster, is_vector
from geonode.utils import resolve_object, llbbox_to_mercator
from geonode.people.forms import ProfileForm, PocForm
from geonode.security.views import _perms_info_json
from geonode.documents.models import get_related_documents
from geonode.utils import build_social_links
from geonode.base.views import batch_modify
from geonode.base.models import Thesaurus
from geonode.maps.models import Map
from geonode.geoserver.helpers import (cascading_delete, gs_catalog,
                                       ogc_server_settings, save_style,
                                       extract_name_from_sld, _invalidate_geowebcache_layer)

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import _render_thumbnail
if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    from geonode.qgis_server.models import QGISServerLayer
CONTEXT_LOG_FILE = ogc_server_settings.LOG_FILE

logger = logging.getLogger("geonode.layers.views")

DEFAULT_SEARCH_BATCH_SIZE = 10
MAX_SEARCH_BATCH_SIZE = 25
GENERIC_UPLOAD_ERROR = _("There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

METADATA_UPLOADED_PRESERVE_ERROR = _("Note: this layer's orginal metadata was \
populated and preserved by importing a metadata XML file. This metadata cannot be edited.")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this layer")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this layer.')
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this layer")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this layer's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this layer")


def log_snippet(log_file):
    if not os.path.isfile(log_file):
        return "No log file at %s" % log_file

    with open(log_file, "r") as f:
        f.seek(0, 2)  # Seek @ EOF
        fsize = f.tell()  # Get Size
        f.seek(max(fsize - 10024, 0), 0)  # Set pos @ last n chars
        return f.read()


def _resolve_layer(request, alternate, permission='base.view_resourcebase',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = alternate.split(":", 1)

    if Service.objects.filter(name=service_typename[0]).exists():
        service = Service.objects.filter(name=service_typename[0])
        return resolve_object(
            request,
            Layer,
            {
                'alternate': service_typename[1] if service[0].method != "C" else alternate},
            permission=permission,
            permission_msg=msg,
            **kwargs)
    else:
        return resolve_object(request,
                              Layer,
                              {'alternate': alternate},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)


# Basic Layer Views #


@login_required
def layer_upload(request, template='upload/layer_upload.html'):
    if request.method == 'GET':
        mosaics = Layer.objects.filter(is_mosaic=True).order_by('name')
        ctx = {
            'mosaics': mosaics,
            'charsets': CHARSETS,
            'is_layer': True,
        }
        return render_to_response(template, RequestContext(request, ctx))
    elif request.method == 'POST':
        form = NewLayerUploadForm(request.POST, request.FILES)
        tempdir = None
        errormsgs = []
        out = {'success': False}
        if form.is_valid():
            title = form.cleaned_data["layer_title"]

            # Replace dots in filename - GeoServer REST API upload bug
            # and avoid any other invalid characters.
            # Use the title if possible, otherwise default to the filename
            if title is not None and len(title) > 0:
                name_base = title
            else:
                name_base, __ = os.path.splitext(
                    form.cleaned_data["base_file"].name)
                title = slugify(name_base.replace(".", "_"))
            name = slugify(name_base.replace(".", "_"))

            if form.cleaned_data["abstract"] is not None and len(form.cleaned_data["abstract"]) > 0:
                abstract = form.cleaned_data["abstract"]
            else:
                abstract = "No abstract provided."

            try:
                # Moved this inside the try/except block because it can raise
                # exceptions when unicode characters are present.
                # This should be followed up in upstream Django.
                tempdir, base_file = form.write_files()
                if not form.cleaned_data["style_upload_form"]:
                    saved_layer = file_upload(
                        base_file,
                        name=name,
                        user=request.user,
                        overwrite=False,
                        charset=form.cleaned_data["charset"],
                        abstract=abstract,
                        title=title,
                        metadata_uploaded_preserve=form.cleaned_data[
                            "metadata_uploaded_preserve"],
                        metadata_upload_form=form.cleaned_data["metadata_upload_form"])
                else:
                    saved_layer = Layer.objects.get(alternate=title)
                    if not saved_layer:
                        msg = 'Failed to process.  Could not find matching layer.'
                        raise Exception(msg)
                    sld = open(base_file).read()
                    # Check SLD is valid
                    extract_name_from_sld(gs_catalog, sld, sld_file=base_file)

                    match = None
                    styles = list(saved_layer.styles.all()) + [
                        saved_layer.default_style]
                    for style in styles:
                        if style and style.name == saved_layer.name:
                            match = style
                            break
                    cat = gs_catalog
                    layer = cat.get_layer(title)
                    if match is None:
                        try:
                            cat.create_style(saved_layer.name, sld, raw=True)
                            style = cat.get_style(saved_layer.name)
                            if layer and style:
                                layer.default_style = style
                                cat.save(layer)
                                saved_layer.default_style = save_style(style)
                        except Exception as e:
                            logger.exception(e)
                    else:
                        style = cat.get_style(saved_layer.name)
                        # style.update_body(sld)
                        try:
                            cat.create_style(saved_layer.name, sld, overwrite=True, raw=True)
                            style = cat.get_style(saved_layer.name)
                            if layer and style:
                                layer.default_style = style
                                cat.save(layer)
                                saved_layer.default_style = save_style(style)
                        except Exception as e:
                            logger.exception(e)

                    # Invalidate GeoWebCache for the updated resource
                    _invalidate_geowebcache_layer(saved_layer.alternate)

            except Exception as e:
                exception_type, error, tb = sys.exc_info()
                logger.exception(e)
                out['success'] = False
                out['errors'] = str(error)
                # Assign the error message to the latest UploadSession from
                # that user.
                latest_uploads = UploadSession.objects.filter(
                    user=request.user).order_by('-date')
                if latest_uploads.count() > 0:
                    upload_session = latest_uploads[0]
                    upload_session.error = str(error)
                    upload_session.traceback = traceback.format_exc(tb)
                    upload_session.context = log_snippet(CONTEXT_LOG_FILE)
                    upload_session.save()
                    out['traceback'] = upload_session.traceback
                    out['context'] = upload_session.context
                    out['upload_session'] = upload_session.id
            else:
                out['success'] = True
                if hasattr(saved_layer, 'info'):
                    out['info'] = saved_layer.info
                out['url'] = reverse(
                    'layer_detail', args=[
                        saved_layer.service_typename])
                if hasattr(saved_layer, 'bbox_string'):
                    out['bbox'] = saved_layer.bbox_string
                if hasattr(saved_layer, 'srid'):
                    out['crs'] = {
                        'type': 'name',
                        'properties': saved_layer.srid
                    }
                out['ogc_backend'] = settings.OGC_SERVER['default']['BACKEND']
                upload_session = saved_layer.upload_session
                if upload_session:
                    upload_session.processed = True
                    upload_session.save()
                permissions = form.cleaned_data["permissions"]
                if permissions is not None and len(permissions.keys()) > 0:
                    saved_layer.set_permissions(permissions)
                saved_layer.handle_moderated_uploads()
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)
        else:
            for e in form.errors.values():
                errormsgs.extend([escape(v) for v in e])
            out['errors'] = form.errors
            out['errormsgs'] = errormsgs
        if out['success']:
            status_code = 200
        else:
            status_code = 400
        if settings.MONITORING_ENABLED:
            request.add_resource('layer', saved_layer.alternate if saved_layer else name)
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=status_code)


def layer_detail(request, layername, template='layers/layer_detail.html'):
    layer = _resolve_layer(
        request,
        layername,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    # assert False, str(layer_bbox)
    config = layer.attribute_config()

    # Add required parameters for GXP lazy-loading
    layer_bbox = layer.bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    if hasattr(layer, 'srid'):
        config['crs'] = {
            'type': 'name',
            'properties': layer.srid
        }
    config["srs"] = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:900913')
    config["bbox"] = bbox if config["srs"] != 'EPSG:900913' \
        else llbbox_to_mercator([float(coord) for coord in bbox])
    config["title"] = layer.title
    config["queryable"] = True

    if layer.storeType == "remoteStore":
        service = layer.service
        source_params = {
            "ptype": service.ptype,
            "remote": True,
            "url": service.base_url,
            "name": service.name}
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    layer.view_count_up(request.user)

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(
        projection=getattr(
            settings,
            'DEFAULT_MAP_CRS',
            'EPSG:900913'))

    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config(request)[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    granules = None
    all_granules = None
    filter = None
    if layer.is_mosaic:
        try:
            cat = gs_catalog
            cat._cache.clear()
            store = cat.get_store(layer.name)
            coverages = cat.mosaic_coverages(store)

            filter = None
            try:
                if request.GET["filter"]:
                    filter = request.GET["filter"]
            except BaseException:
                pass

            offset = 10 * (request.page - 1)
            granules = cat.mosaic_granules(
                coverages['coverages']['coverage'][0]['name'],
                store,
                limit=10,
                offset=offset,
                filter=filter)
            all_granules = cat.mosaic_granules(
                coverages['coverages']['coverage'][0]['name'], store, filter=filter)
        except BaseException:
            granules = {"features": []}
            all_granules = {"features": []}

    group = None
    if layer.group:
        try:
            group = GroupProfile.objects.get(slug=layer.group.name)
        except GroupProfile.DoesNotExist:
            group = None
    # a flag to be used for qgis server
    show_popup = False
    if 'show_popup' in request.GET and request.GET["show_popup"]:
        show_popup = True

    context_dict = {
        'resource': layer,
        'group': group,
        'perms_list': get_perms(request.user, layer.get_self_resource()),
        "permissions_json": _perms_info_json(layer),
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
        "granules": granules,
        "all_granules": all_granules,
        "show_popup": show_popup,
        "filter": filter,
    }

    if 'access_token' in request.session:
        access_token = request.session['access_token']
    else:
        u = uuid.uuid1()
        access_token = u.hex

    context_dict["viewer"] = json.dumps(map_obj.viewer_json(
        request.user, access_token, * (NON_WMS_BASE_LAYERS + [maplayer])))
    context_dict["preview"] = getattr(
        settings,
        'LAYER_PREVIEW_LIBRARY',
        'leaflet')
    context_dict["crs"] = getattr(
        settings,
        'DEFAULT_MAP_CRS',
        'EPSG:900913')

    # provide bbox in EPSG:4326 for leaflet
    if context_dict["preview"] == 'leaflet':
        srid, wkt = layer.geographic_bounding_box.split(';')
        srid = re.findall(r'\d+', srid)
        geom = GEOSGeometry(wkt, srid=int(srid[0]))
        geom.transform(4326)
        context_dict["layer_bbox"] = ','.join([str(c) for c in geom.extent])

    if layer.storeType == 'dataStore':
        links = layer.link_set.download().filter(
            name__in=settings.DOWNLOAD_FORMATS_VECTOR)
    else:
        links = layer.link_set.download().filter(
            name__in=settings.DOWNLOAD_FORMATS_RASTER)
    links_view = [item for idx, item in enumerate(links) if
                  item.url and 'wms' in item.url or 'gwc' in item.url]
    links_download = [item for idx, item in enumerate(
        links) if item.url and 'wms' not in item.url and 'gwc' not in item.url]
    for item in links_view:
        if item.url and access_token and 'access_token' not in item.url:
            params = {'access_token': access_token}
            item.url = Request('GET', item.url, params=params).prepare().url
    for item in links_download:
        if item.url and access_token and 'access_token' not in item.url:
            params = {'access_token': access_token}
            item.url = Request('GET', item.url, params=params).prepare().url

    if request.user.has_perm('view_resourcebase', layer.get_self_resource()):
        context_dict["links"] = links_view
    if request.user.has_perm(
        'download_resourcebase',
            layer.get_self_resource()):
        if layer.storeType == 'dataStore':
            links = layer.link_set.download().filter(
                name__in=settings.DOWNLOAD_FORMATS_VECTOR)
        else:
            links = layer.link_set.download().filter(
                name__in=settings.DOWNLOAD_FORMATS_RASTER)
        context_dict["links_download"] = links_download

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, layer)
    layers_names = layer.alternate
    try:
        if 'geonode' in layers_names:
            workspace, name = layers_names.split(':', 1)
        else:
            name = layers_names
    except:
        print "Can not identify workspace type and layername"

    context_dict["layer_name"] = json.dumps(layers_names)

    try:
        # get type of layer (raster or vector)
        if layer.storeType == 'coverageStore':
            context_dict["layer_type"] = "raster"
        elif layer.storeType == 'dataStore':
            context_dict["layer_type"] = "vector"

            location = "{location}{service}".format(** {
                'location': settings.OGC_SERVER['default']['LOCATION'],
                'service': 'wms',
            })
            # get schema for specific layer
            username = settings.OGC_SERVER['default']['USER']
            password = settings.OGC_SERVER['default']['PASSWORD']
            schema = get_schema(location, name, username=username, password=password)

            # get the name of the column which holds the geometry
            if 'the_geom' in schema['properties']:
                schema['properties'].pop('the_geom', None)
            elif 'geom' in schema['properties']:
                schema['properties'].pop("geom", None)

            # filter the schema dict based on the values of layers_attributes
            layer_attributes_schema = []
            for key in schema['properties'].keys():
                    layer_attributes_schema.append(key)

            filtered_attributes = layer_attributes_schema
            context_dict["schema"] = schema
            context_dict["filtered_attributes"] = filtered_attributes

    except:
        print "Possible error with OWSLib. Turning all available properties to string"

    # maps owned by user needed to fill the "add to existing map section" in template
    if request.user.is_authenticated():
        context_dict["maps"] = Map.objects.filter(owner=request.user)
    return TemplateResponse(
        request, template, RequestContext(request, context_dict))


# Loads the data using the OWS lib when the "Do you want to filter it" button is clicked.
def load_layer_data(request, template='layers/layer_detail.html'):
    context_dict = {}
    data_dict = json.loads(request.POST.get('json_data'))
    layername = data_dict['layer_name']
    filtered_attributes = data_dict['filtered_attributes']
    workspace, name = layername.split(':')
    location = "{location}{service}".format(** {
        'location': settings.OGC_SERVER['default']['LOCATION'],
        'service': 'wms',
    })

    try:
        username = settings.OGC_SERVER['default']['USER']
        password = settings.OGC_SERVER['default']['PASSWORD']
        wfs = WebFeatureService(location, version='1.1.0', username=username, password=password)
        response = wfs.getfeature(typename=name, propertyname=filtered_attributes, outputFormat='application/json')
        x = response.read()
        x = json.loads(x)
        features_response = json.dumps(x)
        decoded = json.loads(features_response)
        decoded_features = decoded['features']
        properties = {}
        for key in decoded_features[0]['properties']:
            properties[key] = []

        # loop the dictionary based on the values on the list and add the properties
        # in the dictionary (if doesn't exist) together with the value
        for i in range(len(decoded_features)):

            for key, value in decoded_features[i]['properties'].iteritems():
                if value != '' and isinstance(value, (string_types, int, float)):
                    properties[key].append(value)

        for key in properties:
            properties[key] = list(set(properties[key]))
            properties[key].sort()

        context_dict["feature_properties"] = properties
    except:
        print "Possible error with OWSLib."
    return HttpResponse(json.dumps(context_dict), content_type="application/json")


def layer_feature_catalogue(
        request,
        layername,
        template='../../catalogue/templates/catalogue/feature_catalogue.xml'):
    layer = _resolve_layer(request, layername)
    if layer.storeType != 'dataStore':
        out = {
            'success': False,
            'errors': 'layer is not a feature type'
        }
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=400)

    attributes = []

    for attrset in layer.attribute_set.order_by('display_order'):
        attr = {
            'name': attrset.attribute,
            'type': attrset.attribute_type
        }
        attributes.append(attr)

    context_dict = {
        'layer': layer,
        'attributes': attributes,
        'metadata': settings.PYCSW['CONFIGURATION']['metadata:main']
    }
    return render_to_response(
        template,
        context_dict,
        content_type='application/xml')


@login_required
def layer_metadata(
        request,
        layername,
        template='layers/layer_metadata.html',
        ajax=True):
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase_metadata',
        _PERMISSION_MSG_METADATA)
    layer_attribute_set = inlineformset_factory(
        Layer,
        Attribute,
        extra=0,
        form=LayerAttributeForm,
    )
    topic_category = layer.category

    poc = layer.poc
    metadata_author = layer.metadata_author

    # assert False, str(layer_bbox)
    config = layer.attribute_config()

    # Add required parameters for GXP lazy-loading
    layer_bbox = layer.bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    if hasattr(layer, 'srid'):
        config['crs'] = {
            'type': 'name',
            'properties': layer.srid
        }
    config["srs"] = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:900913')
    config["bbox"] = bbox if config["srs"] != 'EPSG:900913' \
        else llbbox_to_mercator([float(coord) for coord in bbox])
    config["title"] = layer.title
    config["queryable"] = True

    if layer.storeType == "remoteStore":
        service = layer.service
        source_params = {
            "ptype": service.ptype,
            "remote": True,
            "url": service.base_url,
            "name": service.name}
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != layer.owner and not request.user.is_superuser:
        Layer.objects.filter(
            id=layer.id).update(popular_count=F('popular_count') + 1)

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(
        projection=getattr(
            settings,
            'DEFAULT_MAP_CRS',
            'EPSG:900913'))

    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config(request)[1] if la.ows_url is None]

    if request.method == "POST":
        if layer.metadata_uploaded_preserve:  # layer metadata cannot be edited
            out = {
                'success': False,
                'errors': METADATA_UPLOADED_PRESERVE_ERROR
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)

        layer_form = LayerForm(request.POST, instance=layer, prefix="resource")
        attribute_form = layer_attribute_set(
            request.POST,
            instance=layer,
            prefix="layer_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST else None)
        tkeywords_form = TKeywordForm(
            request.POST,
            prefix="tkeywords")

    else:
        layer_form = LayerForm(instance=layer, prefix="resource")
        attribute_form = layer_attribute_set(
            instance=layer,
            prefix="layer_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

        # Keywords from THESAURI management
        layer_tkeywords = layer.tkeywords.all()
        tkeywords_list = ''
        lang = 'en'  # TODO: use user's language
        if layer_tkeywords and len(layer_tkeywords) > 0:
            tkeywords_ids = layer_tkeywords.values_list('id', flat=True)
            if hasattr(settings, 'THESAURI'):
                for el in settings.THESAURI:
                    thesaurus_name = el['name']
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(
                                    map(str, tkl.values_list('id', flat=True)))
                                tkeywords_list += "," + \
                                    tkl_ids if len(
                                        tkeywords_list) > 0 else tkl_ids
                    except BaseException:
                        tb = traceback.format_exc()
                        logger.error(tb)

        tkeywords_form = TKeywordForm(
            prefix="tkeywords",
            initial={'tkeywords': tkeywords_list})

    if request.method == "POST" and layer_form.is_valid() and attribute_form.is_valid(
    ) and category_form.is_valid() and tkeywords_form.is_valid():
        new_poc = layer_form.cleaned_data['poc']
        new_author = layer_form.cleaned_data['metadata_author']

        if new_poc is None:
            if poc is None:
                poc_form = ProfileForm(
                    request.POST,
                    prefix="poc",
                    instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.is_valid():
                if len(poc_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = poc_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set a point of contact for this resource'))
                    poc = None
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.is_valid():
                if len(author_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = author_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set an author for this resource'))
                    metadata_author = None
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        new_category = TopicCategory.objects.get(
            id=category_form.cleaned_data['category_choice_field'])

        for form in attribute_form.cleaned_data:
            la = Attribute.objects.get(id=int(form['id'].id))
            la.description = form["description"]
            la.attribute_label = form["attribute_label"]
            la.visible = form["visible"]
            la.display_order = form["display_order"]
            la.save()

        if new_poc is not None or new_author is not None:
            if new_poc is not None:
                layer.poc = new_poc
            if new_author is not None:
                layer.metadata_author = new_author

        new_keywords = [x.strip() for x in layer_form.cleaned_data['keywords']]
        if new_keywords is not None:
            layer.keywords.clear()
            layer.keywords.add(*new_keywords)

        try:
            the_layer = layer_form.save()
        except BaseException:
            tb = traceback.format_exc()
            if tb:
                logger.debug(tb)
            the_layer = layer

        up_sessions = UploadSession.objects.filter(layer=the_layer.id)
        if up_sessions.count() > 0 and up_sessions[0].user != the_layer.owner:
            up_sessions.update(user=the_layer.owner)

        if new_category is not None:
            Layer.objects.filter(id=the_layer.id).update(
                category=new_category
            )

        if getattr(settings, 'SLACK_ENABLED', False):
            try:
                from geonode.contrib.slack.utils import build_slack_message_layer, send_slack_messages
                send_slack_messages(
                    build_slack_message_layer(
                        "layer_edit", the_layer))
            except BaseException:
                print "Could not send slack message."

        if not ajax:
            return HttpResponseRedirect(
                reverse(
                    'layer_detail',
                    args=(
                        layer.service_typename,
                    )))

        message = layer.alternate

        try:
            # Keywords from THESAURI management
            tkeywords_to_add = []
            tkeywords_cleaned = tkeywords_form.clean()
            if tkeywords_cleaned and len(tkeywords_cleaned) > 0:
                tkeywords_ids = []
                for i, val in enumerate(tkeywords_cleaned):
                    try:
                        cleaned_data = [value for key, value in tkeywords_cleaned[i].items(
                        ) if 'tkeywords-tkeywords' in key.lower() and 'autocomplete' not in key.lower()]
                        tkeywords_ids.extend(map(int, cleaned_data[0]))
                    except BaseException:
                        pass

                if hasattr(settings, 'THESAURI'):
                    for el in settings.THESAURI:
                        thesaurus_name = el['name']
                        try:
                            t = Thesaurus.objects.get(
                                identifier=thesaurus_name)
                            for tk in t.thesaurus.all():
                                tkl = tk.keyword.filter(pk__in=tkeywords_ids)
                                if len(tkl) > 0:
                                    tkeywords_to_add.append(tkl[0].keyword_id)
                        except BaseException:
                            tb = traceback.format_exc()
                            logger.error(tb)

            layer.tkeywords.add(*tkeywords_to_add)
        except BaseException:
            tb = traceback.format_exc()
            logger.error(tb)

        return HttpResponse(json.dumps({'message': message}))

    if settings.ADMIN_MODERATE_UPLOADS:
        if not request.user.is_superuser:
            layer_form.fields['is_published'].widget.attrs.update({'disabled': 'true'})
        if not request.user.is_superuser and not request.user.is_staff:
            can_change_metadata = request.user.has_perm(
                'change_resourcebase_metadata',
                layer.get_self_resource())
            try:
                is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
            except:
                is_manager = False
            if not is_manager or not can_change_metadata:
                layer_form.fields['is_approved'].widget.attrs.update({'disabled': 'true'})

    if poc is not None:
        layer_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True
    else:
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = False

    if metadata_author is not None:
        layer_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True
    else:
        author_form = ProfileForm(prefix="author")
        author_form.hidden = False

    if 'access_token' in request.session:
        access_token = request.session['access_token']
    else:
        u = uuid.uuid1()
        access_token = u.hex

    viewer = json.dumps(map_obj.viewer_json(
        request.user, access_token, * (NON_WMS_BASE_LAYERS + [maplayer])))

    metadataxsl = False
    if "geonode.contrib.metadataxsl" in settings.INSTALLED_APPS:
        metadataxsl = True

    metadata_author_groups = []
    if request.user.is_superuser or request.user.is_staff:
        metadata_author_groups = GroupProfile.objects.all()
    else:
        try:
            all_metadata_author_groups = chain(
                request.user.group_list_all().distinct(),
                GroupProfile.objects.exclude(access="private").exclude(access="public-invite"))
        except:
            all_metadata_author_groups = GroupProfile.objects.exclude(
                access="private").exclude(access="public-invite")
        [metadata_author_groups.append(item) for item in all_metadata_author_groups
            if item not in metadata_author_groups]

    return render_to_response(template, RequestContext(request, {
        "resource": layer,
        "layer": layer,
        "layer_form": layer_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "attribute_form": attribute_form,
        "category_form": category_form,
        "tkeywords_form": tkeywords_form,
        "viewer": viewer,
        "preview": getattr(settings, 'LAYER_PREVIEW_LIBRARY', 'leaflet'),
        "crs": getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:900913'),
        "metadataxsl": metadataxsl,
        "freetext_readonly": getattr(
            settings,
            'FREETEXT_KEYWORDS_READONLY',
            False),
        "metadata_author_groups": metadata_author_groups,
        "GROUP_MANDATORY_RESOURCES":
            getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
    }))


@login_required
def layer_metadata_advanced(request, layername):
    return layer_metadata(
        request,
        layername,
        template='layers/layer_metadata_advanced.html')


@login_required
def layer_change_poc(request, ids, template='layers/layer_change_poc.html'):
    layers = Layer.objects.filter(id__in=ids.split('_'))

    if settings.MONITORING_ENABLED:
        for l in layers:
            request.add_resource('layer', l.altername)
    if request.method == 'POST':
        form = PocForm(request.POST)
        if form.is_valid():
            for layer in layers:
                layer.poc = form.cleaned_data['contact']
                layer.save()
            # Process the data in form.cleaned_data
            # ...
            # Redirect after POST
            return HttpResponseRedirect('/admin/maps/layer')
    else:
        form = PocForm()  # An unbound form
    return render_to_response(
        template, RequestContext(
            request, {
                'layers': layers, 'form': form}))


@login_required
def layer_replace(request, layername, template='layers/layer_replace.html'):
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_MODIFY)

    if request.method == 'GET':
        ctx = {
            'charsets': CHARSETS,
            'layer': layer,
            'is_featuretype': layer.is_vector(),
            'is_layer': True,
        }
        return render_to_response(template,
                                  RequestContext(request, ctx))
    elif request.method == 'POST':

        form = LayerUploadForm(request.POST, request.FILES)
        tempdir = None
        out = {}

        if form.is_valid():
            try:
                tempdir, base_file = form.write_files()
                if layer.is_vector() and is_raster(base_file):
                    out['success'] = False
                    out['errors'] = _(
                        "You are attempting to replace a vector layer with a raster.")
                elif (not layer.is_vector()) and is_vector(base_file):
                    out['success'] = False
                    out['errors'] = _(
                        "You are attempting to replace a raster layer with a vector.")
                else:
                    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                        # delete geoserver's store before upload
                        cat = gs_catalog
                        cascading_delete(cat, layer.typename)
                        out['ogc_backend'] = geoserver.BACKEND_PACKAGE
                    elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
                        try:
                            qgis_layer = QGISServerLayer.objects.get(
                                layer=layer)
                            qgis_layer.delete()
                        except QGISServerLayer.DoesNotExist:
                            pass
                        out['ogc_backend'] = qgis_server.BACKEND_PACKAGE

                    saved_layer = file_upload(
                        base_file,
                        name=layer.name,
                        user=request.user,
                        overwrite=True,
                        charset=form.cleaned_data["charset"],
                    )
                    out['success'] = True
                    out['url'] = reverse(
                        'layer_detail', args=[
                            saved_layer.service_typename])
            except Exception as e:
                logger.exception(e)
                tb = traceback.format_exc()
                out['success'] = False
                out['errors'] = str(tb)
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)
        else:
            errormsgs = []
            for e in form.errors.values():
                errormsgs.append([escape(v) for v in e])

            out['errors'] = form.errors
            out['errormsgs'] = errormsgs

        if out['success']:
            status_code = 200
        else:
            status_code = 400
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=status_code)


@login_required
def layer_remove(request, layername, template='layers/layer_remove.html'):
    layer = _resolve_layer(
        request,
        layername,
        'base.delete_resourcebase',
        _PERMISSION_MSG_DELETE)

    if (request.method == 'GET'):
        return render_to_response(template, RequestContext(request, {
            "layer": layer
        }))
    if (request.method == 'POST'):
        try:
            with transaction.atomic():
                delete_layer.delay(object_id=layer.id)
        except Exception as e:
            traceback.print_exc()
            message = '{0}: {1}.'.format(
                _('Unable to delete layer'), layer.alternate)

            if 'referenced by layer group' in getattr(e, 'message', ''):
                message = _(
                    'This layer is a member of a layer group, you must remove the layer from the group '
                    'before deleting.')

            messages.error(request, message)
            return render_to_response(
                template, RequestContext(
                    request, {
                        "layer": layer}))
        return HttpResponseRedirect(reverse("layer_browse"))
    else:
        return HttpResponse("Not allowed", status=403)


@login_required
def layer_granule_remove(
        request,
        granule_id,
        layername,
        template='layers/layer_granule_remove.html'):
    layer = _resolve_layer(
        request,
        layername,
        'base.delete_resourcebase',
        _PERMISSION_MSG_DELETE)

    if (request.method == 'GET'):
        return render_to_response(template, RequestContext(request, {
            "granule_id": granule_id,
            "layer": layer
        }))
    if (request.method == 'POST'):
        try:
            cat = gs_catalog
            cat._cache.clear()
            store = cat.get_store(layer.name)
            coverages = cat.mosaic_coverages(store)
            cat.mosaic_delete_granule(
                coverages['coverages']['coverage'][0]['name'], store, granule_id)
        except Exception as e:
            traceback.print_exc()
            message = '{0}: {1}.'.format(
                _('Unable to delete layer'), layer.alternate)

            if 'referenced by layer group' in getattr(e, 'message', ''):
                message = _(
                    'This layer is a member of a layer group, you must remove the layer from the group '
                    'before deleting.')

            messages.error(request, message)
            return render_to_response(
                template, RequestContext(
                    request, {
                        "layer": layer}))
        return HttpResponseRedirect(
            reverse(
                'layer_detail', args=(
                    layer.service_typename,)))
    else:
        return HttpResponse("Not allowed", status=403)


def layer_thumbnail(request, layername):
    if request.method == 'POST':
        layer_obj = _resolve_layer(request, layername)

        try:
            try:
                preview = json.loads(request.body).get('preview', None)
            except:
                preview = None

            if preview and preview == 'react':
                format, image = json.loads(
                    request.body)['image'].split(';base64,')
                image = base64.b64decode(image)
            else:
                image = _render_thumbnail(request.body)

            if not image:
                return
            filename = "layer-%s-thumb.png" % layer_obj.uuid
            layer_obj.save_thumbnail(filename, image)

            return HttpResponse('Thumbnail saved')
        except BaseException:
            return HttpResponse(
                content='error saving thumbnail',
                status=500,
                content_type='text/plain'
            )


def get_layer(request, layername):
    """Get Layer object as JSON"""

    # Function to treat Decimal in json.dumps.
    # http://stackoverflow.com/a/16957370/1198772
    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError
    logger.debug('Call get layer')
    if request.method == 'GET':
        layer_obj = _resolve_layer(request, layername)
        logger.debug(layername)
        response = {
            'typename': layername,
            'name': layer_obj.name,
            'title': layer_obj.title,
            'url': layer_obj.get_tiles_url(),
            'bbox_string': layer_obj.bbox_string,
            'bbox_x0': layer_obj.bbox_x0,
            'bbox_x1': layer_obj.bbox_x1,
            'bbox_y0': layer_obj.bbox_y0,
            'bbox_y1': layer_obj.bbox_y1,
        }
        return HttpResponse(json.dumps(
            response,
            ensure_ascii=False,
            default=decimal_default
        ),
            content_type='application/javascript')


def layer_metadata_detail(
        request,
        layername,
        template='layers/layer_metadata_detail.html'):
    layer = _resolve_layer(
        request,
        layername,
        'view_resourcebase',
        _PERMISSION_MSG_METADATA)
    group = None
    if layer.group:
        try:
            group = GroupProfile.objects.get(slug=layer.group.name)
        except GroupProfile.DoesNotExist:
            group = None
    return render_to_response(template, RequestContext(request, {
        "resource": layer,
        "group": group,
        'SITEURL': settings.SITEURL[:-1]
    }))


def layer_metadata_upload(
        request,
        layername,
        template='layers/layer_metadata_upload.html'):
    layer = _resolve_layer(
        request,
        layername,
        'view_resourcebase',
        _PERMISSION_MSG_METADATA)
    return render_to_response(template, RequestContext(request, {
        "resource": layer,
        "layer": layer,
        'SITEURL': settings.SITEURL[:-1]
    }))


def layer_sld_upload(
        request,
        layername,
        template='layers/layer_style_upload.html'):
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_METADATA)
    return render_to_response(template, RequestContext(request, {
        "resource": layer,
        "layer": layer,
        'SITEURL': settings.SITEURL[:-1]
    }))


@login_required
def layer_batch_metadata(request, ids):
    return batch_modify(request, ids, 'Layer')


def layer_view_counter(layer_id, viewer):
    l = Layer.objects.get(id=layer_id)
    u = get_user_model().objects.get(username=viewer)
    l.view_count_up(u, do_local=True)
