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
import re
import os
import json
import logging
import zipfile
import traceback

from osgeo import ogr
from lxml import etree
from itertools import islice
from owslib.etree import etree as dlxml

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import filesizeformat

from geoserver.catalog import FailedRequestError, ConflictingDataError

from geonode.upload.api.exceptions import FileUploadLimitException, GeneralUploadException, UploadParallelismLimitException
from geonode.upload.models import Upload, UploadSizeLimit, UploadParallelismLimit
from geonode.utils import json_response as do_json_response, unzip_file, mkdtemp
from geonode.geoserver.helpers import (
    gs_catalog,
    gs_uploader,
    ogc_server_settings,
    get_store,
    set_time_dimension)  # mosaic_delete_first_granule

ogr.UseExceptions()

logger = logging.getLogger(__name__)


def _log(msg, *args, level='error'):
    # this logger is used also for debug purpose with error level
    getattr(logger, level)(msg, *args)


iso8601 = re.compile(r'^(?P<full>((?P<year>\d{4})([/-]?(?P<mon>(0[1-9])|(1[012]))' +
                     r'([/-]?(?P<mday>(0[1-9])|([12]\d)|(3[01])))?)?(?:[ T]?(?P<hour>([01][0-9])' +
                     r'|(?:2[0123]))(\:?(?P<min>[0-5][0-9])(\:?(?P<sec>[0-5][0-9]([\,\.]\d{1,10})?))?)' +
                     r'?(?:Z|([\-+](?:([01][0-9])|(?:2[0123]))(\:?(?:[0-5][0-9]))?))?)?))$').match

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

_ASYNC_UPLOAD = (ogc_server_settings and ogc_server_settings.DATASTORE is not None and len(ogc_server_settings.DATASTORE) > 0)

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


class JSONResponse(HttpResponse):

    """JSON response class."""

    def __init__(self,
                 obj='',
                 json_opts=None,
                 content_type="application/json", *args, **kwargs):

        if json_opts is None:
            json_opts = {}
        content = json.dumps(obj, **json_opts)
        super().__init__(
            content, content_type, *args, **kwargs)


def json_response(*args, **kw):
    # if 'exception' in kw:
    #     logger.warn(traceback.format_exc(kw['exception']))
    return do_json_response(*args, **kw)


def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )


def json_loads_byteified(json_text, charset):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, str):
        return data
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.items()
        }
    # if it's anything else, return it in its original form
    return data


def get_kml_doc(kml_bytes):
    """Parse and return an etree element with the kml file's content"""
    kml_doc = dlxml.fromstring(
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
    'tif': ('srs', 'run', 'final'),
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

_latitude_names = {'latitude', 'lat'}
_longitude_names = {'longitude', 'lon', 'lng', 'long'}


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


def get_max_amount_of_steps():
    # We add 1 here to count the save step (implied as first step)
    return max([len(page) for page in _pages.values()]) + 1


def get_next_step(upload_session, offset=1):
    assert upload_session.upload_type is not None

    if upload_session.completed_step == 'error':
        return 'error'

    try:
        pages = _pages[upload_session.upload_type]
    except KeyError as e:
        raise Exception(_(f'Unsupported file type: {e.message}'))
    index = -1
    if upload_session.completed_step and upload_session.completed_step != 'save':
        index = pages.index(upload_session.completed_step)
    return pages[max(min(len(pages) - 1, index + offset), 0)]


def get_previous_step(upload_session, post_to):
    assert upload_session.upload_type is not None

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
    _force_ajax = '&force_ajax=true' if req and force_ajax and 'force_ajax' not in req.GET else ''
    if not upload_session:
        return json_response(
            {
                'status': 'error',
                'success': False,
                'id': None,
                'error_msg': 'No Upload Session provided.',
            }
        )

    import_session = upload_session.import_session
    # if the current step is the view POST for this step, advance one
    if req and req.method == 'POST':
        if upload_session.completed_step:
            _advance_step(req, upload_session)
        else:
            upload_session.completed_step = 'save'

    next = get_next_step(upload_session)

    if next == 'error':
        return json_response(
            {
                'status': 'error',
                'success': False,
                'id': import_session.id,
                'error_msg': str(upload_session.error_msg),
            }
        )

    if next == 'check' and import_session.tasks:
        store_type = import_session.tasks[0].target.store_type
        if store_type == 'coverageStore' or _force_ajax:
            # @TODO we skip time steps for coverages currently
            upload_session.completed_step = 'check'
            return next_step_response(req, upload_session, force_ajax=True)
        if force_ajax:
            url = f"{reverse('data_upload')}?id={import_session.id}"
            return json_response(
                {
                    'url': url,
                    'status': 'incomplete',
                    'success': True,
                    'id': import_session.id,
                    'redirect_to': f"{settings.SITEURL}upload/check?id={import_session.id}{_force_ajax}",
                }
            )

    if next == 'time' and import_session.tasks:
        store_type = import_session.tasks[0].target.store_type
        layer = import_session.tasks[0].layer
        (has_time_dim, dataset_values) = dataset_eligible_for_time_dimension(
            req,
            layer,
            upload_session=upload_session)
        if store_type == 'coverageStore' or not has_time_dim:
            # @TODO we skip time steps for coverages currently
            upload_session.completed_step = 'time'
            return next_step_response(req, upload_session, False)
        if upload_session.time is None or not upload_session.time:
            upload_session.completed_step = 'time'
        if force_ajax:
            url = f"{reverse('data_upload')}?id={import_session.id}"
            return json_response(
                {
                    'url': url,
                    'status': 'incomplete',
                    'required_input': has_time_dim,
                    'success': True,
                    'id': import_session.id,
                    'redirect_to': f"{settings.SITEURL}upload/time?id={import_session.id}{_force_ajax}",
                }
            )
        else:
            return next_step_response(req, upload_session, force_ajax)

    if next == 'mosaic' and force_ajax:
        url = f"{reverse('data_upload')}?id={import_session.id}"
        return json_response(
            {
                'url': url,
                'status': 'incomplete',
                'required_input': len(_force_ajax) == 0,
                'success': True,
                'id': import_session.id,
                'redirect_to': f"{settings.SITEURL}upload/mosaic?id={import_session.id}{_force_ajax}",
            }
        )

    if next == 'srs' and force_ajax:
        url = f"{reverse('data_upload')}?id={import_session.id}"
        return json_response(
            {
                'url': url,
                'status': 'incomplete',
                'required_input': len(_force_ajax) == 0,
                'success': True,
                'id': import_session.id,
                'redirect_to': f"{settings.SITEURL}upload/srs?id={import_session.id}{_force_ajax}",
            }
        )

    if next == 'csv' and force_ajax:
        url = f"{reverse('data_upload')}?id={import_session.id}"
        return json_response(
            {
                'url': url,
                'status': 'incomplete',
                'required_input': len(_force_ajax) == 0,
                'success': True,
                'id': import_session.id,
                'redirect_to': f"{settings.SITEURL}upload/csv?id={import_session.id}{_force_ajax}",
            }
        )

    # @todo this is not handled cleanly - run is not a real step in that it
    # has no corresponding view served by the 'view' function.
    if next == 'run' and import_session.tasks:
        upload_session.completed_step = next
        if (_ASYNC_UPLOAD and not req) or (req and req.is_ajax()):
            return run_response(req, upload_session)
        else:
            # on sync we want to run the import and advance to the next step
            run_import(upload_session, async_upload=False)
            return next_step_response(req, upload_session,
                                      force_ajax=force_ajax)
    session_id = None
    if req and 'id' in req.GET:
        session_id = f"?id={req.GET['id']}"
    elif import_session and import_session.id:
        session_id = f"?id={import_session.id}"

    if req and req.is_ajax() or force_ajax:
        content_type = 'text/html' if req and not req.is_ajax() else None
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
    return any([_l in colname.lower() for _l in _latitude_names])


def is_longitude(colname):
    return any([_l in colname.lower() for _l in _longitude_names])


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
            invalid = [a for a in layer.attributes if str(a.name).find(' ') >= 0]
            if invalid:
                att_list = f"<pre>{'. '.join([a.name for a in invalid])}</pre>"
                msg = f"Attributes with spaces are not supported : {att_list}"
                upload_session.completed_step = 'error'
                upload_session.error_msg = msg
            return layer
        except Exception as e:
            return render(request,
                          'upload/dataset_upload_error.html', context={'error_msg': str(e)})
    elif store_type == 'coverageStore':
        return True


def _get_time_dimensions(layer, upload_session, values=None):
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
        return any([_kw in b.lower() for _kw in date_time_keywords])

    att_list = []
    try:
        dataset_values = values or _get_dataset_values(layer, upload_session, expand=1)
        if layer and dataset_values:
            ft = dataset_values[0]
            attributes = [{'name': k, 'binding': ft[k]['binding'] or 0} for k in ft.keys()]
            for a in attributes:
                if (('Integer' in a['binding'] or 'Long' in a['binding']) and 'id' != a['name'].lower()) \
                        and filter_name(a['name'].lower()):
                    if dataset_values:
                        for feat in dataset_values:
                            if iso8601(str(feat.get(a['name'])['value'])):
                                if a not in att_list:
                                    att_list.append(a)
                elif 'Date' in a['binding']:
                    att_list.append(a)
                elif 'String' in a['binding'] \
                        and filter_name(a['name'].lower()):
                    if dataset_values:
                        for feat in dataset_values:
                            if feat.get(a['name'])['value'] and \
                                    iso8601(str(feat.get(a['name'])['value'])):
                                if a not in att_list:
                                    att_list.append(a)
                    else:
                        pass
    except Exception:
        traceback.print_exc()
        return None
    return att_list


def _fixup_base_file(absolute_base_file, tempdir=None):
    if not tempdir or not os.path.exists(tempdir):
        tempdir = mkdtemp()
    if not os.path.isfile(absolute_base_file):
        tmp_files = [f for f in os.listdir(tempdir) if os.path.isfile(os.path.join(tempdir, f))]
        for f in tmp_files:
            if zipfile.is_zipfile(os.path.join(tempdir, f)):
                absolute_base_file = unzip_file(os.path.join(tempdir, f), '.shp', tempdir=tempdir)
                absolute_base_file = os.path.join(tempdir, absolute_base_file)
    elif zipfile.is_zipfile(absolute_base_file):
        absolute_base_file = unzip_file(absolute_base_file, '.shp', tempdir=tempdir)
        absolute_base_file = os.path.join(tempdir, absolute_base_file)
    if os.path.exists(absolute_base_file):
        return absolute_base_file
    else:
        raise Exception(_(f'File does not exist: {absolute_base_file}'))


def _get_dataset_values(layer, upload_session, expand=0):
    dataset_values = []
    if upload_session:
        try:
            absolute_base_file = _fixup_base_file(
                upload_session.base_file[0].base_file,
                upload_session.tempdir)

            inDataSource = ogr.Open(absolute_base_file)
            lyr = inDataSource.GetLayer(str(layer.name))
            limit = 10
            for feat in islice(lyr, 0, limit):
                feat_values = json_loads_byteified(
                    feat.ExportToJson(),
                    upload_session.charset).get('properties')
                if feat_values:
                    for k in feat_values.keys():
                        type_code = feat.GetFieldDefnRef(k).GetType()
                        binding = feat.GetFieldDefnRef(k).GetFieldTypeName(type_code)
                        feat_value = feat_values[k] if str(feat_values[k]) != 'None' else 0
                        if expand > 0:
                            ff = {'value': feat_value, 'binding': binding}
                            feat_values[k] = ff
                        else:
                            feat_values[k] = feat_value
                    dataset_values.append(feat_values)
        except Exception as e:
            logger.exception(e)
    return dataset_values


def dataset_eligible_for_time_dimension(
        request, layer, values=None, upload_session=None):
    _is_eligible = False
    dataset_values = values or _get_dataset_values(layer, upload_session, expand=0)
    att_list = _get_time_dimensions(layer, upload_session)
    _is_eligible = att_list or False
    if upload_session and _is_eligible:
        upload_session.time = True
    return (_is_eligible, dataset_values)


def run_import(upload_session, async_upload=_ASYNC_UPLOAD):
    """Run the import, possibly asynchronously.

    Returns the target datastore.
    """
    # run_import can raise an exception which callers should handle
    import_session = upload_session.import_session
    import_session = gs_uploader.get_session(import_session.id)
    if import_session.tasks:
        task = import_session.tasks[0]
        import_execution_requested = False
        if import_session.state == 'INCOMPLETE':
            if task.state != 'ERROR':
                raise Exception(_(f'unknown item state: {task.state}'))
        elif import_session.state == 'PENDING' and task.target.store_type == 'coverageStore':
            if task.state == 'READY':
                _log(f"run_import: async_upload[{async_upload}] Commit Import Session {import_session.id} - target: / - alternate: {task.get_target_layer_name()}")
                import_session.commit(async_upload)
                import_execution_requested = True
            if task.state == 'ERROR':
                progress = task.get_progress()
                raise Exception(_(f"error during import: {progress.get('message')}"))

        # if a target datastore is configured, ensure the datastore exists
        # in geoserver and set the uploader target appropriately

        _log(f'run_import: Running Import Session {import_session.id}')
        # run async if using a database
        if not import_execution_requested:
            import_session.commit(async_upload)

        # @todo check status of import session - it may fail, but due to protocol,
        # this will not be reported during the commit
        import_session = import_session.reload()
        return import_session.tasks[0].target
    return None


def progress_redirect(step, upload_id):
    return json_response(dict(
        success=True,
        id=upload_id,
        redirect_to=f"{reverse('data_upload', args=[step])}?id={upload_id}",
        progress=f"{reverse('data_upload_progress')}?id={upload_id}"
    ))


def run_response(req, upload_session):
    run_import(upload_session)

    if _ASYNC_UPLOAD:
        next = get_next_step(upload_session)
        return progress_redirect(next, upload_session.import_session.id)

    return next_step_response(req, upload_session)


def get_max_upload_size(slug):
    try:
        max_size = UploadSizeLimit.objects.get(slug=slug).max_size
    except ObjectDoesNotExist:
        max_size = getattr(settings, "DEFAULT_MAX_UPLOAD_SIZE", 104857600)
    return max_size


def get_max_upload_parallelism_limit(slug):
    try:
        max_number = UploadParallelismLimit.objects.get(slug=slug).max_number
    except ObjectDoesNotExist:
        max_number = getattr(settings, "DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER", 5)
    return max_number


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
            with open(aux) as timeregex_prop_file:
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
        raise GeneralUploadException(detail=_("Could not find any valid Time Regex for the Mosaic files."))

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
    head = re.sub('^[^a-zA-Z]*|[^a-zA-Z]*$', '', head)

    # 1. Create a zip file containing the ImageMosaic .properties files
    # 1a. Let's check and prepare the DB based DataStore
    cat = gs_catalog
    workspace = cat.get_workspace(settings.DEFAULT_WORKSPACE)
    db = ogc_server_settings.datastore_db
    db_engine = 'postgis' if \
        'postgis' in db['ENGINE'] else db['ENGINE']

    if not db_engine == 'postgis':
        raise GeneralUploadException(detail=_("Unsupported DataBase for Mosaics!"))

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
                 db['PORT'], str) else str(db['PORT']) or '5432',
             'database': db['NAME'],
             'user': db['USER'],
             'passwd': db['PASSWORD'],
             'dbtype': db_engine}
        )
        cat.save(ds)
        ds = get_store(cat, dsname, workspace=workspace)
        ds_exists = (ds is not None)

    if not ds_exists:
        raise GeneralUploadException(detail=_("Unsupported DataBase for Mosaics!"))

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

    indexer_template = """AbsolutePath={abs_path_flag}
Schema= the_geom:Polygon,location:String,{time_attr}
CheckAuxiliaryMetadata={aux_metadata_flag}
SuggestedSPI=it.geosolutions.imageioimpl.plugins.tiff.TIFFImageReaderSpi"""
    if mosaic_time_regex:
        indexer_template = """AbsolutePath={abs_path_flag}
TimeAttribute={time_attr}
Schema= the_geom:Polygon,location:String,{time_attr}:java.util.Date
PropertyCollectors=TimestampFileNameExtractorSPI[timeregex]({time_attr})
CheckAuxiliaryMetadata={aux_metadata_flag}
SuggestedSPI=it.geosolutions.imageioimpl.plugins.tiff.TIFFImageReaderSpi"""

        timeregex_template = """regex=(?<=_)({mosaic_time_regex})"""

        if not os.path.exists(f"{dirname}/timeregex.properties"):
            with open(f"{dirname}/timeregex.properties", 'w') as timeregex_prop_file:
                timeregex_prop_file.write(timeregex_template.format(**context))

    datastore_template = r"""SPI=org.geotools.data.postgis.PostgisNGDataStoreFactory
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

    if not os.path.exists(f"{dirname}/indexer.properties"):
        with open(f"{dirname}/indexer.properties", 'w') as indexer_prop_file:
            indexer_prop_file.write(indexer_template.format(**context))

    if not os.path.exists(f"{dirname}/datastore.properties"):
        with open(f"{dirname}/datastore.properties", 'w') as datastore_prop_file:
            datastore_prop_file.write(datastore_template.format(**context))

    files_to_upload = []
    if not append_to_mosaic_opts and spatial_files:
        z = zipfile.ZipFile(f"{dirname}/{head}.zip", "w", allowZip64=True)
        for spatial_file in spatial_files:
            f = spatial_file.base_file
            dst_basename = os.path.basename(f)
            dst_head, dst_tail = os.path.splitext(dst_basename)
            if not files_to_upload:
                # Let's import only the first granule
                z.write(spatial_file.base_file, arcname=dst_head + dst_tail)
            files_to_upload.append(spatial_file.base_file)
        if os.path.exists(f"{dirname}/indexer.properties"):
            z.write(f"{dirname}/indexer.properties", arcname='indexer.properties')
        if os.path.exists(f"{dirname}/datastore.properties"):
            z.write(
                f"{dirname}/datastore.properties",
                arcname='datastore.properties')
        if mosaic_time_regex:
            z.write(
                f"{dirname}/timeregex.properties",
                arcname='timeregex.properties')
        z.close()

        # 2. Send a "create ImageMosaic" request to GeoServer through gs_config
        # - name = name of the ImageMosaic (equal to the base_name)
        # - data = abs path to the zip file
        # - configure = parameter allows for future configuration after harvesting
        name = head

        with open(f"{dirname}/{head}.zip", 'rb') as data:
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


class UploadLimitValidator:
    def __init__(self, user) -> None:
        self.user = user

    def validate_parallelism_limit_per_user(self):
        max_parallel_uploads = self._get_max_parallel_uploads()
        parallel_uploads_count = self._get_parallel_uploads_count()
        if parallel_uploads_count >= max_parallel_uploads:
            raise UploadParallelismLimitException(_(
                f"The number of active parallel uploads exceeds {max_parallel_uploads}. Wait for the pending ones to finish."
            ))

    def validate_files_sum_of_sizes(self, file_dict):
        max_size = self._get_uploads_max_size()
        total_size = self._get_uploaded_files_total_size(file_dict)
        if total_size > max_size:
            raise FileUploadLimitException(_(
                f'Total upload size exceeds {filesizeformat(max_size)}. Please try again with smaller files.'
            ))

    def _get_uploads_max_size(self):
        try:
            max_size_db_obj = UploadSizeLimit.objects.get(slug="dataset_upload_size")
        except UploadSizeLimit.DoesNotExist:
            max_size_db_obj = UploadSizeLimit.objects.create_default_limit()
        return max_size_db_obj.max_size

    def _get_uploaded_files(self):
        """Return a list with all of the uploaded files"""
        return [django_file for field_name, django_file in self.files.items()
                if field_name != "base_file"]

    def _get_uploaded_files_total_size(self, file_dict):
        """Return a list with all of the uploaded files"""
        excluded_files = ("zip_file", "shp_file", )
        _iterate_files = file_dict.data_items if hasattr(file_dict, 'data_items') else file_dict
        uploaded_files_sizes = [
            file_obj.size for field_name, file_obj in _iterate_files.items()
            if field_name not in excluded_files
        ]
        total_size = sum(uploaded_files_sizes)
        return total_size

    def _get_max_parallel_uploads(self):
        try:
            parallelism_limit = UploadParallelismLimit.objects.get(slug="default_max_parallel_uploads")
        except UploadParallelismLimit.DoesNotExist:
            parallelism_limit = UploadParallelismLimit.objects.create_default_limit()
        return parallelism_limit.max_number

    def _get_parallel_uploads_count(self):
        return Upload.objects.get_incomplete_uploads(self.user).count()
