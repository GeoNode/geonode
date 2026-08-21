#########################################################################
#
# Copyright (C) 2021 OSGeo
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
from django.conf import settings
from django.urls import include, re_path

from . import config


class HarvestingAppConfig(AppConfig):
    name = "geonode.harvesting"

    def ready(self):
        from geonode.urls import urlpatterns
        from . import signals  # noqa

        urlpatterns += [re_path(r"^api/v2/", include("geonode.harvesting.api.urls"))]
        settings.CELERY_BEAT_SCHEDULE["harvesting-scheduler"] = {
            "task": "geonode.harvesting.tasks.harvesting_scheduler",
            # ponytail: celery's bare-number `schedule` is SECONDS, so this needs
            # a minutes->seconds conversion (*60), not *0.5. With the 0.5-minute
            # default that bug ran this task every 0.25s (4x/second, 24/7)
            # instead of the intended every 30s — confirmed via live Postgres
            # statement logging (SELECT * FROM harvesting_harvester every ~250ms
            # even with zero harvesters configured).
            "schedule": config.get_setting("HARVESTER_SCHEDULER_FREQUENCY_MINUTES") * 60,
        }
