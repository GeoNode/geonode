#########################################################################
#
# Copyright (C) 2020 OSGeo
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
import ast
import json
import logging
import warnings
import traceback

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views.decorators.clickjacking import xframe_options_sameorigin
from geonode.base.enumerations import SOURCE_TYPE_LOCAL

from geonode.client.hooks import hookset
from geonode.people.forms import ProfileForm
from geonode.base import register_event
from geonode.groups.models import GroupProfile
from geonode.monitoring.models import EventType
from geonode.base.auth import get_or_create_token
from geonode.security.views import _perms_info_json
from geonode.security.utils import get_user_visible_groups
from geonode.geoapps.models import GeoApp
from geonode.resource.manager import resource_manager
from geonode.decorators import check_keyword_write_perms

from geonode.base.forms import CategoryForm, TKeywordForm, ThesaurusAvailableForm
from geonode.base.models import Thesaurus, TopicCategory
from geonode.utils import resolve_object

from .forms import GeoAppForm

logger = logging.getLogger("geonode.geoapps.views")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this app.")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this app.")
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this app")
_PERMISSION_MSG_SAVE = _("You are not permitted to save or edit this app.")
_PERMISSION_MSG_METADATA = _("You are not allowed to modify this app's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this app.")
_PERMISSION_MSG_UNKNOWN = _("An unknown error has occured.")


def _resolve_geoapp(request, id, permission="base.change_resourcebase", msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the GeoApp by the provided typename and check the optional permission.
    """

    return resolve_object(request, GeoApp, {"pk": id}, permission=permission, permission_msg=msg, **kwargs)


@login_required
def new_geoapp(request, template="apps/app_new.html"):
    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    if request.method == "GET":
        _ctx = {
            "user": request.user,
            "access_token": access_token,
        }
        return render(request, template, context=_ctx)

    return HttpResponseRedirect(hookset.geoapp_list_url())


@xframe_options_sameorigin
def geoapp_edit(request, geoappid, template="apps/app_edit.html"):
    """
    The view that returns the app composer opened to
    the app with the given app ID.
    """
    try:
        geoapp_obj = _resolve_geoapp(request, geoappid, "base.view_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(geoapp_obj)

    perms_list = geoapp_obj.get_user_perms(request.user)

    group = None
    if geoapp_obj.group:
        try:
            group = GroupProfile.objects.get(slug=geoapp_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    r = geoapp_obj
    if request.method in ("POST", "PATCH", "PUT"):
        r = resource_manager.update(geoapp_obj.uuid, instance=geoapp_obj, notify=True)

        resource_manager.set_permissions(
            geoapp_obj.uuid, instance=geoapp_obj, permissions=ast.literal_eval(permissions_json)
        )

        resource_manager.set_thumbnail(geoapp_obj.uuid, instance=geoapp_obj, overwrite=False)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    _config = json.dumps(r.blob)
    _ctx = {
        "appId": geoappid,
        "appType": geoapp_obj.resource_type,
        "config": _config,
        "user": request.user,
        "access_token": access_token,
        "resource": geoapp_obj,
        "group": group,
        "perms_list": perms_list,
        "permissions_json": permissions_json,
        "preview": getattr(settings, "GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY", "mapstore"),
    }

    return render(request, template, context=_ctx)


def geoapp_metadata_detail(request, geoappid, template="apps/app_metadata_detail.html", custom_metadata=None):
    try:
        geoapp_obj = _resolve_geoapp(request, geoappid, "view_resourcebase", _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    group = None
    if geoapp_obj.group:
        try:
            group = GroupProfile.objects.get(slug=geoapp_obj.group.name)
        except ObjectDoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, geoapp_obj)

    return render(
        request,
        template,
        context={
            "resource": geoapp_obj,
            "group": group,
            "SITEURL": site_url,
            "custom_metadata": custom_metadata,
        },
    )


@login_required
@check_keyword_write_perms
def geoapp_metadata(
    request,
    geoappid,
    template="apps/app_metadata.html",
    ajax=True,
    panel_template="layouts/app_panels.html",
    custom_metadata=None,
):
    geoapp_obj = None
    try:
        geoapp_obj = _resolve_geoapp(request, geoappid, "base.change_resourcebase_metadata", _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    geoapp_obj.add_missing_metadata_author_or_poc()
    resource_type = geoapp_obj.resource_type
    topic_category = geoapp_obj.category
    current_keywords = [keyword.name for keyword in geoapp_obj.keywords.all()]

    topic_thesaurus = geoapp_obj.tkeywords.all()

    if request.method == "POST":
        geoapp_form = GeoAppForm(request.POST, instance=geoapp_obj, prefix="resource", user=request.user)
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
        geoapp_form = GeoAppForm(instance=geoapp_obj, prefix="resource", user=request.user)
        geoapp_form.disable_keywords_widget_for_non_superuser(request.user)
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
            dataset_tkeywords = geoapp_obj.tkeywords.all()
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
            tkeywords_form = TKeywordForm(instance=geoapp_obj)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix="tkeywords")
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in topic_thesaurus if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    if request.method == "POST" and geoapp_form.is_valid() and category_form.is_valid() and tkeywords_form.is_valid():
        new_keywords = current_keywords if request.keyword_readonly else geoapp_form.cleaned_data.pop("keywords")
        new_regions = geoapp_form.cleaned_data.pop("regions")

        new_category = None
        if (
            category_form
            and "category_choice_field" in category_form.cleaned_data
            and category_form.cleaned_data["category_choice_field"]
        ):
            new_category = TopicCategory.objects.get(id=int(category_form.cleaned_data["category_choice_field"]))
        geoapp_form.cleaned_data.pop("ptype")

        geoapp_obj = geoapp_form.instance
        # update contact roles
        geoapp_obj.set_contact_roles_from_metadata_edit(geoapp_form)

        vals = dict(category=new_category)

        geoapp_form.cleaned_data.pop("metadata")
        extra_metadata = geoapp_form.cleaned_data.pop("extra_metadata")

        geoapp_form.save_linked_resources()
        geoapp_form.cleaned_data.pop("linked_resources")

        vals.update({"resource_type": resource_type, "sourcetype": SOURCE_TYPE_LOCAL})

        register_event(request, EventType.EVENT_CHANGE_METADATA, geoapp_obj)
        if not ajax:
            return HttpResponseRedirect(hookset.geoapp_detail_url(geoapp_obj))

        message = geoapp_obj.id

        try:
            # Keywords from THESAURUS management
            # Rewritten to work with updated autocomplete
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({"message": "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, "THESAURUS", None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data["tkeywords"]
                tkeywords_data = tkeywords_data.filter(thesaurus__identifier=thesaurus_setting["name"])
                geoapp_obj.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                geoapp_obj.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        if "group" in geoapp_form.changed_data:
            vals["group"] = geoapp_form.cleaned_data.get("group")
        if any([x in geoapp_form.changed_data for x in ["is_approved", "is_published"]]):
            vals["is_approved"] = geoapp_form.cleaned_data.get("is_approved", geoapp_obj.is_approved)
            vals["is_published"] = geoapp_form.cleaned_data.get("is_published", geoapp_obj.is_published)
        else:
            vals.pop("is_approved", None)
            vals.pop("is_published", None)

        resource_manager.update(
            geoapp_obj.uuid,
            instance=geoapp_obj,
            keywords=new_keywords,
            regions=new_regions,
            notify=True,
            vals=vals,
            extra_metadata=json.loads(extra_metadata),
        )

        resource_manager.set_thumbnail(geoapp_obj.uuid, instance=geoapp_obj, overwrite=False)

        return HttpResponse(json.dumps({"message": message}))
    elif request.method == "POST" and (
        not geoapp_form.is_valid() or not category_form.is_valid() or not tkeywords_form.is_valid()
    ):
        errors_list = {
            **geoapp_form.errors.as_data(),
            **category_form.errors.as_data(),
            **tkeywords_form.errors.as_data(),
        }
        logger.error(f"GeoApp Metadata form is not valid: {errors_list}")
        out = {"success": False, "errors": [f"{x}: {y[0].messages[0]}" for x, y in errors_list.items()]}
        return HttpResponse(json.dumps(out), content_type="application/json", status=400)
    # - POST Request Ends here -

    # define contact role forms
    contact_role_forms_context = {}
    for role in geoapp_obj.get_multivalue_role_property_names():
        geoapp_form.fields[role].initial = [p.username for p in geoapp_obj.__getattribute__(role)]
        role_form = ProfileForm(prefix=role)
        role_form.hidden = True
        contact_role_forms_context[f"{role}_form"] = role_form

    metadata_author_groups = get_user_visible_groups(request.user)

    if not request.user.can_publish(geoapp_obj):
        geoapp_form.fields["is_published"].widget.attrs.update({"disabled": "true"})
    if not request.user.can_approve(geoapp_obj):
        geoapp_form.fields["is_approved"].widget.attrs.update({"disabled": "true"})

    register_event(request, EventType.EVENT_VIEW_METADATA, geoapp_obj)
    return render(
        request,
        template,
        context={
            "resource": geoapp_obj,
            "geoapp": geoapp_obj,
            "panel_template": panel_template,
            "custom_metadata": custom_metadata,
            "geoapp_form": geoapp_form,
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
            "UI_ROLES_IN_TOGGLE_VIEW": geoapp_obj.get_ui_toggled_role_property_names(),
        },
    )


@login_required
def geoapp_metadata_advanced(request, geoappid):
    return geoapp_metadata(request, geoappid, template="apps/app_metadata_advanced.html")
