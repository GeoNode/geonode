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
from geonode.documents.models import Document
from geonode.documents.tasks import create_document_thumbnail

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ("Update documents. For the moment only thumbnails can be updated")

    def add_arguments(self, parser):
        parser.add_argument(
            '--updatethumbnails',
            action='store_true',
            dest="updatethumbnails",
            default=False,
            help="Generate thumbnails for documents. Only documents without a thumbnail will be considered, unless --force is used.")

        parser.add_argument(
            '--force',
            action='store_true',
            dest="force",
            default=False,
            help="Force the update of thumbnails for all documents.")

    def handle(self, *args, **options):
        updatethumbnails = options.get('updatethumbnails')
        force = options.get('force')
        for doc in Document.objects.all():
            if updatethumbnails:
                if (doc.thumbnail_url is None or doc.thumbnail_url == '') or force:
                    try:
                        create_document_thumbnail(doc.id)
                    except Exception:
                        logger.error(f"[ERROR] Thumbnail for [{doc.name}] couldn't be created")
