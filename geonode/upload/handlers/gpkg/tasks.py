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
