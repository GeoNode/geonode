from django.utils import dateformat
from django.utils import timezone
from django.utils import simplejson as json
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from geonode.documents.models import Document
from geonode.layers.models import UploadSession, Style
from geonode.layers.utils import file_upload
from geonode.people.models import Profile
from geonode.people.views import profile_detail
from geonode.security.views import _perms_info_json

from geonode.datarequests.forms import (
    DataRequestProfileForm, DataRequestProfileShapefileForm,
    DataRequestProfileRejectForm, DataRequestDetailsForm,
    DataRequestInfoForm, DataRequestProjectForm, DataRequestShapefileForm)
    
from geonode.datarequests.models import DataRequestProfile, DataRequest, ProfileRequest

def registration_part_one(request):

    shapefile_session = request.session.get('data_request_shapefile', None)
    request_object = request.session.get('request_object', None)
    datarequest_shapefile=request.session.get('data_request_shapefile', None)

    form = DataRequestInfoForm()

    if request.method == 'GET':
        if request.user.is_authenticated():

            request_object = ProfileRequest(
                profile = request.user,
                first_name = request.user.first_name,
                middle_name = request.user.middle_name,
                last_name = request.user.last_name,
                organization = request.user.organization,
                organization_type = request.user.organization_type,
                organization_other = request.user.organization_other,
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
                    'organization': request_object.organization,
                    'organization_type': request_object.organization_type,
                    'organization_other': request_object.organization_other,
                    'email': request_object.email,
                    'contact_number': request_object.contact_number,
                    'location': request_object.location
                }
                form = DataRequestInfoForm(initial = initial)
    elif request.method == 'POST':
        if request.user.is_authenticated():
            request_object = create_request_obj(request.user)

            if not request_object:
                messages.info(request, "Please update your middle name and/or organization in your profile")
                return redirect(reverse('profile_detail',  args= [request.user.username]))

            request.session['request_object']=request_object

        else:
            form = DataRequestInfoForm(
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
    if request.user.is_authenticated() and request.user is not Profile.objects.get(username="AnonymousUser") :
        is_new_auth_req = request.session.get('is_new_auth_req', None)
        try:
            last_submitted_dr = DataRequest.objects.filter(profile=request.user).latest('date_submitted')
            part_two_initial['project_summary']=last_submitted_dr.project_summary
            part_two_initial['data_type_requested']=last_submitted_dr.data_type_requested
        except ObjectDoesNotExist as e:
            pprint("No previous request from "+request.user.username)

    request.session['data_request_shapefile'] = True
    saved_request_object= request.session.get('request_object', None)

    if not saved_request_object:
        return redirect(reverse('datarequests:registration_part_one'))

    form = DataRequestProjectForm(initial=part_two_initial)

    juris_data_size = 0.0
    #area_coverage = get_area_coverage(saved_layer.name)
    area_coverage = 0

    if request.method == 'POST' :
        post_data = request.POST.copy()
        post_data['permissions'] = '{"users":{"dataRegistrationUploader": ["view_resourcebase"] }}'
        form = DataRequestProjectForm(post_data, request.FILES)
        if u'base_file' in request.FILES:
            form = DataRequestShapefileForm(post_data, request.FILES)

        tempdir = None
        errormsgs = []
        out = {}
        #request_profile =  request.session['request_object']
        # request_profile = saved_request_object
        place_name = None
        pprint(post_data)
        if form.is_valid():
            request_data = DataRequestProjectForm(post_data, request.FILES).save()
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
                        pprint("saving jurisdiction")
                        saved_layer = file_upload(
                            base_file,
                            name=name,
                            user=registration_uploader,
                            overwrite=False,
                            charset=form.cleaned_data["charset"],
                            abstract=form.cleaned_data["abstract"],
                            title=form.cleaned_data["layer_title"],
                        )
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

                        #bbox = gs_layer.resource.latlon_bbox
                        #bbox_lon = (float(bbox[0])+float(bbox[1]))/2
                        #bbox_lat = (float(bbox[2])+float(bbox[3]))/2
                        #place_name = get_place_name(bbox_lon, bbox_lat)
                        juris_data_size = 0.0
                        area_coverage = 0.0

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

                        jurisdiction_style.delay(saved_layer)

                    finally:
                        if tempdir is not None:
                            shutil.rmtree(tempdir)

            #Now store the data request
                #data_request_form = DataRequestProfileForm(
                #                profile_form_data)


                if 'request_object' in request.session :
                    if 'success' not in out:
                    #     request_data, letter = update_datarequest_obj(
                    #         datarequest=  request.session['request_object'],
                    #         parameter_dict = form.clean(),
                    #         request_letter = form.clean()['letter_file'],
                    #         interest_layer = interest_layer
                    #     )
                    #
                        out['success']=True
                    # else:
                    #     if out['success']:
                    #         request_data, letter = update_datarequest_obj(
                    #             datarequest=  request.session['request_object'],
                    #             parameter_dict = form.clean(),
                    #             request_letter = form.clean()['letter_file'],
                    #             interest_layer = interest_layer
                    #         )
                    request_data, letter = map_letter_shapefile(
                        datarequest =  request_data,
                        profile_session = request.session['request_object'],
                        request_letter = form.clean()['letter_file'],
                        interest_layer = interest_layer
                    )
                    request_data.date_submitted = datetime.datetime.now()

                    if interest_layer:
                        request_data.place_name = None
                        request_data.juris_data_size = juris_data_size
                        request_data.area_coverage = area_coverage
                        request_data.save()

                    if request.user.is_authenticated():
                        request_data.profile = request.user
                        request_data.request_status = 'pending'
                        request_data.username = request.user.username
                        request_data.set_verification_key()
                        request_data.save()
                    else:
                        request_data.profile_request = saved_request_object
                        request_data.save()
                        saved_request_object.data_request = request_data
                        saved_request_object.save()

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
            pprint("request has been succesfully submitted")
            if request_data and not request_data.profile:
            #    request_data.send_verification_email()

                out['success_url'] = reverse('datarequests:email_verification_send')

                out['redirect_to'] = reverse('datarequests:email_verification_send')

            elif request_data and request_data.profile:
                out['success_url'] = reverse('home')

                out['redirect_to'] = reverse('home')

                request_data.date = timezone.now()
                request_data.save()

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
            profile_request = ProfileRequest.objects.get(
                email=email,
                verification_key=key,
            )
            # Only verify once
            if not data_request.date:
                profile_request.request_status = 'pending'
                profile_request.date = timezone.now()
                pprint(email+" has been confirmed")
                profile_request.save()
                profile_request.send_new_request_notif_to_admins()
                if profile_request.data_request:
                    dr = profile_request.data_request
                    dr.request_status = 'pending'
                    dr.save()
                    
        except ObjectDoesNotExist:
            profile_request = None

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
