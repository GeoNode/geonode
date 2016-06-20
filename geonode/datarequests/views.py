import os
import sys
import shutil
import traceback
import datetime
import time
import csv
from urlparse import parse_qs

from crispy_forms.utils import render_crispy_form

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.utils import dateformat
from django.utils import timezone
from django.utils import simplejson as json
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from geonode.base.enumerations import CHARSETS
from geonode.cephgeo.models import UserJurisdiction
from geonode.documents.models import get_related_documents
from geonode.documents.models import Document
from geonode.layers.models import UploadSession, Style
from geonode.layers.utils import file_upload
from geonode.people.models import Profile
from geonode.people.views import profile_detail
from geonode.security.views import _perms_info_json
from geonode.utils import default_map_config
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.utils import llbbox_to_mercator
from geonode.utils import build_social_links

from geoserver.catalog import Catalog

from unidecode import unidecode
from pprint import pprint


from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

from .forms import (
    DataRequestProfileForm, DataRequestProfileShapefileForm,
    DataRequestProfileRejectForm, DataRequestDetailsForm)
from .models import DataRequestProfile
from .utils import (
    get_place_name, get_juris_data_size, get_area_coverage)

def registration_part_one(request):

    shapefile_session = request.session.get('data_request_shapefile', None)
    request_object = request.session.get('request_object', None)
    datarequest_shapefile=request.session.get('data_request_shapefile', None)

    form = DataRequestProfileForm( )

    if request.method == 'GET':
        if request.user.is_authenticated():

            request_object = DataRequestProfile(
                profile = request.user,
                first_name = request.user.first_name,
                middle_name = request.user.middle_name,
                last_name = request.user.last_name,
                organization = request.user.organization,
                email = request.user.email,
                contact_number = request.user.voice,
                request_status = 'pending'
            )
            pprint(request_object.first_name)
            request.session['request_object']=request_object

            return HttpResponseRedirect(
                reverse('datarequests:registration_part_two')
            )
        else:
            if datarequest_shapefile and request_object:
                ## the user pressed back
                initial = {
                    'first_name': request_object.first_name,
                    'middle_name': request_object.middle_name,
                    'last_name': request_object.last_name,
                    'organization': request_object.last_name,
                    'email': request_object.email,
                    'contact_number': request_object.contact_number,
                    'location': request_object.location
                }
                form = DataRequestProfileForm(initial = initial)
    elif request.method == 'POST':
        if request.user.is_authenticated():
            request_object = create_request_obj(request.user)

            if not request_object:
                messages.info(request, "Please update your middle name and/or organization in your profile")
                return redirect(reverse('profile_detail',  args= [request.user.username]))

            request.session['request_object']=request_object

        else:
            form = DataRequestProfileForm(
                request.POST
            )
            if form.is_valid():

                if request_object and datarequest_shapefile:
                    request_object.first_name= form.cleaned_data['first_name']
                    request_object.middle_name= form.cleaned_data['middle_name']
                    request_object.last_name= form.cleaned_data['last_name']
                    request_object.organization= form.cleaned_data['organization']
                    request_object.contact_number= form.cleaned_data['contact_number']
                    request_object.save()
                    if not request_object.email == form.cleaned_data['email']:
                        request_object.email=form.cleaned_data['email']
                        request_object.save()
                        request_object.send_verification_email()
                else:
                    request_object = form.save()
                    request_object.send_verification_email()

                request.session['request_object']= request_object
                request.session.set_expiry(900)
                return HttpResponseRedirect(
                    reverse('datarequests:registration_part_two')
                )
    return render(
        request,
        'datarequests/registration/profile.html',
        {'form': form}
    )

def registration_part_two(request):
    part_two_initial ={}
    is_new_auth_req = False
    last_submitted_dr = None
    if request.user.is_authenticated():
        is_new_auth_req = request.session.get('is_new_auth_req', None)
        try:
            last_submitted_dr = DataRequestProfile.objects.filter(profile=request.user).latest('key_created_date')
            part_two_initial['project_summary']=last_submitted_dr.project_summary
            part_two_initial['data_type_requested']=last_submitted_dr.data_type_requested
        except ObjectDoesNotExist as e:
            pprint("No previous request from "+request.user.username)

    request.session['data_request_shapefile'] = True
    saved_request_object= request.session.get('request_object', None)

    if not saved_request_object:
        return redirect(reverse('datarequests:registration_part_one'))

    form = DataRequestDetailsForm(initial=part_two_initial)

    if request.method == 'POST' :
        post_data = request.POST.copy()
        post_data['permissions'] = '{"users":{"dataRegistrationUploader": ["view_resourcebase"] }}'
        form = DataRequestDetailsForm(post_data, request.FILES)
        if u'base_file' in request.FILES:
            form = DataRequestProfileShapefileForm(post_data, request.FILES)

        tempdir = None
        errormsgs = []
        out = {}
        #request_profile =  request.session['request_object']
        request_profile = saved_request_object
        place_name = None
        pprint(post_data)
        if form.is_valid():
            if last_submitted_dr and not is_new_auth_req:
                if last_submitted_dr.request_status.encode('utf8') == 'pending' or last_submitted_dr.request_status.encode('utf8') == 'unconfirmed':
                    pprint("updating request_status")
                    last_submitted_dr.request_status = 'cancelled'
                    last_submitted_dr.save()
            if form.cleaned_data:
                interest_layer = None
                if u'base_file' in request.FILES:
                    pprint(request.FILES)
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
                        def_style = Style.objects.get(name="Boundary")
                        saved_layer.styles.add(def_style)
                        saved_layer.default_style=def_style
                        saved_layer.is_published = False
                        saved_layer.save()
                        interest_layer =  saved_layer

                        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                            username=settings.OGC_SERVER['default']['USER'],
                            password=settings.OGC_SERVER['default']['PASSWORD'])

                        boundary_style = cat.get_style('Boundary')
                        gs_layer = cat.get_layer(saved_layer.name)
                        if boundary_style:
                            gs_layer._set_default_style(boundary_style)
                            cat.save(gs_layer) #save in geoserver
                            saved_layer.sld_body = boundary_style.sld_body
                            saved_layer.save() #save in geonode

                        bbox = gs_layer.resource.latlon_bbox
                        bbox_lon = (float(bbox[0])+float(bbox[1]))/2
                        bbox_lat = (float(bbox[2])+float(bbox[3]))/2
                        place_name = get_place_name(bbox_lon, bbox_lat)
                        juris_data_size = 0.0
                        area_coverage = get_area_coverage(saved_layer.name)

                    except Exception as e:
                        exception_type, error, tb = sys.exc_info()
                        print traceback.format_exc()
                        out['success'] = False
                        out['errors'] = "An unexpected error was encountered. Check the files you have uploaded, clear your selected files, and try again."
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
                            'users': {'dataRegistrationUploader': []},
                            'groups': {}
                        }
                        if request.user.is_authenticated():
                            permissions = {
                                'users': {request.user.username : ['view_resourcebase']},
                                'groups': {}
                            }


                        if permissions is not None and len(permissions.keys()) > 0:

                            saved_layer.set_permissions(permissions)

                    finally:
                        if tempdir is not None:
                            shutil.rmtree(tempdir)

            #Now store the data request
                #data_request_form = DataRequestProfileForm(
                #                profile_form_data)


                if 'request_object' in request.session :
                    if 'success' not in out:
                        request_profile, letter = update_datarequest_obj(
                            datarequest=  request.session['request_object'],
                            parameter_dict = form.clean(),
                            request_letter = form.clean()['letter_file'],
                            interest_layer = interest_layer
                        )

                        out['success']=True
                    else:
                        if out['success']:
                            request_profile, letter = update_datarequest_obj(
                                datarequest=  request.session['request_object'],
                                parameter_dict = form.clean(),
                                request_letter = form.clean()['letter_file'],
                                interest_layer = interest_layer
                            )

                    if interest_layer:
                        request_profile.place_name = place_name['state']
                        request_profile.juris_data_size = juris_data_size
                        request_profile.area_coverage = area_coverage
                        request_profile.save()

                    if request.user.is_authenticated():
                        request_profile.profile = request.user
                        request_profile.request_status = 'pending'
                        request_profile.username = request.user.username
                        request_profile.set_verification_key()
                        request_profile.save()

                else:
                    pprint("unable to retrieve request object")

                    for e in form.errors.values():
                        errormsgs.extend([escape(v) for v in e])
                    out['success'] = False
                    out['errors'] =  dict(
                        (k, map(unicode, v))
                        for (k,v) in form.errors.iteritems()
                    )
                    pprint(out['errors'])
                    out['errormsgs'] = out['errors']
        else:
            for e in form.errors.values():
                errormsgs.extend([escape(v) for v in e])
            out['success'] = False
            out['errors'] = dict(
                    (k, map(unicode, v))
                    for (k,v) in form.errors.iteritems()
            )
            pprint(out['errors'])
            out['errormsgs'] = out['errors']

        if out['success']:
            status_code = 200

            if request_profile and not request_profile.profile:
#                request_profile.send_verification_email()

                out['success_url'] = reverse('datarequests:email_verification_send')

                out['redirect_to'] = reverse('datarequests:email_verification_send')

            elif request_profile and request_profile.profile:
                out['success_url'] = reverse('home')

                out['redirect_to'] = reverse('home')

                request_profile.date = timezone.now()
                request_profile.save()

            del request.session['data_request_shapefile']
            del request.session['request_object']
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
            'form': form,
            'support_email': settings.LIPAD_SUPPORT_MAIL,
        })


class DataRequestPofileList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/data_request_list.html'
    raise_exception = True

@login_required
def data_request_csv(request):
    if not request.user.is_superuser:
        raise HttpResponseForbidden

    response = HttpResponse(content_type='text/csv')
    datetoday = timezone.now()
    response['Content-Disposition'] = 'attachment; filename="datarequests-"'+str(datetoday.month)+str(datetoday.day)+str(datetoday.year)+'.csv"'

    writer = csv.writer(response)
    fields = ['id','name','email','contact_number', 'organization', 'organization_type','has_letter','has_shapefile','project_summary', 'created','request_status', 'date of action','rejection_reason','juris_data_size','area_coverage']
    writer.writerow( fields)

    objects = DataRequestProfile.objects.all().order_by('pk')

    for o in objects:
        writer.writerow(o.to_values_list(fields))

    return response

def email_verification_send(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('home'))

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
                data_request.request_status = 'pending'
                data_request.date = timezone.now()
                pprint(email+" has been confirmed")
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

    request_profile = get_object_or_404(DataRequestProfile, pk=pk)

    if not request.user.is_superuser and not request_profile.profile == request.user:
        raise PermissionDenied


    #if not request_profile.date:
    #    raise Http404

    context_dict={"request_profile": request_profile}

    if request_profile.jurisdiction_shapefile:
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

        context_dict ["resource"] = layer
        context_dict ["permissions_json"] = _perms_info_json(layer)
        context_dict ["documents"] = get_related_documents(layer)
        context_dict ["metadata"] =  metadata
        context_dict ["is_layer"] = True
        context_dict ["wps_enabled"] = settings.OGC_SERVER['default']['WPS_ENABLED'],

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


def data_request_profile_reject(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    request_profile = get_object_or_404(DataRequestProfile, pk=pk)

    if request_profile.request_status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        request_profile.rejection_reason = form['rejection_reason'][0]
        request_profile.request_status = 'rejected'
        if 'additional_rejection_reason' in form.keys():
            request_profile.additional_rejection_reason = form['additional_rejection_reason'][0]
        request_profile.administrator = request.user
        request_profile.action_date = timezone.now()
        request_profile.save()
        if request_profile.profile:
            pprint("sending request rejection email")
            request_profile.send_request_rejection_email()
        else:
            pprint("sending account rejection email")
            request_profile.send_account_rejection_email()

    url = request.build_absolute_uri(request_profile.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

def data_request_profile_cancel(request, pk):
    request_profile = get_object_or_404(DataRequestProfile, pk=pk)

    if not request.user.is_superuser and  not request_profile.profile == request.user:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    request_profile = get_object_or_404(DataRequestProfile, pk=pk)

    if request_profile.request_status == 'pending' or request_profile.request_status == 'unconfirmed':
        pprint("Yown pasok")
        form = request.POST.get('form', None)
        request_profile.request_status = 'cancelled'
        if form:
            form_parsed = parse_qs(request.POST.get('form', None))
            if 'rejection_reason' in form_parsed.keys():
                request_profile.rejection_reason = form_parsed['rejection_reason'][0]

            if 'additional_rejection_reason' in form_parsed.keys():
                request_profile.additional_rejection_reason = form_parsed['additional_rejection_reason'][0]

        request_profile.administrator = request.user
        request_profile.action_date = timezone.now()
        request_profile.save()

    url = request.build_absolute_uri(request_profile.get_absolute_url())
    if request.user.is_superuser:
        return HttpResponse(
            json.dumps({
                'result': 'success',
                'errors': '',
                'url': url}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponseRedirect(reverse('datarequests:data_request_profile', args=[pk]))



def data_request_profile_approve(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(DataRequestProfile, pk=pk)

        if not request_profile.has_verified_email or request_profile.request_status != 'pending':
            raise PermissionDenied

        result = True
        message = ''
        is_new_acc=True

        if not request_profile.profile or not request_profile.username or not request_profile.ftp_folder:
            result, message = request_profile.create_account() #creates account in AD if AD profile does not exist
        else:
            is_new_acc = False

        if not result:
            messages.error (request, _(message))
        else:
            if request_profile.jurisdiction_shapefile:
                request_profile.assign_jurisdiction() #assigns/creates jurisdiction object
            else:
                try:
                    uj = UserJurisdiction.objects.get(user=request_profile.profile)
                    uj.delete()
                except ObjectDoesNotExist as e:
                    pprint("Jurisdiction Shapefile not found, nothing to delete. Carry on")

            request_profile.set_approved(is_new_acc)


        return HttpResponseRedirect(request_profile.get_absolute_url())

    else:
        return HttpResponseRedirect("/forbidden/")


def data_request_profile_reconfirm(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(DataRequestProfile, pk=pk)

        request_profile.send_verification_email()
        return HttpResponseRedirect(request_profile.get_absolute_url())

def data_request_profile_recreate_dir(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(DataRequestProfile, pk=pk)

        request_profile.create_directory()
        return HttpResponseRedirect(request_profile.get_absolute_url())

def data_request_facet_count(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    if not request.method == 'POST':
        raise PermissionDenied

    facets_count = {
        'pending': DataRequestProfile.objects.filter(
            request_status='pending').exclude(date=None).count(),
        'approved': DataRequestProfile.objects.filter(
            request_status='approved').count(),
        'rejected': DataRequestProfile.objects.filter(
            request_status='rejected').count(),
        'cancelled': DataRequestProfile.objects.filter(
            request_status='cancelled').exclude(date=None).count(),
    }

    return HttpResponse(
        json.dumps(facets_count),
        status=200,
        mimetype='text/plain'
    )

def update_datarequest_obj(datarequest=None, parameter_dict=None, interest_layer=None, request_letter = None):
    if datarequest is None or parameter_dict is None or request_letter is None:
        raise HttpResponseBadRequest

    ### Updating the other fields of the request
    datarequest.project_summary = parameter_dict['project_summary']
    datarequest.data_type_requested = parameter_dict['data_type_requested']

    if parameter_dict['purpose']  == 'other':
        datarequest.purpose = parameter_dict['purpose_other']
    else:
        datarequest.purpose = parameter_dict['purpose']

    datarequest.intended_use_of_dataset = parameter_dict['intended_use_of_dataset']
    datarequest.organization_type = parameter_dict['organization_type']
    datarequest.request_level = parameter_dict['request_level']
    datarequest.funding_source = parameter_dict['funding_source']
    datarequest.is_consultant = parameter_dict['is_consultant']

    if interest_layer:
        datarequest.jurisdiction_shapefile = interest_layer

    requester_name = unidecode(datarequest.first_name+" "+datarequest.last_name)
    letter = Document()
    letter_owner, created =  Profile.objects.get_or_create(username='dataRegistrationUploader')
    letter.owner = letter_owner
    letter.doc_file = request_letter
    letter.title = requester_name+ " Request Letter " +datetime.datetime.now().strftime("%Y-%m-%d")
    letter.is_published = False
    letter.save()
    letter.set_permissions( {"users":{"dataRegistrationUploader":["view_resourcebase"]}})

    datarequest.request_letter =letter;

    datarequest.save()

    return (datarequest, letter)
