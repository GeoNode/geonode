
"""
Custom views for creating, editing and viewing site-specific user profiles.

"""

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list
from geonode.profiles.forms import ContactProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime, timedelta
from profiles import utils

def edit_profile(request, form_class=None, success_url=None,
                 template_name='profiles/edit_profile.html',
                 extra_context=None):
    """
    Edit the current user's profile.
    
    If the user does not already have a profile (as determined by
    ``User.get_profile()``), a redirect will be issued to the
    :view:`profiles.views.create_profile` view; if no profile model
    has been specified in the ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.
    
    **Optional arguments:**
    
    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``form_class``
        The form class to use for validating and editing the user
        profile. This form class must operate similarly to a standard
        Django ``ModelForm`` in that it must accept an instance of the
        object to be edited as the keyword argument ``instance`` to
        its constructor, and it must implement a method named
        ``save()`` which will save the updates to the object. If this
        argument is not specified, this view will use a ``ModelForm``
        generated from the model specified in the
        ``AUTH_PROFILE_MODULE`` setting.
    
    ``success_url``
        The URL to redirect to following a successful edit. If not
        specified, this will default to the URL of
        :view:`profiles.views.profile_detail` for the profile object
        being edited.
    
    ``template_name``
        The template to use when displaying the profile-editing
        form. If not specified, this will default to
        :template:`profiles/edit_profile.html`.
    
    **Context:**
    
    ``form``
        The form for editing the profile.
        
    ``profile``
         The user's current profile.
    
    **Template:**
    
    ``template_name`` keyword argument or
    :template:`profiles/edit_profile.html`.
    
    """
    try:
        profile_obj = request.user.get_profile()
            
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('profiles_create_profile'))
    
    #
    # See the comment in create_profile() for discussion of why
    # success_url is set up here, rather than as a default value for
    # the argument.
    #
    
    if success_url is None:
        success_url = reverse('profiles_profile_detail',
                              kwargs={ 'username': request.user.username })
    if form_class is None:
        form_class = ContactProfileForm(instance=profile_obj)
    if request.method == 'POST':
        form = ContactProfileForm(data=request.POST, files=request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(success_url)
    else:
        form = ContactProfileForm(instance=profile_obj)
    
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value




    return render_to_response(template_name,
                              { 'form': form,
                                'profile': profile_obj,
                                'is_org_user': settings.USE_CUSTOM_ORG_AUTHORIZATION and profile_obj.is_org_member,
                                'is_org_current': settings.USE_CUSTOM_ORG_AUTHORIZATION and profile_obj.member_expiration_dt is not None and profile_obj.member_expiration_dt > datetime.today().date(),
                                'org_expiration_dt': datetime.today().date().strftime("%B %d %Y") if profile_obj.member_expiration_dt is None else profile_obj.member_expiration_dt.strftime("%B %d %Y")
                                },
                              context_instance=context)
edit_profile = login_required(edit_profile)