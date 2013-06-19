# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
import logging
import shutil
from lxml import etree

from django.contrib.auth import authenticate, get_backends as get_auth_backends
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.utils.html import escape
from django.views.decorators.http import require_POST
from django.template.defaultfilters import slugify
from django.shortcuts import get_object_or_404
from django.forms.models import inlineformset_factory
from django.utils.datastructures import MultiValueDictKeyError 

from geoserver.catalog import FailedRequestError

from geonode.utils import http_client, _get_basic_auth_info, json_response
from geonode.layers.forms import LayerForm, LayerUploadForm, NewLayerUploadForm, LayerAttributeForm, LayerStyleUploadForm
from geonode.layers.models import Layer, Attribute, set_styles
from geonode.base.models import ContactRole
from geonode.utils import default_map_config
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.layers.utils import save
from geonode.layers.utils import layer_set_permissions
from geonode.utils import resolve_object
from geonode.people.forms import ProfileForm, PocForm
from geonode.security.views import _perms_info_json
from geonode.documents.models import get_related_documents

from geoserver.resource import FeatureType

logger = logging.getLogger("geonode.layers.views")

_user, _password = settings.GEOSERVER_CREDENTIALS

DEFAULT_SEARCH_BATCH_SIZE = 10
MAX_SEARCH_BATCH_SIZE = 25
GENERIC_UPLOAD_ERROR = _("There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

LAYER_LEV_NAMES = {
    Layer.LEVEL_NONE  : _('No Permissions'),
    Layer.LEVEL_READ  : _('Read Only'),
    Layer.LEVEL_WRITE : _('Read/Write'),
    Layer.LEVEL_ADMIN : _('Administrative')
}

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this layer")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this layer.')
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this layer")
_PERMISSION_MSG_METADATA = _("You are not permitted to modify this layer's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this layer")


def _resolve_layer(request, typename, permission='layers.change_layer',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the layer by the provided typename and check the optional permission.
    '''
    return resolve_object(request, Layer, {'typename':typename},
                          permission = permission, permission_msg=msg, **kwargs)


#### Basic Layer Views ####

def layer_list(request, template='layers/layer_list.html'):
    from geonode.search.views import search_page
    post = request.POST.copy()
    post.update({'type': 'layer'})
    request.POST = post
    return search_page(request, template=template)

def layer_tag(request, slug, template='layers/layer_list.html'):
    layer_list = Layer.objects.filter(keywords__slug__in=[slug])
    return render_to_response(
        template,
        RequestContext(request, {
            "object_list": layer_list,
            "layer_tag": slug
            }
        )
    )

@login_required
def layer_upload(request, template='upload/layer_upload.html'):
    if request.method == 'GET':
        return render_to_response(template,
                                  RequestContext(request, {}))
    elif request.method == 'POST':
        form = NewLayerUploadForm(request.POST, request.FILES)
        tempdir = None
        errormsgs = []
        out = {'success': False}

        if form.is_valid():
            tempdir, base_file = form.write_files()
            title = form.cleaned_data["layer_title"]

            # Replace dots in filename - GeoServer REST API upload bug
            # and avoid any other invalid characters.
            # Use the title if possible, otherwise default to the filename
            if title is not None and len(title) > 0:
                name_base = title
            else:
                name_base, __ = os.path.splitext(form.cleaned_data["base_file"].name)

            name = slugify(name_base.replace(".","_"))

            try:
                saved_layer = save(name, base_file, request.user,
                        overwrite = False,
                        abstract = form.cleaned_data["abstract"],
                        title = form.cleaned_data["layer_title"],
                        permissions = form.cleaned_data["permissions"]
                        )
            except Exception, e:
                out['success'] = False
                out['errors'] = str(e)
            else:
                out['success'] = True
                out['url'] = reverse('layer_detail', args=[saved_layer.typename])
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
            status_code = 500
        return HttpResponse(json.dumps(out), mimetype='application/json', status=status_code)


def layer_detail(request, layername, template='layers/layer_detail.html'):
    layer = _resolve_layer(request, layername, 'layers.view_layer', _PERMISSION_MSG_VIEW)

    maplayer = GXPLayer(name = layer.typename, ows_url = settings.GEOSERVER_BASE_URL + "wms", layer_params=json.dumps( layer.attribute_config()))

    layer.srid_url = "http://www.spatialreference.org/ref/" + layer.srid.replace(':','/').lower() + "/"

    #layer.popular_count += 1
    #layer.save()

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection="EPSG:900913")
    DEFAULT_BASE_LAYERS = default_map_config()[1]

    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "viewer": json.dumps(map_obj.viewer_json(* (DEFAULT_BASE_LAYERS + [maplayer]))),
        "permissions_json": _perms_info_json(layer, LAYER_LEV_NAMES),
        "documents": get_related_documents(layer),
    }))


@login_required

def layer_metadata(request, layername, template='layers/layer_metadata.html'):
    layer = _resolve_layer(request, layername, 'layers.change_layer', _PERMISSION_MSG_METADATA)
    layer_attribute_set = inlineformset_factory(Layer, Attribute, extra=0, form=LayerAttributeForm, )

    poc = layer.poc
    metadata_author = layer.metadata_author

    ContactRole.objects.get(resource=layer, role=layer.poc_role)
    ContactRole.objects.get(resource=layer, role=layer.metadata_author_role)

    if request.method == "POST":
        layer_form = LayerForm(request.POST, instance=layer, prefix="layer")
        attribute_form = layer_attribute_set(request.POST, instance=layer, prefix="layer_attribute_set", queryset=Attribute.objects.order_by('display_order'))
    else:
        layer_form = LayerForm(instance=layer, prefix="layer")
        attribute_form = layer_attribute_set(instance=layer, prefix="layer_attribute_set", queryset=Attribute.objects.order_by('display_order'))

    if request.method == "POST" and layer_form.is_valid():
        new_poc = layer_form.cleaned_data['poc']
        new_author = layer_form.cleaned_data['metadata_author']
        new_keywords = layer_form.cleaned_data['keywords']

        if new_poc is None:
            poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        if attribute_form.is_valid():
            for form in attribute_form.cleaned_data:
                la = Attribute.objects.get(id=int(form['id'].id))
                la.attribute_label = form["attribute_label"]
                la.visible = form["visible"]
                la.display_order = form["display_order"]
                la.save()

        if new_poc is not None and new_author is not None:
            the_layer = layer_form.save()
            the_layer.poc = new_poc
            the_layer.metadata_author = new_author
            the_layer.keywords.clear()
            the_layer.keywords.add(*new_keywords)
            return HttpResponseRedirect(reverse('layer_detail', args=(layer.typename,)))

    if poc.user is None:
        poc_form = ProfileForm(instance=poc, prefix="poc")
    else:
        layer_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden=True

    if metadata_author.user is None:
        author_form = ProfileForm(instance=metadata_author, prefix="author")
    else:
        layer_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden=True

    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "attribute_form": attribute_form,
    }))


@login_required
@require_POST
def layer_style(request, layername):
    layer = _resolve_layer(request, layername, 'layers.change_layer',_PERMISSION_MSG_MODIFY)

    style_name = request.POST.get('defaultStyle')

    # would be nice to implement
    # better handling of default style switching
    # in layer model or deeper (gsconfig.py, REST API)

    old_default = layer.default_style
    if old_default.name == style_name:
        return HttpResponse("Default style for %s remains %s" % (layer.name, style_name), status=200)

    # This code assumes without checking
    # that the new default style name is included
    # in the list of possible styles.

    new_style = (style for style in layer.styles if style.name == style_name).next()

    # Does this change this in geoserver??
    layer.default_style = new_style
    layer.styles = [s for s in layer.styles if s.name != style_name] + [old_default]
    layer.save()

    return HttpResponse("Default style for %s changed to %s" % (layer.name, style_name),status=200)


@login_required
def layer_style_upload(req, layername):
    def respond(*args,**kw):
        kw['content_type'] = 'text/html'
        return json_response(*args,**kw)
    form = LayerStyleUploadForm(req.POST,req.FILES)
    if not form.is_valid():
        return respond(errors="Please provide an SLD file.")
    
    data = form.cleaned_data
    layer = _resolve_layer(req, layername, 'layers.change_layer',_PERMISSION_MSG_MODIFY)
    
    sld = req.FILES['sld'].read()

    try:
        dom = etree.XML(sld)
    except Exception,ex:
        return respond(errors="The uploaded SLD file is not valid XML")
    
    el = dom.findall("{http://www.opengis.net/sld}NamedLayer/{http://www.opengis.net/sld}Name")
    if len(el) == 0 and not data.get('name'):
        return respond(errors="Please provide a name, unable to extract one from the SLD.")
    name = data.get('name') or el[0].text
    if data['update']:
        match = None
        styles = list(layer.styles) + [layer.default_style]
        for style in styles:
            if style.sld_name == name:
                match = style; break
        if match is None:
            return respond(errors="Cannot locate style : " + name)
        match.update_body(sld)
    else:
        try:
            cat = Layer.objects.gs_catalog
            cat.create_style(name, sld)
            layer.styles = layer.styles + [ type('style',(object,),{'name' : name}) ]
            cat.save(layer.publishing)
        except ConflictingDataError,e:
            return respond(errors="""A layer with this name exists. Select
                                     the update option if you want to update.""")
    return respond(body={'success':True,'style':name,'updated':data['update']})

@login_required
def layer_style_manage(req, layername):
    layer = _resolve_layer(req, layername, 'layers.change_layer',_PERMISSION_MSG_MODIFY)
    if req.method == 'GET':
        try:
            cat = Layer.objects.gs_catalog
            # First update the layer style info from GS to GeoNode's DB
            set_styles(layer, cat)

            all_available_gs_styles = cat.get_styles()
            gs_styles = []
            for style in all_available_gs_styles:
                gs_styles.append(style.name)

            current_layer_styles = layer.styles.all()
            layer_styles = []
            for style in current_layer_styles:
                layer_styles.append(style.name)

            # Render the form
            return render_to_response(
                'layers/layer_style_manage.html',
                RequestContext(req, {
                    "layer": layer,
                    "gs_styles": gs_styles,
                    "layer_styles": layer_styles,
                    "default_style": layer.default_style.name
                    }
                )
            )
        except (FailedRequestError, EnvironmentError) as e:
            msg = ('Could not connect to geoserver at "%s"'
               'to manage style information for layer "%s"' % (
                settings.GEOSERVER_BASE_URL, layer.name)
            )
            logger.warn(msg, e)
            # If geoserver is not online, return an error
            return render_to_response(
                'layers/layer_style_manage.html',
                RequestContext(req, {
                    "layer": layer,
                    "error": msg
                    }
                )
            )
    elif req.method == 'POST':
        try:
            selected_styles = req.POST.getlist('style-select')
            default_style = req.POST['default_style']
            # Save to GeoServer
            cat = Layer.objects.gs_catalog
            gs_layer = cat.get_layer(layer.name)
            gs_layer.default_style = default_style
            styles = []
            for style in selected_styles:
                styles.append(type('style',(object,),{'name' : style}))
            gs_layer.styles = styles 
            cat.save(gs_layer)

            # Save to Django
            set_styles(layer, cat)
            return HttpResponseRedirect(reverse('layer_detail', args=(layer.typename,)))
        except (FailedRequestError, EnvironmentError, MultiValueDictKeyError) as e:
            msg = ('Error Saving Styles for Layer "%s"'  % (layer.name)
            )
            logger.warn(msg, e)
            return render_to_response(
                'layers/layer_style_manage.html',
                RequestContext(req, {
                    "layer": layer,
                    "error": msg
                    }
                )
            )

@login_required
def layer_change_poc(request, ids, template = 'layers/layer_change_poc.html'):
    layers = Layer.objects.filter(id__in=ids.split('_'))
    if request.method == 'POST':
        form = PocForm(request.POST)
        if form.is_valid():
            for layer in layers:
                layer.poc = form.cleaned_data['contact']
                layer.save()
            # Process the data in form.cleaned_data
            # ...
            return HttpResponseRedirect('/admin/maps/layer') # Redirect after POST
    else:
        form = PocForm() # An unbound form
    return render_to_response(template, RequestContext(request,
                                  {'layers': layers, 'form': form }))


@login_required
def layer_replace(request, layername, template='layers/layer_replace.html'):
    layer = _resolve_layer(request, layername, 'layers.change_layer',_PERMISSION_MSG_MODIFY)

    if request.method == 'GET':
        cat = Layer.objects.gs_catalog
        info = cat.get_resource(layer.name)
        is_featuretype = info.resource_type == FeatureType.resource_type

        return render_to_response(template,
                                  RequestContext(request, {'layer': layer,
                                                           'is_featuretype': is_featuretype}))
    elif request.method == 'POST':

        form = LayerUploadForm(request.POST, request.FILES)
        tempdir = None

        if form.is_valid():
            try:
                tempdir, base_file = form.write_files()
                saved_layer = save(layer, base_file, request.user, overwrite=True, 
                    permissions=layer.get_all_level_info())
                return HttpResponse(json.dumps({
                    "success": True,
                    "redirect_to": reverse('layer_metadata', args=[saved_layer.typename])}))
            except Exception, e:
                logger.info("Unexpected error during upload.")
                return HttpResponse(json.dumps({
                    "success": False,
                    "errors": ["Unexpected error during upload: " + escape(str(e))]}))
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)

        else:
            errors = []
            for e in form.errors.values():
                errors.extend([escape(v) for v in e])
            return HttpResponse(json.dumps({ "success": False, "errors": errors}))

@login_required
def layer_remove(request, layername, template='layers/layer_remove.html'):
    layer = _resolve_layer(request, layername, 'layers.delete_layer',
                           _PERMISSION_MSG_DELETE)

    if (request.method == 'GET'):
        return render_to_response(template,RequestContext(request, {
            "layer": layer
        }))
    if (request.method == 'POST'):
        layer.delete()
        return HttpResponseRedirect(reverse("layer_browse"))
    else:
        return HttpResponse("Not allowed",status=403)


def layer_batch_download(request):
    """
    batch download a set of layers

    POST - begin download
    GET?id=<download_id> monitor status
    """

    # currently this just piggy-backs on the map download backend
    # by specifying an ad hoc map that contains all layers requested
    # for download. assumes all layers are hosted locally.
    # status monitoring is handled slightly differently.

    if request.method == 'POST':
        layers = request.POST.getlist("layer")
        layers = Layer.objects.filter(typename__in=list(layers))

        def layer_son(layer):
            return {
                "name" : layer.typename,
                "service" : layer.service_type,
                "metadataURL" : "",
                "serviceURL" : ""
            }

        readme = """This data is provided by GeoNode.\n\nContents:"""
        def list_item(lyr):
            return "%s - %s.*" % (lyr.title, lyr.name)

        readme = "\n".join([readme] + [list_item(l) for l in layers])

        fake_map = {
            "map": { "readme": readme },
            "layers" : [layer_son(lyr) for lyr in layers]
        }

        url = "%srest/process/batchDownload/launch/" % settings.GEOSERVER_BASE_URL
        resp, content = http_client.request(url,'POST',body=json.dumps(fake_map))
        return HttpResponse(content, status=resp.status)


    if request.method == 'GET':
        # essentially, this just proxies back to geoserver
        download_id = request.GET.get('id', None)
        if download_id is None:
            return HttpResponse(status=404)

        url = "%srest/process/batchDownload/status/%s" % (settings.GEOSERVER_BASE_URL, download_id)
        resp,content = http_client.request(url,'GET')
        return HttpResponse(content, status=resp.status)

def layer_permissions(request, layername):
    try:
        layer = _resolve_layer(request, layername, 'layers.change_layer_permissions')
    except PermissionDenied:
        # we are handling this in a non-standard way
        return HttpResponse(
            'You are not allowed to change permissions for this layer',
            status=401,
            mimetype='text/plain')

    if request.method == 'POST':
        permission_spec = json.loads(request.raw_post_data)
        layer_set_permissions(layer, permission_spec)

        return HttpResponse(
            json.dumps({'success': True}),
            status=200,
            mimetype='text/plain'
        )

    elif request.method == 'GET':
        permission_spec = json.dumps(layer.get_all_level_info())
        return HttpResponse(
            json.dumps({'success': True, 'permissions': permission_spec}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponse(
            'No methods other than get and post are allowed',
            status=401,
            mimetype='text/plain')


def resolve_user(request):
    user = None
    geoserver = False
    superuser = False
    if 'HTTP_AUTHORIZATION' in request.META:
        username, password = _get_basic_auth_info(request)
        acl_user = authenticate(username=username, password=password)
        if acl_user:
            user = acl_user.username
            superuser = acl_user.is_superuser
        elif _get_basic_auth_info(request) == settings.GEOSERVER_CREDENTIALS:
            geoserver = True
            superuser = True
    if not any([user, geoserver, superuser]) and not request.user.is_anonymous():
        user = request.user.username
        superuser = request.user.is_superuser
    return HttpResponse(json.dumps({
        'user' : user,
        'geoserver' : geoserver,
        'superuser' : superuser
    }))


def layer_acls(request):
    """
    returns json-encoded lists of layer identifiers that
    represent the sets of read-write and read-only layers
    for the currently authenticated user.
    """

    # the layer_acls view supports basic auth, and a special
    # user which represents the geoserver administrator that
    # is not present in django.
    acl_user = request.user
    if 'HTTP_AUTHORIZATION' in request.META:
        try:
            username, password = _get_basic_auth_info(request)
            acl_user = authenticate(username=username, password=password)

            # Nope, is it the special geoserver user?
            if (acl_user is None and
                username == settings.GEOSERVER_CREDENTIALS[0] and
                password == settings.GEOSERVER_CREDENTIALS[1]):
                # great, tell geoserver it's an admin.
                result = {
                   'rw': [],
                   'ro': [],
                   'name': username,
                   'is_superuser':  True,
                   'is_anonymous': False
                }
                return HttpResponse(json.dumps(result), mimetype="application/json")
        except Exception:
            pass

        if acl_user is None:
            return HttpResponse(_("Bad HTTP Authorization Credentials."),
                                status=401,
                                mimetype="text/plain")


    all_readable = set()
    all_writable = set()
    for bck in get_auth_backends():
        if hasattr(bck, 'objects_with_perm'):
            all_readable.update(bck.objects_with_perm(acl_user,
                                                      'layers.view_layer',
                                                      Layer))
            all_writable.update(bck.objects_with_perm(acl_user,
                                                      'layers.change_layer',
                                                      Layer))
    read_only = [x for x in all_readable if x not in all_writable]
    read_write = [x for x in all_writable if x in all_readable]

    read_only = [x[0] for x in Layer.objects.filter(id__in=read_only).values_list('typename').all()]
    read_write = [x[0] for x in Layer.objects.filter(id__in=read_write).values_list('typename').all()]

    result = {
        'rw': read_write,
        'ro': read_only,
        'name': acl_user.username,
        'is_superuser':  acl_user.is_superuser,
        'is_anonymous': acl_user.is_anonymous()
    }

    return HttpResponse(json.dumps(result), mimetype="application/json")

def feature_edit_check(request, layername):
    """
    If the layer is not a raster and the user has edit permission, return a status of 200 (OK).
    Otherwise, return a status of 401 (unauthorized).
    """
    layer = get_object_or_404(Layer, typename=layername)
    feature_edit = any((getattr(settings, a, None) for a in ("GEOGIT_DATASTORE", "DB_DATASTORE"))) 
    if request.user.has_perm('maps.change_layer', obj=layer) and layer.storeType == 'dataStore' and feature_edit:
        return HttpResponse(json.dumps({'authorized': True}), mimetype="application/json")
    else:
        return HttpResponse(json.dumps({'authorized': False}), mimetype="application/json")
