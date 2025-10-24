import logging

from django.apps import AppConfig
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class IndexingConfig(AppConfig):

    name = "geonode.indexing"

    def ready(self):
        super(IndexingConfig, self).ready()
