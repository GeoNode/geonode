import os
import sys
import shutil
import traceback
from urlparse import parse_qs

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils import simplejson as json
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from geonode.base.enumerations import CHARSETS
from geonode.documents.models import get_related_documents
from geonode.layers.models import UploadSession
from geonode.layers.utils import file_upload
from geonode.people.models import Profile
from geonode.security.views import _perms_info_json
from geonode.utils import default_map_config
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.utils import llbbox_to_mercator
from geonode.utils import build_social_links

from pprint import pprint

import unicodedata

from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

from .forms import (
    DataRequestProfileForm, DataRequestProfileShapefileForm,
    DataRequestProfileRejectForm, DataRequestProfileCaptchaForm)
from .models import DataRequestProfile


def registration_part_one(request):
    if request.user.is_authenticated():
        return redirect(reverse('home'))

    shapefile_session = request.session.get('data_request_shapefile', None)
    profile_form_data = request.session.get('data_request_info', None)
    if not shapefile_session and profile_form_data:
        del request.session['data_request_info']
        request.session.modified = True

    form = DataRequestProfileForm(
        request.POST or None,
        initial=profile_form_data
    )
    if request.method == 'POST':
        if form.is_valid():
            request.session['data_request_info'] = form.cleaned_data
            return HttpResponseRedirect(
                reverse('datarequests:registration_part_two')
            )
    return render(
        request,
        'datarequests/registration/profile.html',
        {'form': form}
    )


def registration_part_two(request):
    if request.user.is_authenticated():
        return redirect(reverse('home'))

    request.session['data_request_shapefile'] = True
    profile_form_data = request.session.get('data_request_info', None)
    form = DataRequestProfileCaptchaForm()

    if not profile_form_data:
        return redirect(reverse('datarequests:registration_part_one'))

    if request.method == 'POST':
        form = DataRequestProfileShapefileForm(request.POST, request.FILES)
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

            name = slugify(name_base.replace(".", "_"))

            try:
                # Moved this inside the try/except block because it can raise
                # exceptions when unicode characters are present.
                # This should be followed up in upstream Django.
                tempdir, base_file = form.write_files()
                registration_uploader, created = Profile.objects.get_or_create(username='dataRegistrationUploader')

                saved_layer = file_upload(
                    base_file,
                    name=name,
                    user=registration_uploader,
                    overwrite=False,
                    charset=form.cleaned_data["charset"],
                    abstract=form.cleaned_data["abstract"],
                    title=form.cleaned_data["layer_title"],
                )
                saved_layer.is_published = False
                saved_layer.save()
                data_request_form = DataRequestProfileForm(
                    request.session.get('data_request_info', None))
                if data_request_form.is_valid():
                    request_profile = data_request_form.save()
                    request_profile.jurisdiction_shapefile = saved_layer
                    request_profile.save()
                else:
                    out['errors'] = form.data_request_form
            except Exception as e:
                exception_type, error, tb = sys.exc_info()
                out['success'] = False
                out['errors'] = "An unexpected error was encountered. Please try again later."

                # Assign the error message to the latest UploadSession of the data request uploader user.
                latest_uploads = UploadSession.objects.filter(
                    user=registration_uploader
                ).order_by('-date')
                if latest_uploads.count() > 0:
                    upload_session = latest_uploads[0]
                    upload_session.error = str(error)
                    upload_session.traceback = traceback.format_exc(tb)
                    upload_session.context = "Data requester's jurisdiction file upload"
                    upload_session.save()
                    out['traceback'] = upload_session.traceback
                    out['context'] = upload_session.context
                    out['upload_session'] = upload_session.id
            else:
                out['success'] = True
                out['url'] = reverse(
                    'layer_detail', args=[
                        saved_layer.service_typename])

                upload_session = saved_layer.upload_session
                upload_session.processed = True
                upload_session.save()
                permissions = {
                    'users': {'AnonymousUser': []},
                    'groups': {}
                }
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

            if request_profile:
                request_profile.send_verification_email()

            out['success_url'] = request.build_absolute_uri(
                reverse('datarequests:email_verification_send')
            )

            del request.session['data_request_info']
            del request.session['data_request_shapefile']
            request.session.modified = True
        else:
            status_code = 400
        return HttpResponse(
            json.dumps(out),
            mimetype='application/json',
            status=status_code)
    return render(
        request,
        'datarequests/registration/shapefile.html',
        {
            'charsets': CHARSETS,
            'is_layer': True,
            'form': form
        })


class DataRequestPofileList(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'datarequests/data_request_list.html'
    raise_exception = True


def email_verification_send(request):
    context = {
        'support_email': settings.LIPAD_SUPPORT_MAIL,
    }
    return render(
        request,
        'datarequests/registration/verification_sent.html',
        context
    )


def email_verification_confirm(request):
    key = request.GET.get('key', None)
    email = request.GET.get('email', None)

    context = {
        'support_email': settings.LIPAD_SUPPORT_MAIL,
    }

    if key and email:
        try:
            data_request = DataRequestProfile.objects.get(
                email=email,
                verification_key=key,
            )
            # Only verify once
            if not data_request.date:
                data_request.date = timezone.now()
                data_request.save()
                data_request.send_new_request_notif_to_admins()
        except ObjectDoesNotExist:
            data_request = None

        if data_request:
            return render(
                request,
                'datarequests/registration/verification_done.html',
                context
            )

    return render(
        request,
        'datarequests/registration/verification_failed.html',
        context
    )


def data_request_profile(request, pk, template='datarequests/profile_detail.html'):

    if not request.user.is_superuser:
        raise PermissionDenied

    request_profile = get_object_or_404(DataRequestProfile, pk=pk)

    if not request_profile.date:
        raise Http404

    layer = request_profile.jurisdiction_shapefile
    # assert False, str(layer_bbox)
    config = layer.attribute_config()
    # Add required parameters for GXP lazy-loading
    layer_bbox = layer.bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    srid = layer.srid

    # Transform WGS84 to Mercator.
    config["srs"] = srid if srid != "EPSG:4326" else "EPSG:900913"
    config["bbox"] = llbbox_to_mercator([float(coord) for coord in bbox])

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
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection="EPSG:900913")
    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config()[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    context_dict = {
        "request_profile": request_profile,
        "resource": layer,
        "permissions_json": _perms_info_json(layer),
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
    }

    context_dict["viewer"] = json.dumps(
        map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
    context_dict["preview"] = getattr(
        settings,
        'LAYER_PREVIEW_LIBRARY',
        'leaflet')

    if request.user.has_perm('download_resourcebase', layer.get_self_resource()):
        if layer.storeType == 'dataStore':
            links = layer.link_set.download().filter(
                name__in=settings.DOWNLOAD_FORMATS_VECTOR)
        else:
            links = layer.link_set.download().filter(
                name__in=settings.DOWNLOAD_FORMATS_RASTER)
        context_dict["links"] = links

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, layer)

    context_dict["request_reject_form"]= DataRequestProfileRejectForm(instance=request_profile)

    return render_to_response(template, RequestContext(request, context_dict))


@require_POST
def data_request_profile_reject(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    request_profile = get_object_or_404(DataRequestProfile, pk=pk)
    if not request_profile.date:
        raise Http404

    if request_profile.request_status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        request_profile.rejection_reason = form['rejection_reason'][0]
        request_profile.request_status = 'rejected'
        if 'additional_rejection_reason' in form.keys():
            request_profile.additional_rejection_reason = form['additional_rejection_reason'][0]
        request_profile.save()
        request_profile.send_rejection_email()

    url = request.build_absolute_uri(request_profile.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )


@require_POST
def data_request_profile_approve(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(DataRequestProfile, pk=pk)
        if not request_profile.date:
            raise Http404
        try:
            request_profile.ftp_folder =str(request.POST[u'ftp-directory'])
            request_profile.request_status = 'approved'
            username = str(request.POST[u'username'])
            password = str(request.POST[u'password'])
            request_profile.create_account(username,password, request_profile.ftp_folder)
             request_profile.save()
            return HttpResponseRedirect(request_profile.get_absolute_url())
        except:
            message = _('An unexpected error was encountered during the creation of the account.')
            messages.error(request, message)
            return HttpResponseRedirect(request_profile.get_absolute_url())
    else:
        return HttpResponse("Not allowed", status=403)


@require_POST
def data_request_facet_count(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    facets_count = {
        'pending': DataRequestProfile.objects.filter(
            request_status='pending').exclude(date=None).count(),
        'approved': DataRequestProfile.objects.filter(
            request_status='approved').count(),
        'rejected': DataRequestProfile.objects.filter(
            request_status='rejected').count(),
        'commercial': DataRequestProfile.objects.filter(
            requester_type='commercial').exclude(date=None).count(),
        'noncommercial': DataRequestProfile.objects.filter(
            requester_type='noncommercial').exclude(date=None).count(),
        'academe': DataRequestProfile.objects.filter(
            requester_type='academe').exclude(date=None).count(),
    }

    return HttpResponse(
        json.dumps(facets_count),
        status=200,
        mimetype='text/plain'
    )
