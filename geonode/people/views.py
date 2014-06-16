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

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic.list import ListView
from django.contrib.sites.models import Site
from django.conf import settings

from itertools import chain

from geonode.people.models import Profile
from geonode.people.forms import ProfileForm
from geonode.people.forms import ForgotUsernameForm
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document


@login_required
def profile_edit(request, username=None):
    if username is None:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return redirect("profile_browse")
    else:
        profile = get_object_or_404(Profile, username=username)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile profile updated.")
            return redirect(reverse('profile_detail', args=[request.user.username]))
    else:
        form = ProfileForm(instance=profile)

    return render(request, "people/profile_edit.html", {
        "form": form,
    })

def profile_detail(request, username):
    profile = get_object_or_404(Profile, username=username)
    # combined queryset from each model content type
    user_objects = profile.resourcebase_set.all()

    content_filter = 'all'

    if ('content' in request.GET):
      content = request.GET['content']
      if content != 'all':
          if (content == 'layers'):
              content_filter = 'layers'
              user_objects = user_objects.instance_of(Layer)
          if (content == 'maps'):
              content_filter = 'maps'
              user_objects = user_objects.instance_of(Map)
          if (content == 'documents'):
              content_filter = 'documents'
              user_objects = user_objects.instance_of(Document)

    sortby_field = 'date'
    if ('sortby' in request.GET):
        sortby_field = request.GET['sortby']
    if sortby_field == 'title':
        user_objects = user_objects.order_by('title')
    else:
        user_objects = user_objects.order_by('-date')
    
    return render(request, "people/profile_detail.html", {
        "profile": profile,
        "sortby_field": sortby_field,
        "content_filter": content_filter,
        "object_list": user_objects,
    })

def forgot_username(request):
    """ Look up a username based on an email address, and send an email
    containing the username if found"""

    username_form = ForgotUsernameForm()

    message = ''

    site = Site.objects.get_current()

    email_subject = _("Your username for " + site.name)

    if request.method == 'POST':
        username_form = ForgotUsernameForm(request.POST)
        if username_form.is_valid():

            users = get_user_model().objects.filter(
                        email=username_form.cleaned_data['email'])
            if len(users) > 0:
                username = users[0].username
                email_message = email_subject + " : " + username
                send_mail(email_subject, email_message,
                          settings.DEFAULT_FROM_EMAIL,
                          [username_form.cleaned_data['email']],
                          fail_silently=False)
                message = _("Your username has been emailed to you.")
            else:
                message = _("No user could be found with that email address.")

    return render_to_response('people/forgot_username_form.html',
        RequestContext(request, {
            'message': message,
            'form': username_form
    }))
