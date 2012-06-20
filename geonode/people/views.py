from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
from geonode.people.forms import ForgotUsernameForm

def forgot_username(request):
    """ Look up a username based on an email address, and send an email
    containing the username if found"""
    
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

    return render_to_response('people/forgot_username_form.html', RequestContext(request, {
        'message': message,
        'form' : username_form
    }))