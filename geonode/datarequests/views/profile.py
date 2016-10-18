
class ProfileRequestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/profile_request_list.html'
    raise_exception = True
    
    
def profile_request_detail(request, pk, template='datarequests/profile_detail.html'):

    profile_request = get_object_or_404(ProfileRequest, pk=pk)

    if not request.user.is_superuser and not request_profile.profile == request.user:
        raise PermissionDenied


    #if not request_profile.date:
    #    raise Http404

    context_dict={"request_profile": profile_request}

    context_dict["request_reject_form"]= RejectionForm(instance=profile_request)

    return render_to_response(template, RequestContext(request, context_dict))

def data_request_profile_approve(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied
    if not request.method == 'POST':
        raise PermissionDenied

    if request.method == 'POST':
        request_profile = get_object_or_404(ProfileRequest, pk=pk)

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
            request_profile.profile.organization_type = request_profile.organization_type
            request_profile.profile.organization_other = request_profile.organization_other
            request_profile.profile.save()

            if request_profile.jurisdiction_shapefile:
                request_profile.assign_jurisdiction() #assigns/creates jurisdiction object
                #place_name_update.delay([request_profile])
                #compute_size_update.delay([request_profile])
                assign_grid_refs.delay(request_profile.profile)
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
