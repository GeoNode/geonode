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
import os
import re
import json
import logging
import zipfile
import traceback
import gsimporter
import tempfile

from httplib import BadStatusLine
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.html import escape
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.generic import CreateView, DeleteView
from geonode.utils import unzip_file
from geonode.base.enumerations import CHARSETS

from .forms import (
    LayerUploadForm,
    SRSForm,
    TimeForm,
    UploadFileForm,
)
from .models import Upload, UploadFile
from .files import (get_scan_hint,
                    scan_file
)
from .utils import (
    _ALLOW_TIME_STEP,
    _SUPPORTED_CRS,
    _ASYNC_UPLOAD,
    _geoserver_down_error_msg,
    _get_time_dimensions,
    check_import_session_is_valid,
    error_response,
    is_async_step,
    is_latitude,
    is_longitude,
    JSONResponse,
    json_response,
    get_previous_step,
    layer_eligible_for_time_dimension,
    next_step_response,
)
from .upload import (save_step, srs_step, time_step, csv_step, final_step,
                     LayerNotReady, UploaderSession)

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


def data_upload_progress(req):
    """This would not be needed if geoserver REST did not require admin role
    and is an inefficient way of getting this information"""
    if 'id' in req.GET:
        upload_id = str(req.GET['id'])
        if upload_id in req.session:
            upload_obj = get_object_or_404(
                Upload, import_id=upload_id, user=req.user)
            upload_session = upload_obj.get_session()
        else:
            upload_session = req.session[upload_id]

        if upload_session:
            import_session = upload_session.import_session
            progress = import_session.tasks[0].get_progress()
            return json_response(progress)

    return json_response({'state': 'NONE'})


def _write_uploaded_files_to_disk(target_dir, files):
    result = []
    for django_file in files:
        path = os.path.join(target_dir, django_file.name)
        with open(path, 'wb') as fh:
            for chunk in django_file.chunks():
                fh.write(chunk)
        result = path
    return result


def _select_relevant_files(allowed_extensions, files):
    """Filter the input files list for relevant files only

    Relevant files are those whose extension is in the ``allowed_extensions``
    iterable.

    :param allowed_extensions: list of strings with the extensions to keep
    :param files: list of django files with the files to be filtered

    """
    result = []
    for django_file in files:
        extension = os.path.splitext(django_file.name)[-1].lower()[1:]
        if extension in allowed_extensions or get_scan_hint(allowed_extensions):
            already_selected = django_file.name in (f.name for f in result)
            if not already_selected:
                result.append(django_file)
    return result


def save_step_view(req, session):
    if req.method == 'GET':
        return render(
            req,
            'upload/layer_upload.html',
            {
                'async_upload': _ASYNC_UPLOAD,
                'incomplete': Upload.objects.get_incomplete_uploads(req.user),
                'charsets': CHARSETS
            }
        )
    form = LayerUploadForm(req.POST, req.FILES)
    if form.is_valid():
        tempdir = tempfile.mkdtemp(dir=settings.FILE_UPLOAD_TEMP_DIR)
        logger.info("valid_extensions: {}".format(form.cleaned_data["valid_extensions"]))
        relevant_files = _select_relevant_files(
            form.cleaned_data["valid_extensions"],
            req.FILES.itervalues()
        )
        logger.info("relevant_files: {}".format(relevant_files))
        _write_uploaded_files_to_disk(tempdir, relevant_files)
        base_file = os.path.join(tempdir, form.cleaned_data["base_file"].name)
        name, ext = os.path.splitext(os.path.basename(base_file))
        logger.debug('Name: {0}, ext: {1}'.format(name, ext))
        logger.debug("base_file: {}".format(base_file))
        scan_hint = get_scan_hint(form.cleaned_data["valid_extensions"])
        spatial_files = scan_file(
            base_file,
            scan_hint=scan_hint
        )
        logger.info("spatial_files: {}".format(spatial_files))
        import_session = save_step(
            req.user,
            name,
            spatial_files,
            overwrite=False,
            mosaic=form.cleaned_data['mosaic'] or scan_hint == 'zip-mosaic',
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

        if spatial_files[0].sld_files:
            sld = spatial_files[0].sld_files[0]
        if not os.path.isfile(os.path.join(tempdir, spatial_files[0].base_file)):
            tmp_files = [f for f in os.listdir(tempdir) if os.path.isfile(os.path.join(tempdir, f))]
            for f in tmp_files:
                if zipfile.is_zipfile(os.path.join(tempdir, f)):
                    unzip_file(os.path.join(tempdir, f), '.shp', tempdir=tempdir)

        _log('provided sld is %s' % sld)
        # upload_type = get_upload_type(base_file)
        upload_session = UploaderSession(
            tempdir=tempdir,
            base_file=spatial_files,
            name=name,
            import_session=import_session,
            layer_abstract=form.cleaned_data["abstract"],
            layer_title=form.cleaned_data["layer_title"],
            permissions=form.cleaned_data["permissions"],
            import_sld_file=sld,
            upload_type=spatial_files[0].file_type.code,
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
        _log('saved session : %s',
             req.session[str(upload_session.import_session.id)])
        return next_step_response(req, upload_session, force_ajax=True)
    else:
        errors = []
        for e in form.errors.values():
            errors.extend([escape(v) for v in e])
        return error_response(req, errors=errors)


def srs_step_view(request, upload_session):
    import_session = upload_session.import_session
    assert import_session is not None

    # form errors to display to user
    error = None
    native_crs = None
    _crs_already_configured = False

    form = SRSForm()
    for task in import_session.tasks:
        # CRS missing/unknown
        if task.state == 'NO_CRS':
            native_crs = task.layer.srs
        else:
            _crs_already_configured = True
        if form:
            name = task.layer.name

    if request.method == 'GET':
        # layer = check_import_session_is_valid(
        #     request, upload_session, import_session)

        if not _crs_already_configured:
            context = dict(form=form,
                           supported_crs=_SUPPORTED_CRS,
                           async_upload=False,
                           native_crs=native_crs or None,
                           layer_name=name,
                           error=error
                           )
            return render(request, 'upload/layer_upload_crs.html', context=context)
        else:
            upload_session.completed_step = 'srs'
            return next_step_response(request, upload_session)
    elif request.method != 'POST':
        raise Exception()

    source = request.POST.get('source', '')
    target = request.POST.get('target', '')
    if not source:
        error = 'Source SRS is mandatory. Please insert an EPSG code (e.g.: EPSG:4326).'
    elif not re.search(r'\:', source) and re.search(r'EPSG', source):
        source = re.sub(r'(EPSG)', r'EPSG:', source)

    if not source.startswith("EPSG:"):
        error = 'Source SRS is not valid. Please insert a valid EPSG code (e.g.: EPSG:4326).'
    else:
        if not target:
            target = source
        elif not re.search(r'\:', target) and re.search(r'EPSG', target):
            target = re.sub(r'(EPSG)', r'EPSG:', target)

        if not target.startswith("EPSG:"):
            error = 'Target SRS is not valid. Please insert a valid EPSG code (e.g.: EPSG:4326).'
        else:
            srs_step(upload_session, source, target)
            return next_step_response(request, upload_session)

    if error:
        return json_response(
            {'status': 'error',
             'success': False,
             'id': upload_session.import_session.id,
             'error_msg': "%s" % error,
             }
        )
    else:
        upload_session.completed_step = 'srs'

    return next_step_response(request, upload_session)


def csv_step_view(request, upload_session):
    import_session = upload_session.import_session
    assert import_session is not None

    # form errors to display to user
    error = None

    # need to check if geometry is found
    # if so, can proceed directly to next step
    attributes = import_session.tasks[0].layer.attributes
    for attr in attributes:
        if attr.binding == u'com.vividsolutions.jts.geom.Point':
            upload_session.completed_step = 'csv'
            return next_step_response(request, upload_session)

    # no geometry found, let's find all the numerical columns
    number_names = ['java.lang.Integer', 'java.lang.Double']
    point_candidates = sorted([attr.name for attr in attributes
                               if attr.binding in number_names])

    lat_field = request.POST.get('lat', '')
    lng_field = request.POST.get('lng', '')

    if request.method == 'GET':
        # layer = check_import_session_is_valid(
        #     request, upload_session, import_session)

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
                       async_upload=False,
                       selected_lat=selected_lat,
                       selected_lng=selected_lng,
                       guessed_lat_or_lng=guessed_lat_or_lng,
                       layer_name=import_session.tasks[0].layer.name,
                       error=error,
                       possible_data_problems=possible_data_problems
                       )
        return render(request, 'upload/layer_upload_csv.html', context=context)
    elif request.method == 'POST':
        if not lat_field or not lng_field:
            error = 'Please choose which columns contain the latitude and longitude data.'
        elif (lat_field not in point_candidates or
              lng_field not in point_candidates):
            error = 'Invalid latitude/longitude columns'
        elif lat_field == lng_field:
            error = 'You cannot select the same column for latitude and longitude data.'

        if error:
            return json_response(
                {'status': 'error',
                 'success': False,
                 'id': upload_session.import_session.id,
                 'error_msg': "%s" % error,
                 }
            )
        else:
            csv_step(upload_session, lat_field, lng_field)
            return next_step_response(request, upload_session)
    elif request.method != 'POST':
        raise Exception()


def check_step_view(request, upload_session):
    import_session = upload_session.import_session
    assert import_session is not None

    if request.method == 'GET':
        layer = check_import_session_is_valid(
            request, upload_session, import_session)
        if upload_session.completed_step != 'error':
            if not layer:
                upload_session.completed_step = 'error'
                upload_session.error_msg = 'Could not access/read the uploaded file!'
            else:
                (has_time_dim, layer_values) = \
                    layer_eligible_for_time_dimension(request,
                                                      import_session.tasks[0].layer, upload_session=upload_session)
                if has_time_dim:
                    upload_session.completed_step = 'check'
                else:
                    # This command skip completely 'time' configuration
                    upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'run'
    elif request.method != 'POST':
        raise Exception()
    return next_step_response(request, upload_session)


def create_time_form(request, upload_session, form_data):
    feature_type = upload_session.import_session.tasks[0].layer

    (has_time, layer_values) = layer_eligible_for_time_dimension(
        request, feature_type, upload_session=upload_session)
    att_list = []
    if has_time:
        att_list = _get_time_dimensions(feature_type, upload_session)
    else:
        att_list = [{'name': a.name, 'binding': a.binding} for a in feature_type.attributes]

    def filter_type(b):
        return [att['name'] for att in att_list if b in att['binding']]

    args = dict(
        time_names=filter_type('Date'),
        text_names=filter_type('String'),
        year_names=filter_type('Integer') + filter_type('Long') + filter_type('Double')
    )
    if form_data:
        return TimeForm(form_data, **args)
    return TimeForm(**args)


def time_step_view(request, upload_session):
    import_session = upload_session.import_session
    assert import_session is not None

    if request.method == 'GET':
        layer = check_import_session_is_valid(
            request, upload_session, import_session)
        if layer:
            (has_time_dim, layer_values) = layer_eligible_for_time_dimension(request,
                                                                             layer, upload_session=upload_session)
            if has_time_dim and layer_values:
                context = {
                    'time_form': create_time_form(request, upload_session, None),
                    'layer_name': layer.name,
                    'layer_values': layer_values,
                    'layer_attributes': layer_values[0].keys(),
                    'async_upload': is_async_step(upload_session)
                }
                return render(request, 'upload/layer_upload_time.html', context=context)
            else:
                upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'run'
                return next_step_response(request, upload_session)
        else:
            # TODO: Error
            upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'run'
            return next_step_response(request, upload_session)
    elif request.method != 'POST':
        raise Exception()

    form = create_time_form(request, upload_session, request.POST)
    if not form.is_valid():
        logger.warning('Invalid upload form: %s', form.errors)
        return error_response(request, errors=["Invalid Submission"])

    cleaned = form.cleaned_data
    start_attribute_and_type = cleaned.get('start_attribute', None)
    if upload_session.time_transforms:
        upload_session.import_session.tasks[0].remove_transforms(
            upload_session.time_transforms,
            save=True
        )
        upload_session.import_session.tasks[0].save_transforms()
        upload_session.time_transforms = None

    if upload_session.import_session.tasks[0].transforms:
        for transform in upload_session.import_session.tasks[0].transforms:
            if 'type' in transform and \
                    (str(transform['type']) == 'DateFormatTransform' or
                     str(transform['type']) == 'CreateIndexTransform'):
                upload_session.import_session.tasks[0].remove_transforms(
                    [transform],
                    save=True
                )
                upload_session.import_session.tasks[0].save_transforms()

    upload_session.import_session = import_session.reload()

    if start_attribute_and_type:
        upload_session.completed_step = 'check'

        def tx(type_name):
            # return None if type_name is None or type_name == 'Date' \
            return None if type_name is None \
                else 'DateFormatTransform'
        end_attribute, end_type = cleaned.get('end_attribute', (None, None))
        time_step(
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
    else:
        upload_session.completed_step = 'time' if _ALLOW_TIME_STEP else 'run'

    return next_step_response(request, upload_session)


def final_step_view(req, upload_session):
    _json_response = None
    if upload_session:
        import_session = upload_session.import_session
        _log('Checking session %s validity', import_session.id)
        if not check_import_session_is_valid(
                req, upload_session, import_session):
            error_msg = upload_session.import_session.tasks[0].error_message
            url = "/upload/layer_upload_invalid.html"
            _json_response = json_response(
                {'url': url,
                    'status': 'error',
                    'id': req.GET['id'],
                    'error_msg': error_msg or 'Import Session is Invalid!',
                    'success': True
                 }
            )
            return _json_response
        else:
            try:
                saved_layer = final_step(upload_session, req.user)

                # this response is different then all of the other views in the
                # upload as it does not return a response as a json object
                _json_response = json_response(
                    {
                        'status': 'finished',
                        'id': req.GET['id'],
                        'url': saved_layer.get_absolute_url(),
                        'bbox': saved_layer.bbox_string,
                        'crs': {
                            'type': 'name',
                            'properties': saved_layer.srid
                        },
                        'success': True
                    }
                )
                return _json_response
            except LayerNotReady:
                return json_response({'status': 'pending',
                                      'success': True,
                                      'id': req.GET['id'],
                                      'redirect_to': '/upload/final' + "?id=%s" % req.GET['id']})
    else:
        # url = reverse('layer_browse') + '?limit={}'.format(settings.CLIENT_RESULTS_LIMIT)
        url = "upload/layer_upload_invalid.html"
        _json_response = json_response(
            {'status': 'error',
             'url': url,
             'error_msg': 'Upload Session invalid or no more accessible!',
             'success': True
             }
        )
        return _json_response


"""
    Workflow Views Definition
"""
_steps = {
    'save': save_step_view,
    'srs': srs_step_view,
    'csv': csv_step_view,
    'check': check_step_view,
    'time': time_step_view,
    'final': final_step_view,
}


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
                return next_step_response(req, session)
        step = 'save'

        # delete existing session
        if upload_id and upload_id in req.session:
            del req.session[upload_id]
    else:
        if not upload_id:
            return render(
                req,
                "upload/layer_upload_invalid.html",
                context={})

        upload_obj = get_object_or_404(
            Upload, import_id=upload_id, user=req.user)
        session = upload_obj.get_session()
        try:
            if session:
                upload_session = session
            else:
                upload_session = req.session[upload_id]
        except BaseException:
            traceback.print_exc()
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

                    if delete_session:
                        # we're done with this session, wax it
                        Upload.objects.update_from_session(upload_session)
                        upload_session = None
                        del req.session[upload_id]
                except BaseException:
                    pass
            else:
                try:
                    req.session[upload_id] = upload_session
                except BaseException:
                    traceback.print_exc()
        elif upload_id in req.session:
            upload_session = req.session[upload_id]
        if upload_session:
            Upload.objects.update_from_session(upload_session)
        return resp
    except BadStatusLine:
        logger.exception('bad status line, geoserver down?')
        return error_response(req, errors=[_geoserver_down_error_msg])
    except gsimporter.RequestFailed as e:
        logger.exception('request failed')
        errors = e.args
        # http bad gateway or service unavailable
        if int(errors[0]) in (502, 503):
            errors = [_geoserver_down_error_msg]
        return error_response(req, errors=errors)
    except gsimporter.BadRequest as e:
        logger.exception('bad request')
        return error_response(req, errors=e.args)
    except Exception as e:
        return error_response(req, exception=e)


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
            response = JSONResponse(
                True, {}, response_content_type(self.request))
            response['Content-Disposition'] = 'inline; filename=files.json'
            return response
        else:
            return HttpResponseRedirect(reverse('data_upload_new'))
