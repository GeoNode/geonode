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

from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from django.db.models import Q
from django.template import RequestContext
from geonode.utils import ogc_server_settings

def index(request, template='index.html'):
    from geonode.search.views import search_page
    post = request.POST.copy()
    post.update({'type': 'layer'})
    request.POST = post
    return search_page(request, template=template)

class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()

def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
                content="ajax login requires HTTP POST",
                status=405,
                mimetype="text/plain"
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
                    mimetype="text/plain"
                )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(
                    content="successful login",
                    status=200,
                    mimetype="text/plain"
                )
    else:
        return HttpResponse(
                "The form you submitted doesn't look like a username/password combo.",
                mimetype="text/plain",
                status=400
            )

def ajax_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            mimetype='text/plain'
        )
    keyword = request.POST['query']
    users = User.objects.filter(Q(username__startswith=keyword) |
        Q(profile__name__contains=keyword) | 
        Q(profile__organization__contains=keyword))
    json_dict = {
        'users': [({'username': u.username}) for u in users],
        'count': users.count(),
    }
    return HttpResponse(
        content=json.dumps(json_dict),
        mimetype='text/plain'
    )

def _handleThumbNail(req, obj):
    # object will either be a map or a layer, one or the other permission must apply
    if not req.user.has_perm('maps.change_map', obj=obj) and not req.user.has_perm('maps.change_layer', obj=obj):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(req, {'error_message':
                _("You are not permitted to modify this object")})), status=401)
    if req.method == 'GET':
        return HttpResponseRedirect(obj.get_thumbnail_url())
    elif req.method == 'POST':
        try:
            spec = _fixup_ows_url(req.raw_post_data)
            obj.save_thumbnail(spec)
            return HttpResponseRedirect(obj.get_thumbnail_url())
        except:
            return HttpResponse(
                content='error saving thumbnail',
                status=500,
                mimetype='text/plain'
            )

def _fixup_ows_url(thumb_spec):
    #@HACK - for whatever reason, a map's maplayers ows_url contains only /geoserver/wms
    # so rendering of thumbnails fails - replace those uri's with full geoserver URL
    import re
    gspath = '"' + ogc_server_settings.public_url # this should be in img src attributes
    repl = '"' + ogc_server_settings.LOCATION
    return re.sub(gspath, repl, thumb_spec)

def err403(request):
    return HttpResponseRedirect(reverse('account_login') + '?next=' + request.get_full_path())