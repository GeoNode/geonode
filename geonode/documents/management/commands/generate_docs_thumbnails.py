#########################################################################
#
# Copyright (C) 2022 OSGeo
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

from django.core.management.base import BaseCommand
from django.db.models import Q
from geonode.documents.models import Document
from geonode.documents.tasks import create_document_thumbnail

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ("Create thumbnails for documents with an emtpy thumbnail.")

    def handle(self, *args, **options):
        docs_without_thumbnails = Document.objects.filter(Q(thumbnail_url__exact='') | Q(thumbnail_url__isnull=True))
        for doc in docs_without_thumbnails:
            try:
                create_document_thumbnail(doc.id)
            except Exception:
                logger.error(f"[ERROR] Thumbnail for [{doc.name}] couldn't be created")
