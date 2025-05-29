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
import ast
import warnings
import traceback

from dal import views, autocomplete
from user_messages.models import Message
from guardian.shortcuts import get_objects_for_user

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import FormView
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
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

from geonode.base.forms import BatchEditForm, OwnerRightsRequestForm
from geonode.base.models import Region, ResourceBase, HierarchicalKeyword, ThesaurusKeyword, ThesaurusKeywordLabel

from geonode.base.enumerations import SOURCE_TYPE_LOCAL

from geonode.client.hooks import hookset
from geonode.people.forms import ProfileForm
from geonode.monitoring.models import EventType
from geonode.base.auth import get_or_create_token
from geonode.security.views import _perms_info_json
from geonode.security.utils import get_user_visible_groups
from geonode.decorators import check_keyword_write_perms

from geonode.base.forms import CategoryForm, TKeywordForm, ThesaurusAvailableForm
from geonode.base.models import Thesaurus, TopicCategory

from .forms import ResourceBaseForm

logger = logging.getLogger(__name__)


def get_url_for_app_model(model, model_class):
    return reverse(f"admin:{model_class._meta.app_label}_{model}_changelist")
    # was: return f'/admin/{model_class._meta.app_label}/{model}/'


def get_url_for_model(model):
    url = f"admin:{model.lower()}s_{model.lower()}_changelist"
    if model.lower() == "dataset":
        url = f"admin:layers_{model.lower()}_changelist"
    return reverse(url)
    # was: f'/admin/{model.lower()}s/{model.lower()}/'


def user_and_group_permission(request, model):
    if not request.user.is_superuser:
        raise PermissionDenied

    model_mapper = {"profile": get_user_model(), "groupprofile": GroupProfile}

    model_class = model_mapper[model]

    ids = request.POST.get("ids")
    if "cancel" in request.POST or not ids:
        return HttpResponseRedirect(get_url_for_app_model(model, model_class))

    users_usernames = None
    groups_names = None

    if request.method == "POST":
        form = UserAndGroupPermissionsForm(request.POST)
        ids = ids.split(",")
        _message = ""
        _errors = False
        if form.is_valid():
            resources_names = form.cleaned_data.get("layers")
            users_usernames = (
                [user.username for user in model_class.objects.filter(id__in=ids)] if model == "profile" else None
            )
            groups_names = (
                [group_profile.group.name for group_profile in model_class.objects.filter(id__in=ids)]
                if model in ("group", "groupprofile")
                else None
            )

            if (
                users_usernames
                and "AnonymousUser" in users_usernames
                and (not groups_names or "anonymous" not in groups_names)
            ):
                if not groups_names:
                    groups_names = []
                groups_names.append("anonymous")
            if (
                groups_names
                and "anonymous" in groups_names
                and (not users_usernames or "AnonymousUser" not in users_usernames)
            ):
                if not users_usernames:
                    users_usernames = []
                users_usernames.append("AnonymousUser")

            delete_flag = form.cleaned_data.get("mode") == "unset"
            permissions_names = form.cleaned_data.get("permission_type")

            if permissions_names:
                if "edit" in permissions_names and users_usernames and "AnonymousUser" in users_usernames:
                    if not _errors:
                        _message = '"EDIT" permissions not allowed for the "AnonymousUser".'
                        _errors = True
                else:
                    set_permissions.apply_async(
                        args=([permissions_names], resources_names, users_usernames, groups_names, delete_flag),
                        expiration=30,
                    )
                    if not _errors:
                        _message = f'The asyncronous permissions {form.cleaned_data.get("mode")} request for {", ".join(users_usernames or groups_names)} has been sent'
            else:
                if not _errors:
                    _message = "No permissions have been set."
                    _errors = True
        else:
            if not _errors:
                _message = f"Some error has occured {form.errors}"
                _errors = True

            if "layers" in form.errors and "invalid_choice" in (x.code for x in form.errors["layers"].data):
                _invalid_dataset_id = []
                for el in form.errors["layers"]:
                    _invalid_dataset_id.extend([x for x in el.split(" ") if x.isnumeric()])
                _message = f"The following dataset ID selected are not part of the available choices: {','.join(_invalid_dataset_id)}. They are probably in a dirty state, Please try again later"

        messages.add_message(request, (messages.INFO if not _errors else messages.ERROR), _message)
        return HttpResponseRedirect(get_url_for_app_model(model, model_class))

    form = UserAndGroupPermissionsForm(
        {
            "permission_type": "view",
            "mode": "set",
        }
    )
    return render(request, "base/user_and_group_permissions.html", context={"form": form, "model": model})


def batch_modify(request, model):
    if not request.user.is_superuser:
        raise PermissionDenied
    if model == "Document":
        Resource = Document
    if model == "Dataset":
        Resource = Dataset
    if model == "Map":
        Resource = Map
    template = "base/batch_edit.html"
    ids = request.POST.get("ids")

    if "cancel" in request.POST or not ids:
        return HttpResponseRedirect(get_url_for_model(model))

    if request.method == "POST":
        form = BatchEditForm(request.POST)
        if form.is_valid():
            keywords = [keyword.strip() for keyword in form.cleaned_data.pop("keywords").split(",") if keyword]
            regions = form.cleaned_data.pop("regions")
            ids = form.cleaned_data.pop("ids")
            if not form.cleaned_data.get("date"):
                form.cleaned_data.pop("date")

            to_update = {}
            for _key, _value in form.cleaned_data.items():
                if _value:
                    to_update[_key] = _value
            resources = Resource.objects.filter(id__in=ids.split(","))
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
                    new_keywords += [
                        keywords_through(content_object=resource, tag_id=keyword.pk) for resource in resources
                    ]
                keywords_through.objects.bulk_create(new_keywords, ignore_conflicts=True)

            return HttpResponseRedirect(get_url_for_model(model))

        return render(
            request,
            template,
            context={
                "form": form,
                "ids": ids,
                "model": model,
            },
        )

    form = BatchEditForm()
    return render(
        request,
        template,
        context={
            "form": form,
            "ids": ids,
            "model": model,
        },
    )


class SimpleSelect2View(autocomplete.Select2QuerySetView):
    """Generic select2 view for autocompletes
    Params:
        model: model to perform the autocomplete query on
        filter_arg: property to filter with ie. name__icontains
    """

    def __init__(self, *args, **kwargs):
        super(views.BaseQuerySetView, self).__init__(*args, **kwargs)
        if not hasattr(self, "filter_arg"):
            raise AttributeError("SimpleSelect2View missing required 'filter_arg' argument")

    def get_queryset(self):
        qs = super(views.BaseQuerySetView, self).get_queryset().order_by("pk")

        if self.q:
            qs = qs.filter(**{self.filter_arg: self.q})
        return qs


class ResourceBaseAutocomplete(autocomplete.Select2QuerySetView):
    """Base resource autocomplete - searches all the resources by title
    returns any visible resources in this queryset for autocomplete
    """

    def get_queryset(self):
        request = self.request

        permitted = get_objects_for_user(request.user, "base.view_resourcebase")
        qs = ResourceBase.objects.all().filter(id__in=permitted)

        if self.q:
            qs = qs.filter(title__icontains=self.q).order_by("title")

        return get_visible_resources(
            qs,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
        )[:100]


class LinkedResourcesAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ResourceBase.objects.order_by("title")

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        if self.forwarded and "exclude" in self.forwarded:
            qs = qs.exclude(pk=self.forwarded["exclude"])

        return get_visible_resources(
            qs,
            self.request.user if self.request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES,
        )

    def get_result_label(self, result):
        return f"{result.title} [{_(result.polymorphic_ctype.model)}]"


class RegionAutocomplete(SimpleSelect2View):
    model = Region
    filter_arg = "name__icontains"


class HierarchicalKeywordAutocomplete(SimpleSelect2View):
    model = HierarchicalKeyword
    filter_arg = "slug__icontains"


class ThesaurusKeywordLabelAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        thesaurus = settings.THESAURUS
        tname = thesaurus["name"]
        lang = "en"

        # Filters thesaurus results based on thesaurus name and language
        qs = ThesaurusKeywordLabel.objects.all().filter(keyword__thesaurus__identifier=tname, lang=lang)

        if self.q:
            qs = qs.filter(label__icontains=self.q)

        return qs

    # Overides the get results method to return custom json to frontend
    def get_results(self, context):
        return [
            {
                "id": self.get_result_value(result.keyword),
                "text": self.get_result_label(result),
                "selected_text": self.get_selected_result_label(result),
            }
            for result in context["object_list"]
        ]


class DatasetsAutocomplete(SimpleSelect2View):
    model = Dataset
    filter_arg = "title__icontains"

    def get_results(self, context):
        return [
            {
                "id": self.get_result_value(result),
                "text": self.get_result_label(result.title),
                "selected_text": self.get_selected_result_label(result.title),
            }
            for result in context["object_list"]
        ]


class ThesaurusAvailable(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        tid = self.request.GET.get("sysid")
        lang = get_language()
        keyword_id_for_given_thesaurus = ThesaurusKeyword.objects.filter(thesaurus_id=tid)

        # try find results found for given language e.g. (en-us) if no results found remove country code from language to (en) and try again
        qs_keyword_ids = ThesaurusKeywordLabel.objects.filter(
            lang=lang, keyword_id__in=keyword_id_for_given_thesaurus
        ).values("keyword_id")
        if len(qs_keyword_ids) == 0:
            lang = remove_country_from_languagecode(lang)
            qs_keyword_ids = ThesaurusKeywordLabel.objects.filter(
                lang=lang, keyword_id__in=keyword_id_for_given_thesaurus
            ).values("keyword_id")

        not_qs_ids = (
            ThesaurusKeywordLabel.objects.exclude(keyword_id__in=qs_keyword_ids)
            .order_by("keyword_id")
            .distinct("keyword_id")
            .values("keyword_id")
        )
        qs = ThesaurusKeywordLabel.objects.filter(lang=lang, keyword_id__in=keyword_id_for_given_thesaurus)
        if self.q:
            qs = qs.filter(label__istartswith=self.q)

        qs_local = list(qs)
        qs_non_local = list(keyword_id_for_given_thesaurus.filter(id__in=not_qs_ids))
        return qs_local + qs_non_local

    def get_results(self, context):
        return [
            {
                "id": str(result.keyword.pk) if isinstance(result, ThesaurusKeywordLabel) else str(result.pk),
                "text": self.get_result_label(result),
                "selected_text": self.get_selected_result_label(result),
            }
            for result in context["object_list"]
        ]


class OwnerRightsRequestView(LoginRequiredMixin, FormView):
    template_name = "owner_rights_request.html"
    form_class = OwnerRightsRequestForm
    resource = None
    redirect_field_name = "next"

    def get_success_url(self):
        return self.resource.get_absolute_url()

    def get(self, request, *args, **kwargs):
        r_base = ResourceBase.objects.get(pk=kwargs.get("pk"))
        self.resource = OwnerRightsRequestViewUtils.get_resource(r_base)
        initial = {"resource": r_base}
        form = self.form_class(initial=initial)
        return render(request, self.template_name, {"form": form, "resource": self.resource})

    def post(self, request, *args, **kwargs):
        r_base = ResourceBase.objects.get(pk=kwargs.get("pk"))
        self.resource = OwnerRightsRequestViewUtils.get_resource(r_base)
        form = self.form_class(request.POST)
        if form.is_valid():
            reason = form.cleaned_data["reason"]
            notice_type_label = "request_resource_edit"
            recipients = OwnerRightsRequestViewUtils.get_message_recipients(self.resource.owner)

            Message.objects.new_message(
                from_user=request.user,
                to_users=recipients,
                subject=_("System message: A request to modify resource"),
                content=_("The resource owner has requested to modify the resource") + ".\n"
                " " + _("Resource title") + ": " + self.resource.title + ".\n"
                " "
                + _("Reason for the request")
                + ': "'
                + reason
                + '".\n'
                + " "
                + _(
                    'To allow the change, set the resource to not "Approved" under the metadata settings'
                    + "and write message to the owner to notify him"
                )
                + ".",
            )
            send_notification(
                recipients,
                notice_type_label,
                {"resource": self.resource, "site_url": settings.SITEURL[:-1], "reason": reason},
            )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


logger = logging.getLogger("geonode.base.metadata")

_PERMISSION_MSG_GENERIC = _("You do not have permissions for this resource.")
_PERMISSION_MSG_METADATA = _("You are not allowed to modify this resource's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this resource.")


def _resolve_resourcebase(request, id, permission="base.change_resourcebase", msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the resourcebase by the provided typename and check the optional permission.
    """

    return resolve_object(request, ResourceBase, {"pk": id}, permission=permission, permission_msg=msg, **kwargs)


@xframe_options_sameorigin
def resourcebase_embed(request, resourcebaseid, template="base/base_edit.html"):
    """
    The view that returns the app composer opened to
    the app with the given app ID.
    """
    try:
        resourcebase_obj = _resolve_resourcebase(
            request, resourcebaseid, "base.view_resourcebase", _PERMISSION_MSG_VIEW
        )
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not resourcebase_obj:
        raise Http404(_("Not found"))

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(resourcebase_obj)

    perms_list = resourcebase_obj.get_user_perms(request.user)

    group = None
    if resourcebase_obj.group:
        try:
            group = GroupProfile.objects.get(slug=resourcebase_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    r = resourcebase_obj
    if request.method in ("POST", "PATCH", "PUT"):
        r = resource_manager.update(resourcebase_obj.uuid, instance=resourcebase_obj, notify=True)

        resource_manager.set_permissions(
            resourcebase_obj.uuid, instance=resourcebase_obj, permissions=ast.literal_eval(permissions_json)
        )

        resource_manager.set_thumbnail(resourcebase_obj.uuid, instance=resourcebase_obj, overwrite=False)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    _config = json.dumps(r.blob)
    _ctx = {
        "appId": resourcebaseid,
        "appType": resourcebase_obj.resource_type,
        "config": _config,
        "user": request.user,
        "access_token": access_token,
        "resource": resourcebase_obj,
        "group": group,
        "perms_list": perms_list,
        "permissions_json": permissions_json,
        "preview": getattr(settings, "GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY", "mapstore"),
    }

    return render(request, template, context=_ctx)


def resourcebase_metadata_detail(
    request, resourcebaseid, template="base/base_metadata_detail.html", custom_metadata=None
):
    try:
        resourcebase_obj = _resolve_resourcebase(request, resourcebaseid, "view_resourcebase", _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not resourcebase_obj:
        raise Http404(_("Not found"))

    group = None
    if resourcebase_obj.group:
        try:
            group = GroupProfile.objects.get(slug=resourcebase_obj.group.name)
        except ObjectDoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, resourcebase_obj)

    return render(
        request,
        template,
        context={
            "resource": resourcebase_obj,
            "group": group,
            "SITEURL": site_url,
            "custom_metadata": custom_metadata,
        },
    )


@login_required
@check_keyword_write_perms
def resourcebase_metadata(
    request,
    resourcebaseid,
    template="base/base_metadata.html",
    ajax=True,
    panel_template="base/base_panels.html",
    custom_metadata=None,
):
    resourcebase_obj = None
    try:
        resourcebase_obj = _resolve_resourcebase(
            request, resourcebaseid, "base.change_resourcebase_metadata", _PERMISSION_MSG_METADATA
        )
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not resourcebase_obj:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    resourcebase_obj.add_missing_metadata_author_or_poc()
    resource_type = resourcebase_obj.resource_type
    topic_category = resourcebase_obj.category
    subtype = resourcebase_obj.subtype
    current_keywords = [keyword.name for keyword in resourcebase_obj.keywords.all()]

    topic_thesaurus = resourcebase_obj.tkeywords.all()

    if request.method == "POST":
        resourcebase_form = ResourceBaseForm(
            request.POST, instance=resourcebase_obj, prefix="resource", user=request.user
        )
        category_form = CategoryForm(
            request.POST,
            prefix="category_choice_field",
            initial=(
                int(request.POST["category_choice_field"])
                if "category_choice_field" in request.POST and request.POST["category_choice_field"]
                else None
            ),
        )

        if hasattr(settings, "THESAURUS"):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix="tkeywords")

    else:
        resourcebase_form = ResourceBaseForm(instance=resourcebase_obj, prefix="resource", user=request.user)
        resourcebase_form.disable_keywords_widget_for_non_superuser(request.user)
        category_form = CategoryForm(
            prefix="category_choice_field", initial=topic_category.id if topic_category else None
        )

        # Create THESAURUS widgets
        lang = settings.THESAURUS_DEFAULT_LANG if hasattr(settings, "THESAURUS_DEFAULT_LANG") else "en"
        if hasattr(settings, "THESAURUS") and settings.THESAURUS:
            warnings.warn(
                "The settings for Thesaurus has been moved to Model, \
            this feature will be removed in next releases",
                DeprecationWarning,
            )
            dataset_tkeywords = resourcebase_obj.tkeywords.all()
            tkeywords_list = ""
            if dataset_tkeywords and len(dataset_tkeywords) > 0:
                tkeywords_ids = dataset_tkeywords.values_list("id", flat=True)
                if hasattr(settings, "THESAURUS") and settings.THESAURUS:
                    el = settings.THESAURUS
                    thesaurus_name = el["name"]
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(map(str, tkl.values_list("id", flat=True)))
                                tkeywords_list += f",{tkl_ids}" if len(tkeywords_list) > 0 else tkl_ids
                    except Exception:
                        tb = traceback.format_exc()
                        logger.error(tb)
            tkeywords_form = TKeywordForm(instance=resourcebase_obj)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix="tkeywords")
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in topic_thesaurus if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    if (
        request.method == "POST"
        and resourcebase_form.is_valid()
        and category_form.is_valid()
        and tkeywords_form.is_valid()
    ):
        new_keywords = current_keywords if request.keyword_readonly else resourcebase_form.cleaned_data.pop("keywords")
        new_regions = resourcebase_form.cleaned_data.pop("regions")

        new_category = None
        if (
            category_form
            and "category_choice_field" in category_form.cleaned_data
            and category_form.cleaned_data["category_choice_field"]
        ):
            new_category = TopicCategory.objects.get(id=int(category_form.cleaned_data["category_choice_field"]))
        resourcebase_form.cleaned_data.pop("ptype")

        resourcebase_obj = resourcebase_form.instance
        # update contact roles
        resourcebase_obj.set_contact_roles_from_metadata_edit(resourcebase_form)

        vals = dict(category=new_category, subtype=subtype)

        resourcebase_form.cleaned_data.pop("metadata")
        extra_metadata = resourcebase_form.cleaned_data.pop("extra_metadata")

        resourcebase_form.save_linked_resources()
        resourcebase_form.cleaned_data.pop("linked_resources")

        vals.update({"resource_type": resource_type, "sourcetype": SOURCE_TYPE_LOCAL})

        register_event(request, EventType.EVENT_CHANGE_METADATA, resourcebase_obj)
        if not ajax:
            return HttpResponseRedirect(hookset.resourcebase_detail_url(resourcebase_obj))

        message = resourcebase_obj.id

        try:
            # Keywords from THESAURUS management
            # Rewritten to work with updated autocomplete
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({"message": "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, "THESAURUS", None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data["tkeywords"]
                tkeywords_data = tkeywords_data.filter(thesaurus__identifier=thesaurus_setting["name"])
                resourcebase_obj.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                resourcebase_obj.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        if "group" in resourcebase_form.changed_data:
            vals["group"] = resourcebase_form.cleaned_data.get("group")
        if any([x in resourcebase_form.changed_data for x in ["is_approved", "is_published"]]):
            vals["is_approved"] = resourcebase_form.cleaned_data.get("is_approved", resourcebase_obj.is_approved)
            vals["is_published"] = resourcebase_form.cleaned_data.get("is_published", resourcebase_obj.is_published)
        else:
            vals.pop("is_approved", None)
            vals.pop("is_published", None)

        resource_manager.update(
            resourcebase_obj.uuid,
            instance=resourcebase_obj,
            keywords=new_keywords,
            regions=new_regions,
            notify=True,
            vals=vals,
            extra_metadata=json.loads(extra_metadata),
        )

        resource_manager.set_thumbnail(resourcebase_obj.uuid, instance=resourcebase_obj, overwrite=False)

        return HttpResponse(json.dumps({"message": message}))
    elif request.method == "POST" and (
        not resourcebase_form.is_valid() or not category_form.is_valid() or not tkeywords_form.is_valid()
    ):
        errors_list = {
            **resourcebase_form.errors.as_data(),
            **category_form.errors.as_data(),
            **tkeywords_form.errors.as_data(),
        }
        logger.error(f"resourcebase Metadata form is not valid: {errors_list}")
        out = {"success": False, "errors": [f"{x}: {y[0].messages[0]}" for x, y in errors_list.items()]}
        return HttpResponse(json.dumps(out), content_type="application/json", status=400)
    # - POST Request Ends here -

    # define contact role forms
    contact_role_forms_context = {}
    for role in resourcebase_obj.get_multivalue_role_property_names():
        resourcebase_form.fields[role].initial = [p.username for p in resourcebase_obj.__getattribute__(role)]
        role_form = ProfileForm(prefix=role)
        role_form.hidden = True
        contact_role_forms_context[f"{role}_form"] = role_form

    metadata_author_groups = get_user_visible_groups(request.user)

    if not request.user.can_publish(resourcebase_obj):
        resourcebase_form.fields["is_published"].widget.attrs.update({"disabled": "true"})
    if not request.user.can_approve(resourcebase_obj):
        resourcebase_form.fields["is_approved"].widget.attrs.update({"disabled": "true"})

    register_event(request, EventType.EVENT_VIEW_METADATA, resourcebase_obj)
    return render(
        request,
        template,
        context={
            "resource": resourcebase_obj,
            "resourcebase": resourcebase_obj,
            "panel_template": panel_template,
            "custom_metadata": custom_metadata,
            "resourcebase_form": resourcebase_form,
            "category_form": category_form,
            "tkeywords_form": tkeywords_form,
            "metadata_author_groups": metadata_author_groups,
            "TOPICCATEGORY_MANDATORY": getattr(settings, "TOPICCATEGORY_MANDATORY", False),
            "GROUP_MANDATORY_RESOURCES": getattr(settings, "GROUP_MANDATORY_RESOURCES", False),
            "UI_MANDATORY_FIELDS": list(
                set(getattr(settings, "UI_DEFAULT_MANDATORY_FIELDS", []))
                | set(getattr(settings, "UI_REQUIRED_FIELDS", []))
            ),
            **contact_role_forms_context,
            "UI_ROLES_IN_TOGGLE_VIEW": resourcebase_obj.get_ui_toggled_role_property_names(),
        },
    )


@login_required
def resourcebase_metadata_advanced(request, resourcebaseid):
    return resourcebase_metadata(request, resourcebaseid, template="base/base_metadata_advanced.html")
