from geonode.documents.models import Document
from geonode.resource.handler import BaseResourceHandler
import logging

logger = logging.getLogger()


class DocumentHandler(BaseResourceHandler):

    @staticmethod
    def can_handle(instance):
        return isinstance(instance, Document)

    def download_urls(self, **kwargs):
        """
        Specific method that return the download URL of the document
        """
        super().download_urls()
        return [
            {
                "url": self.instance.download_url,
                "ajax_safe": self.instance.download_is_ajax_safe,
            },
        ]
