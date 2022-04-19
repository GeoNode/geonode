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
import json
import logging
import traceback
import warnings

from django.conf import settings
from django.db.models import F
from django.urls import reverse
from django.shortcuts import render
from django.forms.utils import ErrorList
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.clickjacking import xframe_options_sameorigin

from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.security.views import _perms_info_json
from geonode.geoapps.models import GeoApp, GeoAppData
from geonode.decorators import check_keyword_write_perms
from geonode.base import register_event
from geonode.monitoring.models import EventType

from geonode.people.forms import ProfileForm
from geonode.base.forms import CategoryForm, TKeywordForm, ThesaurusAvailableForm

from geonode.base.models import ExtraMetadata, Thesaurus, TopicCategory

from geonode.security.utils import (
    get_user_visible_groups,
    AdvancedSecurityWorkflowManager)

from geonode.utils import (
    resolve_object,
    build_social_links
)

from .forms import GeoAppForm

logger = logging.getLogger("geonode.geoapps.views")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this app.")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this app.")
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this app")
_PERMISSION_MSG_SAVE = _("You are not permitted to save or edit this app.")
_PERMISSION_MSG_METADATA = _(
    "You are not allowed to modify this app's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this app.")
_PERMISSION_MSG_UNKNOWN = _("An unknown error has occured.")


def _resolve_geoapp(request, id, permission='base.change_resourcebase',
                    msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the GeoApp by the provided typename and check the optional permission.
    '''
    if GeoApp.objects.filter(urlsuffix=id).exists():
        key = 'urlsuffix'
    else:
        key = 'pk'

    return resolve_object(request, GeoApp, {key: id}, permission=permission,
                          permission_msg=msg, **kwargs)


@login_required
def new_geoapp(request, template='apps/app_new.html'):

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    if request.method == 'GET':
        _ctx = {
            'user': request.user,
            'access_token': access_token,
        }
        return render(request, template, context=_ctx)

    return HttpResponseRedirect(reverse("apps_browse"))


def geoapp_detail(request, geoappid, template='apps/app_detail.html'):
    """
    The view that returns the app composer opened to
    the app with the given app ID.
    """
    try:
        geoapp_obj = _resolve_geoapp(
            request,
            geoappid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    geoapp_obj.add_missing_metadata_author_or_poc()

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != geoapp_obj.owner and not request.user.is_superuser:
        GeoApp.objects.filter(
            id=geoapp_obj.id).update(
            popular_count=F('popular_count') + 1)

    _data = GeoAppData.objects.filter(resource__id=geoappid).first()
    _config = _data.blob if _data else {}

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(geoapp_obj)

    perms_list = list(
        geoapp_obj.get_self_resource().get_user_perms(request.user)
        .union(geoapp_obj.get_user_perms(request.user))
    )
    group = None
    if geoapp_obj.group:
        try:
            group = GroupProfile.objects.get(slug=geoapp_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        'appId': geoappid,
        'appType': geoapp_obj.type,
        'config': _config,
        'user': request.user,
        'access_token': access_token,
        'resource': geoapp_obj,
        'group': group,
        'perms_list': perms_list,
        'permissions_json': permissions_json,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore'),
        'crs': getattr(
            settings,
            'DEFAULT_MAP_CRS',
            'EPSG:3857')
    }

    if request.user.is_authenticated:
        if getattr(settings, 'FAVORITE_ENABLED', False):
            from geonode.favorite.utils import get_favorite_info
            context_dict["favorite_info"] = get_favorite_info(request.user, geoapp_obj)

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, geoapp_obj)

    register_event(request, EventType.EVENT_VIEW, request.path)

    return render(request, template, context=context_dict)


@xframe_options_sameorigin
def geoapp_edit(request, geoappid, template='apps/app_edit.html'):
    """
    The view that returns the app composer opened to
    the app with the given app ID.
    """
    try:
        geoapp_obj = _resolve_geoapp(
            request,
            geoappid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(geoapp_obj)

    perms_list = list(
        geoapp_obj.get_self_resource().get_user_perms(request.user)
        .union(geoapp_obj.get_user_perms(request.user))
    )

    group = None
    if geoapp_obj.group:
        try:
            group = GroupProfile.objects.get(slug=geoapp_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    _data = GeoAppData.objects.filter(resource__id=geoappid).first()
    _config = _data.blob if _data else {}
    _ctx = {
        'appId': geoappid,
        'appType': geoapp_obj.type,
        'config': _config,
        'user': request.user,
        'access_token': access_token,
        'resource': geoapp_obj,
        'group': group,
        'perms_list': perms_list,
        "permissions_json": permissions_json,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore')
    }

    return render(request, template, context=_ctx)


@login_required
def geoapp_remove(request, geoappid, template='apps/app_remove.html'):
    try:
        geoapp_obj = _resolve_geoapp(
            request,
            geoappid,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    if request.method == 'GET':
        return render(request, template, context={
            "resource": geoapp_obj
        })
    elif request.method == 'POST':
        geoapp_obj.delete()
        register_event(request, EventType.EVENT_REMOVE, geoapp_obj)
        return HttpResponseRedirect(reverse("apps_browse"))
    else:
        return HttpResponse("Not allowed", status=403)


def geoapp_metadata_detail(request, geoappid, template='apps/app_metadata_detail.html'):
    try:
        geoapp_obj = _resolve_geoapp(
            request,
            geoappid,
            'view_resourcebase',
            _PERMISSION_MSG_METADATA)
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
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, geoapp_obj)
    return render(request, template, context={
        "resource": geoapp_obj,
        "group": group,
        'SITEURL': site_url
    })


@login_required
@check_keyword_write_perms
def geoapp_metadata(request, geoappid, template='apps/app_metadata.html', ajax=True):
    geoapp_obj = None
    try:
        geoapp_obj = _resolve_geoapp(
            request,
            geoappid,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    geoapp_obj.add_missing_metadata_author_or_poc()
    poc = geoapp_obj.poc
    metadata_author = geoapp_obj.metadata_author
    topic_category = geoapp_obj.category
    current_keywords = [keyword.name for keyword in geoapp_obj.keywords.all()]

    topic_thesaurus = geoapp_obj.tkeywords.all()

    if request.method == "POST":
        geoapp_form = GeoAppForm(
            request.POST,
            instance=geoapp_obj,
            prefix="resource")
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
            request.POST["category_choice_field"] else None)

        if hasattr(settings, 'THESAURUS'):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix='tkeywords')

    else:
        geoapp_form = GeoAppForm(instance=geoapp_obj, prefix="resource")
        geoapp_form.disable_keywords_widget_for_non_superuser(request.user)
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

        # Create THESAURUS widgets
        lang = settings.THESAURUS_DEFAULT_LANG if hasattr(settings, 'THESAURUS_DEFAULT_LANG') else 'en'
        if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
            warnings.warn('The settings for Thesaurus has been moved to Model, \
            this feature will be removed in next releases', DeprecationWarning)
            layer_tkeywords = geoapp_obj.tkeywords.all()
            tkeywords_list = ''
            if layer_tkeywords and len(layer_tkeywords) > 0:
                tkeywords_ids = layer_tkeywords.values_list('id', flat=True)
                if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
                    el = settings.THESAURUS
                    thesaurus_name = el['name']
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(
                                    map(str, tkl.values_list('id', flat=True)))
                                tkeywords_list += f",{tkl_ids}" if len(
                                    tkeywords_list) > 0 else tkl_ids
                    except Exception:
                        tb = traceback.format_exc()
                        logger.error(tb)
            tkeywords_form = TKeywordForm(instance=geoapp_obj)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix='tkeywords')
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in topic_thesaurus if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    initial_thumb_url = geoapp_obj.thumbnail_url
    if request.method == "POST" and geoapp_form.is_valid(
    ) and category_form.is_valid() and tkeywords_form.is_valid():
        new_poc = geoapp_form.cleaned_data.pop('poc')
        new_author = geoapp_form.cleaned_data.pop('metadata_author')
        new_keywords = current_keywords if request.keyword_readonly else geoapp_form.cleaned_data.pop('keywords')
        new_regions = geoapp_form.cleaned_data.pop('regions')

        new_category = None
        if category_form and 'category_choice_field' in category_form.cleaned_data and \
                category_form.cleaned_data['category_choice_field']:
            new_category = TopicCategory.objects.get(
                id=int(category_form.cleaned_data['category_choice_field']))

        if new_poc is None:
            if poc is None:
                poc_form = ProfileForm(
                    request.POST,
                    prefix="poc",
                    instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.is_valid():
                if len(poc_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = poc_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set a point of contact for this resource'))
                    poc = None
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.is_valid():
                if len(author_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = author_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set an author for this resource'))
                    metadata_author = None
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        geoapp_obj = geoapp_form.instance
        if new_poc is not None and new_author is not None:
            geoapp_obj.poc = new_poc
            geoapp_obj.metadata_author = new_author

        if initial_thumb_url and not geoapp_obj.thumbnail_url:
            geoapp_obj.thumbnail_url = initial_thumb_url

        geoapp_obj.keywords.clear()
        geoapp_obj.keywords.add(*new_keywords)
        geoapp_obj.regions.clear()
        geoapp_obj.regions.add(*new_regions)
        geoapp_obj.category = new_category

        geoapp_obj.save(notify=True)
        # clearing old metadata from the resource
        geoapp_obj.metadata.all().delete()
        # creating new metadata for the resource
        for _m in json.loads(geoapp_form.cleaned_data['extra_metadata']):
            new_m = ExtraMetadata.objects.create(
                resource=geoapp_obj,
                metadata=_m
            )
            geoapp_obj.metadata.add(new_m)

        register_event(request, EventType.EVENT_CHANGE_METADATA, geoapp_obj)
        if not ajax:
            return HttpResponseRedirect(
                reverse(
                    'geoapp_detail',
                    args=(
                        geoapp_obj.id,
                    )))

        message = geoapp_obj.id

        try:
            # Keywords from THESAURUS management
            # Rewritten to work with updated autocomplete
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({'message': "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, 'THESAURUS', None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data['tkeywords']
                tkeywords_data = tkeywords_data.filter(
                    thesaurus__identifier=thesaurus_setting['name']
                )
                geoapp_obj.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                geoapp_obj.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        vals = {}
        _group_status_changed = False
        _approval_status_changed = False
        if 'group' in geoapp_form.changed_data:
            _group_status_changed = True
            vals['group'] = geoapp_form.cleaned_data.get('group')
        if any([x in geoapp_form.changed_data for x in ['is_approved', 'is_published']]):
            _approval_status_changed = True
            vals['is_approved'] = geoapp_form.cleaned_data.get('is_approved', geoapp_obj.is_approved)
            vals['is_published'] = geoapp_form.cleaned_data.get('is_published', geoapp_obj.is_published)
        geoapp_obj.save(notify=True)
        geoapp_obj.set_permissions(approval_status_changed=_approval_status_changed, group_status_changed=_group_status_changed)
        return HttpResponse(json.dumps({'message': message}))
    elif request.method == "POST" and (not geoapp_form.is_valid(
    ) or not category_form.is_valid() or not tkeywords_form.is_valid()):
        errors_list = {**geoapp_form.errors.as_data(), **category_form.errors.as_data(), **tkeywords_form.errors.as_data()}
        logger.error(f"GeoApp Metadata form is not valid: {errors_list}")
        out = {
            'success': False,
            "errors": [f"{x}: {y[0].messages[0]}" for x, y in errors_list.items()]
        }
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=400)
    # - POST Request Ends here -

    # Request.GET
    if poc is not None:
        geoapp_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True

    if metadata_author is not None:
        geoapp_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True

    metadata_author_groups = get_user_visible_groups(request.user)

    if not AdvancedSecurityWorkflowManager.is_allowed_to_publish(request.user, geoapp_obj):
        geoapp_form.fields['is_published'].widget.attrs.update({'disabled': 'true'})
    if not AdvancedSecurityWorkflowManager.is_allowed_to_approve(request.user, geoapp_obj):
        geoapp_form.fields['is_approved'].widget.attrs.update({'disabled': 'true'})

    register_event(request, EventType.EVENT_VIEW_METADATA, geoapp_obj)
    return render(request, template, context={
        "resource": geoapp_obj,
        "geoapp": geoapp_obj,
        "geoapp_form": geoapp_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "category_form": category_form,
        "tkeywords_form": tkeywords_form,
        "metadata_author_groups": metadata_author_groups,
        "TOPICCATEGORY_MANDATORY": getattr(settings, 'TOPICCATEGORY_MANDATORY', False),
        "GROUP_MANDATORY_RESOURCES": getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
        "UI_MANDATORY_FIELDS": list(
            set(getattr(settings, 'UI_DEFAULT_MANDATORY_FIELDS', []))
            |
            set(getattr(settings, 'UI_REQUIRED_FIELDS', []))
        )
    })


@login_required
def geoapp_metadata_advanced(request, geoappid):
    return geoapp_metadata(
        request,
        geoappid,
        template='apps/app_metadata_advanced.html')
