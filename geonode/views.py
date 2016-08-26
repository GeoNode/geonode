# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.db.models import Q
from django.template.response import TemplateResponse

from geonode import get_version
from geonode.base.templatetags.base_tags import facets
from geonode.groups.models import GroupProfile


class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()


def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
            content="ajax login requires HTTP POST",
            status=405,
            content_type="text/plain"
        )
    form = AjaxLoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse(
                content="bad credentials or disabled user",
                status=400,
                content_type="text/plain"
            )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(
                content="successful login",
                status=200,
                content_type="text/plain"
            )
    else:
        return HttpResponse(
            "The form you submitted doesn't look like a username/password combo.",
            content_type="text/plain",
            status=400)


def ajax_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            content_type='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            content_type='text/plain')
    keyword = request.POST['query']
    users = get_user_model().objects.filter(Q(username__istartswith=keyword) |
                                            Q(first_name__icontains=keyword) |
                                            Q(organization__icontains=keyword)).exclude(username='AnonymousUser')
    groups = GroupProfile.objects.filter(Q(title__istartswith=keyword) |
                                         Q(description__icontains=keyword))
    json_dict = {
        'users': [({'username': u.username}) for u in users],
        'count': users.count(),
    }

    json_dict['groups'] = [({'name': g.slug, 'title': g.title}) for g in groups]
    return HttpResponse(
        content=json.dumps(json_dict),
        content_type='text/plain'
    )


def err403(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(
            reverse('account_login') +
            '?next=' +
            request.get_full_path())
    else:
        return TemplateResponse(request, '401.html', {}, status=401).render()


def ident_json(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(
            reverse('account_login') +
            '?next=' +
            request.get_full_path())

    json_data = {}
    json_data['siteurl'] = settings.SITEURL
    json_data['name'] = settings.PYCSW['CONFIGURATION']['metadata:main']['identification_title']

    json_data['poc'] = {
        'name': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_name'],
        'email': settings.PYCSW['CONFIGURATION']['metadata:main']['contact_email'],
        'twitter': 'https://twitter.com/%s' % settings.TWITTER_SITE
    }

    json_data['version'] = get_version()

    json_data['services'] = {
        'csw': settings.CATALOGUE['default']['URL'],
        'ows': settings.OGC_SERVER['default']['LOCATION']
    }

    json_data['counts'] = facets({'request': request, 'facet_type': 'home'})

    return HttpResponse(content=json.dumps(json_data), mimetype='application/json')


def h_keywords(request):
    from geonode.base.models import HierarchicalKeyword as hk
    keywords = json.dumps(hk.dump_bulk_tree())
    return HttpResponse(content=keywords)
