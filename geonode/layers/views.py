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
from django.template.defaultfilters import slugify
from django.shortcuts import get_object_or_404
from django.forms.models import inlineformset_factory

from geonode.utils import _get_basic_auth_info
from geonode.layers.forms import LayerForm, LayerUploadForm, NewLayerUploadForm, LayerAttributeForm
from geonode.layers.models import Layer, Attribute

from geonode.utils import default_map_config
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.layers.utils import save
from geonode.utils import resolve_object
from geonode.people.forms import ProfileForm, PocForm
from geonode.security.views import _perms_info_json
from geonode.documents.models import get_related_documents


logger = logging.getLogger("geonode.layers.views")

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
    """
    Resolve the layer by the provided typename and check the optional permission.
    """
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
                # Moved this inside the try/except block because it can raise
                # exceptions when unicode characters are present.
                # This should be followed up in upstream Django.
                tempdir, base_file = form.write_files()
                saved_layer = save(name, base_file, request.user,
                        overwrite = False,
                        charset = form.cleaned_data["charset"],
                        abstract = form.cleaned_data["abstract"],
                        title = form.cleaned_data["layer_title"],
                        )

            except Exception, e:
                logger.exception(e)
                out['success'] = False
                out['errors'] = str(e)
            else:
                out['success'] = True
                out['url'] = reverse('layer_detail', args=[saved_layer.typename])

                permissions = form.cleaned_data["permissions"]
                if permissions is not None and len(permissions.keys()) > 0:
                    saved_layer.set_permissions(permissions)

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

    maplayer = GXPLayer(name = layer.name, ows_url = layer.get_ows_url(), layer_params=json.dumps( layer.attribute_config()))

    # Update count for popularity ranking.
    Layer.objects.filter(id=layer.id).update(popular_count=layer.popular_count +1)

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection="EPSG:900913")
    NON_WMS_BASE_LAYERS = [la for la in default_map_config()[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    context_dict = {
        "layer": layer,
        "permissions_json": _perms_info_json(layer, LAYER_LEV_NAMES),
        "documents": get_related_documents(layer),
        "metadata": metadata,
    }

    context_dict["viewer"] = json.dumps(map_obj.viewer_json(* (NON_WMS_BASE_LAYERS + [maplayer])))

    if layer.storeType=='dataStore':
        links = layer.link_set.download().filter(
        name__in=settings.DOWNLOAD_FORMATS_VECTOR)
    else:
        links = layer.link_set.download().filter(
        name__in=settings.DOWNLOAD_FORMATS_RASTER)


    context_dict["links"] = links

    return render_to_response(template, RequestContext(request, context_dict))


@login_required
def layer_metadata(request, layername, template='layers/layer_metadata.html'):
    layer = _resolve_layer(request, layername, 'layers.change_layer', _PERMISSION_MSG_METADATA)
    layer_attribute_set = inlineformset_factory(Layer, Attribute, extra=0, form=LayerAttributeForm, )

    poc = layer.poc
    metadata_author = layer.metadata_author

    if request.method == "POST":
        layer_form = LayerForm(request.POST, instance=layer, prefix="resource")
        attribute_form = layer_attribute_set(request.POST, instance=layer, prefix="layer_attribute_set", queryset=Attribute.objects.order_by('display_order'))
    else:
        layer_form = LayerForm(instance=layer, prefix="resource")
        attribute_form = layer_attribute_set(instance=layer, prefix="layer_attribute_set", queryset=Attribute.objects.order_by('display_order'))

    if request.method == "POST" and layer_form.is_valid() and attribute_form.is_valid():
        new_poc = layer_form.cleaned_data['poc']
        new_author = layer_form.cleaned_data['metadata_author']
        new_keywords = layer_form.cleaned_data['keywords']

        if new_poc is None:
            if poc.user is None:
                poc_form = ProfileForm(request.POST, prefix="poc", instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author.user is None:
                author_form = ProfileForm(request.POST, prefix="author", 
                    instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        for form in attribute_form.cleaned_data:
            la = Attribute.objects.get(id=int(form['id'].id))
            la.description = form["description"]
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
        return render_to_response(template,
                                  RequestContext(request, {'layer': layer,
                                                           'is_featuretype': layer.is_vector()}))
    elif request.method == 'POST':

        form = LayerUploadForm(request.POST, request.FILES)
        tempdir = None
        out = {}

        if form.is_valid():
            try:
                tempdir, base_file = form.write_files()
                saved_layer = save(layer, base_file, request.user, overwrite=True)
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

@login_required
def layer_remove(request, layername, template='layers/layer_remove.html'):
    try:
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
    except PermissionDenied:
        return HttpResponse(
                'You are not allowed to delete this layer',
                mimetype="text/plain",
                status=401
        )

def layer_batch_download(request):
    """
    batch download a set of layers

    POST - begin download
    GET?id=<download_id> monitor status
    """

    from geonode.utils import http_client, _get_basic_auth_info
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

        url = "%srest/process/batchDownload/launch/" % ogc_server_settings.LOCATION
        resp, content = http_client.request(url,'POST',body=json.dumps(fake_map))
        return HttpResponse(content, status=resp.status)


    if request.method == 'GET':
        # essentially, this just proxies back to geoserver
        download_id = request.GET.get('id', None)
        if download_id is None:
            return HttpResponse(status=404)

        url = "%srest/process/batchDownload/status/%s" % (ogc_server_settings.LOCATION, download_id)
        resp,content = http_client.request(url,'GET')
        return HttpResponse(content, status=resp.status)

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
        elif _get_basic_auth_info(request) == ogc_server_settings.credentials:
            geoserver = True
            superuser = True
        else:
            return HttpResponse(_("Bad HTTP Authorization Credentials."),
                                status=401,
                                mimetype="text/plain")
    if not any([user, geoserver, superuser]) and not request.user.is_anonymous():
        user = request.user.username
        superuser = request.user.is_superuser
    resp = {
        'user' : user,
        'geoserver' : geoserver,
        'superuser' : superuser,
    }
    if request.user.is_authenticated():
        resp['fullname'] = request.user.profile.name
        resp['email'] = request.user.profile.email
    return HttpResponse(json.dumps(resp))


def layer_acls(request):
    from geonode.utils import http_client, _get_basic_auth_info
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
                username == ogc_server_settings.USER and
                password == ogc_server_settings.PASSWORD):
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
        'is_anonymous': acl_user.is_anonymous(),
    }
    if acl_user.is_authenticated():
        result['fullname'] = acl_user.profile.name
        result['email'] = acl_user.profile.email

    return HttpResponse(json.dumps(result), mimetype="application/json")

