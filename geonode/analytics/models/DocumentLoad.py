from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.conf import settings

from geonode.documents.models import  Document

from CommonField import CommonField


class DocumentLoad(CommonField):
    document = models.ForeignKey(Document, related_name="document_load")

    def __str__(self):
        return self.document.title
