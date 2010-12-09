from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from geonode.accountforms.forms import UserRegistrationForm
import logging

logger = logging.getLogger("geonode.accountforms.views")

ISITE_URL = "http://about.africamap.harvard.edu/icb/icb.do?keyword=k28501&pageid=icb.page129893&pageContentId=icb.pagecontent795722&state=maximize&login=yes"

def registerHarvard(request, success_url=None,
             form_class=UserRegistrationForm, profile_callback=None,
             template_name='registration/registration_form.html',
             extra_context=None):

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = form.save(profile_callback=profile_callback)
            # success_url needs to be dynamically generated here; setting a
            # a default value using reverse() will cause circular-import
            # problems with the default URLConf for this application, which
            # imports this file.
            if new_user.get_profile().is_harvard:
                request.session["harvard_username"] = new_user.username
                logger.debug("Set harvard username to [%s]", new_user.username)
                return HttpResponseRedirect(ISITE_URL)
            else:
                return HttpResponseRedirect(success_url or reverse('registration_complete'))
        else:
            form = form_class()
    
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(template_name,
                              { 'form': form },
                              context_instance=context)# Create your views here.


def registercompleteHarvard(request, template_name='registration/registration_complete.html',):
    
    if "harvard_username" in request.session:
        username = request.session["harvard_username"]
        logger.debug("Harvard username is [%s]", username)
        logger.debug("Referring URL is [%s]", request.META['HTTP_REFERRER'])
        if request.META['HTTP_REFERRER'] == ISITE_URL or request.META['HTTP_REFERRER'] == "http://worldmap.harvard.edu/accountforms/registercomplete":
            user = User.objects.get(username=username)
            user.is_staff = True
            user.save()
            del request.session["harvard_username"]
        
        userProfile = user.get_profile()
        userProfile.is_harvard = user.is_staff
        userProfile.save()
    return render_to_response(template_name)
        
            
            
            