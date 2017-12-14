import ast
import datetime
import os
import shutil
import sys
import traceback

import geonode.settings as settings

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template.defaultfilters import slugify
from django.utils import dateformat
from django.utils import timezone
from django.utils import simplejson as json
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from geonode.base.enumerations import CHARSETS
from geonode.cephgeo.models import TileDataClass
from geonode.documents.models import Document
from geonode.layers.models import UploadSession, Style
from geonode.layers.utils import file_upload
from geonode.people.models import Profile
from geonode.people.views import profile_detail
from geonode.security.views import _perms_info_json

from geonode.datarequests.forms import (
    ProfileRequestForm, DataRequestForm, DataRequestShapefileForm)

from geonode.datarequests.models import DataRequestProfile, DataRequest, ProfileRequest, BaseRequest

from geonode.tasks.jurisdiction import place_name_update, jurisdiction_style
from geonode.tasks.jurisdiction2 import compute_size_update
from geonode.tasks.requests import set_status_for_multiple_requests, tag_request_suc

from pprint import pprint
from unidecode import unidecode

from geonode.cephgeo.models import UserJurisdiction
from geonode.tasks.jurisdiction2 import compute_size_update, assign_grid_refs_all, assign_grid_refs

def register(request):
    return HttpResponseRedirect(
        reverse('datarequests:profile_request_form'))

def profile_request_view(request):
    profile_request_obj = request.session.get('profile_request_obj', None)
    data_request_session=request.session.get('data_request_session', None)

    form = ProfileRequestForm()

    if request.user.is_authenticated():
        return HttpResponseRedirect(
            reverse('datarequests:data_request_form')
        )
    else:
        if request.method == 'POST':
            form = ProfileRequestForm(request.POST)
            if form.is_valid():
                if profile_request_obj and data_request_session:
                    profile_request_obj.first_name = form.cleaned_data['first_name']
                    profile_request_obj.middle_name = form.cleaned_data['middle_name']
                    profile_request_obj.last_name = form.cleaned_data['last_name']
                    profile_request_obj.organization = form.cleaned_data['organization']
                    profile_request_obj.org_type=form.cleaned_data['org_type'].val
                    profile_request_obj.contact_number = form.cleaned_data['contact_number']
                    if not profile_request_obj.email == form.cleaned_data['email']:
                        profile_request_obj.email = form.cleaned_data['email']
                        profile_request_obj.save()
                        profile_request_obj.send_verification_email()
                else:
                    profile_request_obj = form.save()
                    profile_request_obj.status = "unconfirmed"
                    profile_request_obj.save()
                    profile_request_obj.send_verification_email()

                request.session['profile_request_obj']= profile_request_obj
                request.session.set_expiry(900)
                return HttpResponseRedirect(
                    reverse('datarequests:data_request_form')
                )
        elif request.method == 'GET':
            if data_request_session and profile_request_obj:
                ## the user pressed back
                initial = {
                    'first_name': profile_request_obj.first_name,
                    'middle_name': profile_request_obj.middle_name,
                    'last_name': profile_request_obj.last_name,
                    'organization': profile_request_obj.organization,
                    'org_type': profile_request_obj.org_type,
                    'organization_other': profile_request_obj.organization_other,
                    'email': profile_request_obj.email,
                    'contact_number': profile_request_obj.contact_number,
                    'location': profile_request_obj.location
                }
                form = ProfileRequestForm(initial = initial)

        return render(
            request,
            'datarequests/registration/profile.html',
            {'form': form}
        )

def data_request_view(request):
    profile_request_obj = request.session.get('profile_request_obj', None)
    if not profile_request_obj:
        pprint("no profile request object found")
    if not request.user.is_authenticated() and not profile_request_obj:
        return redirect(reverse('datarequests:profile_request_form'))

    request.session['data_request_session'] = True

    form = DataRequestForm()

    if request.method == 'POST' :
        pprint("detected data request post")
        post_data = request.POST.copy()
        post_data['permissions'] = '{"users":{"dataRegistrationUploader": ["view_resourcebase"] }}'
        data_classes = post_data.getlist('data_class_requested')
        #data_classes = post_data.get('data_class_requested')
        data_class_objs = []
        pprint(data_classes)
        pprint("len:"+str(len(data_classes)))

        if len(data_classes) == 1:
            post_data.setlist('data_class_requested',data_classes[0].replace('[','').replace(']','').replace('"','').split(','))
            pprint(post_data.getlist('data_class_requested'))

        details_form = DataRequestForm(post_data, request.FILES)
        data_request_obj = None

        errormsgs = []
        out = {}
        out['errors'] = {}
        out['success'] = False
        saved_layer = None
        if not details_form.is_valid():
            for e in details_form.errors.values():
                errormsgs.extend([escape(v) for v in e])

            out['errors'] =  dict(
                (k, map(unicode, v))
                for (k,v) in details_form.errors.iteritems())

            pprint(out['errors'])
        else:
            tempdir = None
            shapefile_form = DataRequestShapefileForm(post_data, request.FILES)
            if u'base_file' in request.FILES:
                if shapefile_form.is_valid():
                    title = shapefile_form.cleaned_data["layer_title"]

                    # Replace dots in filename - GeoServer REST API upload bug
                    # and avoid any other invalid characters.
                    # Use the title if possible, otherwise default to the filename
                    if title is not None and len(title) > 0:
                        name_base = title
                    else:
                        name_base, __ = os.path.splitext(
                            shapefile_form.cleaned_data["base_file"].name)

                    name = slugify(name_base.replace(".", "_"))

                    try:
                        # Moved this inside the try/except block because it can raise
                        # exceptions when unicode characters are present.
                        # This should be followed up in upstream Django.
                        tempdir, base_file = shapefile_form.write_files()
                        registration_uploader, created = Profile.objects.get_or_create(username='dataRegistrationUploader')
                        pprint("saving jurisdiction")
                        saved_layer = file_upload(
                            base_file,
                            name=name,
                            user=registration_uploader,
                            overwrite=False,
                            charset=shapefile_form.cleaned_data["charset"],
                            abstract=shapefile_form.cleaned_data["abstract"],
                            title=shapefile_form.cleaned_data["layer_title"],
                        )

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
                        pprint("layer_upload is successful")
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

                        jurisdiction_style.delay(saved_layer)


                    finally:
                        if tempdir is not None:
                            shutil.rmtree(tempdir)

                else:
                    for e in shapefile_form.errors.values():
                        errormsgs.extend([escape(v) for v in e])
                    out['success'] = False
                    out['errors'].update(dict(
                            (k, map(unicode, v))
                            for (k,v) in shapefile_form.errors.iteritems()
                    ))
                    pprint(out['errors'])
                    out['errormsgs'] = out['errors']

        #if out['success']:
        if not out['errors']:
            out['success'] = True
            data_request_obj = details_form.save()
            if request.user.is_authenticated() and not request.user.username  == 'AnonymousUser':
                request_letter = create_letter_document(details_form.clean()['letter_file'], profile = request.user)
                data_request_obj.request_letter = request_letter
                data_request_obj.save()
                data_request_obj.profile = request.user
                data_request_obj.save()
                data_request_obj.set_status("pending")
            else:
                request_letter = create_letter_document(details_form.clean()['letter_file'], profile_request = profile_request_obj)
                data_request_obj.request_letter = request_letter
                data_request_obj.save()
                data_request_obj.profile_request = profile_request_obj
                data_request_obj.save()
                profile_request_obj.data_request= data_request_obj
                profile_request_obj.save()
            data_request_obj.save()
            if saved_layer:
                data_request_obj.jurisdiction_shapefile = saved_layer
                data_request_obj.save()
                place_name_update.delay([data_request_obj])
                compute_size_update.delay([data_request_obj])
                tag_request_suc.delay([data_request_obj])
            status_code = 200
            pprint("request has been succesfully submitted")
            if profile_request_obj and not request.user.is_authenticated():
            #    request_data.send_verification_email()

                out['success_url'] = reverse('datarequests:email_verification_send')

                out['redirect_to'] = reverse('datarequests:email_verification_send')

            elif request.user.is_authenticated():
                messages.info(request, "Your request has been submitted")
                out['success_url'] = reverse('home')

                out['redirect_to'] = reverse('home')

                if data_request_obj.jurisdiction_shapefile:
                    data_request_obj.assign_jurisdiction() #assigns/creates jurisdiction object
                    assign_grid_refs.delay(data_request_obj.profile)
                else:
                    try:
                        uj = UserJurisdiction.objects.get(user=data_request_obj.profile)
                        uj.delete()
                    except ObjectDoesNotExist as e:
                        pprint("Jurisdiction Shapefile not found, nothing to delete. Carry on")
                data_request_obj.set_status('approved')
                data_request_obj.send_approval_email(data_request_obj.profile.username)
                messages.info(request, "Request "+str(data_request_obj.pk)+" has been approved.")

            del request.session['data_request_session']

            if 'profile_request_obj' in request.session:
                del request.session['profile_request_obj']

        else:
            status_code = 400
        pprint("sending this out")
        return HttpResponse(
            json.dumps(out),
            mimetype='application/json',
            status=status_code)
    pprint("i'm here")
    return render(
        request,
        'datarequests/registration/shapefile.html',
        {
            'charsets': CHARSETS,
            'is_layer': True,
            'form': form,
            'support_email': settings.LIPAD_SUPPORT_MAIL,
        })

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
        profile_request = None
        try:
            profile_request = ProfileRequest.objects.get(
                email=email,
                verification_key=key,
            )
            pprint(profile_request.status)
            # Only verify once
            if profile_request.status == "unconfirmed":
                #[DEPRECIATED] Requests with admin approval
                """
                profile_request.status = "pending"
                profile_request.verification_date = timezone.now()
                pprint(email+" "+profile_request.status)
                profile_request.save()
                """
                #Requests auto approval
                if profile_request.email in Profile.objects.all().values_list('email', flat=True):
                    messages.info(request,'The email for this profile request is already in use')
                    pprint(request,'The email for this profile request is already in use')
                    return render(
                        request,
                        'datarequests/registration/verification_failed.html',
                        context
                    )
                result = True
                message = ''
                result, message = profile_request.create_account() #creates account in AD if AD profile does not exist
                if not result:
                    messages.error (request, _(message))
                else:
                    profile_request.profile.organization_type = profile_request.organization_type
                    profile_request.profile.org_type = profile_request.org_type
                    profile_request.profile.organization_other = profile_request.organization_other
                    profile_request.save()
                    profile_request.profile.save()

                    profile_request.set_status('approved')

                    if profile_request.data_request:
                        profile_request.data_request.profile = profile_request.profile

                        if profile_request.data_request.jurisdiction_shapefile:
                            profile_request.data_request.assign_jurisdiction() #assigns/creates jurisdiction object
                            assign_grid_refs.delay(profile_request.data_request.profile)
                        else:
                            try:
                                uj = UserJurisdiction.objects.get(user=profile_request.data_request.profile)
                                uj.delete()
                            except ObjectDoesNotExist as e:
                                pprint("Jurisdiction Shapefile not found, nothing to delete. Carry on")
                        profile_request.data_request.save()
                        profile_request.data_request.set_status('approved')
                        profile_request.data_request.send_approval_email(profile_request.data_request.profile.username)
                        pprint(request, "Request "+str(profile_request.data_request.pk)+" has been approved.")
                    profile_request.send_approval_email()

                pprint(email+" "+profile_request.status)
                profile_request.send_new_request_notif_to_admins()
                profile_requests = ProfileRequest.objects.filter(email=email, status="unconfirmed")
                set_status_for_multiple_requests.delay(profile_requests,"cancelled")


        except ObjectDoesNotExist:
            profile_request = None

        if profile_request:
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

def create_letter_document(request_letter, profile=None, profile_request=None):
    if not profile and not profile_request:
        raise PermissionDenied

    details = None
    letter_owner = None
    permissions = None

    if profile:
        pprint("profile is not empty")
        details = profile
        letter_owner = profile
        permissions = {"users":{profile.username:["view_resourcebase","download_resourcebase"]}}
    else:
        pprint("profile request is not empty")
        details = profile_request
        letter_owner, created = Profile.objects.get_or_create(username='dataRegistrationUploader')
        permissions = {"users":{"dataRegistrationUploader":["view_resourcebase"]}}

    requester_name = unidecode(details.first_name+" " +details.last_name)
    letter = Document()
    letter.owner = letter_owner
    letter.doc_file = request_letter
    letter.title = requester_name + " Request Letter " +datetime.datetime.now().strftime("%Y-%m-%d")
    letter.is_published = False
    letter.save()
    letter.set_permissions(permissions)

    return letter
