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
import json
import logging

from dal import views, autocomplete
from user_messages.models import Message
from guardian.shortcuts import get_objects_for_user

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import FormView
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import get_language

# Geonode dependencies
from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.utils import resolve_object
from geonode.base import register_event
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile
from geonode.tasks.tasks import set_permissions
from geonode.resource.manager import resource_manager
from geonode.security.utils import get_visible_resources
from geonode.notifications_helper import send_notification
from geonode.base.utils import OwnerRightsRequestViewUtils, remove_country_from_languagecode
from geonode.base.forms import UserAndGroupPermissionsForm

from geonode.base.forms import (
    BatchEditForm,
    OwnerRightsRequestForm
)
from geonode.base.models import (
    Region,
    ResourceBase,
    HierarchicalKeyword,
    ThesaurusKeyword,
    ThesaurusKeywordLabel
)

logger = logging.getLogger(__name__)


def get_url_for_app_model(model, model_class):
    return reverse(f'admin:{model_class._meta.app_label}_{model}_changelist')
    # was: return f'/admin/{model_class._meta.app_label}/{model}/'


def get_url_for_model(model):
    url = f'admin:{model.lower()}s_{model.lower()}_changelist'
    if model.lower() == 'dataset':
        url = f'admin:layers_{model.lower()}_changelist'
    return reverse(url)
    # was: f'/admin/{model.lower()}s/{model.lower()}/'


def user_and_group_permission(request, model):
    if not request.user.is_superuser:
        raise PermissionDenied

    model_mapper = {
        "profile": get_user_model(),
        "groupprofile": GroupProfile
    }

    model_class = model_mapper[model]

    ids = request.POST.get("ids")
    if "cancel" in request.POST or not ids:
        return HttpResponseRedirect(
            get_url_for_app_model(model, model_class))

    if request.method == 'POST':
        form = UserAndGroupPermissionsForm(request.POST)
        ids = ids.split(",")
        if form.is_valid():
            resources_names = [layer.name for layer in form.cleaned_data.get('layers')]
            users_usernames = [user.username for user in model_class.objects.filter(
                id__in=ids)] if model == 'profile' else None
            groups_names = [group_profile.group.name for group_profile in model_class.objects.filter(
                id__in=ids)] if model in ('group', 'groupprofile') else None

            if users_usernames and 'AnonymousUser' in users_usernames and \
                    (not groups_names or 'anonymous' not in groups_names):
                if not groups_names:
                    groups_names = []
                groups_names.append('anonymous')
            if groups_names and 'anonymous' in groups_names and \
                    (not users_usernames or 'AnonymousUser' not in users_usernames):
                if not users_usernames:
                    users_usernames = []
                users_usernames.append('AnonymousUser')

            delete_flag = form.cleaned_data.get('mode') == 'unset'
            permissions_names = form.cleaned_data.get('permission_type')

            if permissions_names:
                set_permissions.apply_async(
                    (permissions_names, resources_names, users_usernames, groups_names, delete_flag))

        return HttpResponseRedirect(
            get_url_for_app_model(model, model_class))

    form = UserAndGroupPermissionsForm({
        'permission_type': ('r', ),
        'mode': 'set',
    })
    return render(
        request,
        "base/user_and_group_permissions.html",
        context={
            "form": form,
            "model": model
        }
    )


def batch_modify(request, model):
    if not request.user.is_superuser:
        raise PermissionDenied
    if model == 'Document':
        Resource = Document
    if model == 'Dataset':
        Resource = Dataset
    if model == 'Map':
        Resource = Map
    template = 'base/batch_edit.html'
    ids = request.POST.get("ids")

    if "cancel" in request.POST or not ids:
        return HttpResponseRedirect(
            get_url_for_model(model))

    if request.method == 'POST':
        form = BatchEditForm(request.POST)
        if form.is_valid():
            keywords = [keyword.strip() for keyword in
                        form.cleaned_data.pop("keywords").split(',') if keyword]
            regions = form.cleaned_data.pop("regions")
            ids = form.cleaned_data.pop("ids")
            if not form.cleaned_data.get("date"):
                form.cleaned_data.pop("date")

            to_update = {}
            for _key, _value in form.cleaned_data.items():
                if _value:
                    to_update[_key] = _value
            resources = Resource.objects.filter(id__in=ids.split(','))
            resources.update(**to_update)
            if regions:
                regions_through = Resource.regions.through
                new_regions = [regions_through(region=regions, resourcebase=resource) for resource in resources]
                regions_through.objects.bulk_create(new_regions, ignore_conflicts=True)

            if keywords:
                keywords_through = Resource.keywords.through
                keywords_through.objects.filter(content_object__in=resources).delete()

                def get_or_create(keyword):
                    try:
                        return HierarchicalKeyword.objects.get(name=keyword)
                    except HierarchicalKeyword.DoesNotExist:
                        return HierarchicalKeyword.add_root(name=keyword)
                hierarchical_keyword = [get_or_create(keyword) for keyword in keywords]

                new_keywords = []
                for keyword in hierarchical_keyword:
                    new_keywords += [keywords_through(
                        content_object=resource, tag_id=keyword.pk) for resource in resources]
                keywords_through.objects.bulk_create(new_keywords, ignore_conflicts=True)

            return HttpResponseRedirect(
                get_url_for_model(model))

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


class ThesaurusAvailable(autocomplete.Select2QuerySetView):
    def get_queryset(self):

        tid = self.request.GET.get("sysid")
        lang = get_language()
        keyword_id_for_given_thesaurus = ThesaurusKeyword.objects.filter(thesaurus_id=tid)

        # try find results found for given language e.g. (en-us) if no results found remove country code from language to (en) and try again
        qs_keyword_ids = ThesaurusKeywordLabel.objects.filter(lang=lang, keyword_id__in=keyword_id_for_given_thesaurus).values("keyword_id")
        if len(qs_keyword_ids) == 0:
            lang = remove_country_from_languagecode(lang)
            qs_keyword_ids = ThesaurusKeywordLabel.objects.filter(lang=lang, keyword_id__in=keyword_id_for_given_thesaurus).values("keyword_id")

        not_qs_ids = ThesaurusKeywordLabel.objects.exclude(keyword_id__in=qs_keyword_ids).order_by("keyword_id").distinct("keyword_id").values("keyword_id")
        qs = ThesaurusKeywordLabel.objects.filter(lang=lang, keyword_id__in=keyword_id_for_given_thesaurus)
        if self.q:
            qs = qs.filter(label__istartswith=self.q)

        qs_local = list(qs)
        qs_non_local = list(keyword_id_for_given_thesaurus.filter(id__in=not_qs_ids))
        return qs_local + qs_non_local

    def get_results(self, context):
        return [
            {
                'id': str(result.keyword.pk) if isinstance(result, ThesaurusKeywordLabel) else str(result.pk),
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
            recipients = OwnerRightsRequestViewUtils.get_message_recipients(self.resource.owner)

            Message.objects.new_message(
                from_user=request.user,
                to_users=recipients,
                subject=_('System message: A request to modify resource'),
                content=_('The resource owner has requested to modify the resource') + '.\n'
                ' ' +
                _('Resource title') + ': ' + self.resource.title + '.\n'
                ' ' +
                _('Reason for the request') + ': "' + reason + '".\n' +
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


@login_required
def resource_clone(request):
    try:
        uuid = request.POST['uuid']
        resource = resolve_object(
            request, ResourceBase, {
                'uuid': uuid}, 'base.change_resourcebase')
    except PermissionDenied:
        return HttpResponse("Not allowed", status=403)
    except Exception:
        raise Http404("Not found")
    if not resource:
        raise Http404("Not found")

    out = {}
    try:
        getattr(resource_manager, "copy")(
            resource.get_real_instance(),
            uuid=None,
            defaults={
                'user': request.user})
        out['success'] = True
        out['message'] = _("Resource Cloned Successfully!")
    except Exception as e:
        logger.exception(e)
        out['success'] = False
        out['message'] = _(f"Error Occurred while Cloning the Resource: {e}")
        out['errors'] = str(e)

    if out['success']:
        status_code = 200
        register_event(request, 'change', resource)
    else:
        status_code = 400

    return HttpResponse(
        json.dumps(out),
        content_type='application/json',
        status=status_code)
