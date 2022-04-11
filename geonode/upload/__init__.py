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
from django.conf import settings
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class LayerNotReady(Exception):
    pass


def run_setup_hooks(sender, **kwargs):
    from django.utils import timezone

    # Initialize periodic tasks
    if 'django_celery_beat' in settings.INSTALLED_APPS and \
            getattr(settings, 'CELERY_BEAT_SCHEDULER', None) == 'django_celery_beat.schedulers:DatabaseScheduler':
        from django_celery_beat.models import (
            IntervalSchedule,
            PeriodicTask,
        )

        check_intervals = IntervalSchedule.objects.filter(every=600, period="seconds")
        if not check_intervals.exists():
            check_interval, _ = IntervalSchedule.objects.get_or_create(
                every=10,
                period="seconds"
            )
        else:
            check_interval = check_intervals.first()

        PeriodicTask.objects.update_or_create(
            name="finalize-incomplete-session-resources",
            defaults=dict(
                task="geonode.upload.tasks.finalize_incomplete_session_uploads",
                interval=check_interval,
                args='',
                start_time=timezone.now()
            )
        )


class UploadAppConfig(AppConfig):

    name = "geonode.upload"

    def ready(self):
        super().ready()
        post_migrate.connect(run_setup_hooks, sender=self)
        settings.CELERY_BEAT_SCHEDULE['finalize-incomplete-session-resources'] = {
            'task': 'geonode.upload.tasks.finalize_incomplete_session_uploads',
            'schedule': 10.0,
        }


default_app_config = "geonode.upload.UploadAppConfig"
