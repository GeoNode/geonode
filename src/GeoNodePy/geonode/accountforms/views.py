from datetime import datetime, timedelta
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from geonode.accountforms.forms import UserRegistrationForm, ForgotUsernameForm
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
import logging

logger = logging.getLogger("geonode.accountforms.views")

def forgotUsername(request,template_name='registration/username_form.html'):

    username_form = ForgotUsernameForm()
    message = ''

    email_subject = _("Your username for ") + settings.SITENAME


    if request.method == 'POST':
        username_form = ForgotUsernameForm(request.POST)
        if username_form.is_valid():

            users = User.objects.filter(email=username_form.cleaned_data['email'])
            if len(users) > 0:
                username = users[0].username
                email_message = email_subject + " : " + username
                send_mail(email_subject, email_message, settings.DEFAULT_FROM_EMAIL,
                    [username_form.cleaned_data['email']], fail_silently=False)
                message = _("Your username has been emailed to you.")
            else:
                message = _("No user could be found with that email address.")


    return render_to_response(template_name, RequestContext(request, {
        'message': message,
        'form' : username_form
        }))



def confirm(request):
    if request.user and settings.CUSTOM_ORG_AUTH_URL is not None:
        request.session["group_username"] = request.user.username
        logger.debug("group username set to [%s]", request.user.username)
        return HttpResponseRedirect(settings.CUSTOM_ORG_AUTH_URL)
    else:
        return HttpResponseRedirect("/")


def registerOrganizationUser(request, success_url=None,
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
            if new_user.get_profile().is_org_member:
                request.session["group_username"] = new_user.username
                logger.debug("group username set to [%s]", new_user.username)
                return HttpResponseRedirect(settings.CUSTOM_ORG_AUTH_URL)
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


def registercompleteOrganizationUser(request, template_name='registration/registration_complete.html',):

    if settings.ORG_AUTH_COOKIE in request.COOKIES:
        username = request.session["group_username"]
        user = User.objects.get(username=username)
        userProfile = user.get_profile()
        if user:
            userProfile.is_org_member = True
            userProfile.member_expiration_dt = datetime.today() + timedelta(days=365)
            userProfile.save()
            del request.session["group_username"]
            #else:
            #    userProfile.is_org_member = False
            #    userProfile.save()
            if user.is_active:
                return HttpResponseRedirect(user.get_profile().get_absolute_url())
    else:
        logger.debug("harvard username is not found")
        if request.user and  request.user.is_active:
                return HttpResponseRedirect(request.user.get_profile().get_absolute_url())

    return render_to_response(template_name, RequestContext(request))