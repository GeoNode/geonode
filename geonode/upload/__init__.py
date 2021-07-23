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

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UploadException(Exception):

    '''A handled exception meant to be presented to the user'''

    @staticmethod
    def from_exc(msg, ex):
        args = [msg]
        args.extend(ex.args)
        return UploadException(*args)


class LayerNotReady(Exception):
    pass


def run_setup_hooks(sender, **kwargs):
    from django.utils import timezone
    from django_celery_beat.models import (
        IntervalSchedule,
        PeriodicTask,
    )

    check_intervals = IntervalSchedule.objects.filter(every=25, period="seconds")
    if not check_intervals.exists():
        check_interval, _ = IntervalSchedule.objects.get_or_create(
            every=25,
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
        super(UploadAppConfig, self).ready()
        post_migrate.connect(run_setup_hooks, sender=self)


default_app_config = "geonode.upload.UploadAppConfig"
