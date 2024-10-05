#########################################################################
#
# Copyright (C) 2024 OSGeo
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


class UploadAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geonode.upload"

    def ready(self):
        """Finalize setup"""
        run_setup_hooks()
        super(UploadAppConfig, self).ready()
        settings.CELERY_BEAT_SCHEDULE["clean-up-old-task-result"] = {
            "task": "geonode.upload.tasks.cleanup_celery_task_entries",
            "schedule": 86400.0,
        }


def run_setup_hooks(*args, **kwargs):
    """
    Run basic setup configuration for the importer app.
    Here we are overriding the upload API url
    """
    from geonode.urls import urlpatterns
    from django.urls import re_path, include

    url_already_injected = any(
        [
            "geonode.upload.urls" in x.urlconf_name.__name__
            for x in urlpatterns
            if hasattr(x, "urlconf_name") and not isinstance(x.urlconf_name, list)
        ]
    )

    if not url_already_injected:
        urlpatterns.insert(
            0,
            re_path(r"^api/v2/", include("geonode.upload.api.urls")),
        )
