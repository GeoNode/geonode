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
from django.utils.translation import ugettext_noop as _
from django.conf import settings
from functools import wraps

from geonode.notifications_helper import NotificationsAppConfigBase, has_notifications
from django.db.models.signals import post_migrate

log = logging.getLogger(__name__)


def run_setup_hooks(*args, **kwargs):
    from django.conf import settings
    from django.utils import timezone
    from geonode.monitoring.models import populate

    # Initialize periodic tasks
    if 'django_celery_beat' in settings.INSTALLED_APPS and \
            getattr(settings, 'CELERY_BEAT_SCHEDULER', None) == 'django_celery_beat.schedulers:DatabaseScheduler':
        from django_celery_beat.models import (
            IntervalSchedule,
            PeriodicTask,
        )

        check_intervals = IntervalSchedule.objects.filter(every=300, period="seconds")
        if not check_intervals.exists():
            check_interval, _ = IntervalSchedule.objects.get_or_create(
                every=300,
                period="seconds"
            )
        else:
            check_interval = check_intervals.first()

        PeriodicTask.objects.update_or_create(
            name="collect_metrics",
            defaults=dict(
                task="geonode.monitoring.tasks.collect_metrics",
                interval=check_interval,
                args='',
                start_time=timezone.now()
            )
        )

    # Initialize notifications
    if not has_notifications:
        log.warning("Monitoring requires notifications app to be enabled. "
                    "Otherwise, no notifications will be send")
    populate()


class MonitoringAppConfig(NotificationsAppConfigBase):
    name = 'geonode.monitoring'
    NOTIFICATION_NAME = 'monitoring_alert'
    NOTIFICATIONS = ((NOTIFICATION_NAME,
                      _("Monitoring alert"),
                      _("Alert situation reported by monitoring"),
                      ),
                     )

    def ready(self):
        super().ready()
        post_migrate.connect(run_setup_hooks, sender=self)
        settings.CELERY_BEAT_SCHEDULE['collect_metrics'] = {
            'task': 'geonode.monitoring.tasks.collect_metrics',
            'schedule': 300.0,
        }


default_app_config = 'geonode.monitoring.MonitoringAppConfig'


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
                register_event(request, event_type or 'view', request.path)
            return view(*args, **kwargs)
        return inner
    return _register_url_event


def register_event(request, event_type, resource):
    """
    Wrapper function to be used inside views to collect event and resource

    @param request Request object
    @param event_type name of event type
    @param resource string (then resource type will be url) or Resource instance

    >>> from geonode.monitoring import register_event
    >>> def view(request):
            register_event(request, 'view', layer)
    """
    if not settings.MONITORING_ENABLED:
        return
    from geonode.base.models import ResourceBase
    if isinstance(resource, str):
        resource_type = 'url'
        resource_name = request.path
        resource_id = None
    elif isinstance(resource, ResourceBase):
        resource_type = resource.__class__._meta.verbose_name_raw
        resource_name = getattr(resource, 'alternate', None) or resource.title
        resource_id = resource.id
    else:
        raise ValueError(f"Invalid resource: {resource}")
    if request and hasattr(request, 'register_event'):
        request.register_event(event_type, resource_type, resource_name, resource_id)


def register_proxy_event(request):
    """
    Process request to geoserver proxy. Extract layer and ows type
    """
