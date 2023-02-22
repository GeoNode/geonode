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

"""celery tasks for geonode.layers."""
from geonode.celery_app import app
from celery.utils.log import get_task_logger

from geonode.layers.models import Dataset
from geonode.resource.manager import resource_manager

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    name="geonode.layers.tasks.delete_dataset",
    queue="cleanup",
    expires=30,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False,
)
def delete_dataset(self, dataset_id):
    """
    Deletes a layer.
    """
    try:
        layer = Dataset.objects.get(id=dataset_id)
    except Dataset.DoesNotExist:
        logger.warning(f"Layers {dataset_id} does not exist!")
        return
    logger.debug(f"Deleting Dataset {layer}")
    resource_manager.delete(uuid=layer.uuid, instance=layer)
