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
from functools import wraps

from django.conf import settings


def register_url_event(event_type=None):
    """
    Decorator on views, which will register url event

    usage:
    >> register_url_event()(TemplateView.view_as_view())

    """

    def _register_url_event(view):
        @wraps(view)
        def inner(*args, **kwargs):
            if settings.MONITORING_ENABLED:
                request = args[0]
                register_event(request, event_type or "view", request.path)
            return view(*args, **kwargs)

        return inner

    return _register_url_event


def register_event(request, event_type, resource):
    """
    Wrapper function to be used inside views to collect event and resource

    @param request Request object
    @param event_type name of event type
    @param resource string (then resource type will be url) or Resource instance

    >>> from geonode.base import register_event
    >>> def view(request):
            register_event(request, 'view', layer)
    """
    if not settings.MONITORING_ENABLED:
        return

    from geonode.base.models import ResourceBase

    if isinstance(resource, str):
        resource_type = "url"
        resource_name = request.path
        resource_id = None
    elif isinstance(resource, ResourceBase):
        resource_type = resource.__class__._meta.verbose_name_raw
        resource_name = getattr(resource, "alternate", None) or resource.title
        resource_id = resource.id
    else:
        raise ValueError(f"Invalid resource: {resource}")
    if request and hasattr(request, "register_event"):
        request.register_event(event_type, resource_type, resource_name, resource_id)


def register_proxy_event(request):
    """
    Process request to geoserver proxy. Extract layer and ows type
    """
