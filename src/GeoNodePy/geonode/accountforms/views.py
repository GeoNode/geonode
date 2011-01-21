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
                logger.debug("harvard username set to [%s]", new_user.username)
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
        user = User.objects.get(username=username)
        userProfile = user.get_profile()
        if user:
            logger.debug("harvard username is [%s]", username)
            logger.debug("page referrer is [%s]", request.META['HTTP_REFERER'])
            if 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'] == ISITE_URL or request.META['HTTP_REFERER'] == "http://worldmap.harvard.edu/accounts/registercomplete/":
                userProfile.is_harvard = True
                userProfile.save()
                del request.session["harvard_username"]
            else:
                userProfile.is_harvard = False
                userProfile.save()
    else:
        logger.debug("harvard username is not found")
    return render_to_response(template_name, RequestContext(request))