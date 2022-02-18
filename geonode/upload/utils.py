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
import shutil
import logging
import zipfile
import tempfile
import traceback

from osgeo import ogr
from lxml import etree
from itertools import islice
from defusedxml import lxml as dlxml

from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _

from geonode.utils import json_response as do_json_response, unzip_file
from geonode.geoserver.helpers import (
    gs_uploader,
    ogc_server_settings,
    create_geoserver_db_featurestore)  # mosaic_delete_first_granule
from geonode.base.models import HierarchicalKeyword, ThesaurusKeyword
ogr.UseExceptions()

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


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


def error_response(req, exception=None, errors=None, force_ajax=True):
    if exception:
        logger.exception(f'Unexpected error in upload step: {exception}')
    else:
        logger.error(f'Upload error response: {errors}')
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
        context={'error_msg': f'Unexpected error : {exception}'})


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

    if next == 'check':
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

    if next == 'time':
        store_type = import_session.tasks[0].target.store_type
        layer = import_session.tasks[0].layer
        (has_time_dim, layer_values) = layer_eligible_for_time_dimension(
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
    if next == 'run':
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
                          'upload/layer_upload_error.html', context={'error_msg': str(e)})
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
    tempdir_was_created = False
    if not tempdir or not os.path.exists(tempdir):
        tempdir = tempfile.mkdtemp(dir=settings.STATIC_ROOT)
        tempdir_was_created = True
    try:
        if not os.path.isfile(absolute_base_file):
            tmp_files = [f for f in os.listdir(tempdir) if os.path.isfile(os.path.join(tempdir, f))]
            for f in tmp_files:
                if zipfile.is_zipfile(os.path.join(tempdir, f)):
                    absolute_base_file = unzip_file(os.path.join(tempdir, f), '.shp', tempdir=tempdir)
                    absolute_base_file = os.path.join(tempdir,
                                                      absolute_base_file)
        elif zipfile.is_zipfile(absolute_base_file):
            absolute_base_file = unzip_file(absolute_base_file,
                                            '.shp', tempdir=tempdir)
            absolute_base_file = os.path.join(tempdir,
                                              absolute_base_file)
        if os.path.exists(absolute_base_file):
            return absolute_base_file
        else:
            raise Exception(_(f'File does not exist: {absolute_base_file}'))
    finally:
        if tempdir_was_created:
            # Get rid if temporary files that have been uploaded via Upload form
            try:
                logger.debug(f"... Cleaning up the temporary folders {tempdir}")
                shutil.rmtree(tempdir)
            except Exception as e:
                logger.warning(e)


def _get_layer_values(layer, upload_session, expand=0):
    layer_values = []
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
                    layer_values.append(feat_values)
        except Exception as e:
            logger.exception(e)
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


def run_import(upload_session, async_upload=_ASYNC_UPLOAD):
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
            raise Exception(_(f'unknown item state: {task.state}'))
    elif import_session.state == 'PENDING' and task.target.store_type == 'coverageStore':
        if task.state == 'READY':
            import_session.commit(async_upload)
            import_execution_requested = True
        if task.state == 'ERROR':
            progress = task.get_progress()
            raise Exception(_(f"error during import: {progress.get('message')}"))

    # if a target datastore is configured, ensure the datastore exists
    # in geoserver and set the uploader target appropriately
    if ogc_server_settings.datastore_db and task.target.store_type != 'coverageStore':
        target = create_geoserver_db_featurestore(
            # store_name=ogc_server_settings.DATASTORE,
            store_name=ogc_server_settings.datastore_db['NAME'],
            workspace=settings.DEFAULT_WORKSPACE
        )
        _log(
            f'setting target datastore {target.name} {target.workspace.name}')
        task.set_target(target.name, target.workspace.name)
    else:
        target = task.target

    if upload_session.update_mode:
        _log(f'setting updateMode to {upload_session.update_mode}')
        task.set_update_mode(upload_session.update_mode)

    _log('running import session')
    # run async if using a database
    if not import_execution_requested:
        import_session.commit(async_upload)

    # @todo check status of import session - it may fail, but due to protocol,
    # this will not be reported during the commit
    return target


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


"""
 - ImageMosaics Management
"""


class KeywordHandler:
    '''
    Object needed to handle the keywords coming from the XML
    The expected input are:
     - instance (Layer/Document/Map): instance of any object inherited from ResourceBase.
     - keywords (list(dict)): Is required to analyze the keywords to find if some thesaurus is available.
    '''

    def __init__(self, instance, keywords):
        self.instance = instance
        self.keywords = keywords

    def set_keywords(self):
        '''
        Method with the responsible to set the keywords (free and thesaurus) to the object.
        At return there is always a call to final_step to let it hookable.
        '''
        keywords, tkeyword = self.handle_metadata_keywords()
        self._set_free_keyword(keywords)
        self._set_tkeyword(tkeyword)
        return self.instance

    def handle_metadata_keywords(self):
        '''
        Method the extract the keyword from the dict.
        If the keyword are passed, try to extract them from the dict
        by splitting free-keyword from the thesaurus
        '''
        fkeyword = []
        tkeyword = []
        if len(self.keywords) > 0:
            for dkey in self.keywords:
                if isinstance(dkey, HierarchicalKeyword):
                    fkeyword += [dkey.name]
                    continue
                if dkey['type'] == 'place':
                    continue
                thesaurus = dkey['thesaurus']
                if thesaurus['date'] or thesaurus['datetype'] or thesaurus['title']:
                    for k in dkey['keywords']:
                        tavailable = self.is_thesaurus_available(thesaurus, k)
                        if tavailable.exists():
                            tkeyword += [tavailable.first()]
                        else:
                            fkeyword += [k]
                else:
                    fkeyword += dkey['keywords']
            return fkeyword, tkeyword
        return self.keywords, []

    @staticmethod
    def is_thesaurus_available(thesaurus, keyword):
        is_available = ThesaurusKeyword.objects.filter(alt_label=keyword).filter(thesaurus__title=thesaurus['title'])
        return is_available

    def _set_free_keyword(self, keywords):
        if len(keywords) > 0:
            if not self.instance.keywords:
                self.instance.keywords = keywords
            else:
                self.instance.keywords.add(*keywords)
        return keywords

    def _set_tkeyword(self, tkeyword):
        if len(tkeyword) > 0:
            if not self.instance.tkeywords:
                self.instance.tkeywords = tkeyword
            else:
                self.instance.tkeywords.add(*tkeyword)
        return [t.alt_label for t in tkeyword]


def metadata_storers(layer, custom={}):
    from django.utils.module_loading import import_string
    available_storers = (
        settings.METADATA_STORERS
        if hasattr(settings, "METADATA_STORERS")
        else []
    )
    for storer_path in available_storers:
        storer = import_string(storer_path)
        storer(layer, custom)
    return layer
