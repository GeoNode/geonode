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
from django.conf.urls import url, include

from . import config


class HarvestingAppConfig(AppConfig):

    name = "geonode.harvesting"

    def ready(self):
        from geonode.urls import urlpatterns

        urlpatterns += [
            url(r'^api/v2/', include('geonode.harvesting.api.urls'))
        ]
        settings.CELERY_BEAT_SCHEDULE['harvesting-scheduler'] = {
            "task": "geonode.harvesting.tasks.harvesting_scheduler",
            "schedule": config.get_setting("HARVESTER_SCHEDULER_FREQUENCY_MINUTES") * 60,
        }
