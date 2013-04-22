import json, os

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

from geonode.utils import resolve_object
from geonode.maps.views import _perms_info
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.people.forms import ProfileForm

from geonode.documents.models import Document
from geonode.documents.forms import DocumentForm

IMGTYPES = ['jpg','jpeg','tif','tiff','png','gif']

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES

DOCUMENT_LEV_NAMES = {
    Document.LEVEL_NONE  : _('No Permissions'),
    Document.LEVEL_READ  : _('Read Only'),
    Document.LEVEL_WRITE : _('Read/Write'),
    Document.LEVEL_ADMIN : _('Administrative')
}

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this document.')
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _("You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")

def _resolve_document(request, docid, permission='layers.change_layer',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the layer by the provided typename and check the optional permission.
    '''
    return resolve_object(request, Document, {'pk':docid},
                          permission = permission, permission_msg=msg, **kwargs)

def document_list(request, template='documents/document_list.html'):
    from geonode.search.views import search_page
    post = request.POST.copy()
    post.update({'type': 'document'})
    request.POST = post
    return search_page(request, template=template)

def document_tag(request, slug, template='documents/document_list.html'):
    document_list = Document.objects.filter(keywords__slug__in=[slug])
    return render_to_response(
        template,
        RequestContext(request, {
            "object_list": document_list,
            "document_tag": slug
            }
        )
    )

def document_detail(request, docid):
    """
    The view that show details of each document
    """
    document = get_object_or_404(Document, pk=docid)
    if not request.user.has_perm('documents.view_document', obj=document):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(request, {'error_message':
                _("You are not allowed to view this document.")})), status=401)
    try:
        related = document.content_type.get_object_for_this_type(id=document.object_id)
    except:
        related = ''

    return render_to_response("documents/document_detail.html", RequestContext(request, {
        'permissions_json': json.dumps(_perms_info(document, DOCUMENT_LEV_NAMES)),
        'document': document,
        'imgtypes': IMGTYPES,
        'related': related
    }))


@login_required
def document_upload(request):
    if request.method == 'GET':
        return render_to_response('documents/document_upload.html',
                                  RequestContext(request),
                                  context_instance=RequestContext(request)
        )

    elif request.method == 'POST':
        
        try:
            content_type = ContentType.objects.get(name=request.POST['type'])
            object_id = request.POST['q']
        except:
            content_type = None
            object_id = None
        
        if not os.path.splitext(request.FILES['file'].name)[1].lower()[1:] in ALLOWED_DOC_TYPES:
            return HttpResponse('This file type is not allowed.')
        if not request.FILES['file'].size < settings.MAX_DOCUMENT_SIZE * 1024 * 1024:
            return HttpResponse('This file is too big.')

        doc_file = request.FILES['file']
        title = request.POST['title']
        document = Document(content_type=content_type, object_id=object_id, title=title, doc_file=doc_file)
        document.owner = request.user
        document.save()
        permissionsStr = request.POST['permissions']
        permissions = json.loads(permissionsStr)
        document_set_permissions(document, permissions)

        return HttpResponseRedirect(reverse('document_metadata', args=(document.id,)))

@login_required
def document_metadata(request, docid, template='documents/document_metadata.html'):
    document = Document.objects.get(id=docid)

    poc = document.poc
    metadata_author = document.metadata_author

    if request.method == "POST":
        document_form = DocumentForm(request.POST, instance=document, prefix="document")
    else:
        document_form = DocumentForm(instance=document, prefix="document")

    if request.method == "POST" and document_form.is_valid():
        new_poc = document_form.cleaned_data['poc']
        new_author = document_form.cleaned_data['metadata_author']
        new_keywords = document_form.cleaned_data['keywords']

        if new_poc is None:
            poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        if new_poc is not None and new_author is not None:
            the_document = document_form.save(commit=False)
            the_document.poc = new_poc
            the_document.metadata_author = new_author
            the_document.keywords.add(*new_keywords)
            the_document.save()
            return HttpResponseRedirect(reverse('document_detail', args=(document.id,)))

    if poc.user is None:
        poc_form = ProfileForm(instance=poc, prefix="poc")
    else:
        document_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden=True

    if metadata_author.user is None:
        author_form = ProfileForm(instance=metadata_author, prefix="author")
    else:
        document_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden=True

    return render_to_response(template, RequestContext(request, {
        "document": document,
        "document_form": document_form,
        "poc_form": poc_form,
        "author_form": author_form,
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

def document_permissions(request, docid):
    try:
        document = _resolve_document(request, docid, 'documents.change_document_permissions')
    except PermissionDenied:
        # we are handling this in a non-standard way
        return HttpResponse(
            'You are not allowed to change permissions for this layer',
            status=401,
            mimetype='text/plain')

    if request.method == 'POST':
        permission_spec = json.loads(request.raw_post_data)
        document_set_permissions(document, permission_spec)

        return HttpResponse(
            json.dumps({'success': True}),
            status=200,
            mimetype='text/plain'
        )

    elif request.method == 'GET':
        permission_spec = json.dumps(document.get_all_level_info())
        return HttpResponse(
            json.dumps({'success': True, 'permissions': permission_spec}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponse(
            'No methods other than get and post are allowed',
            status=401,
            mimetype='text/plain')

def document_set_permissions(document, perm_spec):
    if "authenticated" in perm_spec:
        document.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        document.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    users = [n[0] for n in perm_spec['users']]
    excluded = users + [document.owner]
    existing = document.get_user_levels().exclude(user__username__in=excluded)
    existing.delete()
    for username, level in perm_spec['users']:
        user = User.objects.get(username=username)
        document.set_user_level(user, level)

@login_required
def document_replace(request, docid, template='documents/document_replace.html'):
    document = _resolve_document(request, docid, 'documents.change_document')

    if request.method == 'GET':
        return render_to_response(template,RequestContext(request, {
            "document": document
        }))
    if request.method == 'POST':
        if not os.path.splitext(request.FILES['file'].name)[1].lower()[1:] in ALLOWED_DOC_TYPES:
            return HttpResponse('This file type is not allowed.')
        if not request.FILES['file'].size < settings.MAX_DOCUMENT_SIZE * 1024 * 1024:
            return HttpResponse('This file is too big.')

        doc_file = request.FILES['file']
        document.doc_file=doc_file
        document.save()
        return HttpResponseRedirect(reverse('document_detail', args=(document.id,)))

@login_required
def document_remove(request, docid, template='documents/document_remove.html'):
    document = _resolve_document(request, docid, 'documents.delete_document',
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