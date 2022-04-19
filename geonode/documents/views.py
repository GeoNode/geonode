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
import traceback
import warnings

from guardian.shortcuts import get_objects_for_user

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views.generic.edit import UpdateView, CreateView
from django.db.models import F
from django.forms.utils import ErrorList

from geonode.decorators import check_keyword_write_perms
from geonode.documents.utils import get_download_response
from geonode.utils import resolve_object
from geonode.security.views import _perms_info_json
from geonode.people.forms import ProfileForm
from geonode.base.auth import get_or_create_token
from geonode.base.bbox_utils import BBOXHelper
from geonode.base.forms import CategoryForm, TKeywordForm, ThesaurusAvailableForm
from geonode.base.models import (
    ExtraMetadata,
    Thesaurus,
    TopicCategory)
from geonode.documents.enumerations import DOCUMENT_TYPE_MAP, DOCUMENT_MIMETYPE_MAP
from geonode.documents.models import Document, get_related_resources
from geonode.documents.forms import DocumentForm, DocumentCreateForm, DocumentReplaceForm
from geonode.utils import build_social_links
from geonode.groups.models import GroupProfile
from geonode.base.views import batch_modify
from geonode.base import register_event
from geonode.monitoring.models import EventType
from geonode.security.utils import get_visible_resources

from geonode.security.utils import (
    get_user_visible_groups,
    AdvancedSecurityWorkflowManager)

from dal import autocomplete

logger = logging.getLogger("geonode.documents.views")

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this document.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")


def _resolve_document(request, docid, permission='base.change_resourcebase',
                      msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the document by the provided primary key and check the optional permission.
    '''
    return resolve_object(request, Document, {'pk': docid},
                          permission=permission, permission_msg=msg, **kwargs)


def document_detail(request, docid):
    """
    The view that show details of each document
    """
    try:
        document = _resolve_document(
            request,
            docid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not document:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    document.add_missing_metadata_author_or_poc()

    related = get_related_resources(document)

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != document.owner and not request.user.is_superuser:
        Document.objects.filter(
            id=document.id).update(
            popular_count=F('popular_count') + 1)

    metadata = document.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(document)

    perms_list = list(
        document.get_self_resource().get_user_perms(request.user)
        .union(document.get_user_perms(request.user))
    )

    group = None
    if document.group:
        try:
            group = GroupProfile.objects.get(slug=document.group.name)
        except ObjectDoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    AUDIOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'audio']
    IMGTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'image']
    VIDEOTYPES = [_e for _e, _t in DOCUMENT_TYPE_MAP.items() if _t == 'video']

    context_dict = {
        'access_token': access_token,
        'resource': document,
        'perms_list': perms_list,
        'permissions_json': permissions_json,
        'group': group,
        'metadata': metadata,
        'audiotypes': AUDIOTYPES,
        'imgtypes': IMGTYPES,
        'videotypes': VIDEOTYPES,
        'mimetypemap': DOCUMENT_MIMETYPE_MAP,
        'related': related}

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(
            request, document)

    if getattr(settings, 'EXIF_ENABLED', False):
        try:
            from geonode.documents.exif.utils import exif_extract_dict
            exif = exif_extract_dict(document)
            if exif:
                context_dict['exif_data'] = exif
        except Exception:
            logger.error("Exif extraction failed.")

    if request.user.is_authenticated:
        if getattr(settings, 'FAVORITE_ENABLED', False):
            from geonode.favorite.utils import get_favorite_info
            context_dict["favorite_info"] = get_favorite_info(request.user, document)

    register_event(request, EventType.EVENT_VIEW, document)

    return render(
        request,
        "documents/document_detail.html",
        context=context_dict)


def document_download(request, docid):
    response = get_download_response(request, docid, attachment=True)
    return response


def document_link(request, docid):
    response = get_download_response(request, docid)
    return response


class DocumentUploadView(CreateView):
    template_name = 'documents/document_upload.html'
    form_class = DocumentCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        return context

    def form_invalid(self, form):
        messages.error(self.request, f"{form.errors}")
        if self.request.GET.get('no__redirect', False):
            plaintext_errors = []
            for field in form.errors.values():
                plaintext_errors.append(field.data[0].message)
            out = {'success': False}
            out['message'] = '.'.join(plaintext_errors)
            status_code = 400
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            form.name = None
            form.title = None
            form.doc_file = None
            form.doc_url = None
            return self.render_to_response(
                self.get_context_data(request=self.request, form=form))

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.handle_moderated_uploads()
        self.object.save()
        form.save_many2many()
        self.object.set_permissions(form.cleaned_data['permissions'], created=True)

        abstract = None
        date = None
        regions = []
        keywords = []
        bbox = None

        out = {'success': False}

        if getattr(settings, 'EXIF_ENABLED', False):
            try:
                from geonode.documents.exif.utils import exif_extract_metadata_doc
                exif_metadata = exif_extract_metadata_doc(self.object)
                if exif_metadata:
                    date = exif_metadata.get('date', None)
                    keywords.extend(exif_metadata.get('keywords', []))
                    bbox = exif_metadata.get('bbox', None)
                    abstract = exif_metadata.get('abstract', None)
            except Exception:
                logger.debug("Exif extraction failed.")

        if abstract:
            self.object.abstract = abstract

        if date:
            self.object.date = date
            self.object.date_type = "Creation"

        if len(regions) > 0:
            self.object.regions.add(*regions)

        if len(keywords) > 0:
            self.object.keywords.add(*keywords)

        if bbox:
            bbox = BBOXHelper.from_xy(bbox)
            self.object.bbox_polygon = bbox.as_polygon()

        self.object.save(notify=True)
        register_event(self.request, EventType.EVENT_UPLOAD, self.object)

        if self.request.GET.get('no__redirect', False):
            out['success'] = True
            out['url'] = reverse(
                'document_detail',
                args=(
                    self.object.id,
                ))
            if out['success']:
                status_code = 200
            else:
                status_code = 400
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            return HttpResponseRedirect(
                reverse(
                    'document_detail',
                    args=(
                        self.object.id,
                    )))


class DocumentUpdateView(UpdateView):
    template_name = 'documents/document_replace.html'
    pk_url_kwarg = 'docid'
    form_class = DocumentReplaceForm
    queryset = Document.objects.all()
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        return context

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save()
        register_event(self.request, EventType.EVENT_CHANGE, self.object)
        return HttpResponseRedirect(
            reverse(
                'document_detail',
                args=(
                    self.object.id,
                )))


@login_required
@check_keyword_write_perms
def document_metadata(
        request,
        docid,
        template='documents/document_metadata.html',
        ajax=True):
    document = None
    try:
        document = _resolve_document(
            request,
            docid,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not document:
        raise Http404(_("Not found"))

    # Add metadata_author or poc if missing
    document.add_missing_metadata_author_or_poc()
    poc = document.poc
    metadata_author = document.metadata_author
    topic_category = document.category
    current_keywords = [keyword.name for keyword in document.keywords.all()]

    if request.method == "POST":
        document_form = DocumentForm(
            request.POST,
            instance=document,
            prefix="resource")
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
            request.POST["category_choice_field"] else None)

        if hasattr(settings, 'THESAURUS'):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix='tkeywords')

    else:
        document_form = DocumentForm(instance=document, prefix="resource")
        document_form.disable_keywords_widget_for_non_superuser(request.user)
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

        # Keywords from THESAURUS management
        doc_tkeywords = document.tkeywords.all()
        if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
            warnings.warn('The settings for Thesaurus has been moved to Model, \
            this feature will be removed in next releases', DeprecationWarning)
            tkeywords_list = ''
            lang = 'en'  # TODO: use user's language
            if doc_tkeywords and len(doc_tkeywords) > 0:
                tkeywords_ids = doc_tkeywords.values_list('id', flat=True)
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

            tkeywords_form = TKeywordForm(instance=document)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix='tkeywords')
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in doc_tkeywords if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    if request.method == "POST" and document_form.is_valid(
    ) and category_form.is_valid() and tkeywords_form.is_valid():
        new_poc = document_form.cleaned_data['poc']
        new_author = document_form.cleaned_data['metadata_author']
        new_keywords = current_keywords if request.keyword_readonly else document_form.cleaned_data['keywords']
        new_regions = document_form.cleaned_data['regions']

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
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        document = document_form.instance
        if new_poc is not None and new_author is not None:
            document.poc = new_poc
            document.metadata_author = new_author
        document.keywords.clear()
        document.keywords.add(*new_keywords)
        document.regions.clear()
        document.regions.add(*new_regions)
        document.category = new_category

        # deleting old metadata from the resource
        document.metadata.all().delete()
        # creating new metadata for the resource
        for _m in json.loads(document_form.cleaned_data['extra_metadata']):
            new_m = ExtraMetadata.objects.create(
                resource=document,
                metadata=_m
            )
            document.metadata.add(new_m)

        document.save(notify=True)
        document_form.save_many2many()

        register_event(request, EventType.EVENT_CHANGE_METADATA, document)
        if not ajax:
            return HttpResponseRedirect(
                reverse(
                    'document_detail',
                    args=(
                        document.id,
                    )))
        message = document.id

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
                document.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                document.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        vals = {}
        _group_status_changed = False
        _approval_status_changed = False
        if 'group' in document_form.changed_data:
            _group_status_changed = True
            vals['group'] = document_form.cleaned_data.get('group')
        if any([x in document_form.changed_data for x in ['is_approved', 'is_published']]):
            _approval_status_changed = True
            vals['is_approved'] = document_form.cleaned_data.get('is_approved', document.is_approved)
            vals['is_published'] = document_form.cleaned_data.get('is_published', document.is_published)
        document.save(notify=True)
        document.set_permissions(approval_status_changed=_approval_status_changed, group_status_changed=_group_status_changed)
        return HttpResponse(json.dumps({'message': message}))
    elif request.method == "POST" and (not document_form.is_valid(
    ) or not category_form.is_valid() or not tkeywords_form.is_valid()):
        errors_list = {**document_form.errors.as_data(), **category_form.errors.as_data(), **tkeywords_form.errors.as_data()}
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
        document_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True

    if metadata_author is not None:
        document_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True

    metadata_author_groups = get_user_visible_groups(request.user)

    if not AdvancedSecurityWorkflowManager.is_allowed_to_publish(request.user, document):
        document_form.fields['is_published'].widget.attrs.update({'disabled': 'true'})
    if not AdvancedSecurityWorkflowManager.is_allowed_to_approve(request.user, document):
        document_form.fields['is_approved'].widget.attrs.update({'disabled': 'true'})

    register_event(request, EventType.EVENT_VIEW_METADATA, document)
    return render(request, template, context={
        "resource": document,
        "document": document,
        "document_form": document_form,
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
def document_metadata_advanced(request, docid):
    return document_metadata(
        request,
        docid,
        template='documents/document_metadata_advanced.html')


def document_search_page(request):
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    return render(
        request,
        'documents/document_search.html',
        context={'init_search': json.dumps(params or {}), "site": settings.SITEURL})


@login_required
def document_remove(request, docid, template='documents/document_remove.html'):
    try:
        document = _resolve_document(
            request,
            docid,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not document:
        raise Http404(_("Not found"))

    if request.method == 'GET':
        return render(request, template, context={
            "document": document
        })
    if request.method == 'POST':
        document.delete()
        register_event(request, EventType.EVENT_REMOVE, document)
        return HttpResponseRedirect(reverse("document_browse"))
    else:
        return HttpResponse(_("Not allowed"), status=403)


def document_metadata_detail(
        request,
        docid,
        template='documents/document_metadata_detail.html'):
    try:
        document = _resolve_document(
            request,
            docid,
            'view_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not document:
        raise Http404(_("Not found"))

    group = None
    if document.group:
        try:
            group = GroupProfile.objects.get(slug=document.group.name)
        except ObjectDoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, document)
    return render(request, template, context={
        "resource": document,
        "group": group,
        'SITEURL': site_url
    })


@login_required
def document_batch_metadata(request):
    return batch_modify(request, 'Document')


class DocumentAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        request = self.request
        permitted = get_objects_for_user(
            request.user,
            'base.view_resourcebase')
        qs = Document.objects.all().filter(id__in=permitted)

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return get_visible_resources(
            qs,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)
