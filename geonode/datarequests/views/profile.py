from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template import RequestContext
from django.utils import simplejson as json
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

from geonode.people.models import Profile
from geonode.datarequests.forms import RejectionForm
from geonode.datarequests.admin_edit_forms import ProfileRequestEditForm
from geonode.datarequests.models import (
    ProfileRequest, DataRequest, LipadOrgType)

from pprint import pprint
from urlparse import parse_qs

import csv

class ProfileRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/profile_request_list.html'
    raise_exception = True

#@login_required
def profile_request_detail(request, pk, template='datarequests/profile_detail.html'):

    profile_request = get_object_or_404(ProfileRequest, pk=pk)

    #if not request.user.is_superuser and not profile_request.profile == request.user:
    #    return HttpResponseRedirect('/forbidden')

    pprint("profile_request "+profile_request.status)
    context_dict={"profile_request": profile_request}

    if profile_request.data_request:
        pprint("no data request attached")
        context_dict['data_request'] = profile_request.data_request.get_absolute_url()

    context_dict["request_reject_form"]= RejectionForm(instance=profile_request)

    return render_to_response(template, RequestContext(request, context_dict))

@login_required
def profile_request_edit(request, pk, template ='datarequests/profile_detail_edit.html'):
    profile_request = get_object_or_404(ProfileRequest, pk=pk)
    if not  request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')
    
    if request.method == 'GET': 
        context_dict={"profile_request":profile_request}
        context_dict["form"] = ProfileRequestEditForm(initial = model_to_dict(profile_request))
        return render(request, template, context_dict)
    else:
        form = ProfileRequestEditForm(request.POST)
        if form.is_valid():
            pprint("form is valid")
            for k, v in form.cleaned_data.iteritems():
                if k=='org_type':
                    pprint(v)
                    setattr(profile_request, k, v.val)
                elif k=='email':
                    if form.cleaned_data[k] != profile_request.email and profile_request.status == 'pending' :
                        profile_request.status = 'unconfirmed'
                    setattr(profile_request, k, v)
                else:
                    setattr(profile_request, k, v)
            profile_request.administrator = request.user
            profile_request.save()
        else:
            pprint("form is invalid")
            return render( request, template, {'form': form, 'profile_request': profile_request})
        return HttpResponseRedirect(profile_request.get_absolute_url())

def profile_request_approve(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')
    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if request.method == 'POST':
        profile_request = get_object_or_404(ProfileRequest, pk=pk)

        if not profile_request.has_verified_email:
            if profile_request.status == 'pending':
                profile_request.status = 'unconfirmed'
                profile_request.save()
            messages.info(request,'This request does not have a verified email')
            return HttpResponseRedirect(profile_request.get_absolute_url())
        
        if profile_request.email in Profile.objects.all().values_list('email', flat=True):
            messages.info(request,'The email for this profile request is already in use')
            return HttpResponseRedirect(profile_request.get_absolute_url())
        
        if profile_request.status != 'pending':
            return HttpResponseRedirect('/forbidden')

        result = True
        message = ''
        # this should be it
        result, message = profile_request.create_account() #creates account in AD if AD profile does not exist

        if not result:
            messages.error (request, _(message))
        else:
            profile_request.profile.organization_type = profile_request.organization_type
            profile_request.profile.org_type = profile_request.org_type
            profile_request.profile.organization_other = profile_request.organization_other
            profile_request.save()
            profile_request.profile.save()

            profile_request.set_status('approved',administrator = request.user)

            if profile_request.data_request:
                profile_request.data_request.profile = profile_request.profile
                profile_request.data_request.save()
                profile_request.data_request.set_status('pending')

            profile_request.send_approval_email()

        return HttpResponseRedirect(profile_request.get_absolute_url())

    else:
        return HttpResponseRedirect("/forbidden/")

def profile_request_reject(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden/')

    if not request.method == 'POST':
         return HttpResponseRedirect('/forbidden/')

    profile_request = get_object_or_404(ProfileRequest, pk=pk)

    if profile_request.status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        profile_request.rejection_reason = form['rejection_reason'][0]
        if 'additional_rejection_reason' in form.keys():
            profile_request.additional_rejection_reason = form['additional_rejection_reason'][0]
        profile_request.save()

        profile_request.set_status('rejected',administrator = request.user)
        profile_request.send_rejection_email()

    url = request.build_absolute_uri(profile_request.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

def profile_request_reconfirm(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if request.method == 'POST':
        profile_request = get_object_or_404(ProfileRequest, pk=pk)

        profile_request.send_verification_email()

        messages.info(request, "Confirmation email resent")
        return HttpResponseRedirect(profile_request.get_absolute_url())

def profile_request_recreate_dir(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if request.method == 'POST':
        profile_request = get_object_or_404(ProfileRequest, pk=pk)

        profile_request.create_directory()

        messages.info(request, "Folder creation has been scheduled. Check folder location in a few minutes")
        return HttpResponseRedirect(profile_request.get_absolute_url())

def profile_request_cancel(request,pk):
    profile_request = get_object_or_404(ProfileRequest, pk=pk)
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if profile_request.status == 'pending' or profile_request.status == 'unconfirmed':
        form = parse_qs(request.POST.get('form', None))
        profile_request.rejection_reason = form['rejection_reason'][0]
        profile_request.save()

        if not request.user.is_superuser:
            profile_request.set_status('cancelled')
        else:
            profile_request.set_status('cancelled',administrator = request.user)

    url = request.build_absolute_uri(profile_request.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

@login_required
def profile_requests_csv(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect("/forbidden")
    else:
        response = HttpResponse(content_type='text/csv')
        datetoday = timezone.now()
        response['Content-Disposition'] = 'attachment; filename="profilerequests-"'+str(datetoday.month)+str(datetoday.day)+str(datetoday.year)+'.csv"'

        writer = csv.writer(response)
        fields = ['id','name','email','contact_number', 'organization', 'org_type','organization_other', 'created','status', 'status changed','has_data_request', 'place_name', 'area_coverage','estimated_data_size', ]
        writer.writerow( fields)

        objects = ProfileRequest.objects.all().order_by('pk')

        for o in objects:
            writer.writerow(o.to_values_list(fields))

        return response

def profile_request_facet_count(request):

    facets_count = {
        'pending': ProfileRequest.objects.filter(
            status='pending').count(),
        'approved': ProfileRequest.objects.filter(
            status='approved').count(),
        'rejected': ProfileRequest.objects.filter(
            status='rejected').count(),
        'unconfirmed': ProfileRequest.objects.filter(
            status='unconfirmed').count(),
    }

    return HttpResponse(
        json.dumps(facets_count),
        status=200,
        mimetype='text/plain'
    )
