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
from django.views.generic import ListView
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from taggit.models import Tag


from geonode import get_version
from geonode.base.templatetags.base_tags import facets
from geonode.groups.models import GroupProfile
from geonode.base.forms import TopicCategoryForm, TagForm
from geonode.base.libraries.decorators import superuser_check
from geonode.base.models import TopicCategory



class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()


@csrf_exempt
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
    users = get_user_model().objects.filter((Q(username__istartswith=keyword) |
                                            Q(first_name__icontains=keyword) |
                                            Q(organization__icontains=keyword)) & Q(is_active=True)).exclude(username='AnonymousUser')
    groups = GroupProfile.objects.filter(Q(title__istartswith=keyword) |
                                         Q(description__icontains=keyword))
    json_dict = {

        'users': [({'username': u.username, 'eamil': u.email }) for u in users],

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

#@jahangir091

@login_required
@user_passes_test(superuser_check)
def topiccategory_create(request):
    """
    This view is for adding topic category from web. Only super admin can add topic category
    """

    if request.method == 'POST':
        form = TopicCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.info(request, 'Added category successfully')
            return HttpResponseRedirect(reverse('topiccategory-list'))
    else:
        form = TopicCategoryForm()
    return render(request, "category/upload_category.html", {'form': form, })


@login_required
@user_passes_test(superuser_check)
def topiccategory_list(request, template='category/category_list.html'):
    """
    This view is for listing topic category from web. Only super admin can list topic category
    """
    context_dict = {
        "category_list": TopicCategory.objects.all(),
    }
    return render_to_response(template, RequestContext(request, context_dict))


@login_required
@user_passes_test(superuser_check)
def topiccategory_delete(request):
    """
    This view is for deleting topic category from web. Only super admin can delete topic category
    """

    if request.method == 'POST':
        cat_ids = request.POST.getlist('category_id')
        for id in cat_ids:
            cat_id = int(id)
            category = get_object_or_404(TopicCategory, pk=cat_id)
            status, resource = category.is_used_in_any_resource()
            if status:
                messages.info(request, 'Category "%s" cannot be deleted because this category is used in %s' %(category.gn_description, resource))
            else:
                category.delete()
                messages.info(request, 'Deleted category "%s" successfully' %(category.gn_description))
        return HttpResponseRedirect(reverse('topiccategory-list'))
    else:
        return HttpResponseRedirect(reverse('topiccategory-list'))



@login_required
@user_passes_test(superuser_check)
def keyword_create(request):
    """
    This view is for adding keyword from web. Only super admin can add keywords
    """

    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.info(request, 'Added keyword successfully')
            return HttpResponseRedirect(reverse('keyword-list'))
    else:
        form = TagForm()
    return render(request, "keywords/upload_keyword.html", {'form': form, })


@login_required
@user_passes_test(superuser_check)
def keyword_list(request, template='keywords/keyword_list.html'):
    """
    This view is for listing keywords from web. Only super admin can list keywords
    """
    context_dict = {
        "keyword_list": Tag.objects.all().order_by('name'),
    }
    return render_to_response(template, RequestContext(request, context_dict))


@login_required
@user_passes_test(superuser_check)
def keyword_delete(request):
    """
    This view is for deleting keyword from web. Only super admin can delete keyword
    """

    if request.method == 'POST':
        cat_ids = request.POST.getlist('keyword_id')
        for id in cat_ids:
            cat_id = int(id)
            keyword = get_object_or_404(Tag, pk=cat_id)
            keyword.delete()
            messages.info(request, 'Deleted keyword "%s" successfully' %(keyword.name))
        return HttpResponseRedirect(reverse('keyword-list'))
    else:
        return HttpResponseRedirect(reverse('keyword-list'))
#end

