from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

class ProfileRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/profile_request_list.html'
    raise_exception = True
    
    
def profile_request_detail(request, pk, template='datarequests/profile_detail.html'):

    profile_request = get_object_or_404(ProfileRequest, pk=pk)

    if not request.user.is_superuser and not profile_request.profile == request.user:
        raise PermissionDenied


    #if not profile_request.date:
    #    raise Http404

    context_dict={"profile_request": profile_request}

    context_dict["request_reject_form"]= RejectionForm(instance=profile_request)

    return render_to_response(template, RequestContext(request, context_dict))

def data_profile_request_approve(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        profile_request = get_object_or_404(ProfileRequest, pk=pk)

        if not profile_request.has_verified_email or profile_request.request_status != 'pending':
            raise PermissionDenied

        result = True
        message = ''
        is_new_acc=True

        if not profile_request.profile or not profile_request.username or not profile_request.ftp_folder:
            result, message = profile_request.create_account() #creates account in AD if AD profile does not exist
        else:
            is_new_acc = False

        if not result:
            messages.error (request, _(message))
        else:
            profile_request.profile.organization_type = profile_request.organization_type
            profile_request.profile.organization_other = profile_request.organization_other
            profile_request.profile.save()

            profile_request.set_approved(is_new_acc)

        return HttpResponseRedirect(profile_request.get_absolute_url())

    else:
        return HttpResponseRedirect("/forbidden/")
