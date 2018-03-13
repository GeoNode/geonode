# -*- coding: utf-8 -*-
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

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import loader
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.cache import cache_control
from geonode.security.views import _perms_info_json
from geonode.layers.models import Layer
from geonode.proxy.views import proxy
from urlparse import urljoin
from urllib import quote
from .serviceprocessors import get_service_handler
from . import enumerations
from . import forms
from .models import HarvestJob
from .models import Service
from . import tasks

logger = logging.getLogger("geonode.core.layers.views")


@requires_csrf_token
@cache_control(public=True, must_revalidate=True, max_age=604800)
def service_proxy(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if not service.proxy_base:
        service_url = service.base_url
    else:
        service_url = "{ows_url}?{ows_request}".format(
            ows_url=service.base_url, ows_request=request.META['QUERY_STRING'])
        if urljoin(settings.SITEURL, reverse('proxy')) != service.proxy_base:
            service_url = "{proxy_base}?url={service_url}".format(proxy_base=service.proxy_base,
                                                                  service_url=quote(service_url, safe=''))
    return proxy(request, url=service_url)


@login_required
def services(request):
    """This view shows the list of all registered services"""
    return render(
        request,
        "services/service_list.html",
        {"services": Service.objects.all()}
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
            service.full_clean()
            service.save()
            service.keywords.add(*service_handler.get_keywords())
            service.set_default_permissions()
            if service_handler.indexing_method == enumerations.CASCADED:
                service_handler.create_cascaded_store()
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
        service.base_url, service.proxy_base, service.type)
    request.session[service.base_url] = service_handler
    logger.debug("Added handler to the session")
    return service_handler


@login_required()
def harvest_resources(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    try:
        handler = request.session[service.base_url]
    except KeyError:  # handler is not saved on the session, recreate it
        return redirect(
            reverse("rescan_service", kwargs={"service_id": service.id})
        )
    available_resources = handler.get_resources()
    is_sync = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
    if request.method == "GET":
        already_harvested = HarvestJob.objects.values_list(
            "resource_id", flat=True).filter(service=service)
        not_yet_harvested = [
            r for r in available_resources if r.id not in already_harvested]
        not_yet_harvested.sort(key=lambda resource: resource.id)
        paginator = Paginator(
            not_yet_harvested, getattr(settings, "CLIENT_RESULTS_LIMIT", 100))
        page = request.GET.get('page')
        try:
            harvestable_resources = paginator.page(page)
        except PageNotAnInteger:
            harvestable_resources = paginator.page(1)
        except EmptyPage:
            harvestable_resources = paginator.page(paginator.num_pages)
        result = render(
            request,
            "services/service_resources_harvest.html",
            {
                "service_handler": handler,
                "service": service,
                "importable": not_yet_harvested,
                "resources": harvestable_resources,
                "is_sync": is_sync,
            }
        )
    elif request.method == "POST":
        requested = request.POST.getlist("resource_list")
        resources_to_harvest = []
        for id in _gen_harvestable_ids(requested, available_resources):
            logger.debug("id: {}".format(id))
            harvest_job, created = HarvestJob.objects.get_or_create(
                service=service,
                resource_id=id,
            )
            if created:
                resources_to_harvest.append(id)
                tasks.harvest_resource.apply_async((harvest_job.id,))
            else:
                logger.warning(
                    "resource {} already has a harvest job".format(id))
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
    else:
        result = None
    return result


@login_required()
def harvest_single_resource(request, service_id, resource_id):
    service = get_object_or_404(Service, pk=service_id)
    handler = _get_service_handler(request, service)
    try:  # check that resource_id is valid for this handler
        handler.get_resource(resource_id)
    except KeyError:
        raise Http404()
    harvest_job, created = HarvestJob.objects.get_or_create(
        service=service,
        resource_id=resource_id,
    )
    if not created and harvest_job.status == enumerations.IN_PROCESS:
        raise HttpResponse(
            _("Resource is already being processed"), status=409)
    else:
        tasks.harvest_resource.apply_async((harvest_job.id,))
    messages.add_message(
        request,
        messages.SUCCESS,
        _("Resource {} is being processed".format(resource_id))
    )
    return redirect(
        reverse("service_detail",
                kwargs={"service_id": service.id})
    )


def _gen_harvestable_ids(requested_ids, available_resources):
    available_resource_ids = [r.id for r in available_resources]
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
    print("Finished rescaning service. About to redirect back...")
    messages.add_message(
        request, messages.SUCCESS, _("Service rescanned successfully"))
    return redirect(
        reverse("harvest_resources", kwargs={"service_id": service_id}))


def service_detail(request, service_id):
    """This view shows the details of a service"""
    service = get_object_or_404(Service, pk=service_id)
    job_statuses = (
        enumerations.QUEUED,
        enumerations.IN_PROCESS,
        enumerations.FAILED,
    )
    resources_being_harvested = HarvestJob.objects.filter(
        service=service, status__in=job_statuses)
    already_imported_layers = Layer.objects.filter(remote_service=service)
    service_list = service.service_set.all()
    all_resources = (list(resources_being_harvested) +
                     list(already_imported_layers) + list(service_list))
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
        request.session.pop(service.base_url)
    except KeyError:
        pass

    return render(
        request,
        template_name="services/service_detail.html",
        context={
            "service": service,
            "layers": (r for r in resources if isinstance(r, Layer)),
            "services": (r for r in resources if isinstance(r, Service)),
            "resource_jobs": (
                r for r in resources if isinstance(r, HarvestJob)),
            "permissions_json": _perms_info_json(service),
            "resources": resources,
            "total_resources": len(all_resources),
        }
    )


@login_required
def edit_service(request, service_id):
    """
    Edit an existing Service
    """
    service_obj = get_object_or_404(Service, pk=service_id)

    if request.method == "POST":
        service_form = forms.ServiceForm(
            request.POST, instance=service_obj, prefix="service")
        if service_form.is_valid():
            service_obj = service_form.save(commit=False)
            service_obj.keywords.clear()
            service_obj.keywords.add(*service_form.cleaned_data['keywords'])
            service_obj.save()

            return HttpResponseRedirect(service_obj.get_absolute_url())
    else:
        service_form = forms.ServiceForm(
            instance=service_obj, prefix="service")

    return render(request,
                  "services/service_edit.html",
                  context={"service": service_obj, "service_form": service_form})


@login_required
def remove_service(request, service_id):
    """Delete a service and its constituent layers"""
    service = get_object_or_404(Service, pk=service_id)
    if not request.user.has_perm('maps.delete_service', obj=service):
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
            _("Service {} has been deleted".format(service.name))
        )
        return HttpResponseRedirect(reverse("services"))
