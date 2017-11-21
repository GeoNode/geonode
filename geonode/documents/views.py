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

import json
from guardian.shortcuts import get_perms

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django_downloadview.response import DownloadResponse
from django.views.generic.edit import UpdateView, CreateView
from django.db.models import F
from django.forms.util import ErrorList


#@jahangir091
from django.views.generic import ListView
from django.contrib import messages

from notify.signals import notify
#end


from geonode.utils import resolve_object
from geonode.security.views import _perms_info_json
from geonode.people.forms import ProfileForm
from geonode.base.forms import CategoryForm, ResourceDenyForm, ResourceApproveForm
from geonode.base.models import TopicCategory, ResourceBase
from geonode.documents.models import Document, DocumentLayers
from geonode.documents.forms import DocumentForm, DocumentCreateForm, DocumentReplaceForm
from geonode.documents.models import IMGTYPES
from geonode.utils import build_social_links


#@jahangir091
from geonode.documents.models import DocumentSubmissionActivity, DocumentAuditActivity
from geonode.groups.models import GroupProfile
#end

import logging


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
    
    #@jahangir091
    try:
        user_role = request.GET['user_role']
    except:
        user_role=None
    #end


    document = None
    try:
        document = _resolve_document(
            request,
            docid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)

    except Http404:
        return HttpResponse(
            loader.render_to_string(
                '404.html', RequestContext(
                    request, {
                        })), status=404)

    except PermissionDenied:
        return HttpResponse(
            loader.render_to_string(
                '401.html', RequestContext(
                    request, {
                        'error_message': _("You are not allowed to view this document.")})), status=403)

    if document is None:
        return HttpResponse(
            'An unknown error has occured.',
            content_type="text/plain",
            status=401
        )

    else:
        try:
            related = document.content_type.get_object_for_this_type(
                id=document.object_id)
        except:
            related = ''

        # Update count for popularity ranking,
        # but do not includes admins or resource owners
        if request.user != document.owner and not request.user.is_superuser:
            Document.objects.filter(id=document.id).update(popular_count=F('popular_count') + 1)

        metadata = document.link_set.metadata().filter(
            name__in=settings.DOWNLOAD_FORMATS_METADATA)
        
        #@jahangir091
        approve_form = ResourceApproveForm()
        deny_form = ResourceDenyForm()
        #@jahangir091


        context_dict = {
            'perms_list': get_perms(request.user, document.get_self_resource()),
            'permissions_json': _perms_info_json(document),
            'resource': document,
            'metadata': metadata,
            'imgtypes': IMGTYPES,
            'related': related,
            "user_role": user_role,
            "status": document.status,
            "approve_form": approve_form,
            "deny_form": deny_form,
            "denied_comments": DocumentAuditActivity.objects.filter(document_submission_activity__document=document),
            "document_layers": document.layers.all(),

        }

        if settings.SOCIAL_ORIGINS:
            context_dict["social_links"] = build_social_links(request, document)

        if getattr(settings, 'EXIF_ENABLED', False):
            try:
                from geonode.contrib.exif.utils import exif_extract_dict
                exif = exif_extract_dict(document)
                if exif:
                    context_dict['exif_data'] = exif
            except:
                print "Exif extraction failed."

        return render_to_response(
            "documents/document_detail.html",
            RequestContext(request, context_dict))


def document_download(request, docid):
    document = get_object_or_404(Document, pk=docid)
    if not request.user.has_perm(
            'base.download_resourcebase',
            obj=document.get_self_resource()):
        return HttpResponse(
            loader.render_to_string(
                '401.html', RequestContext(
                    request, {
                        'error_message': _("You are not allowed to view this document.")})), status=401)
    return DownloadResponse(document.doc_file)


class DocumentUploadView(CreateView):
    template_name = 'documents/document_upload.html'
    form_class = DocumentCreateForm


    def get_context_data(self, **kwargs):
        context = super(DocumentUploadView, self).get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        context['ogranizations'] = GroupProfile.objects.filter(groupmember__user=self.request.user)
        context['categories'] = TopicCategory.objects.all()
        return context

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        resource_id = self.request.POST.get('resource', None)
        resource_ids = str(resource_id).split(',')
        db_logger = logging.getLogger('db')

        #@jahangir091
        group_id = self.request.POST.get('org-id', None)
        category_id = self.request.POST.get('category-id', None)
        try:
            group = GroupProfile.objects.get(pk=group_id)
        except GroupProfile.DoesNotExist:
            raise Http404('Selected organization does not exists')
        try:
            category = [TopicCategory.objects.get(gn_description=category_id)]

            if isinstance(category, list):
                category = category[0]
        except TopicCategory.DoesNotExist:
            db_logger.error('Selected category does not exists')
            raise Http404('Selected category does not exists')
        self.object.group = group
        self.object.category = category
        #end


        # by default, if RESOURCE_PUBLISHING=True then document.is_published
        # must be set to False
        is_published = True
        if settings.RESOURCE_PUBLISHING:
            is_published = False
        self.object.is_published = is_published

        self.object.save()
        self.object.set_permissions(form.cleaned_data['permissions'])
        document_layers = []
        if '' not in resource_ids:

            for resource_id in resource_ids:
                document_layer_object = DocumentLayers(document=self.object)
                document_layer_object.content_type = ResourceBase.objects.get(id=resource_id).polymorphic_ctype
                document_layer_object.layer_id = resource_id
                document_layer_object.save()
                document_layers.append(document_layer_object.id)

        abstract = None
        date = None
        regions = []
        keywords = []
        bbox = None

        if getattr(settings, 'EXIF_ENABLED', False):
            try:
                from geonode.contrib.exif.utils import exif_extract_metadata_doc
                exif_metadata = exif_extract_metadata_doc(self.object)
                if exif_metadata:
                    date = exif_metadata.get('date', None)
                    keywords.extend(exif_metadata.get('keywords', []))
                    bbox = exif_metadata.get('bbox', None)
                    abstract = exif_metadata.get('abstract', None)
            except:
                db_logger.error("Exif extraction failed.")
                print "Exif extraction failed."

        if getattr(settings, 'NLP_ENABLED', False):
            try:
                from geonode.contrib.nlp.utils import nlp_extract_metadata_doc
                nlp_metadata = nlp_extract_metadata_doc(self.object)
                if nlp_metadata:
                    regions.extend(nlp_metadata.get('regions', []))
                    keywords.extend(nlp_metadata.get('keywords', []))
            except:
                db_logger.error("NLP extraction failed.")
                print "NLP extraction failed."

        if abstract:
            self.object.abstract = abstract
            self.object.save()

        if date:
            self.object.date = date
            self.object.date_type = "Creation"
            self.object.save()

        if len(regions) > 0:
            self.object.regions.add(*regions)

        if len(keywords) > 0:
            self.object.keywords.add(*keywords)

        if bbox:
            bbox_x0, bbox_x1, bbox_y0, bbox_y1 = bbox
            Document.objects.filter(id=self.object.pk).update(
                bbox_x0=bbox_x0,
                bbox_x1=bbox_x1,
                bbox_y0=bbox_y0,
                bbox_y1=bbox_y1)

        if getattr(settings, 'SLACK_ENABLED', False):
            try:
                from geonode.contrib.slack.utils import build_slack_message_document, send_slack_message
                send_slack_message(build_slack_message_document("document_new", self.object))
            except:
                db_logger.error("Could not send slack message for new document.")
                print "Could not send slack message for new document."

        return HttpResponseRedirect(
            reverse(
                'document_metadata',
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
        context = super(DocumentUpdateView, self).get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        return context

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save()
        return HttpResponseRedirect(
            reverse(
                'document_metadata',
                args=(
                    self.object.id,
                )))


@login_required
def document_metadata(
        request,
        docid,
        template='documents/document_metadata.html'):

    document = None
    try:
        document = _resolve_document(
            request,
            docid,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)

    except Http404:
        return HttpResponse(
            loader.render_to_string(
                '404.html', RequestContext(
                    request, {
                        })), status=404)

    except PermissionDenied:
        return HttpResponse(
            loader.render_to_string(
                '401.html', RequestContext(
                    request, {
                        'error_message': _("You are not allowed to edit this document.")})), status=403)

    if document is None:
        return HttpResponse(
            'An unknown error has occured.',
            content_type="text/plain",
            status=401
        )

    else:
        poc = document.poc
        metadata_author = document.metadata_author
        topic_category = document.category

        if request.method == "POST":
            document_form = DocumentForm(
                request.POST,
                instance=document,
                prefix="resource")
            category_form = CategoryForm(
                request.POST,
                prefix="category_choice_field",
                initial=int(
                    request.POST["category_choice_field"]) if "category_choice_field" in request.POST else None)
        else:
            document_form = DocumentForm(instance=document, prefix="resource")
            category_form = CategoryForm(
                prefix="category_choice_field",
                initial=topic_category.id if topic_category else None)

        if request.method == "POST" and document_form.is_valid(
        ) and category_form.is_valid():
            new_poc = document_form.cleaned_data['poc']
            new_author = document_form.cleaned_data['metadata_author']
            new_keywords = document_form.cleaned_data['keywords']
            new_category = TopicCategory.objects.get(
                id=category_form.cleaned_data['category_choice_field'])

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
                        errors = poc_form._errors.setdefault('profile', ErrorList())
                        errors.append(_('You must set a point of contact for this resource'))
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
                        errors = author_form._errors.setdefault('profile', ErrorList())
                        errors.append(_('You must set an author for this resource'))
                        metadata_author = None
                if author_form.has_changed and author_form.is_valid():
                    new_author = author_form.save()

            if new_poc is not None and new_author is not None:
                the_document = document_form.save()
                the_document.poc = new_poc
                the_document.metadata_author = new_author
                the_document.keywords.add(*new_keywords)
                Document.objects.filter(id=the_document.id).update(category=new_category)

                if getattr(settings, 'SLACK_ENABLED', False):
                    try:
                        from geonode.contrib.slack.utils import build_slack_message_document, send_slack_messages
                        send_slack_messages(build_slack_message_document("document_edit", the_document))
                    except:
                        print "Could not send slack message for modified document."

                return HttpResponseRedirect(
                    reverse(
                        'document_detail',
                        args=(
                            document.id,
                        )))

        if poc is not None:
            document_form.fields['poc'].initial = poc.id
            poc_form = ProfileForm(prefix="poc")
            poc_form.hidden = True

        if metadata_author is not None:
            document_form.fields['metadata_author'].initial = metadata_author.id
            author_form = ProfileForm(prefix="author")
            author_form.hidden = True

        return render_to_response(template, RequestContext(request, {
            "document": document,
            "document_form": document_form,
            "poc_form": poc_form,
            "author_form": author_form,
            "category_form": category_form,
        }))


def document_search_page(request):
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    return render_to_response(
        'documents/document_search.html',
        RequestContext(
            request,
            {
                'init_search': json.dumps(
                    params or {}),
                "site": settings.SITEURL}))


@login_required
def document_remove(request, docid, template='documents/document_remove.html'):
    try:
        document = _resolve_document(
            request,
            docid,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)

        if request.method == 'GET':
            return render_to_response(template, RequestContext(request, {
                "document": document
            }))

        if request.method == 'POST':

            if getattr(settings, 'SLACK_ENABLED', False):
                slack_message = None
                try:
                    from geonode.contrib.slack.utils import build_slack_message_document
                    slack_message = build_slack_message_document("document_delete", document)
                except:
                    print "Could not build slack message for delete document."

                document.delete()

                #@jahangir091
                # notify document owner that someone have deleted the document
                if request.user != document.owner:
                    recipient = document.owner
                    notify.send(request.user, recipient=recipient, actor=request.user,
                    target=document, verb='deleted your document')
                #end


                try:
                    from geonode.contrib.slack.utils import send_slack_messages
                    send_slack_messages(slack_message)
                except:
                    print "Could not send slack message for delete document."
            else:
                document.delete()

                #@jahangir091
                # notify document owner that someone have deleted the document
                if request.user != document.owner:
                    recipient = document.owner
                    notify.send(request.user, recipient=recipient, actor=request.user,
                    target=document, verb='deleted your document')
                #end


            return HttpResponseRedirect(reverse("document_browse"))
        else:
            return HttpResponse("Not allowed", status=403)

    except PermissionDenied:
        return HttpResponse(
            loader.render_to_string(
                '401.html', RequestContext(
                    request, {
                        'error_message': _("You are not allowed to delete this document.")})), status=401)
        # return HttpResponse(
        #     'You are not allowed to delete this document',
        #     content_type="text/plain",
        #     status=401
        # )


def document_metadata_detail(request, docid, template='documents/document_metadata_detail.html'):
    document = _resolve_document(
        request,
        docid,
        'view_resourcebase',
        _PERMISSION_MSG_METADATA)
    return render_to_response(template, RequestContext(request, {
        "resource": document,
        'SITEURL': settings.SITEURL[:-1]
    }))



#@jahangir091

@login_required
def document_publish(request, document_pk):
    if request.method == 'POST':
        try:
            document = Document.objects.get(id=document_pk)
        except Document.DoesNotExist:
            raise Http404("Document does not exist")
        else:
            if request.user != document.owner:
                return HttpResponse(
                    loader.render_to_string(
                        '401.html', RequestContext(
                        request, {
                        'error_message': _("you are not allowed to publish this document.")})), status=403)
                # return HttpResponse('you are not allowed to publish this document')
            group = document.group
            document.status = 'PENDING'
            document.current_iteration += 1
            document.save()
            document_submission_activity = DocumentSubmissionActivity(document=document, group=group, iteration=document.current_iteration)
            document_submission_activity.save()
            # notify organization admins about the new published document
            managers = list( group.get_managers())
            notify.send(request.user, recipient_list = managers, actor=request.user,
                        verb='pushed a new document for approval', target=document)
            # set all the permissions for all the managers of the group for this documentt
            document.set_managers_permissions()

            messages.info(request, 'Pushed document succesfully for approval')
            return HttpResponseRedirect(reverse('member-workspace-document'))
    else:
        return HttpResponseRedirect(reverse('member-workspace-document'))


@login_required
def document_approve(request, document_pk):
    if request.method == 'POST':
        form = ResourceApproveForm(request.POST)
        if form.is_valid():
            try:
                document = Document.objects.get(id=document_pk)
            except Document.DoesNotExist:
                raise Http404("requested document does not exists")
            else:
                group = document.group
                if request.user not in group.get_managers():
                    return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("you are not allowed to approve this document.")})), status=401)
                    # return HttpResponse("you are not allowed to approve this document")
                document_submission_activity = DocumentSubmissionActivity.objects.get(document=document, group=group, iteration=document.current_iteration)
                document_audit_activity = DocumentAuditActivity(document_submission_activity=document_submission_activity)
                comment_body = request.POST.get('comment')
                comment_subject = request.POST.get('comment_subject')
                document.status = 'ACTIVE'
                document.last_auditor = request.user
                document.save()

                permissions = _perms_info_json(document)
                perm_dict = json.loads(permissions)
                if request.POST.get('view_permission'):
                    if not 'AnonymousUser' in perm_dict['users']:
                        perm_dict['users']['AnonymousUser'] = []
                        perm_dict['users']['AnonymousUser'].append('view_resourcebase')
                    else:
                        if not 'view_resourcebase' in perm_dict['users']['AnonymousUser']:
                            perm_dict['users']['AnonymousUser'].append('view_resourcebase')

                if request.POST.get('download_permission'):
                    if not 'AnonymousUser' in perm_dict['users']:
                        perm_dict['users']['AnonymousUser'] = []
                        perm_dict['users']['AnonymousUser'].append('download_resourcebase')
                    else:
                        if not 'download_resourcebase' in perm_dict['users']['AnonymousUser']:
                            perm_dict['users']['AnonymousUser'].append('download_resourcebase')
                document.set_permissions(perm_dict)


                # notify document owner that someone have deleted the document
                if request.user != document.owner:
                    recipient = document.owner
                    notify.send(request.user, recipient=recipient, actor=request.user,
                    target=document, verb='deleted your document')

                document_submission_activity.is_audited = True
                document_submission_activity.save()

                document_audit_activity.comment_subject = comment_subject
                document_audit_activity.comment_body = comment_body
                document_audit_activity.result = 'APPROVED'
                document_audit_activity.auditor = request.user
                document_audit_activity.save()

            messages.info(request, 'Approved document succesfully')
            return HttpResponseRedirect(reverse('admin-workspace-document'))
        else:
            messages.info(request, 'Please write an approve comment and try again')
            return HttpResponseRedirect(reverse('admin-workspace-document'))
    else:
        return HttpResponseRedirect(reverse('admin-workspace-document'))


@login_required
def document_deny(request, document_pk):
    if request.method == 'POST':
        form = ResourceDenyForm(request.POST)
        if form.is_valid():
            try:
                document = Document.objects.get(id=document_pk)
            except Document.DoesNotExist:
                raise Http404("requested document does not exists")
            else:
                group = document.group
                if request.user not in group.get_managers():
                    return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("you are not allowed to deny this document.")})), status=401)
                    # return HttpResponse("you are not allowed to deny this document")
                document_submission_activity = DocumentSubmissionActivity.objects.get(document=document, group=group, iteration=document.current_iteration)
                document_audit_activity= DocumentAuditActivity(document_submission_activity=document_submission_activity)
                comment_body = request.POST.get('comment')
                comment_subject = request.POST.get('comment_subject')
                document.status = 'DENIED'
                document.last_auditor = request.user
                document.save()

                # notify document owner that someone have deleted the document
                if request.user != document.owner:
                    recipient = document.owner
                    notify.send(request.user, recipient=recipient, actor=request.user,
                    target=document, verb='deleted your document')

                document_submission_activity.is_audited = True
                document_submission_activity.save()

                document_audit_activity.comment_subject = comment_subject
                document_audit_activity.comment_body = comment_body
                document_audit_activity.result = 'DECLINED'
                document_audit_activity.auditor = request.user
                document_audit_activity.save()

            messages.info(request, 'Denied document successfully')
            return HttpResponseRedirect(reverse('admin-workspace-document'))
        else:
            messages.info(request, 'Please write a deny comment and try again')
            return HttpResponseRedirect(reverse('admin-workspace-document'))

    else:
        return HttpResponseRedirect(reverse('admin-workspace-document'))


@login_required
def document_delete(request, document_pk):
    if request.method == 'POST':
        try:
            document = Document.objects.get(id=document_pk)
        except Document.DoesNotExist:
            raise Http404("requested document does not exists")
        else:
            if document.status == 'DRAFT' and ( request.user == document.owner or request.user in document.group.get_managers()):
                document.status = "DELETED"
                document.save()
            else:
                return HttpResponse(
                        loader.render_to_string(
                            '401.html', RequestContext(
                            request, {
                            'error_message': _("You have no acces to delete the document.")})), status=401)
                # messages.info(request, 'You have no acces to delete the document')

        messages.info(request, 'Deleted the document successfully')
        if request.user == document.owner:
            return HttpResponseRedirect(reverse('member-workspace-document'))
        else:
            return HttpResponseRedirect(reverse('admin-workspace-document'))

    else:
        return HttpResponseRedirect(reverse('member-workspace-document'))

#end