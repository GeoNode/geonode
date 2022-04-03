#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from guardian.shortcuts import assign_perm
from geonode.security.utils import get_visible_resources
import logging

from django.conf import settings
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import loader
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from geonode.security.views import _perms_info_json
from geonode.layers.models import Layer
from geonode.proxy.views import proxy
from urllib.parse import urljoin
from urllib.parse import quote
from .serviceprocessors import get_service_handler
from . import enumerations
from . import forms
from .models import HarvestJob
from .models import Service
from . import tasks

logger = logging.getLogger(__name__)


@requires_csrf_token
@cache_control(public=True, must_revalidate=True, max_age=604800)
def service_proxy(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if not service.proxy_base:
        service_url = service.service_url
    else:
        _query_separator = '?' if '?' not in service.service_url else '&'
        service_url = f"{service.service_url}{_query_separator}{request.META['QUERY_STRING']}"
        if urljoin(settings.SITEURL, reverse('proxy')) != service.proxy_base:
            service_url = f"{service.proxy_base}?url={quote(service_url, safe='')}"
    return proxy(request, url=service_url, sec_chk_hosts=False)


def services(request):
    """This view shows the list of all registered services"""

    return render(
        request,
        "services/service_list.html",
        {
            "services": Service.objects.all(),
            "can_add_resources": request.user.has_perm('base.add_resourcebase')
        }
    )


@login_required
def register_service(request):
    service_register_template = "services/service_register.html"
    if request.method == "POST":
        form = forms.CreateServiceForm(request.POST)
        if form.is_valid():
            service_handler = form.cleaned_data["service_handler"]
            service = service_handler.create_geonode_service(
                owner=request.user)
            try:
                service.full_clean()
            except Exception as e:
                raise Http404(str(e))
            service.save()
            service.keywords.add(*service_handler.get_keywords())

            if service_handler.indexing_method == enumerations.CASCADED:
                service_handler.create_cascaded_store(service)
            request.session[service_handler.url] = service_handler
            logger.debug("Added handler to the session")
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Service registered successfully")
            )
            result = HttpResponseRedirect(
                reverse("harvest_resources",
                        kwargs={"service_id": service.id})
            )
        else:
            result = render(request, service_register_template, {"form": form})
    else:
        form = forms.CreateServiceForm()
        result = render(
            request, service_register_template, {"form": form})
    return result


def _get_service_handler(request, service):
    """Add the service handler to the HttpSession.
    We use the django session object to store the service handler's
    representation of the remote service between sequentially logic steps.
    This is done in order to improve user experience, as we avoid making
    multiple Capabilities requests (this is a time saver on servers that
    feature many layers.
    """
    service_handler = get_service_handler(
        service.service_url, service.type)
    request.session[service.service_url] = service_handler
    logger.debug("Added handler to the session")
    return service_handler


def harvest_resources_handle_get(request, service, handler):
    available_resources = handler.get_resources()
    is_sync = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
    errored_state = False
    _ = _perms_info_json(service)

    perms_list = list(
        service.get_self_resource().get_user_perms(request.user)
        .union(service.get_user_perms(request.user))
    )

    already_harvested = HarvestJob.objects.values_list(
        "resource_id", flat=True).filter(service=service, status=enumerations.PROCESSED)
    if available_resources:
        not_yet_harvested = [
            r for r in available_resources if str(r.id) not in already_harvested]
        not_yet_harvested.sort(key=lambda resource: resource.id)
    else:
        not_yet_harvested = ['Cannot parse any resource at this time!']
        errored_state = True
    paginator = Paginator(
        not_yet_harvested, getattr(settings, "CLIENT_RESULTS_LIMIT", 100))
    page = request.GET.get('page')
    try:
        harvestable_resources = paginator.page(page)
    except PageNotAnInteger:
        harvestable_resources = paginator.page(1)
    except EmptyPage:
        harvestable_resources = paginator.page(paginator.num_pages)

    filter_row = [{}, {"id": 'id-filter', "data_key": "id"},
                  {"id": 'name-filter', "data_key": "title"},
                  {"id": 'desc-filter', "data_key": "abstract"}]
    result = render(
        request,
        "services/service_resources_harvest.html",
        {
            "service_handler": handler,
            "service": service,
            "importable": not_yet_harvested,
            "resources": harvestable_resources,
            "requested": request.GET.getlist("resource_list"),
            "is_sync": is_sync,
            "errored_state": errored_state,
            "can_add_resources": request.user.has_perm('base.add_resourcebase'),
            "filter_row": filter_row,
            "permissions_list": perms_list

        }
    )
    return result


def harvest_resources_handle_post(request, service, handler):
    available_resources = handler.get_resources()
    is_sync = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
    requested = request.POST.getlist("resource_list")
    requested.extend(request.GET.getlist("resource_list"))
    # Let's remove duplicates
    requested = list(set(requested))
    resources_to_harvest = []
    for id in _gen_harvestable_ids(requested, available_resources):
        logger.debug(f"id: {id}")
        harvest_job, created = HarvestJob.objects.get_or_create(
            service=service,
            resource_id=id
        )
        if created or harvest_job.status != enumerations.PROCESSED:
            resources_to_harvest.append(id)
            tasks.harvest_resource.apply_async((harvest_job.id,))
        else:
            logger.warning(
                f"resource {id} already has a harvest job")
        # assign permission of the resource to the user
        perms = [
            'view_resourcebase', 'download_resourcebase',
            'change_resourcebase_metadata', 'change_resourcebase',
            'delete_resourcebase'
        ]
        layer = Layer.objects.filter(alternate=id)
        if layer.exists():
            for perm in perms:
                assign_perm(perm, request.user, layer.first().get_self_resource())
    msg_async = _("The selected resources are being imported")
    msg_sync = _("The selected resources have been imported")
    messages.add_message(
        request,
        messages.SUCCESS,
        msg_sync if is_sync else msg_async
    )
    go_to = (
        "harvest_resources" if handler.has_unharvested_resources(
            service) else "service_detail"
    )
    result = redirect(reverse(go_to, kwargs={"service_id": service.id}))
    return result


@login_required
def harvest_resources(request, service_id):

    service = get_object_or_404(Service, pk=service_id)
    try:
        handler = request.session[service.service_url]
    except KeyError:  # handler is not saved on the session, recreate it
        return redirect(
            reverse("rescan_service", kwargs={"service_id": service.id})
        )
    if request.method == "GET":
        return harvest_resources_handle_get(request, service, handler)
    elif request.method == "POST":
        return harvest_resources_handle_post(request, service, handler)


@login_required
def harvest_single_resource(request, service_id, resource_id):
    service = get_object_or_404(Service, pk=service_id)
    handler = _get_service_handler(request, service)
    try:  # check that resource_id is valid for this handler
        handler.get_resource(resource_id)
    except KeyError as e:
        raise Http404(str(e))
    harvest_job, created = HarvestJob.objects.get_or_create(
        service=service,
        resource_id=resource_id,
    )
    if not created and harvest_job.status == enumerations.IN_PROCESS:
        return HttpResponse(
            _("Resource is already being processed"), status=409)
    else:
        tasks.harvest_resource.apply_async((harvest_job.id,))
    messages.add_message(
        request,
        messages.SUCCESS,
        _(f"Resource {resource_id} is being processed")
    )
    return redirect(
        reverse("service_detail",
                kwargs={"service_id": service.id})
    )


def _gen_harvestable_ids(requested_ids, available_resources):
    available_resource_ids = [str(r.id) for r in available_resources]
    for id in requested_ids:
        identifier = str(id)
        if identifier in available_resource_ids:
            yield identifier


@login_required
def rescan_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    try:
        _get_service_handler(request, service)
    except Exception:
        return render(
            request,
            "services/remote_service_unavailable.html",
            {"service": service}
        )
    logger.debug("Finished rescaning service. About to redirect back...")
    messages.add_message(
        request, messages.SUCCESS, _("Service rescanned successfully"))
    return redirect(
        reverse("harvest_resources", kwargs={"service_id": service_id}))


@login_required
def service_detail(request, service_id):
    """This view shows the details of a service"""

    services = Service.objects.filter(resourcebase_ptr_id=service_id)

    if not services.exists():
        messages.add_message(
            request,
            messages.ERROR,
            _("You dont have enougth rigths to see the resource detail")
        )
        return redirect(
            reverse("services")
        )
    service = services.first()

    permissions_json = _perms_info_json(service)

    perms_list = list(
        service.get_self_resource().get_user_perms(request.user)
        .union(service.get_user_perms(request.user))
    )

    already_imported_layers = get_visible_resources(
        queryset=Layer.objects.filter(remote_service=service),
        user=request.user
    )
    resources_being_harvested = HarvestJob.objects.filter(service=service)

    service_list = service.service_set.all()
    all_resources = (list(resources_being_harvested) + list(already_imported_layers) + list(service_list))

    paginator = Paginator(
        all_resources,
        getattr(settings, "CLIENT_RESULTS_LIMIT", 25),
        orphans=3
    )
    page = request.GET.get("page")
    try:
        resources = paginator.page(page)
    except PageNotAnInteger:
        resources = paginator.page(1)
    except EmptyPage:
        resources = paginator.page(paginator.num_pages)

    # pop the handler out of the session in order to free resources
    # - we had stored the service handler on the session in order to
    # speed up the register/harvest resources flow. However, for services
    # with many resources, keeping the handler in the session leads to degraded
    # performance
    try:
        request.session.pop(service.service_url)
    except KeyError:
        pass

    return render(
        request,
        template_name="services/service_detail.html",
        context={
            "service": service,
            "layers": already_imported_layers,
            "resource_jobs": (
                r for r in resources if isinstance(r, HarvestJob)),
            "permissions_json": permissions_json,
            "permissions_list": perms_list,
            "can_add_resorces": request.user.has_perm('base.add_resourcebase'),
            "resources": resources,
            "total_resources": len(already_imported_layers),
        }
    )


@login_required
def edit_service(request, service_id):
    """
    Edit an existing Service
    """
    service = get_object_or_404(Service, pk=service_id)
    if request.user != service.owner and not request.user.has_perm('change_service', obj=service):
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _(
                        "You are not permitted to change this service."
                    )}, request=request), status=401)
    if request.method == "POST":
        service_form = forms.ServiceForm(
            request.POST, instance=service, prefix="service")
        if service_form.is_valid():
            service = service_form.save(commit=False)
            service.keywords.clear()
            service.keywords.add(*service_form.cleaned_data['keywords'])
            service.save()
            return HttpResponseRedirect(service.get_absolute_url())
    else:
        service_form = forms.ServiceForm(
            instance=service, prefix="service")
    return render(request,
                  "services/service_edit.html",
                  context={"service": service, "service_form": service_form})


@login_required
def remove_service(request, service_id):
    """Delete a service and its constituent layers"""
    service = get_object_or_404(Service, pk=service_id)
    if request.user != service.owner and not request.user.has_perm('delete_service', obj=service):
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _(
                        "You are not permitted to remove this service."
                    )}, request=request), status=401)
    if request.method == 'GET':
        return render(request, "services/service_remove.html",
                      {"service": service})
    elif request.method == 'POST':
        service.layer_set.all().delete()
        service.delete()
        messages.add_message(
            request,
            messages.INFO,
            _(f"Service {service.name} has been deleted")
        )
        return HttpResponseRedirect(reverse("services"))
