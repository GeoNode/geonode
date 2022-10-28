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
import os
import json
import shutil
import logging
import warnings
import traceback


from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.forms.utils import ErrorList
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.views.generic.edit import CreateView, UpdateView
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from geonode.base.api.exceptions import geonode_exception_handler

from geonode.client.hooks import hookset
from geonode.utils import mkdtemp, resolve_object
from geonode.base.views import batch_modify
from geonode.people.forms import ProfileForm
from geonode.base import register_event
from geonode.base.bbox_utils import BBOXHelper
from geonode.groups.models import GroupProfile
from geonode.monitoring.models import EventType
from geonode.storage.manager import storage_manager
from geonode.resource.manager import resource_manager
from geonode.decorators import check_keyword_write_perms
from geonode.security.utils import (
    get_user_visible_groups,
    AdvancedSecurityWorkflowManager)
from geonode.base.forms import (
    CategoryForm,
    TKeywordForm,
    ThesaurusAvailableForm)
from geonode.base.models import (
    Thesaurus,
    TopicCategory)

from .utils import get_download_response

from .models import Document
from .forms import (
    DocumentForm,
    DocumentCreateForm,
    DocumentReplaceForm
)

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


def document_download(request, docid):
    response = get_download_response(request, docid, attachment=True)
    return response


def document_link(request, docid):
    response = get_download_response(request, docid)
    return response


def document_embed(request, docid):
    from django.http.response import HttpResponseRedirect
    document = get_object_or_404(Document, pk=docid)

    if not request.user.has_perm(
            'base.download_resourcebase',
            obj=document.get_self_resource()):
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _("You are not allowed to view this document.")}, request=request), status=401)
    if document.is_image:
        if document.doc_url:
            imageurl = document.doc_url
        else:
            imageurl = reverse('document_link', args=(document.id,))
        context_dict = {
            "image_url": imageurl,
            "resource": document.get_self_resource(),
        }
        return render(
            request,
            "documents/document_embed.html",
            context_dict
        )
    if document.doc_url:
        return HttpResponseRedirect(document.doc_url)
    else:
        context_dict = {
            "document_link": reverse('document_link', args=(document.id,)),
            "resource": document.get_self_resource(),
        }
        return render(
            request,
            "documents/document_embed.html",
            context_dict
        )


class DocumentUploadView(CreateView):
    http_method_names = ['post']
    form_class = DocumentCreateForm

    def post(self, request, *args, **kwargs):
        self.object = None
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            exception_response = geonode_exception_handler(e, {})
            return HttpResponse(
                json.dumps(exception_response.data),
                content_type='application/json',
                status=exception_response.status_code)

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
        doc_form = form.cleaned_data

        file = doc_form.pop('doc_file', None)
        if file:
            tempdir = mkdtemp()
            dirname = os.path.basename(tempdir)
            filepath = storage_manager.save(f"{dirname}/{file.name}", file)
            storage_path = storage_manager.path(filepath)
            self.object = resource_manager.create(
                None,
                resource_type=Document,
                defaults=dict(
                    owner=self.request.user,
                    doc_url=doc_form.pop('doc_url', None),
                    title=doc_form.pop('title', file.name),
                    files=[storage_path])
            )
            if tempdir != os.path.dirname(storage_path):
                shutil.rmtree(tempdir, ignore_errors=True)
        else:
            self.object = resource_manager.create(
                None,
                resource_type=Document,
                defaults=dict(
                    owner=self.request.user,
                    doc_url=doc_form.pop('doc_url', None),
                    title=doc_form.pop('title', None))
            )

        self.object.handle_moderated_uploads()
        resource_manager.set_permissions(
            None, instance=self.object, permissions=form.cleaned_data["permissions"], created=True
        )

        abstract = None
        date = None
        regions = []
        keywords = []
        bbox = None
        url = hookset.document_detail_url(self.object)

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

        resource_manager.update(
            self.object.uuid,
            instance=self.object,
            keywords=keywords,
            regions=regions,
            vals=dict(
                abstract=abstract,
                date=date,
                date_type="Creation",
                bbox_polygon=BBOXHelper.from_xy(bbox).as_polygon() if bbox else None
            ),
            notify=True)
        resource_manager.set_thumbnail(self.object.uuid, instance=self.object, overwrite=False)

        register_event(self.request, EventType.EVENT_UPLOAD, self.object)

        if self.request.GET.get('no__redirect', False):
            out['success'] = True
            out['url'] = url
            if out['success']:
                status_code = 200
            else:
                status_code = 400
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            return HttpResponseRedirect(url)


class DocumentUpdateView(UpdateView):
    template_name = 'documents/document_replace.html'
    pk_url_kwarg = 'docid'
    form_class = DocumentReplaceForm
    queryset = Document.objects.all()
    context_object_name = 'document'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            exception_response = geonode_exception_handler(e, {})
            return HttpResponse(
                json.dumps(exception_response.data),
                content_type='application/json',
                status=exception_response.status_code)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        return context

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        doc_form = form.cleaned_data

        file = doc_form.pop('doc_file', None)
        if file:
            tempdir = mkdtemp()
            dirname = os.path.basename(tempdir)
            filepath = storage_manager.save(f"{dirname}/{file.name}", file)
            storage_path = storage_manager.path(filepath)
            self.object = resource_manager.update(
                self.object.uuid,
                instance=self.object,
                vals=dict(
                    owner=self.request.user,
                    files=[storage_path])
            )
            if tempdir != os.path.dirname(storage_path):
                shutil.rmtree(tempdir, ignore_errors=True)

        register_event(self.request, EventType.EVENT_CHANGE, self.object)
        url = hookset.document_detail_url(self.object)
        return HttpResponseRedirect(url)


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
            prefix="resource",
            user=request.user)
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
            request.POST["category_choice_field"] else None)

        if hasattr(settings, 'THESAURUS'):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix='tkeywords')

    else:
        document_form = DocumentForm(instance=document, prefix="resource", user=request.user)
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
        resource_manager.update(
            document.uuid,
            instance=document,
            keywords=new_keywords,
            regions=new_regions,
            vals=dict(
                poc=new_poc or document.poc,
                metadata_author=new_author or document.metadata_author,
                category=new_category
            ),
            notify=True,
            extra_metadata=json.loads(document_form.cleaned_data['extra_metadata'])
        )

        resource_manager.set_thumbnail(document.uuid, instance=document, overwrite=False)
        document_form.save_many2many()

        register_event(request, EventType.EVENT_CHANGE_METADATA, document)
        url = hookset.document_detail_url(document)
        if not ajax:
            return HttpResponseRedirect(url)
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
        if 'group' in document_form.changed_data:
            vals['group'] = document_form.cleaned_data.get('group')
        if any([x in document_form.changed_data for x in ['is_approved', 'is_published']]):
            vals['is_approved'] = document_form.cleaned_data.get('is_approved', document.is_approved)
            vals['is_published'] = document_form.cleaned_data.get('is_published', document.is_published)
        resource_manager.update(
            document.uuid,
            instance=document,
            notify=True,
            vals=vals,
            extra_metadata=json.loads(document_form.cleaned_data['extra_metadata'])
        )
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
