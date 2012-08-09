#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

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
