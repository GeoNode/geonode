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
from itertools import islice
import re
import os
import json
import logging
import zipfile
import httplib2
import traceback

from lxml import etree
from osgeo import ogr
from urlparse import urlparse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from geoserver.catalog import FailedRequestError, ConflictingDataError
from geonode.upload import UploadException
from geonode.utils import json_response as do_json_response, unzip_file
from geonode.geoserver.helpers import (gs_catalog,
                                       gs_uploader,
                                       ogc_server_settings,
                                       get_store,
                                       set_time_dimension)  # mosaic_delete_first_granule

ogr.UseExceptions()

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


iso8601 = re.compile(r'^(?P<full>((?P<year>\d{4})([/-]?(?P<mon>(0[1-9])|(1[012]))' +
                     '([/-]?(?P<mday>(0[1-9])|([12]\d)|(3[01])))?)?(?:T(?P<hour>([01][0-9])' +
                     '|(?:2[0123]))(\:?(?P<min>[0-5][0-9])(\:?(?P<sec>[0-5][0-9]([\,\.]\d{1,10})?))?)' +
                     '?(?:Z|([\-+](?:([01][0-9])|(?:2[0123]))(\:?(?:[0-5][0-9]))?))?)?))$').match

_SUPPORTED_CRS = getattr(settings, 'UPLOADER', None)
if _SUPPORTED_CRS:
    _SUPPORTED_CRS = _SUPPORTED_CRS.get('SUPPORTED_CRS',
                                        ['EPSG:4326', 'EPSG:3857'])

_SUPPORTED_EXT = getattr(settings, 'UPLOADER', None)
if _SUPPORTED_EXT:
    _SUPPORTED_EXT = _SUPPORTED_EXT.get('SUPPORTED_EXT',
                                        ['.shp', '.csv', '.kml', '.kmz', '.json',
                                         '.geojson', '.tif', '.tiff', '.geotiff',
                                         '.gml', '.xml'])

_ALLOW_TIME_STEP = getattr(settings, 'UPLOADER', False)
if _ALLOW_TIME_STEP:
    _ALLOW_TIME_STEP = _ALLOW_TIME_STEP.get(
        'OPTIONS',
        False).get(
        'TIME_ENABLED',
        False)

_ALLOW_MOSAIC_STEP = getattr(settings, 'UPLOADER', False)
if _ALLOW_MOSAIC_STEP:
    _ALLOW_MOSAIC_STEP = _ALLOW_MOSAIC_STEP.get(
        'OPTIONS',
        False).get(
        'MOSAIC_ENABLED',
        False)

_ASYNC_UPLOAD = True if ogc_server_settings and ogc_server_settings.DATASTORE else False

# at the moment, the various time support transformations require the database
if _ALLOW_TIME_STEP and not _ASYNC_UPLOAD:
    raise Exception(_(
        "To support the time step, you must enable the OGC_SERVER DATASTORE option"))

_geoserver_down_error_msg = """
GeoServer is not responding. Please try again later and sorry for the inconvenience.
"""

_unexpected_error_msg = """
An error occurred while trying to process your request.  Our administrator has
been notified, but if you'd like, please note this error code
below and details on what you were doing when you encountered this error.
That information can help us identify the cause of the problem and help us with
fixing it.  Thank you!
"""

"""
    JSON Responses
"""


class JSONResponse(HttpResponse):

    """JSON response class."""

    def __init__(self,
                 obj='',
                 json_opts=None,
                 content_type="application/json", *args, **kwargs):

        if json_opts is None:
            json_opts = {}
        content = json.dumps(obj, **json_opts)
        super(JSONResponse, self).__init__(
            content, content_type, *args, **kwargs)


def json_response(*args, **kw):
    if 'exception' in kw:
        logger.warn(traceback.format_exc(kw['exception']))
    return do_json_response(*args, **kw)


def error_response(req, exception=None, errors=None, force_ajax=True):
    if exception:
        logger.exception('Unexpected error in upload step')
    else:
        logger.error('upload error: %s', errors)
    if req.is_ajax() or force_ajax:
        content_type = 'text/html' if not req.is_ajax() else None
        return json_response(exception=exception, errors=errors,
                             content_type=content_type, status=400)
    # not sure if any responses will (ideally) ever be non-ajax
    if errors:
        exception = "<br>".join(errors)
    return render(
        req,
        'upload/layer_upload_error.html',
        context={'error_msg': 'Unexpected error : %s,' % exception})


def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )


def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


def get_kml_doc(kml_bytes):
    """Parse and return an etree element with the kml file's content"""
    kml_doc = etree.fromstring(
        kml_bytes,
        parser=etree.XMLParser(resolve_entities=False)
    )
    ns = kml_doc.nsmap.copy()
    ns["kml"] = ns.pop(None)
    return kml_doc, ns


"""
    Upload Workflow: Steps Utilities
"""
# note 'run' is not a "real" step, but handled as a special case
# and 'save' is the implied first step :P
_pages = {
    'shp': ('srs', 'check', 'time', 'run', 'final'),
    'csv': ('csv', 'srs', 'check', 'time', 'run', 'final'),
    'tif': ('run', 'final'),
    'zip-mosaic': ('run', 'final'),
    'asc': ('run', 'final'),
    'kml': ('run', 'final'),
    'kml-overlay': ('run', 'final'),
    'geojson': ('run', 'final'),
    'ntf': ('run', 'final'),  # NITF
    'img': ('run', 'final'),  # ERDAS Imagine
    'i41': ('run', 'final'),  # CIB01 RPF
    'i21': ('run', 'final'),  # CIB05 RPF
    'i11': ('run', 'final'),  # CIB10 RPF
    'gn1': ('run', 'final'),  # GNC RPF
    'jn1': ('run', 'final'),  # JNC RPF
    'on1': ('run', 'final'),  # ONC RPF
    'tp1': ('run', 'final'),  # TPC RPF
    'ja1': ('run', 'final'),  # JOG RPF
    'tc1': ('run', 'final'),  # TLM100 RPF
    'tl1': ('run', 'final'),  # TLM50 RPF
    'jp2': ('run', 'final'),  # JPEG2000 MrSID
    'sid': ('run', 'final'),  # MrSID
}

_latitude_names = set(['latitude', 'lat'])
_longitude_names = set(['longitude', 'lon', 'lng', 'long'])


if not _ALLOW_TIME_STEP:
    for t, steps in _pages.items():
        steps = list(steps)
        if 'time' in steps:
            steps.remove('time')
        _pages[t] = tuple(steps)

if not _ALLOW_MOSAIC_STEP:
    for t, steps in _pages.items():
        steps = list(steps)
        if 'mosaic' in steps:
            steps.remove('mosaic')
        _pages[t] = tuple(steps)

if not _ALLOW_MOSAIC_STEP:
    for t, steps in _pages.items():
        steps = list(steps)
        if 'mosaic' in steps:
            steps.remove('mosaic')
        _pages[t] = tuple(steps)


def get_next_step(upload_session, offset=1):
    assert upload_session.upload_type is not None

    if upload_session.completed_step == 'error':
        return 'error'

    try:
        pages = _pages[upload_session.upload_type]
    except KeyError as e:
        raise Exception(_('Unsupported file type: %s' % e.message))
    index = -1
    if upload_session.completed_step and upload_session.completed_step != 'save':
        index = pages.index(upload_session.completed_step)
    return pages[max(min(len(pages) - 1, index + offset), 0)]


def get_previous_step(upload_session, post_to):
    pages = _pages[upload_session.upload_type]
    if post_to == "undefined":
        post_to = "final"
    index = pages.index(post_to) - 1

    if index < 0:
        return 'save'
    return pages[index]


def _advance_step(req, upload_session):
    if upload_session.completed_step != 'error':
        upload_session.completed_step = get_next_step(upload_session)
    else:
        return 'error'


def next_step_response(req, upload_session, force_ajax=True):
    import_session = upload_session.import_session
    # if the current step is the view POST for this step, advance one
    if req.method == 'POST':
        if upload_session.completed_step:
            _advance_step(req, upload_session)
        else:
            upload_session.completed_step = 'save'
    next = get_next_step(upload_session)
    if next == 'error':
        return json_response(
            {'status': 'error',
             'success': False,
             'id': import_session.id,
             'error_msg': "%s" % upload_session.error_msg,
             }
        )

    if next == 'check':
        # @TODO we skip time steps for coverages currently
        store_type = import_session.tasks[0].target.store_type
        if store_type == 'coverageStore':
            upload_session.completed_step = 'check'
            return next_step_response(req, upload_session, force_ajax)
    if next == 'check' and force_ajax:
        url = reverse('data_upload') + "?id=%s" % import_session.id
        return json_response(
            {'url': url,
             'status': 'incomplete',
             'success': True,
             'id': import_session.id,
             'redirect_to': '/upload/check' + "?id=%s" % import_session.id,
             }
        )

    if next == 'time':
        # @TODO we skip time steps for coverages currently
        store_type = import_session.tasks[0].target.store_type
        layer = import_session.tasks[0].layer
        (has_time_dim, layer_values) = layer_eligible_for_time_dimension(req,
                                                                         layer,
                                                                         upload_session=upload_session)
        if store_type == 'coverageStore' or not has_time_dim:
            upload_session.completed_step = 'time'
            return next_step_response(req, upload_session, False)
    if next == 'time' and (
            upload_session.time is None or not upload_session.time):
        upload_session.completed_step = 'time'
        return next_step_response(req, upload_session, force_ajax)
    if next == 'time' and force_ajax:
        url = reverse('data_upload') + "?id=%s" % import_session.id
        return json_response(
            {'url': url,
             'status': 'incomplete',
             'success': True,
             'id': import_session.id,
             'redirect_to': '/upload/time' + "?id=%s" % import_session.id,
             }
        )

    if next == 'mosaic' and force_ajax:
        url = reverse('data_upload') + "?id=%s" % import_session.id
        return json_response(
            {'url': url,
             'status': 'incomplete',
             'success': True,
             'id': import_session.id,
             'redirect_to': '/upload/mosaic' + "?id=%s" % import_session.id,
             }
        )

    if next == 'srs' and force_ajax:
        url = reverse('data_upload') + "?id=%s" % import_session.id
        return json_response(
            {'url': url,
             'status': 'incomplete',
             'success': True,
             'id': import_session.id,
             'redirect_to': '/upload/srs' + "?id=%s" % import_session.id,
             }
        )

    if next == 'csv' and force_ajax:
        url = reverse('data_upload') + "?id=%s" % import_session.id
        return json_response(
            {'url': url,
             'status': 'incomplete',
             'success': True,
             'id': import_session.id,
             'redirect_to': '/upload/csv' + "?id=%s" % import_session.id,
             }
        )

    # @todo this is not handled cleanly - run is not a real step in that it
    # has no corresponding view served by the 'view' function.
    if next == 'run':
        upload_session.completed_step = next
        if _ASYNC_UPLOAD and req.is_ajax():
            return run_response(req, upload_session)
        else:
            # on sync we want to run the import and advance to the next step
            run_import(upload_session, async=False)
            return next_step_response(req, upload_session,
                                      force_ajax=force_ajax)
    session_id = None
    if 'id' in req.GET:
        session_id = "?id=%s" % req.GET['id']
    elif import_session and import_session.id:
        session_id = "?id=%s" % import_session.id

    if req.is_ajax() or force_ajax:
        content_type = 'text/html' if not req.is_ajax() else None
        if session_id:
            return json_response(
                redirect_to=reverse(
                    'data_upload',
                    args=[next]) + session_id,
                content_type=content_type)
        else:
            return json_response(
                url=reverse(
                    'data_upload',
                    args=[next]),
                content_type=content_type)

    return HttpResponseRedirect(reverse('data_upload', args=[next]))


def is_latitude(colname):
    return colname.lower() in _latitude_names


def is_longitude(colname):
    return colname.lower() in _longitude_names


def is_async_step(upload_session):
    return _ASYNC_UPLOAD and get_next_step(upload_session, offset=2) == 'run'


def check_import_session_is_valid(request, upload_session, import_session):
    # check for failing Import Session and Import Tasks
    assert import_session is not None
    assert len(import_session.tasks) > 0

    for task in import_session.tasks:
        if task.state == 'ERROR':
            progress = task.get_progress()
            upload_session.completed_step = 'error'
            upload_session.error_msg = progress.get('message')
            return None

    # check for invalid attribute names
    store_type = import_session.tasks[0].target.store_type
    if store_type == 'dataStore':
        try:
            layer = import_session.tasks[0].layer
            invalid = filter(
                lambda a: str(a.name).find(' ') >= 0, layer.attributes)
            if invalid:
                att_list = "<pre>%s</pre>" % '. '.join(
                    [a.name for a in invalid])
                msg = "Attributes with spaces are not supported : %s" % att_list
                upload_session.completed_step = 'error'
                upload_session.error_msg = msg
            return layer
        except Exception as e:
            return render(request,
                          'upload/layer_upload_error.html', context={'error_msg': str(e)})
    elif store_type == 'coverageStore':
        return True


def _get_time_dimensions(layer, upload_session):
    date_time_keywords = [
        'date',
        'time',
        'year',
        'create',
        'end',
        'last',
        'update',
        'expire',
        'enddate']

    def filter_name(b):
        return [kw for kw in date_time_keywords if kw in b]

    att_list = []
    try:
        layer_values = _get_layer_values(layer, upload_session, expand=1)
        if layer and layer_values:
            ft = layer_values[0]
            attributes = [{'name': k, 'binding': ft[k]['binding'] or 0} for k in ft.keys()]
            for a in attributes:
                if (('Integer' in a['binding'] or 'Long' in a['binding']) and 'id' != a['name'].lower()) \
                        and filter_name(a['name'].lower()):
                    if layer_values:
                        for feat in layer_values:
                            if iso8601(str(feat.get(a['name'])['value'])):
                                if a not in att_list:
                                    att_list.append(a)
                elif 'Date' in a['binding']:
                    att_list.append(a)
                elif 'String' in a['binding'] \
                        and filter_name(a['name'].lower()):
                    if layer_values:
                        for feat in layer_values:
                            if iso8601(str(feat.get(a['name'])['value'])):
                                if a not in att_list:
                                    att_list.append(a)
                    else:
                        pass
    except BaseException:
        traceback.print_exc()
        return None
    return att_list


def _get_layer_values(layer, upload_session, expand=0):
    layer_values = []
    if upload_session:
        absolute_base_file = upload_session.base_file[0].base_file
        tempdir = upload_session.tempdir

        if not os.path.isfile(absolute_base_file):
            tmp_files = [f for f in os.listdir(tempdir) if os.path.isfile(os.path.join(tempdir, f))]
            for f in tmp_files:
                if zipfile.is_zipfile(os.path.join(tempdir, f)):
                    absolute_base_file = unzip_file(os.path.join(tempdir, f), '.shp', tempdir=tempdir)
                    absolute_base_file = os.path.join(tempdir,
                                                      absolute_base_file)
        elif zipfile.is_zipfile(absolute_base_file):
            absolute_base_file = unzip_file(upload_session.base_file[0].base_file,
                                            '.shp', tempdir=tempdir)
            absolute_base_file = os.path.join(tempdir,
                                              absolute_base_file)
        inDataSource = ogr.Open(absolute_base_file)
        lyr = inDataSource.GetLayer(str(layer.name))
        limit = 100
        for feat in islice(lyr, 0, limit):
            try:
                feat_values = json_loads_byteified(feat.ExportToJson()).get('properties')
                for k in feat_values.keys():
                    type_code = feat.GetFieldDefnRef(k).GetType()
                    binding = feat.GetFieldDefnRef(k).GetFieldTypeName(type_code)
                    feat_value = feat_values[k] if str(feat_values[k]) != 'None' else 0
                    if expand > 0:
                        ff = {'value': feat_value, 'binding': binding}
                        feat_values[k] = ff
                    else:
                        feat_values[k] = feat_value
                layer_values.append(feat_values)
            except BaseException:
                pass
    return layer_values


def layer_eligible_for_time_dimension(
        request, layer, values=None, upload_session=None):
    _is_eligible = False
    layer_values = values or _get_layer_values(layer, upload_session, expand=0)
    att_list = _get_time_dimensions(layer, upload_session)
    _is_eligible = att_list or False
    if upload_session and _is_eligible:
        upload_session.time = True
    return (_is_eligible, layer_values)


def run_import(upload_session, async=_ASYNC_UPLOAD):
    """Run the import, possibly asynchronously.

    Returns the target datastore.
    """
    # run_import can raise an exception which callers should handle
    import_session = upload_session.import_session
    import_session = gs_uploader.get_session(import_session.id)
    task = import_session.tasks[0]
    import_execution_requested = False
    if import_session.state == 'INCOMPLETE':
        if task.state != 'ERROR':
            raise Exception(_('unknown item state: %s' % task.state))
    elif import_session.state == 'PENDING' and task.target.store_type == 'coverageStore':
        if task.state == 'READY':
            import_session.commit(async)
            import_execution_requested = True
        if task.state == 'ERROR':
            progress = task.get_progress()
            raise Exception(_(
                'error during import: %s' %
                progress.get('message')))

    # if a target datastore is configured, ensure the datastore exists
    # in geoserver and set the uploader target appropriately
    if ogc_server_settings.GEOGIG_ENABLED and upload_session.geogig is True \
            and task.target.store_type != 'coverageStore':
        target = create_geoserver_db_featurestore(
            store_type='geogig',
            store_name=upload_session.geogig_store,
            author_name=upload_session.user.username,
            author_email=upload_session.user.email)
        _log(
            'setting target datastore %s %s',
            target.name,
            target.workspace.name)
        task.set_target(target.name, target.workspace.name)
    elif ogc_server_settings.datastore_db and task.target.store_type != 'coverageStore':
        target = create_geoserver_db_featurestore(
            # store_name=ogc_server_settings.DATASTORE,
            store_name=ogc_server_settings.datastore_db['NAME']
        )
        _log(
            'setting target datastore %s %s',
            target.name,
            target.workspace.name)
        task.set_target(target.name, target.workspace.name)
    else:
        target = task.target

    if upload_session.update_mode:
        _log('setting updateMode to %s', upload_session.update_mode)
        task.set_update_mode(upload_session.update_mode)

    _log('running import session')
    # run async if using a database
    if not import_execution_requested:
        import_session.commit(async)

    # @todo check status of import session - it may fail, but due to protocol,
    # this will not be reported during the commit
    return target


def progress_redirect(step, upload_id):
    return json_response(dict(
        success=True,
        id=upload_id,
        redirect_to=reverse('data_upload', args=[step]) + "?id=%s" % upload_id,
        progress=reverse('data_upload_progress') + "?id=%s" % upload_id
    ))


def run_response(req, upload_session):
    run_import(upload_session)

    if _ASYNC_UPLOAD:
        next = get_next_step(upload_session)
        return progress_redirect(next, upload_session.import_session.id)

    return next_step_response(req, upload_session)


"""
    GeoServer Utilities
"""


def create_geoserver_db_featurestore(
        store_type=None, store_name=None,
        author_name='admin', author_email='admin@geonode.org'):
    cat = gs_catalog
    dsname = store_name or ogc_server_settings.DATASTORE
    # get or create datastore
    try:
        if store_type == 'geogig' and ogc_server_settings.GEOGIG_ENABLED:
            if store_name is not None:
                ds = cat.get_store(store_name)
            else:
                ds = cat.get_store(settings.GEOGIG_DATASTORE_NAME)
        elif dsname:
            ds = cat.get_store(dsname)
        else:
            return None
        if ds is None:
            raise FailedRequestError
    except FailedRequestError:
        if store_type == 'geogig':
            if store_name is None and hasattr(
                    settings,
                    'GEOGIG_DATASTORE_NAME'):
                store_name = settings.GEOGIG_DATASTORE_NAME
            logger.debug(
                'Creating target datastore %s' %
                store_name)

            payload = make_geogig_rest_payload(author_name, author_email)
            response = init_geogig_repo(payload, store_name)

            headers, body = response
            if 400 <= int(headers['status']) < 600:
                raise FailedRequestError(_(
                    "Error code (%s) from GeoServer: %s" %
                    (headers['status'], body)))

            ds = cat.create_datastore(store_name)
            ds.type = "GeoGig"
            ds.connection_parameters.update(
                geogig_repository=("geoserver://%s" % store_name),
                branch="master",
                create="true")
            cat.save(ds)
            ds = cat.get_store(store_name)
        else:
            logging.info(
                'Creating target datastore %s' % dsname)
            db = ogc_server_settings.datastore_db
            ds = cat.create_datastore(dsname)
            ds.connection_parameters.update(
                host=db['HOST'],
                port=db['PORT'] if isinstance(
                    db['PORT'], basestring) else str(db['PORT']) or '5432',
                database=db['NAME'],
                user=db['USER'],
                passwd=db['PASSWORD'],
                dbtype='postgis')
            cat.save(ds)
            ds = cat.get_store(dsname)
            assert ds.enabled

    return ds


"""
    GeoGig Utilities
"""


def init_geogig_repo(payload, store_name):
    username = ogc_server_settings.credentials.username
    password = ogc_server_settings.credentials.password
    url = ogc_server_settings.rest
    http = httplib2.Http(disable_ssl_certificate_validation=False)
    http.add_credentials(username, password)
    netloc = urlparse(url).netloc
    http.authorizations.append(
        httplib2.BasicAuthentication(
            (username, password),
            netloc,
            url,
            {},
            None,
            None,
            http
        ))
    rest_url = ogc_server_settings.LOCATION + "geogig/repos/" \
        + store_name + "/init.json"
    headers = {
        "Content-type": "application/json",
        "Accept": "application/json"
    }
    return http.request(rest_url, 'PUT',
                        json.dumps(payload), headers)


def make_geogig_rest_payload(author_name='admin',
                             author_email='admin@geonode.org'):
    payload = {
        "authorName": author_name,
        "authorEmail": author_email
    }
    if settings.OGC_SERVER['default']['PG_GEOGIG'] is True:
        datastore = settings.OGC_SERVER['default']['DATASTORE']
        pg_geogig_db = settings.DATABASES[datastore]
        payload["dbHost"] = pg_geogig_db['HOST']
        payload["dbPort"] = pg_geogig_db.get('PORT', '5432')
        payload["dbName"] = pg_geogig_db['NAME']
        payload["dbSchema"] = pg_geogig_db.get('SCHEMA', 'public')
        payload["dbUser"] = pg_geogig_db['USER']
        payload["dbPassword"] = pg_geogig_db['PASSWORD']
    else:
        payload["parentDirectory"] = \
            ogc_server_settings.GEOGIG_DATASTORE_DIR
    return payload


"""
 - ImageMosaics Management
"""


def _get_time_regex(spatial_files, base_file_name):
    head, tail = os.path.splitext(base_file_name)

    # 1. Look for 'timeregex.properties' files among auxillary_files
    regex = None
    format = None
    for aux in spatial_files[0].auxillary_files:
        basename = os.path.basename(aux)
        aux_head, aux_tail = os.path.splitext(basename)
        if 'timeregex' == aux_head and '.properties' == aux_tail:
            with open(aux, 'r') as timeregex_prop_file:
                rr = timeregex_prop_file.read()
                if rr and rr.split(","):
                    rrff = rr.split(",")
                    regex = rrff[0].split("=")[1]
                    if len(rrff) > 1:
                        for rf in rrff:
                            if 'format' in rf:
                                format = rf.split("=")[1]
                break
    if regex:
        time_regexp = re.compile(regex)
        if time_regexp.match(head):
            time_tokens = time_regexp.match(head).groups()
            if time_tokens:
                return regex, format
    return None, None


def import_imagemosaic_granules(
        spatial_files,
        append_to_mosaic_opts,
        append_to_mosaic_name,
        mosaic_time_regex,
        mosaic_time_value,
        time_presentation,
        time_presentation_res,
        time_presentation_default_value,
        time_presentation_reference_value):

    # The very first step is to rename the granule by adding the selected regex
    #  matching value to the filename.

    f = spatial_files[0].base_file
    dirname = os.path.dirname(f)
    basename = os.path.basename(f)
    head, tail = os.path.splitext(basename)

    if not mosaic_time_regex:
        mosaic_time_regex, mosaic_time_format = _get_time_regex(spatial_files, basename)

    # 0. A Time Regex is mandartory to validate the files
    if not mosaic_time_regex:
        raise UploadException(_("Could not find any valid Time Regex for the Mosaic files."))

    for spatial_file in spatial_files:
        f = spatial_file.base_file
        basename = os.path.basename(f)
        head, tail = os.path.splitext(basename)
        regexp = re.compile(mosaic_time_regex)
        if regexp.match(head).groups():
            mosaic_time_value = regexp.match(head).groups()[0]
            head = head.replace(regexp.match(head).groups()[0], '{mosaic_time_value}')
        if mosaic_time_value:
            dst_file = os.path.join(
                dirname,
                head.replace('{mosaic_time_value}', mosaic_time_value) + tail)
            os.rename(f, dst_file)
            spatial_file.base_file = dst_file

    # We use the GeoServer REST APIs in order to create the ImageMosaic
    #  and later add the granule through the GeoServer Importer.
    head = head.replace('{mosaic_time_value}', '')
    head = re.sub('^[^a-zA-z]*|[^a-zA-Z]*$', '', head)

    # 1. Create a zip file containing the ImageMosaic .properties files
    # 1a. Let's check and prepare the DB based DataStore
    cat = gs_catalog
    workspace = cat.get_workspace(settings.DEFAULT_WORKSPACE)
    db = ogc_server_settings.datastore_db
    db_engine = 'postgis' if \
        'postgis' in db['ENGINE'] else db['ENGINE']

    if not db_engine == 'postgis':
        raise UploadException(_("Unsupported DataBase for Mosaics!"))

    # dsname = ogc_server_settings.DATASTORE
    dsname = db['NAME']

    ds_exists = False
    try:
        ds = get_store(cat, dsname, workspace=workspace)
        ds_exists = (ds is not None)
    except FailedRequestError:
        ds = cat.create_datastore(dsname, workspace=workspace)
        db = ogc_server_settings.datastore_db
        db_engine = 'postgis' if \
            'postgis' in db['ENGINE'] else db['ENGINE']
        ds.connection_parameters.update(
            {'validate connections': 'true',
             'max connections': '10',
             'min connections': '1',
             'fetch size': '1000',
             'host': db['HOST'],
             'port': db['PORT'] if isinstance(
                 db['PORT'], basestring) else str(db['PORT']) or '5432',
             'database': db['NAME'],
             'user': db['USER'],
             'passwd': db['PASSWORD'],
             'dbtype': db_engine}
        )
        cat.save(ds)
        ds = get_store(cat, dsname, workspace=workspace)
        ds_exists = (ds is not None)

    if not ds_exists:
        raise UploadException(_("Unsupported DataBase for Mosaics!"))

    context = {
        "abs_path_flag": "True",
        "time_attr": "time",
        "aux_metadata_flag": "False",
        "mosaic_time_regex": mosaic_time_regex,
        "db_host": db['HOST'],
        "db_port": db['PORT'],
        "db_name": db['NAME'],
        "db_user": db['USER'],
        "db_password": db['PASSWORD'],
        "db_conn_timeout": db['CONN_TOUT'] if 'CONN_TOUT' in db else "10",
        "db_conn_min": db['CONN_MIN'] if 'CONN_MIN' in db else "1",
        "db_conn_max": db['CONN_MAX'] if 'CONN_MAX' in db else "5",
        "db_conn_validate": db['CONN_VALIDATE'] if 'CONN_VALIDATE' in db else "true",
    }

    if mosaic_time_regex:
        indexer_template = """AbsolutePath={abs_path_flag}
TimeAttribute={time_attr}
Schema= the_geom:Polygon,location:String,{time_attr}:java.util.Date
PropertyCollectors=TimestampFileNameExtractorSPI[timeregex]({time_attr})
CheckAuxiliaryMetadata={aux_metadata_flag}
SuggestedSPI=it.geosolutions.imageioimpl.plugins.tiff.TIFFImageReaderSpi"""

        timeregex_template = """regex=(?<=_)({mosaic_time_regex})"""

        if not os.path.exists(dirname + '/timeregex.properties'):
            with open(dirname + '/timeregex.properties', 'w') as timeregex_prop_file:
                timeregex_prop_file.write(timeregex_template.format(**context))
    else:
        indexer_template = """AbsolutePath={abs_path_flag}
Schema= the_geom:Polygon,location:String,{time_attr}
CheckAuxiliaryMetadata={aux_metadata_flag}
SuggestedSPI=it.geosolutions.imageioimpl.plugins.tiff.TIFFImageReaderSpi"""

    datastore_template = """SPI=org.geotools.data.postgis.PostgisNGDataStoreFactory
host={db_host}
port={db_port}
database={db_name}
user={db_user}
passwd={db_password}
Loose\ bbox=true
Estimated\ extends=false
validate\ connections={db_conn_validate}
Connection\ timeout={db_conn_timeout}
min\ connections={db_conn_min}
max\ connections={db_conn_max}"""

    if not os.path.exists(dirname + '/indexer.properties'):
        with open(dirname + '/indexer.properties', 'w') as indexer_prop_file:
            indexer_prop_file.write(indexer_template.format(**context))

    if not os.path.exists(dirname + '/datastore.properties'):
        with open(dirname + '/datastore.properties', 'w') as datastore_prop_file:
            datastore_prop_file.write(datastore_template.format(**context))

    files_to_upload = []
    if not append_to_mosaic_opts and spatial_files:
        z = zipfile.ZipFile(dirname + '/' + head + '.zip', "w")
        for spatial_file in spatial_files:
            f = spatial_file.base_file
            dst_basename = os.path.basename(f)
            dst_head, dst_tail = os.path.splitext(dst_basename)
            if not files_to_upload:
                # Let's import only the first granule
                z.write(spatial_file.base_file, arcname=dst_head + dst_tail)
            files_to_upload.append(spatial_file.base_file)
        if os.path.exists(dirname + '/indexer.properties'):
            z.write(dirname + '/indexer.properties', arcname='indexer.properties')
        if os.path.exists(dirname + '/datastore.properties'):
            z.write(
                dirname +
                '/datastore.properties',
                arcname='datastore.properties')
        if mosaic_time_regex:
            z.write(
                dirname + '/timeregex.properties',
                arcname='timeregex.properties')
        z.close()

        # 2. Send a "create ImageMosaic" request to GeoServer through gs_config
        cat._cache.clear()
        # - name = name of the ImageMosaic (equal to the base_name)
        # - data = abs path to the zip file
        # - configure = parameter allows for future configuration after harvesting
        name = head
        data = open(dirname + '/' + head + '.zip', 'rb')
        try:
            cat.create_imagemosaic(name, data)
        except ConflictingDataError:
            # Trying to append granules to an existing mosaic
            pass

        # configure time as LIST
        if mosaic_time_regex:
            set_time_dimension(
                cat,
                name,
                workspace,
                time_presentation,
                time_presentation_res,
                time_presentation_default_value,
                time_presentation_reference_value)

        # - since GeoNode will upload the first granule again through the Importer, we need to /
        #   delete the one created by the gs_config
        # mosaic_delete_first_granule(cat, name)
        if len(spatial_files) > 1:
            spatial_files = spatial_files[0]
        return head, files_to_upload
    else:
        cat._cache.clear()
        cat.reset()
        # cat.reload()
        return append_to_mosaic_name, files_to_upload
