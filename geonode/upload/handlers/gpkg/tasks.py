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
import logging

from celery import Task

from geonode.upload.handlers.utils import evaluate_error

logger = logging.getLogger("importer")


class SingleMessageErrorHandler(Task):
    max_retries = 1
    track_started = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        THis is separated because for gpkg we have a side effect
        (we rollback dynamic models and ogr2ogr)
        based on this failure step which is not meant for the other
        handlers
        """
        evaluate_error(self, exc, task_id, args, kwargs, einfo)
