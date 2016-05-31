import json

from django.contrib.sites.models import get_current_site
from django.http import Http404, HttpResponse
from django.contrib.auth import authenticate, get_user_model, login
from django.utils.translation import ugettext as _
from django.conf import settings
from django.shortcuts import redirect
from django.db.models import Q

from guardian.shortcuts import get_objects_for_user
from account.views import LoginView

from geonode.utils import _get_basic_auth_info
from geonode.layers.views import _resolve_layer, layer_detail
from geonode.documents.views import _resolve_document, document_detail
from geonode.maps.views import _resolve_map, map_detail
from geonode.base.models import ResourceBase
from geonode.layers.models import Layer
from geonode.geoserver.helpers import ogc_server_settings
from geonode.groups.models import GroupProfile
from geonode.views import AjaxLoginForm

from .models import SiteResources
from .utils import resources_for_site, users_for_site

_PERMISSION_MSG_VIEW = ('You don\'t have permissions to view this document')


def site_layer_detail(request, layername, template='layers/layer_detail.html'):
    # BETTER WAY INSTEAD OF DO TWO _RESOLVE_LAYER PER CALL?
    layer = _resolve_layer(
        request,
        layername,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)
    site = get_current_site(request)
    if not SiteResources.objects.get(site=site).resources.filter(pk=layer.pk).exists():
        raise Http404
    else:
        return layer_detail(request, layername, template='layers/layer_detail.html')


def site_document_detail(request, docid):
    # BETTER WAY INSTEAD OF DO TWO _RESOLVE_DOCUMENT PER CALL?
    document = _resolve_document(
        request,
        docid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)
    site = get_current_site(request)
    if not SiteResources.objects.get(site=site).resources.filter(pk=document.pk).exists():
        raise Http404
    else:
        return document_detail(request, docid)


def site_map_detail(request, mapid):
    # BETTER WAY INSTEAD OF DO TWO _RESOLVE_MAP PER CALL?
    the_map = _resolve_map(
        request,
        mapid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)
    site = get_current_site(request)
    if not SiteResources.objects.get(site=site).resources.filter(pk=the_map.pk).exists():
        raise Http404
    else:
        return map_detail(request, mapid, template='maps/map_detail.html')


def layer_acls(request):
    """
    returns json-encoded lists of layer identifiers that
    represent the sets of read-write and read-only layers
    for the currently authenticated user.
    """
    # the layer_acls view supports basic auth, and a special
    # user which represents the geoserver administrator that
    # is not present in django.
    acl_user = request.user
    if 'HTTP_AUTHORIZATION' in request.META:
        try:
            username, password = _get_basic_auth_info(request)
            acl_user = authenticate(username=username, password=password)

            # Nope, is it the special geoserver user?
            if (acl_user is None and
                    username == ogc_server_settings.USER and
                    password == ogc_server_settings.PASSWORD):
                # great, tell geoserver it's an admin.
                result = {
                    'rw': [],
                    'ro': [],
                    'name': username,
                    'is_superuser': True,
                    'is_anonymous': False
                }
                return HttpResponse(
                    json.dumps(result),
                    mimetype="application/json")
        except Exception:
            pass

        if acl_user is None:
            return HttpResponse(_("Bad HTTP Authorization Credentials."),
                                status=401,
                                mimetype="text/plain")

    # Include permissions on the anonymous user
    # use of polymorphic selectors/functions to optimize performances
    site_resources = resources_for_site()
    resources_readable = get_objects_for_user(acl_user, 'view_resourcebase',
                                              ResourceBase.objects.instance_of(Layer).filter(id__in=site_resources))
    layer_writable = get_objects_for_user(acl_user, 'change_layer_data',
                                          Layer.objects.filter(id__in=site_resources))

    _read = set(Layer.objects.filter(id__in=resources_readable).values_list('typename', flat=True))
    _write = set(layer_writable.values_list('typename', flat=True))

    read_only = _read ^ _write
    read_write = _read & _write

    result = {
        'rw': list(read_write),
        'ro': list(read_only),
        'name': acl_user.username,
        'is_superuser': acl_user.is_superuser,
        'is_anonymous': acl_user.is_anonymous(),
    }
    if acl_user.is_authenticated():
        result['fullname'] = acl_user.get_full_name()
        result['email'] = acl_user.email

    return HttpResponse(json.dumps(result), mimetype="application/json")


def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
            content="ajax login requires HTTP POST",
            status=405,
            mimetype="text/plain"
        )
    form = AjaxLoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        if not users_for_site().filter(username=username).exists():
            return HttpResponse(
                content="bad credentials or disabled user",
                status=400,
                mimetype="text/plain"
            )
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse(
                content="bad credentials or disabled user",
                status=400,
                mimetype="text/plain"
            )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(
                content="successful login",
                status=200,
                mimetype="text/plain"
            )
    else:
        return HttpResponse(
            "The form you submitted doesn't look like a username/password combo.",
            mimetype="text/plain",
            status=400)


def ajax_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            mimetype='text/plain')
    keyword = request.POST['query']
    users = get_user_model().objects.filter(id__in=users_for_site())
    users = users.filter(Q(username__istartswith=keyword) |
                         Q(first_name__icontains=keyword) |
                         Q(organization__icontains=keyword)).exclude(username='AnonymousUser')

    groups = GroupProfile.objects.filter(Q(title__istartswith=keyword) |
                                         Q(description__icontains=keyword))
    json_dict = {
        'users': [({'username': u.username}) for u in users],
        'count': users.count(),
    }

    json_dict['groups'] = [({'name': g.slug, 'title': g.title}) for g in groups]
    return HttpResponse(
        content=json.dumps(json_dict),
        mimetype='text/plain'
    )


class SiteLoginView(LoginView):

    def form_valid(self, form):
        if not users_for_site().filter(username=form.user.username).exists() and not form.user.is_superuser:
            return redirect(settings.ACCOUNT_LOGIN_URL)

        self.login_user(form)
        self.after_login(form)
        return redirect(self.get_success_url())
