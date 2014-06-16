import json, os

from django.shortcuts import render_to_response, get_object_or_404,render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django_downloadview.response import DownloadResponse
from django.views.generic.edit import UpdateView, CreateView
from geonode.utils import resolve_object
from geonode.security.views import _perms_info_json
from geonode.people.forms import ProfileForm
from geonode.base.forms import CategoryForm
from geonode.base.models import TopicCategory
from geonode.documents.models import Document
from geonode.documents.forms import DocumentForm, DocumentCreateForm, DocumentReplaceForm
from geonode.documents.models import IMGTYPES

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this document.')
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _("You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")

def _resolve_document(request, docid, permission='base.change_resourcebase',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the layer by the provided typename and check the optional permission.
    '''
    return resolve_object(request, Document, {'pk':docid},
                          permission = permission, permission_msg=msg, **kwargs)

def document_detail(request, docid):
    """
    The view that show details of each document
    """
    document = get_object_or_404(Document, pk=docid)
    if not request.user.has_perm('view_resourcebase', obj=document.get_self_resource()):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not allowed to view this document.")})), status=403)
    try:
        related = document.content_type.get_object_for_this_type(id=document.object_id)
    except:
        related = ''

    document.popular_count += 1
    document.save()

    return render_to_response("documents/document_detail.html", RequestContext(request, {
        'permissions_json': _perms_info_json(document),
        'resource': document,
        'imgtypes': IMGTYPES,
        'related': related
    }))

def document_download(request, docid):
    document = get_object_or_404(Document, pk=docid)
    if not request.user.has_perm('base.view_resourcebase', obj=document.get_self_resource()):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not allowed to view this document.")})), status=401)
    return DownloadResponse(document.doc_file)

class DocumentUploadView(CreateView):
    template_name = 'documents/document_upload.html'
    form_class = DocumentCreateForm

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        self.object.set_permissions(form.cleaned_data['permissions'])
        return HttpResponseRedirect(reverse('document_metadata', args=(self.object.id,)))

class DocumentUpdateView(UpdateView):
    template_name = 'documents/document_replace.html'
    pk_url_kwarg = 'docid'
    form_class = DocumentReplaceForm
    queryset = Document.objects.all()
    context_object_name = 'document'

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save()
        return HttpResponseRedirect(reverse('document_metadata', args=(self.object.id,)))

@login_required
def document_metadata(request, docid, template='documents/document_metadata.html'):
    document = Document.objects.get(id=docid)

    poc = document.poc
    metadata_author = document.metadata_author
    topic_category = document.category

    if request.method == "POST":
        document_form = DocumentForm(request.POST, instance=document, prefix="resource")
        category_form = CategoryForm(request.POST,prefix="category_choice_field",
             initial=int(request.POST["category_choice_field"]) if "category_choice_field" in request.POST else None)  
    else:
        document_form = DocumentForm(instance=document, prefix="resource")
        category_form = CategoryForm(prefix="category_choice_field", initial=topic_category.id if topic_category else None)

    if request.method == "POST" and document_form.is_valid() and category_form.is_valid():
        new_poc = document_form.cleaned_data['poc']
        new_author = document_form.cleaned_data['metadata_author']
        new_keywords = document_form.cleaned_data['keywords']
        new_category = TopicCategory.objects.get(id=category_form.cleaned_data['category_choice_field'])

        if new_poc is None:
            if poc.user is None:
                poc_form = ProfileForm(request.POST, prefix="poc", instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author.user is None:
                author_form = ProfileForm(request.POST, prefix="author", 
                    instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        if new_poc is not None and new_author is not None:
            the_document = document_form.save()
            the_document.poc = new_poc
            the_document.metadata_author = new_author
            the_document.keywords.add(*new_keywords)
            the_document.category = new_category
            the_document.save()
            return HttpResponseRedirect(reverse('document_detail', args=(document.id,)))

    if poc is None:
        poc_form = ProfileForm(request.POST, prefix="poc")
    else:
        if poc.user is None:
            poc_form = ProfileForm(instance=poc, prefix="poc")
        else:
            document_form.fields['poc'].initial = poc.id
            poc_form = ProfileForm(prefix="poc")
            poc_form.hidden = True

    if metadata_author is None:
            author_form = ProfileForm(request.POST, prefix="author")
    else:
        if metadata_author.user is None:
            author_form = ProfileForm(instance=metadata_author, prefix="author")
        else:
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

    return render_to_response('documents/document_search.html', RequestContext(request, {
        'init_search': json.dumps(params or {}),
         "site" : settings.SITEURL
    }))

@login_required
def document_remove(request, docid, template='documents/document_remove.html'):
    try:
        document = _resolve_document(request, docid, 'base.delete_resourcebase',
                               _PERMISSION_MSG_DELETE)

        if request.method == 'GET':
            return render_to_response(template,RequestContext(request, {
                "document": document
            }))
        if request.method == 'POST':
            document.delete()
            return HttpResponseRedirect(reverse("documents_browse"))
        else:
            return HttpResponse("Not allowed",status=403)

    except PermissionDenied:
        return HttpResponse(
                'You are not allowed to delete this document',
                mimetype="text/plain",
                status=401
        )

