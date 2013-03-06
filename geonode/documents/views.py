import json, unicodedata

from urllib import urlencode

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.views.generic.list import ListView

from geonode.maps.views import _perms_info
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.maps.models import Map
from geonode.layers.models import Layer, TopicCategory
from geonode.people.models import Profile
from geonode.people.forms import ProfileForm

from geonode.documents.models import Document
from geonode.documents.forms import DocumentForm

IMGTYPES = ['jpg','jpeg','tif','tiff','png','gif']

DOCUMENT_LEV_NAMES = {
    Document.LEVEL_NONE  : _('No Permissions'),
    Document.LEVEL_READ  : _('Read Only'),
    Document.LEVEL_WRITE : _('Read/Write'),
    Document.LEVEL_ADMIN : _('Administrative')
}

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
            content_type = ContentType.objects.get(name=request.POST['ctype'])
            object_id = request.POST['objid']
        except:
            content_type = None
            object_id = None
        try:
            int(object_id)
        except: 
            if object_id is not None:
                object_id = Layer.objects.get(uuid=object_id).id

        doc_file = request.FILES['file']
        title = request.POST['title']
        document = Document(content_type=content_type, object_id=object_id, title=title, doc_file=doc_file)
        document.owner = request.user
        document.save()
        document.set_default_permissions()
        permissionsStr = request.POST['permissions']
        permissions = json.loads(permissionsStr)
        set_document_permissions(document, permissions)

        return HttpResponse(json.dumps({'success': True,'redirect_to': reverse('document_metadata', 
                args=(document.id,))}))

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

def ajax_document_permissions(request, docid):
    document = get_object_or_404(Document, pk=docid)

    if not request.method == 'POST':
        return HttpResponse(
            'You must use POST for editing document permissions',
            status=405,
            mimetype='text/plain'
        )

    if not request.user.has_perm("documents.change_document_permissions", obj=document):
        return HttpResponse(
            'You are not allowed to change permissions for this document',
            status=401,
            mimetype='text/plain'
        )

    spec = json.loads(request.raw_post_data)
    set_document_permissions(document, spec)

    return HttpResponse(
        "Permissions updated",
        status=200,
        mimetype='text/plain'
    )

def set_document_permissions(m, perm_spec):
    if "authenticated" in perm_spec:
        m.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        m.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    users = [n for (n, p) in perm_spec['users']]
    m.get_user_levels().exclude(user__username__in = users + [m.owner]).delete()
    for username, level in perm_spec['users']:
        user = User.objects.get(username=username)
        m.set_user_level(user, level)

def resources_search(request):
    """
    Search for maps and layers. Has no limit and allows sorting.
    """
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    ctype = params.get('type','layer')
    qset = Layer.objects.all().order_by('title') if ctype == 'layer' else Map.objects.all().order_by('title')

    resources_list= []

    for item in qset:
         resources_list.append({
            'id' : item.id,
            'title' : item.title,
        })

    result = {'rows': resources_list,'total': qset.count()}
    return HttpResponse(json.dumps(result))

def document_replace(docid):
    #TODO
    pass

def document_remove(docid):
    #TODO
    pass