import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class IndexingConfig(AppConfig):

    name = "geonode.indexing"

    def ready(self):
        super(IndexingConfig, self).ready()
