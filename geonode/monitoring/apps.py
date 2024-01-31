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
from django.apps import AppConfig

from django.conf import settings
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_noop as _

from geonode.notifications_helper import NotificationsAppConfigBase, has_notifications

log = logging.getLogger(__name__)


def run_setup_hooks(*args, **kwargs):
    from django.utils import timezone
    from geonode.monitoring.models import populate

    # Initialize periodic tasks
    if (
        "django_celery_beat" in settings.INSTALLED_APPS
        and getattr(settings, "CELERY_BEAT_SCHEDULER", None) == "django_celery_beat.schedulers:DatabaseScheduler"
    ):
        from django_celery_beat.models import (
            IntervalSchedule,
            PeriodicTask,
        )

        check_intervals = IntervalSchedule.objects.filter(every=300, period="seconds")
        if not check_intervals.exists():
            check_interval, _ = IntervalSchedule.objects.get_or_create(every=300, period="seconds")
        else:
            check_interval = check_intervals.first()

        PeriodicTask.objects.update_or_create(
            name="collect_metrics",
            defaults=dict(
                task="geonode.monitoring.tasks.collect_metrics",
                interval=check_interval,
                args="",
                start_time=timezone.now(),
            ),
        )

    # Initialize notifications
    if not has_notifications:
        log.warning("Monitoring requires notifications app to be enabled. " "Otherwise, no notifications will be send")
    populate()


class MonitoringAppConfig(NotificationsAppConfigBase, AppConfig):
    name = "geonode.monitoring"
    NOTIFICATION_NAME = "monitoring_alert"
    NOTIFICATIONS = (
        (
            NOTIFICATION_NAME,
            _("Monitoring alert"),
            _("Alert situation reported by monitoring"),
        ),
    )

    def ready(self):
        super().ready()
        if settings.MONITORING_ENABLED:
            post_migrate.connect(run_setup_hooks, sender=self)
            settings.CELERY_BEAT_SCHEDULE["collect_metrics"] = {
                "task": "geonode.monitoring.tasks.collect_metrics",
                "schedule": 300.0,
            }
