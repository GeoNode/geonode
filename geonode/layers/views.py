# -*- coding: utf-8 -*-
import re
import os
import logging
import shutil

from urllib import urlencode
from urlparse import urlparse

from django.contrib.auth import authenticate, get_backends as get_auth_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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

from geonode.utils import http_client, _split_query, _get_basic_auth_info, get_csw
from geonode.layers.forms import LayerForm, LayerUploadForm, NewLayerUploadForm
from geonode.layers.models import Layer, ContactRole
from geonode.utils import default_map_config
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.layers.utils import save
from geonode.layers.utils import layer_set_permissions
from geonode.utils import resolve_object
from geonode.people.forms import ContactForm, PocForm
from geonode.security.views import _perms_info_json
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS

from geoserver.resource import FeatureType

from owslib.csw import CswRecord, namespaces
from owslib.util import nspath

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


def data(request):
    return render_to_response('data.html', RequestContext(request, {
        'GEOSERVER_BASE_URL':settings.GEOSERVER_BASE_URL
    }))


def layer_browse(request, template='layers/data.html'):
    return render_to_response(template, RequestContext(request, {}))


@login_required
def layer_upload(request, template='layers/layer_upload.html'):
    if request.method == 'GET':
        return render_to_response(template,
                                  RequestContext(request, {}))
    elif request.method == 'POST':
        form = NewLayerUploadForm(request.POST, request.FILES)
        tempdir = None
        if form.is_valid():
            try:
                tempdir, base_file = form.write_files()
                name, __ = os.path.splitext(form.cleaned_data["base_file"].name)
                saved_layer = save(name, base_file, request.user,
                        overwrite = False,
                        abstract = form.cleaned_data["abstract"],
                        title = form.cleaned_data["layer_title"],
                        permissions = form.cleaned_data["permissions"]
                        )
                return HttpResponse(json.dumps({
                    "success": True,
                    "redirect_to": reverse('layer_metadata', args=[saved_layer.typename])}))
            except Exception, e:
                logger.exception("Unexpected error during upload.")
                return HttpResponse(json.dumps({
                    "success": False,
                    "errormsgs": ["Unexpected error during upload: " + escape(str(e))]}))
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)
        else:
            errormsgs = []
            for e in form.errors.values():
                errormsgs.extend([escape(v) for v in e])
            return HttpResponse(json.dumps({ "success": False, "errors": form.errors, "errormsgs": errormsgs}))


def layer_detail(request, layername, template='layers/layer.html'):
    layer = _resolve_layer(request, layername, 'layers.view_layer', _PERMISSION_MSG_VIEW)
    metadata = layer.metadata_csw()

    maplayer = GXPLayer(name = layer.typename, ows_url = settings.GEOSERVER_BASE_URL + "wms")

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection="EPSG:900913")
    DEFAULT_BASE_LAYERS = default_map_config()[1]

    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "metadata": metadata,
        "viewer": json.dumps(map_obj.viewer_json(* (DEFAULT_BASE_LAYERS + [maplayer]))),
        "permissions_json": _perms_info_json(layer, LAYER_LEV_NAMES),
        "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL
    }))


@login_required
def layer_metadata(request, layername, template='layers/layer_describe.html'):
    layer = _resolve_layer(request, layername, 'layers.change_layer', _PERMISSION_MSG_METADATA) 
        
    poc = layer.poc
    metadata_author = layer.metadata_author
    ContactRole.objects.get(layer=layer, role=layer.poc_role)
    ContactRole.objects.get(layer=layer, role=layer.metadata_author_role)

    if request.method == "POST":
        layer_form = LayerForm(request.POST, instance=layer, prefix="layer")
    else:
        layer_form = LayerForm(instance=layer, prefix="layer")

    if request.method == "POST" and layer_form.is_valid():
        new_poc = layer_form.cleaned_data['poc']
        new_author = layer_form.cleaned_data['metadata_author']
        new_keywords = layer_form.cleaned_data['keywords']

        if new_poc is None:
            poc_form = ContactForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            author_form = ContactForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        if new_poc is not None and new_author is not None:
            the_layer = layer_form.save(commit=False)
            the_layer.poc = new_poc
            the_layer.metadata_author = new_author
            the_layer.keywords.add(*new_keywords)
            the_layer.save()
            return HttpResponseRedirect("/data/" + layer.typename)

    if poc.user is None:
        poc_form = ContactForm(instance=poc, prefix="poc")
    else:
        layer_form.fields['poc'].initial = poc.id
        poc_form = ContactForm(prefix="poc")
        poc_form.hidden=True

    if metadata_author.user is None:
        author_form = ContactForm(instance=metadata_author, prefix="author")
    else:
        layer_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ContactForm(prefix="author")
        author_form.hidden=True

    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
        "poc_form": poc_form,
        "author_form": author_form,
    }))


@login_required
@require_POST
def layer_style(request, layername):
    layer = _resolve_layer(request, typename, 'layers.change_layer',_PERMISSION_MSG_MODIFY)
        
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

    layer.default_style = new_style
    layer.styles = [s for s in layer.styles if s.name != style_name] + [old_default]
    layer.save()
    
    return HttpResponse("Default style for %s changed to %s" % (layer.name, style_name),status=200)


@login_required
def layer_change_poc(request, ids, template = 'layers/change_poc.html'):
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
                saved_layer = save(layer, base_file, request.user, overwrite=True)
                return HttpResponse(json.dumps({
                    "success": True,
                    "redirect_to": reverse('layer_metadata', args=[saved_layer.typename])}))
            except Exception, e:
                logger.exception("Unexpected error during upload.")
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
        return HttpResponseRedirect(reverse("data_home"))
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


#### Layers Search ####


def layer_search_page(request, template='layers/search.html'):
    DEFAULT_BASE_LAYERS = default_map_config()[1]
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    map_obj = GXPMap(projection="EPSG:900913", zoom = 1, center_x = 0, center_y = 0)

    return render_to_response(template, RequestContext(request, {
        'init_search': json.dumps(params or {}),
        'viewer_config': json.dumps(map_obj.viewer_json(*DEFAULT_BASE_LAYERS)),
        'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        "site" : settings.SITEURL
    }))


def layer_search(request):
    """
    handles a basic search for data using the 
    GeoNetwork catalog.

    the search accepts: 
    q - general query for keywords across all fields
    start - skip to this point in the results
    limit - max records to return

    for ajax requests, the search returns a json structure 
    like this: 
    
    {
    'total': <total result count>,
    'next': <url for next batch if exists>,
    'prev': <url for previous batch if exists>,
    'query_info': {
        'start': <integer indicating where this batch starts>,
        'limit': <integer indicating the batch size used>,
        'q': <keywords used to query>,
    },
    'rows': [
      {
        'name': <typename>,
        'abstract': '...',
        'keywords': ['foo', ...],
        'detail' = <link to geonode detail page>,
        'attribution': {
            'title': <language neutral attribution>,
            'href': <url>
        },
        'download_links': [
            ['pdf', 'PDF', <url>],
            ['kml', 'KML', <url>],
            [<format>, <name>, <url>]
            ...
        ],
        'metadata_links': [
           ['text/xml', 'TC211', <url>],
           [<mime>, <name>, <url>],
           ...
        ]
      },
      ...
    ]}
    """
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    # grab params directly to implement defaults as
    # opposed to panicy django forms behavior.
    query = params.get('q', '')
    try:
        start = int(params.get('start', '0'))
    except Exception:
        start = 0
    try:
        limit = min(int(params.get('limit', DEFAULT_SEARCH_BATCH_SIZE)),
                    MAX_SEARCH_BATCH_SIZE)
    except Exception: 
        limit = DEFAULT_SEARCH_BATCH_SIZE

    advanced = {}
    bbox = params.get('bbox', None)
    if bbox:
        try:
            bbox = [float(x) for x in bbox.split(',')]
            if len(bbox) == 4:
                advanced['bbox'] =  bbox
        except Exception:
            # ignore...
            pass

    result = _layer_search(query, start, limit, **advanced)

    # XXX slowdown here to dig out result permissions
    for doc in result['rows']: 
        try: 
            layer = Layer.objects.get(uuid=doc['uuid'])
            doc['_local'] = True
            doc['_permissions'] = {
                'view': request.user.has_perm('layers.view_layer', obj=layer),
                'change': request.user.has_perm('layers.change_layer', obj=layer),
                'delete': request.user.has_perm('layers.delete_layer', obj=layer),
                'change_permissions': request.user.has_perm('layers.change_layer_permissions', obj=layer),
            }
        except Layer.DoesNotExist:
            doc['_local'] = False

    result['success'] = True
    return HttpResponse(json.dumps(result), mimetype="application/json")


def _layer_search(query, start, limit, **kw):
    
    csw = get_csw()

    keywords = _split_query(query)
    
    csw.getrecords(keywords=keywords, startposition=start+1, maxrecords=limit, bbox=kw.get('bbox', None))
    
    
    # build results 
    # XXX this goes directly to the result xml doc to obtain 
    # correct ordering and a fuller view of the result record
    # than owslib currently parses.  This could be improved by
    # improving owslib.
    results = [_build_search_result(doc) for doc in 
               csw._exml.findall('//'+nspath('Record', namespaces['csw']))]

    result = {'rows': results, 
              'total': csw.results['matches']}

    result['query_info'] = {
        'start': start,
        'limit': limit,
        'q': query
    }
    if start > 0: 
        prev = max(start - limit, 0)
        params = urlencode({'q': query, 'start': prev, 'limit': limit})
        result['prev'] = reverse('layer_search_page') + '?' + params

    next_page = csw.results.get('nextrecord', 0) 
    if next_page > 0:
        params = urlencode({'q': query, 'start': next_page - 1, 'limit': limit})
        result['next'] = reverse('layer_search_page') + '?' + params
    
    return result


def layer_search_result_detail(request, template='layers/search_result_snippet.html'):
    uuid = request.GET.get("uuid", None)
    if  uuid is None:
        return HttpResponse(status=400)
    csw = get_csw()
    csw.getrecordbyid([uuid], outputschema=namespaces['gmd'])
    recs = csw.records.values()
    if len(recs) == 0:
        return HttpResponse(status=404)
    rec = recs[0]
    raw_xml = csw._exml.find(nspath('MD_Metadata', namespaces['gmd']))
    extra_links = _extract_links(raw_xml)
    
    try:
        layer = Layer.objects.get(uuid=uuid)
        layer_is_remote = False
    except Exception:
        layer = None
        layer_is_remote = True

    return render_to_response(template, RequestContext(request, {
        'rec': rec,
        'extra_links': extra_links,
        'layer': layer,
        'layer_is_remote': layer_is_remote
    }))


def _extract_links(xml):
    download_links = []
    dl_type_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("protocol", namespaces["gmd"]),
        nspath("CharacterString", namespaces["gco"])
        ])

    dl_name_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("name", namespaces["gmd"]),
        nspath("CharacterString", namespaces["gco"])
        ])

    dl_description_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("description", namespaces["gmd"]),
        nspath("CharacterString", namespaces["gco"])
        ])

    dl_link_path = "/".join([
        nspath("CI_OnlineResource", namespaces["gmd"]),
        nspath("linkage", namespaces["gmd"]),
        nspath("URL", namespaces["gmd"])
        ])

    format_re = re.compile(".*\((.*)(\s*Format*\s*)\).*?")

    for link in xml.findall("*//" + nspath("onLine", namespaces['gmd'])):
        dl_type = link.find(dl_type_path)
        if dl_type is not None and dl_type.text == "WWW:DOWNLOAD-1.0-http--download":
            extension = link.find(dl_name_path).text.split('.')[-1]
            data_format = format_re.match(link.find(dl_description_path).text).groups()[0]
            url = link.find(dl_link_path).text
            download_links.append((extension, data_format, url))
    return dict(download=download_links)


def _build_search_result(doc):
    """
    accepts a node representing a csw result 
    record and builds a POD structure representing 
    the search result.
    """
    if doc is None:
        return None
    # Let owslib do some parsing for us...
    rec = CswRecord(doc)
    result = {}
    result['title'] = rec.title
    result['uuid'] = rec.identifier
    result['abstract'] = rec.abstract
    result['keywords'] = [x for x in rec.subjects if x]
    result['detail'] = getattr(rec,'uri','')

    # XXX needs indexing ? how
    result['attribution'] = {'title': '', 'href': ''}

    # XXX !_! pull out geonode 'typename' if there is one
    # index this directly... 
    if getattr(rec,'uri',None):
        try:
            result['name'] = urlparse(rec.uri).path.split('/')[-1]
        except Exception:
            pass
    # fallback: use geonetwork uuid
    if not result.get('name', ''):
        result['name'] = rec.identifier

    # Take BBOX from GeoNetwork Result...
    # XXX this assumes all our bboxes are in this 
    # improperly specified SRS.
    if rec.bbox is not None and rec.bbox.crs == 'urn:ogc:def:crs:::WGS 1984':
        # slight workaround for ticket 530
        result['bbox'] = {
            'minx': min(rec.bbox.minx, rec.bbox.maxx),
            'maxx': max(rec.bbox.minx, rec.bbox.maxx),
            'miny': min(rec.bbox.miny, rec.bbox.maxy),
            'maxy': max(rec.bbox.miny, rec.bbox.maxy)
        }
    
    # XXX these could be exposed in owslib record...
    # locate all download links
    format_re = re.compile(".*\((.*)(\s*Format*\s*)\).*?")
    result['download_links'] = []
    for link_el in doc.findall(nspath('URI', namespaces['dc'])):
        if link_el.get('protocol', '') == 'WWW:DOWNLOAD-1.0-http--download':
            try:
                extension = link_el.get('name', '').split('.')[-1]
                data_format = format_re.match(link_el.get('description')).groups()[0]
                href = link_el.text
                result['download_links'].append((extension, data_format, href))
            except Exception:
                pass

    # construct the link to the geonetwork metadata record (not self-indexed)
    md_link = settings.GEONETWORK_BASE_URL + "srv/en/csw?" + urlencode({
            "request": "GetRecordById",
            "service": "CSW",
            "version": "2.0.2",
            "OutputSchema": "http://www.isotc211.org/2005/gmd",
            "ElementSetName": "full",
            "id": rec.identifier
        })
    result['metadata_links'] = [("text/xml", "TC211", md_link)]

    return result


@require_POST
def layer_ajax_permissions(request, layername):
    try:
        layer = _resolve_layer(request, layername, 'layers.change_layer_permissions')
    except PermissionDenied:
        # we are handling this in a non-standard way
        return HttpResponse(
            'You are not allowed to change permissions for this layer',
            status=401,
            mimetype='text/plain')

    permission_spec = json.loads(request.raw_post_data)
    layer_set_permissions(layer, permission_spec)

    return HttpResponse(
        "Permissions updated",
        status=200,
        mimetype='text/plain'
    )


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
