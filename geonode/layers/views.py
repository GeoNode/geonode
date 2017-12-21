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

import base64
import decimal
import httplib2
import logging
import os
import shutil
import sys
import traceback
import uuid

import requests
import xmltodict
import  requests
import string
import random
import shutil
from osgeo import gdal, osr
from geonode.layers.utils import (
    reprojection,
    create_tmp_dir,
    upload_files,
    checking_projection,
    collect_epsg
)
import zipfile

from guardian.shortcuts import get_perms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.template import RequestContext, loader
from django.core.files import File
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.utils.html import escape
from django.template.defaultfilters import slugify
from django.forms.models import inlineformset_factory
from django.db import transaction
from django.db.models import F
from django.forms.util import ErrorList
from django.views.generic import View
from requests.auth import HTTPBasicAuth
from geonode.settings import  OGC_SERVER

from notify.signals import notify

from geonode.tasks.deletion import delete_layer
from geonode.services.models import Service
from geonode.layers.forms import LayerForm, LayerUploadForm, NewLayerUploadForm, LayerAttributeForm
from geonode.base.forms import CategoryForm, ResourceApproveForm, ResourceDenyForm
from geonode.layers.models import Layer, Attribute, UploadSession
from geonode.base.enumerations import CHARSETS
from geonode.base.models import TopicCategory

from geonode.utils import default_map_config
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.layers.utils import file_upload, is_raster, is_vector
from geonode.utils import resolve_object, llbbox_to_mercator
from geonode.people.forms import ProfileForm, PocForm
from geonode.security.views import _perms_info_json
from geonode.documents.models import get_related_documents
from geonode.utils import build_social_links
from geonode.geoserver.helpers import cascading_delete, gs_catalog
from geonode.geoserver.helpers import ogc_server_settings
from geonode import GeoNodeException

from geonode.groups.models import GroupProfile
from geonode.layers.models import LayerSubmissionActivity, LayerAuditActivity, StyleExtension
from geonode.base.libraries.decorators import manager_or_member
from geonode.base.models import KeywordIgnoreListModel
from geonode.authentication_decorators import login_required as custom_login_required
from django.db import connection
from osgeo import osr

from geonode.authentication_decorators import login_required as custom_login_required

if 'geonode.geoserver' in settings.INSTALLED_APPS:
    from geonode.geoserver.helpers import _render_thumbnail
    # from geonode.geoserver.views import save_sld_geoserver

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


def _resolve_layer(request, typename, permission='base.view_resourcebase',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = typename.split(":", 1)

    if Service.objects.filter(name=service_typename[0]).exists():
        service = Service.objects.filter(name=service_typename[0])
        return resolve_object(request,
                              Layer,
                              {'typename': service_typename[1] if service[0].method != "C" else typename},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)
    else:
        return resolve_object(request,
                              Layer,
                              {'typename': typename},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)


# Basic Layer Views #


@login_required
@user_passes_test(manager_or_member)
def layer_upload(request, template='upload/layer_upload.html'):
    db_logger = logging.getLogger('db')
    if request.method == 'GET':
        mosaics = Layer.objects.filter(is_mosaic=True).order_by('name')
        ctx = {
            'mosaics': mosaics,
            'charsets': CHARSETS,
            'is_layer': True,
            'allowed_file_types': ['.cst', '.dbf', '.prj', '.shp', '.shx'],
            'categories': TopicCategory.objects.all(),
            'organizations': GroupProfile.objects.filter(groupmember__user=request.user),
        }
        return render_to_response(template, RequestContext(request, ctx))
    elif request.method == 'POST':

        file_extension = request.FILES['base_file'].name.split('.')[1].lower()
        data_dict = dict()
        tmp_dir = ''
        epsg_code = ''
        # Check if zip file then, extract into tmp_dir and convert
        if zipfile.is_zipfile(request.FILES['base_file']):
            tmp_dir = create_tmp_dir()
            with zipfile.ZipFile(request.FILES['base_file']) as zf:
                zf.extractall(tmp_dir)

            prj_file_name = ''
            shp_file_name = ''
            for file in os.listdir(tmp_dir):
                if file.endswith(".prj"):
                    prj_file_name = file

                elif file.endswith(".shp"):
                    shp_file_name = file

            srs = checking_projection(tmp_dir, prj_file_name)

            # collect epsg code
            epsg_code = collect_epsg(tmp_dir, prj_file_name)

            if epsg_code:
                data_dict = reprojection(tmp_dir, shp_file_name)

        if str(file_extension) == 'shp':

            # create temporary directory for conversion
            tmp_dir = create_tmp_dir()

            # Upload files
            upload_files(tmp_dir, request.FILES)

            # collect epsg code
            epsg_code = collect_epsg(tmp_dir, str(request.FILES['prj_file'].name))

            # Checking projection
            srs = checking_projection(tmp_dir, str(request.FILES['prj_file'].name))

            # if srs.IsProjected:
            if epsg_code:

                if srs.GetAttrValue('projcs'):
                    if "WGS" not in srs.GetAttrValue('projcs'):

                        data_dict = reprojection(tmp_dir, str(request.FILES['base_file'].name))

                # check WGS84 projected
                else:
                    # call projection util function
                    data_dict = reprojection(tmp_dir, str(request.FILES['base_file'].name))

        form = NewLayerUploadForm(request.POST, request.FILES)
        tempdir = None
        errormsgs = []
        out = {'success': False}
        if form.is_valid():
            if str(file_extension) == 'shp' and srs.IsProjected:
                form.cleaned_data['base_file'] = data_dict['base_file']
                form.cleaned_data['shx_file'] = data_dict['shx_file']
                form.cleaned_data['dbf_file'] = data_dict['dbf_file']
                form.cleaned_data['prj_file'] = data_dict['prj_file']
                if 'xml_file' in data_dict:
                    form.cleaned_data['xml_file'] = data_dict['xml_file']
                """
                if 'sbn_file' in  data_dict:
                    form.cleaned_data['sbn_file'] = data_dict['sbn_file']
                if 'sbx_file' in data_dict:
                    form.cleaned_data['sbx_file'] = data_dict['sbx_file']
                """

            title = form.cleaned_data["layer_title"]
            category = form.cleaned_data["category"]
            organization_id = form.cleaned_data["organization"]
            admin_upload = form.cleaned_data["admin_upload"]
            group = GroupProfile.objects.get(id=organization_id)
            # Replace dots in filename - GeoServer REST API upload bug
            # and avoid any other invalid characters.
            # Use the title if possible, otherwise default to the filename
            if title is not None and len(title) > 0:
                name_base = title
                keywords = title.split()
            else:
                name_base, __ = os.path.splitext(
                    form.cleaned_data["base_file"].name)
                keywords = name_base.split()
            ignore_keys = KeywordIgnoreListModel.objects.values_list('key', flat=True)
            keyword_list = []
            for key in keywords:
                if key not in ignore_keys and not key.isdigit() and any(c.isalpha() for c in key) and len(key) > 2:
                    keyword_list.append(key)

            keywords = keyword_list

            name = slugify(name_base.replace(".", "_"))
            try:
                # Moved this inside the try/except block because it can raise
                # exceptions when unicode characters are present.
                # This should be followed up in upstream Django.
                tempdir, base_file = form.write_files()
                saved_layer = file_upload(
                    base_file,
                    name=name,
                    user=request.user,
                    category=category,
                    group=group,
                    keywords=keywords,
                    overwrite=False,
                    charset=form.cleaned_data["charset"],
                    abstract=form.cleaned_data["abstract"],
                    title=form.cleaned_data["layer_title"],
                    metadata_uploaded_preserve=form.cleaned_data["metadata_uploaded_preserve"],
                    user_data_epsg=epsg_code
                )
                if admin_upload:
                    saved_layer.status = 'ACTIVE'
                    saved_layer.save()

            except Exception as e:
                db_logger.exception(e)
                exception_type, error, tb = sys.exc_info()
                logger.exception(e)
                out['success'] = False
                out['errors'] = str(error)
                # Assign the error message to the latest UploadSession from that user.
                latest_uploads = UploadSession.objects.filter(user=request.user).order_by('-date')
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
                upload_session = saved_layer.upload_session
                upload_session.processed = True
                upload_session.save()
                permissions = form.cleaned_data["permissions"]
                if permissions is not None and len(permissions.keys()) > 0:
                    saved_layer.set_permissions(permissions)
            finally:
                # Delete temporary files
                shutil.rmtree(tmp_dir)
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
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=status_code)


def layer_detail(request, layername, template='layers/layer_detail.html'):
    try:
        user_role = request.GET['user_role']
    except:
        user_role=None

    layer = _resolve_layer(
        request,
        layername,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    user = request.user
    edit_permit = False
    if layer.owner == user and layer.status in ['DRAFT', 'ACTIVE', 'DENIED']:
        edit_permit = True
    elif user in layer.group.get_managers() and layer.status in ['PENDING', 'ACTIVE', 'DENIED']:
        edit_permit = True

    if not edit_permit and layer.status=='ACTIVE':
        edit_permit = True

    # if the edit request is not valid then just return from here
    if not edit_permit:
        return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("You dont have permission to edit this layer.")})), status=401)
        # return  HttpResponse('You dont have permission to edit this layer')

    # assert False, str(layer_bbox)
    config = layer.attribute_config()

    # Add required parameters for GXP lazy-loading
    layer_bbox = layer.bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    config["srs"] = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:900913')
    config["bbox"] = bbox if config["srs"] != 'EPSG:900913' \
        else llbbox_to_mercator([float(coord) for coord in bbox])
    config["title"] = layer.title
    config["queryable"] = True
    if layer.default_style:
        config["styles"] = layer.default_style.name

    if layer.storeType == "remoteStore":
        service = layer.service
        source_params = {
            "ptype": service.ptype,
            "remote": True,
            "url": service.base_url,
            "name": service.name}
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != layer.owner and not request.user.is_superuser:
        Layer.objects.filter(
            id=layer.id).update(popular_count=F('popular_count') + 1)

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection=getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:900913'))

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
            except:
                pass

            offset = 10 * (request.page - 1)
            granules = cat.mosaic_granules(coverages['coverages']['coverage'][0]['name'], store, limit=10,
                                           offset=offset, filter=filter)
            all_granules = cat.mosaic_granules(coverages['coverages']['coverage'][0]['name'], store, filter=filter)
        except:
            granules = {"features": []}
            all_granules = {"features": []}
    approve_form = ResourceApproveForm()
    deny_form = ResourceDenyForm()
    metadata_field_list = ['owner', 'title', 'date', 'date_type', 'edition', 'abstract', 'purpose',
                           'maintenance_frequency', 'regions', 'restriction_code_type', 'constraints_other', 'license',
                           'language', 'spatial_representation_type', 'resource_type', 'temporal_extent_start',
                           'temporal_extent_end', 'supplemental_information', 'data_quality_statement', 'thumbnail_url',
                            'elevation_regex', 'time_regex', 'keywords',
                           'category']
    if request.user == layer.owner or request.user in layer.group.get_managers():
        if not layer.attributes:
            messages.info(request, 'Please update layer metadata, missing some informations')
        elif not layer.metadata_author:
            messages.info(request, 'Please update layer metadata, missing some informations')
        else:
            for field in metadata_field_list:
                if not getattr(layer, layer._meta.get_field(field).name):
                    messages.info(request, 'Please update layer metadata, missing some informations')
                    break


    # layer_name = layer.service_typename
    # geoserver_user = OGC_SERVER['default']['USER']
    # geoserver_password = OGC_SERVER['default']['PASSWORD']
    # style_url = OGC_SERVER['default']['PUBLIC_LOCATION'] + "rest/layers/" + layer_name + ".json"
    # response1 = requests.get(style_url, auth=HTTPBasicAuth(geoserver_user, geoserver_password))
    # sld_file_name_url = response1.json()['layer']['defaultStyle']['href']
    # response2 = requests.get(sld_file_name_url, auth=HTTPBasicAuth(geoserver_user, geoserver_password))
    # file_name = response2.json()['style']['filename']
    # sld_file_url = OGC_SERVER['default']['PUBLIC_LOCATION'] + "rest/styles/" + file_name
    # sld_content = requests.get(sld_file_url, auth=HTTPBasicAuth(geoserver_user, geoserver_password)).content
    #
    # xlink = ''
    # try:
    #     dict1 = xmltodict.parse(sld_content)
    #     dict2 = dict1['sld:StyledLayerDescriptor']['sld:NamedLayer']['sld:UserStyle']['sld:FeatureTypeStyle']\
    #     ['sld:Rule']['sld:PointSymbolizer']
    #     xlink = dict2['sld:Graphic']['sld:ExternalGraphic']['sld:OnlineResource']['@xlink:href']
    # except:
    #     pass

    xlink = style_chart_legend_color(layer)

    context_dict = {
        "resource": layer,
        'perms_list': get_perms(request.user, layer.get_self_resource()),
        "permissions_json": _perms_info_json(layer),
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
        "granules": granules,
        "all_granules": all_granules,
        "filter": filter,
        "user_role": user_role,
        "approve_form": approve_form,
        "deny_form": deny_form,
        "denied_comments": LayerAuditActivity.objects.filter(layer_submission_activity__layer=layer),
        "status": layer.status,
        "chart_link" : xlink
    }

    if 'access_token' in request.session:
        access_token = request.session['access_token']
    else:
        u = uuid.uuid1()
        access_token = u.hex

    context_dict["viewer"] = json.dumps(
        map_obj.viewer_json(request.user, access_token, * (NON_WMS_BASE_LAYERS + [maplayer])))
    context_dict["preview"] = getattr(
        settings,
        'LAYER_PREVIEW_LIBRARY',
        'leaflet')
    context_dict["crs"] = getattr(
        settings,
        'DEFAULT_MAP_CRS',
        'EPSG:900913')

    if layer.storeType == 'dataStore':
        links = layer.link_set.download().filter(
            name__in=settings.DOWNLOAD_FORMATS_VECTOR)
    else:
        links = layer.link_set.download().filter(
            name__in=settings.DOWNLOAD_FORMATS_RASTER)
    links_view = [item for idx, item in enumerate(links) if
                  item.url and 'wms' in item.url or 'gwc' in item.url]
    links_download = [item for idx, item in enumerate(links) if
                      item.url and 'wms' not in item.url and 'gwc' not in item.url]
    for item in links_view:
        if item.url and access_token:
            item.url = "%s&access_token=%s" % (item.url, access_token)
    for item in links_download:
        if item.url and access_token:
            item.url = "%s&access_token=%s" % (item.url, access_token)

    if request.user.has_perm('view_resourcebase', layer.get_self_resource()):
        context_dict["links"] = links_view
    if request.user.has_perm('download_resourcebase', layer.get_self_resource()):
        if layer.storeType == 'dataStore':
            links = layer.link_set.download().filter(
                name__in=settings.DOWNLOAD_FORMATS_VECTOR)
        else:
            links = layer.link_set.download().filter(
                name__in=settings.DOWNLOAD_FORMATS_RASTER)
        context_dict["links_download"] = links_download

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, layer)

    if str(layer.user_data_epsg) != 'None':
        with connection.cursor() as cursor:
            cursor.execute("SELECT srtext FROM spatial_ref_sys WHERE srid = %s", [str(layer.user_data_epsg)])

            all_data = cursor.fetchall()
        srstext = str(all_data[0][0])

        srs = osr.SpatialReference(wkt=srstext)
        if srs.IsProjected:
            print srs.GetAttrValue('projcs')
        user_proj = srs.GetAttrValue('geogcs')

        context_dict['user_data_proj'] = user_proj
    context_dict["user_data_epsg"] = str(layer.user_data_epsg)

    return render_to_response(template, RequestContext(request, context_dict))


def layer_feature_catalogue(request, layername, template='../../catalogue/templates/catalogue/feature_catalogue.xml'):
    layer = _resolve_layer(request, layername)
    if layer.storeType != 'dataStore':
        out = {
            'success': False,
            'errors': 'layer is not a feature type'
        }
        return HttpResponse(json.dumps(out), content_type='application/json', status=400)

    attributes = []

    for attrset in layer.attribute_set.all():
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
    return render_to_response(template, context_dict, content_type='application/xml')


@login_required
def layer_metadata(request, layername, template='layers/layer_metadata.html'):
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
        category_form = CategoryForm(
            request.POST,
            prefix="category_choice_field",
            initial=int(
                request.POST["category_choice_field"]) if "category_choice_field" in request.POST else None)

    else:
        layer_form = LayerForm(instance=layer, prefix="resource")
        attribute_form = layer_attribute_set(
            instance=layer,
            prefix="layer_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

    if request.method == "POST" and layer_form.is_valid(
    ) and attribute_form.is_valid() and category_form.is_valid():
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
                    errors = poc_form._errors.setdefault('profile', ErrorList())
                    errors.append(_('You must set a point of contact for this resource'))
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
                    errors = author_form._errors.setdefault('profile', ErrorList())
                    errors.append(_('You must set an author for this resource'))
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

        if new_poc is not None and new_author is not None:
            new_keywords = [x.strip() for x in layer_form.cleaned_data['keywords']]
            layer.keywords.clear()
            layer.keywords.add(*new_keywords)
            the_layer = layer_form.save()
            up_sessions = UploadSession.objects.filter(layer=the_layer.id)
            if up_sessions.count() > 0 and up_sessions[0].user != the_layer.owner:
                up_sessions.update(user=the_layer.owner)
            the_layer.poc = new_poc
            the_layer.metadata_author = new_author
            Layer.objects.filter(id=the_layer.id).update(
                category=new_category
                )

            if getattr(settings, 'SLACK_ENABLED', False):
                try:
                    from geonode.contrib.slack.utils import build_slack_message_layer, send_slack_messages
                    send_slack_messages(build_slack_message_layer("layer_edit", the_layer))
                except:
                    print "Could not send slack message."

            return HttpResponseRedirect(
                reverse(
                    'layer_detail',
                    args=(
                        layer.service_typename,
                    )))

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

    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "attribute_form": attribute_form,
        "category_form": category_form,
    }))


@login_required
def layer_change_poc(request, ids, template='layers/layer_change_poc.html'):
    layers = Layer.objects.filter(id__in=ids.split('_'))
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
    db_logger = logging.getLogger('db')
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
                    out['errors'] = _("You are attempting to replace a vector layer with a raster.")
                elif (not layer.is_vector()) and is_vector(base_file):
                    out['success'] = False
                    out['errors'] = _("You are attempting to replace a raster layer with a vector.")
                else:
                    # delete geoserver's store before upload
                    cat = gs_catalog
                    cascading_delete(cat, layer.typename)
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
                db_logger.exception(e)
                out['success'] = False
                out['errors'] = str(e)
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
    db_logger = logging.getLogger('db')
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

                # notify layer owner that someone have deleted the layer
                if request.user != layer.owner:
                    recipient = layer.owner
                    notify.send(request.user, recipient=recipient, actor=request.user,
                    target=layer, verb='deleted your layer')
        except Exception as e:
            db_logger.exception(e)
            message = '{0}: {1}.'.format(_('Unable to delete layer'), layer.typename)

            if 'referenced by layer group' in getattr(e, 'message', ''):
                message = _('This layer is a member of a layer group, you must remove the layer from the group '
                            'before deleting.')

            messages.error(request, message)
            return render_to_response(template, RequestContext(request, {"layer": layer}))
        return HttpResponseRedirect(reverse("layer_browse"))
    else:
        return HttpResponse("Not allowed", status=403)


@login_required
def layer_granule_remove(request, granule_id, layername, template='layers/layer_granule_remove.html'):
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
            cat.mosaic_delete_granule(coverages['coverages']['coverage'][0]['name'], store, granule_id)
        except Exception as e:
            message = '{0}: {1}.'.format(_('Unable to delete layer'), layer.typename)

            if 'referenced by layer group' in getattr(e, 'message', ''):
                message = _('This layer is a member of a layer group, you must remove the layer from the group '
                            'before deleting.')

            messages.error(request, message)
            return render_to_response(template, RequestContext(request, {"layer": layer}))
        return HttpResponseRedirect(reverse('layer_detail', args=(layer.service_typename,)))
    else:
        return HttpResponse("Not allowed", status=403)


def layer_thumbnail(request, layername):
    if request.method == 'POST':
        layer_obj = _resolve_layer(request, layername)

        try:
            image = _render_thumbnail(request.body)

            if not image:
                return
            filename = "layer-%s-thumb.png" % layer_obj.uuid
            layer_obj.save_thumbnail(filename, image)

            return HttpResponse('Thumbnail saved')
        except:
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


def layer_metadata_detail(request, layername, template='layers/layer_metadata_detail.html'):
    layer = _resolve_layer(request, layername, 'view_resourcebase', _PERMISSION_MSG_METADATA)
    return render_to_response(template, RequestContext(request, {
        "resource": layer,
        'SITEURL': settings.SITEURL[:-1]
    }))



#@jahangir091
@login_required
def layer_publish(request, layer_pk):
    if request.method == 'POST':
        try:
            layer = Layer.objects.get(id=layer_pk)
        except Layer.DoesNotExist:
            return Http404("Layer does not exist")
        else:
            if request.user != layer.owner:
                return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("You are not allowed to publish this layer.")})), status=401)
                # return HttpResponse('you are not allowed to publish this layer')
            group = layer.group
            layer.status = 'PENDING'
            layer.current_iteration += 1
            layer.save()
            layer_submission_activity = LayerSubmissionActivity(layer=layer, group=group, iteration=layer.current_iteration)
            layer_submission_activity.save()

            # notify organization admins about the new published layer
            managers = list( group.get_managers())
            notify.send(request.user, recipient_list = managers, actor=request.user,
                        verb='pushed a new layer for approval', target=layer)

            # set all the permissions for all the managers of the group for this layer
            layer.set_managers_permissions()

            messages.info(request, 'Pushed layer succesfully for approval')
            return HttpResponseRedirect(reverse('member-workspace-layer'))
    else:
        return HttpResponseRedirect(reverse('member-workspace-layer'))


@login_required
def layer_approve(request, layer_pk):
    if request.method == 'POST':
        form = ResourceApproveForm(request.POST)
        if form.is_valid():

            try:
                layer = Layer.objects.get(id=layer_pk)
            except Layer.DoesNotExist:
                return Http404("requested layer does not exists")
            else:
                group = layer.group
                if request.user not in group.get_managers():
                    return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("You are not allowed to approve this layer.")})), status=401)
                    # return HttpResponse("you are not allowed to approve this layer")
                layer_submission_activity = LayerSubmissionActivity.objects.get(layer=layer, group=group, iteration=layer.current_iteration)
                layer_audit_activity = LayerAuditActivity(layer_submission_activity=layer_submission_activity)
                comment_body = request.POST.get('comment')
                comment_subject = request.POST.get('comment_subject')
                layer.status = 'ACTIVE'
                layer.last_auditor = request.user
                layer.save()

                permissions = _perms_info_json(layer)
                perm_dict = json.loads(permissions)
                if request.POST.get('view_permission'):
                    if not 'AnonymousUser' in perm_dict['users']:
                        perm_dict['users']['AnonymousUser'] = []
                        perm_dict['users']['AnonymousUser'].append('view_resourcebase')
                    else:
                        if not 'view_resourcebase' in perm_dict['users']['AnonymousUser']:
                            perm_dict['users']['AnonymousUser'].append('view_resourcebase')

                if request.POST.get('download_permission'):
                    if not 'AnonymousUser' in perm_dict['users']:
                        perm_dict['users']['AnonymousUser'] = []
                        perm_dict['users']['AnonymousUser'].append('download_resourcebase')
                    else:
                        if not 'download_resourcebase' in perm_dict['users']['AnonymousUser']:
                            perm_dict['users']['AnonymousUser'].append('download_resourcebase')

                layer.set_permissions(perm_dict)


                # notify layer owner that someone have approved the layer
                if request.user != layer.owner:
                    recipient = layer.owner
                    notify.send(request.user, recipient=recipient, actor=request.user,
                    target=layer, verb='approved your layer')

                layer_submission_activity.is_audited = True
                layer_submission_activity.save()

                layer_audit_activity.comment_subject = comment_subject
                layer_audit_activity.comment_body = comment_body
                layer_audit_activity.result = 'APPROVED'
                layer_audit_activity.auditor = request.user
                layer_audit_activity.save()

            messages.info(request, 'Approved layer succesfully')
            return HttpResponseRedirect(reverse('admin-workspace-layer'))
        else:
            messages.info(request, 'Please write an approve comment and try again')
            return HttpResponseRedirect(reverse('admin-workspace-layer'))
    else:
        return HttpResponseRedirect(reverse('admin-workspace-layer'))


@login_required
def layer_deny(request, layer_pk):
    if request.method == 'POST':
        form = ResourceDenyForm(data=request.POST)
        if form.is_valid():

            try:
                layer = Layer.objects.get(id=layer_pk)
            except:
                return Http404("requested layer does not exists")
            else:
                group = layer.group
                if request.user not in group.get_managers():
                    return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("You are not allowed to deny this layer.")})), status=401)
                    # return HttpResponse("you are not allowed to deny this layer")
                layer_submission_activity = LayerSubmissionActivity.objects.get(layer=layer, group=group, iteration=layer.current_iteration)
                layer_audit_activity = LayerAuditActivity(layer_submission_activity=layer_submission_activity)
                comment_body = request.POST.get('comment')
                comment_subject = request.POST.get('comment_subject')
                layer.status = 'DENIED'
                layer.last_auditor = request.user
                layer.save()

                # notify layer owner that someone have denied the layer
                if request.user != layer.owner:
                    recipient = layer.owner
                    notify.send(request.user, recipient=recipient, actor=request.user,
                    target=layer, verb='denied your layer')

                layer_submission_activity.is_audited = True
                layer_submission_activity.save()

                layer_audit_activity.comment_subject = comment_subject
                layer_audit_activity.comment_body = comment_body
                layer_audit_activity.result = 'DECLINED'
                layer_audit_activity.auditor = request.user
                layer_audit_activity.save()

            messages.info(request, 'layer denied successfully')
            return HttpResponseRedirect(reverse('admin-workspace-layer'))
        else:
            messages.info(request, 'Please write a deny comment and try again')
            return HttpResponseRedirect(reverse('admin-workspace-layer'))
    else:
        return HttpResponseRedirect(reverse('admin-workspace-layer'))


@login_required
def layer_delete(request, layer_pk):
    if request.method == 'POST':
        try:
            layer = Layer.objects.get(id=layer_pk)
        except:
            return Http404("requested layer does not exists")
        else:
            if layer.status == 'ACTIVE' and (request.user == request.user.is_superuser or request.user == layer.owner or request.user in layer.group.get_managers()):
                layer.status = "DELETED"
                layer.save()

            else:
                return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("You have no acces to delete the layer.")})), status=401)
                # messages.info(request, 'You have no acces to delete the layer')

        messages.info(request, 'Deleted layer successfully')
        if request.user == layer.owner:
            return HttpResponseRedirect(reverse('member-workspace-layer'))
        else:
            return HttpResponseRedirect(reverse('admin-workspace-layer'))

    else:
        return HttpResponseRedirect(reverse('member-workspace-layer'))


def style_chart_legend_color(layer):
    layer_name = layer.service_typename
    geoserver_user = OGC_SERVER['default']['USER']
    geoserver_password = OGC_SERVER['default']['PASSWORD']
    style_url = OGC_SERVER['default']['PUBLIC_LOCATION'] + "rest/layers/" + layer_name + ".json"
    response1 = requests.get(style_url, auth=HTTPBasicAuth(geoserver_user, geoserver_password))
    sld_file_name_url = response1.json()['layer']['defaultStyle']['href']
    response2 = requests.get(sld_file_name_url, auth=HTTPBasicAuth(geoserver_user, geoserver_password))
    file_name = response2.json()['style']['filename']
    sld_file_url = OGC_SERVER['default']['PUBLIC_LOCATION'] + "rest/styles/" + file_name
    sld_content = requests.get(sld_file_url, auth=HTTPBasicAuth(geoserver_user, geoserver_password)).content
    sld_content = sld_content.replace('\r', '')
    sld_content = sld_content.replace('\n', '')

    try:
        dict1 = xmltodict.parse(sld_content)
    except:
        pass
    else:
        xlink = finding_xlink(dict1)
    #     dict2 = dict1['sld:StyledLayerDescriptor']['sld:NamedLayer']['sld:UserStyle']['sld:FeatureTypeStyle']\
    #     ['sld:Rule']['sld:PointSymbolizer']
    #     xlink = dict2['sld:Graphic']['sld:ExternalGraphic']['sld:OnlineResource']['@xlink:href']
    # except:
    #     pass

        if xlink:
            return xlink

    return ''



def finding_xlink(dic):

    for key, value in dic.iteritems():
        if key == '@xlink:href':
            return value

        if isinstance(value, dict):
            item = finding_xlink(value)
            if item is not None:
                return item

def save_sld_geoserver(request_method, full_path, sld_body, content_type='application/vnd.ogc.sld+xml'):
    def strip_prefix(path, prefix):
        assert path.startswith(prefix)
        return path[len(prefix):]
    
    proxy_path = '/gs/rest/styles'
    downstream_path='rest/styles'

    path = strip_prefix(full_path, proxy_path)
    url = str("".join([ogc_server_settings.LOCATION, downstream_path, path]))

    http = httplib2.Http()
    username, password = ogc_server_settings.credentials
    auth = base64.encodestring(username + ':' + password)
    headers = dict()
    headers["Content-Type"] = content_type
    headers["Authorization"] = "Basic " + auth

    return http.request(
        url, request_method,
        body=sld_body or None,
        headers=headers)


class LayerStyleView(View):
    def get(self, request, layername):
        layer_obj = _resolve_layer(request, layername)
        layer_style = layer_obj.default_style
        try:
            style_extension = layer_style.styleextension
        except Exception as ex:
            style_extension = None
        return HttpResponse(
                        json.dumps(
                            dict(name=layer_style.name, title=layer_style.sld_title, url=layer_style.sld_url, workspace=layer_style.workspace, style=style_extension.json_field if style_extension else None),
                            ensure_ascii=False), 
                            status=200,
                            content_type='application/javascript')

    @custom_login_required
    def put(self, request, layername, **kwargs):
        layer_obj = _resolve_layer(request, layername)
        data = json.loads(request.body)
        # check already style extension created or not
        try:
            style_extension = layer_obj.default_style.styleextension
            style_extension.json_field = data.get("StyleString", None)
            style_extension.sld_body=data.get('SldStyle', None)
        except Exception as ex:
            # Style extension does not exists
            style_extension = StyleExtension(style=layer_obj.default_style, json_field=data.get("StyleString", None), sld_body=data.get('SldStyle', None), created_by=request.user, modified_by=request.user)
        
        style_extension.save()
        full_path = '/gs/rest/styles/{0}.xml'.format(layer_obj.default_style.name)
        try:
            save_sld_geoserver(request_method='PUT', full_path=full_path, sld_body=style_extension.sld_body )
        except Exception as ex:
            logger.error(ex)

        return HttpResponse(
                    json.dumps(
                        dict(success="OK"),
                        ensure_ascii=False), 
                        status=200,
                        content_type='application/javascript')
#end

