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


# Geonode functionality
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from guardian.shortcuts import get_objects_for_user
from dal import views, autocomplete
from user_messages.models import Message

from geonode.base.utils import OwnerRightsRequestViewUtils
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.base.models import ResourceBase, Region, HierarchicalKeyword, ThesaurusKeywordLabel
from geonode.utils import resolve_object
from geonode.security.utils import get_visible_resources
from geonode.base.forms import BatchEditForm, OwnerRightsRequestForm
from geonode.base.forms import CuratedThumbnailForm
from geonode.notifications_helper import send_notification


def batch_modify(request, ids, model):
    if not request.user.is_superuser:
        raise PermissionDenied
    if model == 'Document':
        Resource = Document
    if model == 'Layer':
        Resource = Layer
    if model == 'Map':
        Resource = Map
    template = 'base/batch_edit.html'

    if "cancel" in request.POST:
        return HttpResponseRedirect(
            '/admin/{model}s/{model}/'.format(model=model.lower())
        )

    if request.method == 'POST':
        form = BatchEditForm(request.POST)
        if form.is_valid():
            for resource in Resource.objects.filter(id__in=ids.split(',')):
                resource.group = form.cleaned_data['group'] or resource.group
                resource.owner = form.cleaned_data['owner'] or resource.owner
                resource.category = form.cleaned_data['category'] or resource.category
                resource.license = form.cleaned_data['license'] or resource.license
                resource.date = form.cleaned_data['date'] or resource.date
                resource.language = form.cleaned_data['language'] or resource.language
                new_region = form.cleaned_data['regions']
                if new_region:
                    resource.regions.add(new_region)
                keywords = form.cleaned_data['keywords']
                if keywords:
                    resource.keywords.clear()
                    for word in keywords.split(','):
                        resource.keywords.add(word.strip())
                resource.save(notify=True)
            return HttpResponseRedirect(
                '/admin/{model}s/{model}/'.format(model=model.lower())
            )
        return render(
            request,
            template,
            context={
                'form': form,
                'ids': ids,
                'model': model,
            }
        )

    form = BatchEditForm()
    return render(
        request,
        template,
        context={
            'form': form,
            'ids': ids,
            'model': model,
        }
    )


def thumbnail_upload(
        request,
        res_id,
        template='base/thumbnail_upload.html'):
    try:
        res = resolve_object(
            request, ResourceBase, {
                'id': res_id}, 'base.change_resourcebase')
    except PermissionDenied:
        return HttpResponse(
            'You are not allowed to change permissions for this resource',
            status=401,
            content_type='text/plain')

    form = CuratedThumbnailForm()

    if request.method == 'POST':
        if 'remove-thumb' in request.POST:
            if hasattr(res, 'curatedthumbnail'):
                res.curatedthumbnail.delete()
        else:
            form = CuratedThumbnailForm(request.POST, request.FILES)
            if form.is_valid():
                ct = form.save(commit=False)
                # remove existing thumbnail if any
                if hasattr(res, 'curatedthumbnail'):
                    res.curatedthumbnail.delete()
                ct.resource = res
                ct.save()
        return HttpResponseRedirect(request.path_info)

    return render(request, template, context={
        'resource': res,
        'form': form
    })


class SimpleSelect2View(autocomplete.Select2QuerySetView):
    """ Generic select2 view for autocompletes
        Params:
            model: model to perform the autocomplete query on
            filter_arg: property to filter with ie. name__icontains
    """

    def __init__(self, *args, **kwargs):
        super(views.BaseQuerySetView, self).__init__(*args, **kwargs)
        if not hasattr(self, 'filter_arg'):
            raise AttributeError("SimpleSelect2View missing required 'filter_arg' argument")

    def get_queryset(self):
        qs = super(views.BaseQuerySetView, self).get_queryset()

        if self.q:
            qs = qs.filter(**{self.filter_arg: self.q})
        return qs


class ResourceBaseAutocomplete(autocomplete.Select2QuerySetView):
    """ Base resource autocomplete - searches all the resources by title
        returns any visible resources in this queryset for autocomplete
    """

    def get_queryset(self):
        request = self.request

        permitted = get_objects_for_user(request.user, 'base.view_resourcebase')
        qs = ResourceBase.objects.all().filter(id__in=permitted)

        if self.q:
            qs = qs.filter(title__icontains=self.q).order_by('title')

        return get_visible_resources(
            qs,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)[:100]


class RegionAutocomplete(SimpleSelect2View):
    model = Region
    filter_arg = 'name__icontains'


class HierarchicalKeywordAutocomplete(SimpleSelect2View):
    model = HierarchicalKeyword
    filter_arg = 'slug__icontains'


class ThesaurusKeywordLabelAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        thesaurus = settings.THESAURUS
        tname = thesaurus['name']
        lang = 'en'

        # Filters thesaurus results based on thesaurus name and language
        qs = ThesaurusKeywordLabel.objects.all().filter(
            keyword__thesaurus__identifier=tname,
            lang=lang
        )

        if self.q:
            qs = qs.filter(label__icontains=self.q)

        return qs

    # Overides the get results method to return custom json to frontend
    def get_results(self, context):
        return [
            {
                'id': self.get_result_value(result.keyword),
                'text': self.get_result_label(result),
                'selected_text': self.get_selected_result_label(result),
            } for result in context['object_list']
        ]


class OwnerRightsRequestView(LoginRequiredMixin, FormView):
    template_name = 'owner_rights_request.html'
    form_class = OwnerRightsRequestForm
    resource = None
    redirect_field_name = 'next'

    def get_success_url(self):
        return self.resource.get_absolute_url()

    def get(self, request, *args, **kwargs):
        r_base = ResourceBase.objects.get(pk=kwargs.get('pk'))
        self.resource = OwnerRightsRequestViewUtils.get_resource(r_base)
        initial = {
            'resource': r_base
        }
        form = self.form_class(initial=initial)
        return render(request, self.template_name, {'form': form, 'resource': self.resource})

    def post(self, request, *args, **kwargs):
        r_base = ResourceBase.objects.get(pk=kwargs.get('pk'))
        self.resource = OwnerRightsRequestViewUtils.get_resource(r_base)
        form = self.form_class(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            notice_type_label = 'request_resource_edit'
            recipients = OwnerRightsRequestViewUtils.get_message_recipients()

            Message.objects.new_message(
                from_user=request.user,
                to_users=recipients,
                subject=_('System message: A request to modify resource'),
                content=_('The resource owner has requested to modify the resource') + '.'
                ' ' +
                _('Resource title') + ': ' + self.resource.title + '.'
                ' ' +
                _('Reason for the request') + ': "' + reason + '".' +
                ' ' +
                _('To allow the change, set the resource to not "Approved" under the metadata settings' +
                  'and write message to the owner to notify him') + '.'
            )
            send_notification(recipients, notice_type_label, {
                'resource': self.resource,
                'site_url': settings.SITEURL[:-1],
                'reason': reason
            })
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
