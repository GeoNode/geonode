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

"""
Provide views for doing an upload.

The upload process may be multi step so views are all handled internally here
by the view function.

The pattern to support separation of view/logic is each step in the upload
process is suffixed with "_step". The view for that step is suffixed with
"_step_view". The goal of separation of view/logic is to support various
programmatic uses of this API. The logic steps should not accept request objects
or return response objects.

State is stored in a UploaderSession object stored in the user's session.
This needs to be made more stateful by adding a model.
"""
import gsimporter
import json
import logging
import os
import traceback

from httplib import BadStatusLine
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.html import escape
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import CreateView, DeleteView
from geonode.base.enumerations import CHARSETS
from geonode.upload import forms, upload, files
from geonode.upload.forms import LayerUploadForm, UploadFileForm
from geonode.upload.models import Upload, UploadFile
from geonode.utils import json_response as do_json_response
from geonode.geoserver.helpers import ogc_server_settings


logger = logging.getLogger(__name__)

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
    raise Exception(
        "To support the time step, you must enable the OGC_SERVER DATASTORE option")

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


def _is_async_step(upload_session):
    return _ASYNC_UPLOAD and get_next_step(upload_session, offset=2) == 'run'


def _progress_redirect(step, upload_id):
    return json_response(dict(
        success=True,
        id=upload_id,
        redirect_to=reverse('data_upload', args=[step]) + "?id=%s" % upload_id,
        progress=reverse('data_upload_progress') + "?id=%s" % upload_id
    ))


def json_response(*args, **kw):
    if 'exception' in kw:
        logger.warn(traceback.format_exc(kw['exception']))
    return do_json_response(*args, **kw)


class JSONResponse(HttpResponse):

    """JSON response class."""

    def __init__(self,
                 obj='',
                 json_opts={},
                 content_type="application/json", *args, **kwargs):

        content = json.dumps(obj, **json_opts)
        super(JSONResponse, self).__init__(content, content_type, *args, **kwargs)


def _error_response(req, exception=None, errors=None, force_ajax=True):
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
    return render_to_response(
        'upload/layer_upload_error.html',
        RequestContext(
            req,
            {
                'error_msg': 'Unexpected error : %s,' %
                exception}))


def _next_step_response(req, upload_session, force_ajax=True):
    # if the current step is the view POST for this step, advance one
    if req.method == 'POST':
        if upload_session.completed_step:
            advance_step(req, upload_session)
        else:
            upload_session.completed_step = 'save'

    next = get_next_step(upload_session)

    if next == 'time':
        # @TODO we skip time steps for coverages currently
        import_session = upload_session.import_session
        store_type = import_session.tasks[0].target.store_type
        if store_type == 'coverageStore':
            upload_session.completed_step = 'time'
            return _next_step_response(req, upload_session, force_ajax)
    if next == 'time' and (
            upload_session.time is None or not upload_session.time):
        upload_session.completed_step = 'time'
        return _next_step_response(req, upload_session, force_ajax)
    if next == 'time' and force_ajax:
        import_session = upload_session.import_session
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
        import_session = upload_session.import_session
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
        import_session = upload_session.import_session
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
        import_session = upload_session.import_session
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
            return _next_step_response(req, upload_session,
                                       force_ajax=force_ajax)
    if req.is_ajax() or force_ajax:
        content_type = 'text/html' if not req.is_ajax() else None
        return json_response(redirect_to=reverse('data_upload', args=[next]) + "?id=%s" % req.GET['id'],
                             content_type=content_type)
    # return HttpResponseRedirect(reverse('data_upload', args=[next]))


def _create_time_form(import_session, form_data):
    feature_type = import_session.tasks[0].layer

    def filter_type(b):
        return [att.name for att in feature_type.attributes if att.binding == b]

    args = dict(
        time_names=filter_type('java.util.Date'),
        text_names=filter_type('java.lang.String'),
        year_names=filter_type('java.lang.Integer') +
        filter_type('java.lang.Long') +
        filter_type('java.lang.Double')
    )
    if form_data:
        return forms.TimeForm(form_data, **args)
    return forms.TimeForm(**args)


def save_step_view(req, session):
    if req.method == 'GET':
        return render_to_response(
            'upload/layer_upload.html',
            RequestContext(
                req,
                {
                    'async_upload': _ASYNC_UPLOAD,
                    'incomplete': Upload.objects.get_incomplete_uploads(
                        req.user),
                    'charsets': CHARSETS}))

    assert session is None

    form = LayerUploadForm(req.POST, req.FILES)
    tempdir = None

    if form.is_valid():
        tempdir, base_file = form.write_files()
        logger.debug('Tempdir: {0}, basefile: {1}'.format(tempdir, base_file))
        name, ext = os.path.splitext(os.path.basename(base_file))
        logger.debug('Name: {0}, ext: {1}'.format(name, ext))
        base_file = files.scan_file(base_file)
        logger.debug(base_file)
        import_session = upload.save_step(
            req.user,
            name,
            base_file,
            overwrite=False,
            mosaic=form.cleaned_data['mosaic'],
            append_to_mosaic_opts=form.cleaned_data['append_to_mosaic_opts'],
            append_to_mosaic_name=form.cleaned_data['append_to_mosaic_name'],
            mosaic_time_regex=form.cleaned_data['mosaic_time_regex'],
            mosaic_time_value=form.cleaned_data['mosaic_time_value'],
            time_presentation=form.cleaned_data['time_presentation'],
            time_presentation_res=form.cleaned_data['time_presentation_res'],
            time_presentation_default_value=form.cleaned_data['time_presentation_default_value'],
            time_presentation_reference_value=form.cleaned_data['time_presentation_reference_value']
        )

        sld = None

        if base_file[0].sld_files:
            sld = base_file[0].sld_files[0]

        logger.info('provided sld is %s' % sld)
        # upload_type = get_upload_type(base_file)
        upload_session = upload.UploaderSession(
            tempdir=tempdir,
            base_file=base_file,
            name=name,
            import_session=import_session,
            layer_abstract=form.cleaned_data["abstract"],
            layer_title=form.cleaned_data["layer_title"],
            permissions=form.cleaned_data["permissions"],
            import_sld_file=sld,
            upload_type=base_file[0].file_type.code,
            geogig=form.cleaned_data['geogig'],
            geogig_store=form.cleaned_data['geogig_store'],
            time=form.cleaned_data['time'],
            mosaic=form.cleaned_data['mosaic'],
            append_to_mosaic_opts=form.cleaned_data['append_to_mosaic_opts'],
            append_to_mosaic_name=form.cleaned_data['append_to_mosaic_name'],
            mosaic_time_regex=form.cleaned_data['mosaic_time_regex'],
            mosaic_time_value=form.cleaned_data['mosaic_time_value'],
            user=req.user
        )
        req.session[str(upload_session.import_session.id)] = upload_session
        return _next_step_response(req, upload_session, force_ajax=True)
    else:
        errors = []
        for e in form.errors.values():
            errors.extend([escape(v) for v in e])
        return _error_response(req, errors=errors)


def data_upload_progress(req):
    """This would not be needed if geoserver REST did not require admin role
    and is an inefficient way of getting this information"""
    if 'id' in req.GET:
        upload_id = str(req.GET['id'])
        if upload_id in req.session:
            upload_obj = get_object_or_404(Upload, import_id=upload_id, user=req.user)
            upload_session = upload_obj.get_session()
        else:
            upload_session = req.session[upload_id]

        import_session = upload_session.import_session
        progress = import_session.tasks[0].get_progress()
        return json_response(progress)
    else:
        return json_response({'state': 'NONE'})


def srs_step_view(req, upload_session):
    import_session = upload_session.import_session

    form = None
    if req.method == 'POST':
        form = forms.SRSForm(req.POST)
        if form.is_valid():
            srs = form.cleaned_data['srs']
            upload.srs_step(upload_session, srs)
            return _next_step_response(req, upload_session)

    task = import_session.tasks[0]
    # CRS missing/unknown
    if task.state == 'NO_CRS':
        native_crs = task.layer.srs
        form = form or forms.SRSForm()

    if form:
        name = task.layer.name
        return render_to_response('upload/layer_upload_crs.html',
                                  RequestContext(req, {
                                      'native_crs': native_crs,
                                      'form': form,
                                      'layer_name': name
                                  }))
    # mark this completed since there is no post-back when skipping
    upload_session.completed_step = 'srs'
    return _next_step_response(req, upload_session)


latitude_names = set(['latitude', 'lat'])
longitude_names = set(['longitude', 'lon', 'lng', 'long'])


def is_latitude(colname):
    return colname.lower() in latitude_names


def is_longitude(colname):
    return colname.lower() in longitude_names


def csv_step_view(request, upload_session):
    import_session = upload_session.import_session
    attributes = import_session.tasks[0].layer.attributes

    # need to check if geometry is found
    # if so, can proceed directly to next step
    for attr in attributes:
        if attr.binding == u'com.vividsolutions.jts.geom.Point':
            upload_session.completed_step = 'csv'
            return _next_step_response(request, upload_session)

    # no geometry found, let's find all the numerical columns
    number_names = ['java.lang.Integer', 'java.lang.Double']
    point_candidates = sorted([attr.name for attr in attributes
                               if attr.binding in number_names])

    # form errors to display to user
    error = None

    lat_field = request.POST.get('lat', '')
    lng_field = request.POST.get('lng', '')

    if request.method == 'POST':
        if not lat_field or not lng_field:
            error = 'Please choose which columns contain the latitude and longitude data.'
        elif (lat_field not in point_candidates or
              lng_field not in point_candidates):
            error = 'Invalid latitude/longitude columns'
        elif lat_field == lng_field:
            error = 'You cannot select the same column for latitude and longitude data.'
        if not error:
            upload.csv_step(upload_session, lat_field, lng_field)
            return _next_step_response(request, upload_session)
    # try to guess the lat/lng fields from the candidates
    lat_candidate = None
    lng_candidate = None
    non_str_in_headers = []
    for candidate in attributes:
        if not isinstance(candidate.name, basestring):
            non_str_in_headers.append(str(candidate.name))
        if candidate.name in point_candidates:
            if is_latitude(candidate.name):
                lat_candidate = candidate.name
            elif is_longitude(candidate.name):
                lng_candidate = candidate.name
    if request.method == 'POST':
        guessed_lat_or_lng = False
        selected_lat = lat_field
        selected_lng = lng_field
    else:
        guessed_lat_or_lng = bool(lat_candidate or lng_candidate)
        selected_lat = lat_candidate
        selected_lng = lng_candidate
    present_choices = len(point_candidates) >= 2
    possible_data_problems = None
    if non_str_in_headers:
        possible_data_problems = "There are some suspicious column names in \
                                 your data. Did you provide column names in the header? \
                                 The following names look wrong: "
        possible_data_problems += ','.join(non_str_in_headers)

    context = dict(present_choices=present_choices,
                   point_candidates=point_candidates,
                   async_upload=_is_async_step(upload_session),
                   selected_lat=selected_lat,
                   selected_lng=selected_lng,
                   guessed_lat_or_lng=guessed_lat_or_lng,
                   layer_name=import_session.tasks[0].layer.name,
                   error=error,
                   possible_data_problems=possible_data_problems
                   )
    return render_to_response('upload/layer_upload_csv.html',
                              RequestContext(request, context))


def time_step_view(request, upload_session):
    import_session = upload_session.import_session

    if request.method == 'GET':
        # check for invalid attribute names
        store_type = import_session.tasks[0].target.store_type
        if store_type == 'dataStore':
            layer = import_session.tasks[0].layer
            invalid = filter(
                lambda a: str(
                    a.name).find(' ') >= 0,
                layer.attributes)
            if invalid:
                att_list = "<pre>%s</pre>" % '. '.join(
                    [a.name for a in invalid])
                msg = "Attributes with spaces are not supported : %s" % att_list
                return render_to_response(
                    'upload/layer_upload_error.html', RequestContext(request, {'error_msg': msg}))
        context = {
            'time_form': _create_time_form(import_session, None),
            'layer_name': import_session.tasks[0].layer.name,
            'async_upload': _is_async_step(upload_session)
        }
        return render_to_response('upload/layer_upload_time.html',
                                  RequestContext(request, context))
    elif request.method != 'POST':
        raise Exception()

    form = _create_time_form(import_session, request.POST)

    if not form.is_valid():
        logger.warning('Invalid upload form: %s', form.errors)
        return _error_response(request, errors=["Invalid Submission"])

    cleaned = form.cleaned_data

    start_attribute_and_type = cleaned.get('start_attribute', None)

    if start_attribute_and_type:

        def tx(type_name):

            return None if type_name is None or type_name == 'Date' \
                else 'DateFormatTransform'

        end_attribute, end_type = cleaned.get('end_attribute', (None, None))
        upload.time_step(
            upload_session,
            time_attribute=start_attribute_and_type[0],
            time_transform_type=tx(start_attribute_and_type[1]),
            time_format=cleaned.get('attribute_format', None),
            end_time_attribute=end_attribute,
            end_time_transform_type=tx(end_type),
            end_time_format=cleaned.get('end_attribute_format', None),
            presentation_strategy=cleaned['presentation_strategy'],
            precision_value=cleaned['precision_value'],
            precision_step=cleaned['precision_step'],
        )

    return _next_step_response(request, upload_session)


def run_import(upload_session, async=_ASYNC_UPLOAD):
    # run_import can raise an exception which callers should handle
    upload.run_import(upload_session, async)


def run_response(req, upload_session):
    run_import(upload_session)

    if _ASYNC_UPLOAD:
        next = get_next_step(upload_session)
        return _progress_redirect(next, upload_session.import_session.id)

    return _next_step_response(req, upload_session)


def final_step_view(req, upload_session):
    try:
        saved_layer = upload.final_step(upload_session, req.user)

    except upload.LayerNotReady:
        return json_response({'status': 'pending',
                              'success': True,
                              'id': req.GET['id'],
                              'redirect_to': '/upload/final' + "?id=%s" % req.GET['id']})

    # this response is different then all of the other views in the
    # upload as it does not return a response as a json object
    return json_response(
        {'url': saved_layer.get_absolute_url(),
         'success': True
         }
    )

_steps = {
    'save': save_step_view,
    'time': time_step_view,
    'srs': srs_step_view,
    'final': final_step_view,
    'csv': csv_step_view,
}

# note 'run' is not a "real" step, but handled as a special case
# and 'save' is the implied first step :P
_pages = {
    'shp': ('srs', 'time', 'run', 'final'),
    'tif': ('run', 'final'),
    'kml': ('run', 'final'),
    'csv': ('csv', 'time', 'run', 'final'),
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
    try:
        pages = _pages[upload_session.upload_type]
    except KeyError as e:
        raise Exception('Unsupported file type: %s' % e.message)
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


def advance_step(req, upload_session):
    upload_session.completed_step = get_next_step(upload_session)


@login_required
def view(req, step):
    """Main uploader view"""
    upload_session = None
    upload_id = req.GET.get('id', None)
    if step is None:
        if upload_id:
            # upload recovery
            upload_obj = get_object_or_404(
                Upload,
                import_id=upload_id,
                user=req.user)
            session = upload_obj.get_session()
            if session:
                req.session[upload_id] = session
                return _next_step_response(req, session)

        step = 'save'

        # delete existing session
        if upload_id and upload_id in req.session:
            del req.session[upload_id]

    else:
        if not upload_id:
            return render_to_response(
                "upload/layer_upload_invalid.html",
                RequestContext(
                    req,
                    {}))

        upload_obj = get_object_or_404(Upload, import_id=upload_id, user=req.user)
        session = upload_obj.get_session()
        if session:
            upload_session = session
        else:
            upload_session = req.session[upload_id]

    try:
        if req.method == 'GET' and upload_session:
            # set the current step to match the requested page - this
            # could happen if the form is ajax w/ progress monitoring as
            # the advance would have already happened @hacky
            upload_session.completed_step = get_previous_step(
                upload_session,
                step)

        resp = _steps[step](req, upload_session)
        # must be put back to update object in session
        if upload_session:
            if step == 'final':
                delete_session = True
                try:
                    resp_js = json.loads(resp.content)
                    delete_session = resp_js.get('status') != 'pending'
                except:
                    pass

                if delete_session:
                    # we're done with this session, wax it
                    Upload.objects.update_from_session(upload_session)
                    upload_session = None
                    del req.session[upload_id]
            else:
                req.session[upload_id] = upload_session
        elif upload_id in req.session:
            upload_session = req.session[upload_id]
        if upload_session:
            Upload.objects.update_from_session(upload_session)
        return resp
    except BadStatusLine:
        logger.exception('bad status line, geoserver down?')
        return _error_response(req, errors=[_geoserver_down_error_msg])
    except gsimporter.RequestFailed as e:
        logger.exception('request failed')
        errors = e.args
        # http bad gateway or service unavailable
        if int(errors[0]) in (502, 503):
            errors = [_geoserver_down_error_msg]
        return _error_response(req, errors=errors)
    except gsimporter.BadRequest as e:
        logger.exception('bad request')
        return _error_response(req, errors=e.args)
    except Exception as e:
        return _error_response(req, exception=e)


@login_required
def delete(req, id):
    upload = get_object_or_404(Upload, import_id=id)
    if req.user != upload.user:
        raise PermissionDenied()
    upload.delete()
    return json_response(dict(
        success=True,
    ))


class UploadFileCreateView(CreateView):
    form_class = UploadFileForm
    model = UploadFile

    def form_valid(self, form):
        self.object = form.save()
        f = self.request.FILES.get('file')
        data = [
            {
                'name': f.name,
                'url': settings.MEDIA_URL +
                "uploads/" +
                f.name.replace(
                    " ",
                    "_"),
                'thumbnail_url': settings.MEDIA_URL +
                "pictures/" +
                f.name.replace(
                    " ",
                    "_"),
                'delete_url': reverse(
                    'data_upload_remove',
                    args=[
                        self.object.id]),
                'delete_type': "DELETE"}]
        response = JSONResponse(data, {}, response_content_type(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

    def form_invalid(self, form):
        data = [{}]
        response = JSONResponse(data, {}, response_content_type(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response


def response_content_type(request):
    if "application/json" in request.META['HTTP_ACCEPT']:
        return "application/json"
    else:
        return "text/plain"


class UploadFileDeleteView(DeleteView):
    model = UploadFile

    def delete(self, request, *args, **kwargs):
        """
        This does not actually delete the file, only the database record.  But
        that is easy to implement.
        """
        self.object = self.get_object()
        self.object.delete()
        if request.is_ajax():
            response = JSONResponse(True, {}, response_content_type(self.request))
            response['Content-Disposition'] = 'inline; filename=files.json'
            return response
        else:
            return HttpResponseRedirect(reverse('data_upload_new'))
