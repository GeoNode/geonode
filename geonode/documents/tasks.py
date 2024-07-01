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
import os
import io

from PIL import Image
import fitz

from celery.utils.log import get_task_logger

from geonode.celery_app import app
from geonode.storage.manager import StorageManager
from geonode.assets.handlers import asset_handler_registry
from geonode.assets.utils import get_default_asset

from ..base.models import ResourceBase
from .models import Document

logger = get_task_logger(__name__)


class DocumentRenderer:
    FILETYPES = ["pdf"]
    # See https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.fit
    CROP_CENTERING = {"pdf": (0.0, 0.0)}

    def __init__(self) -> None:
        pass

    def supports(self, filename):
        return self._get_filetype(filename) in self.FILETYPES

    def render(self, filename):
        content = None
        if self.supports(filename):
            filetype = self._get_filetype(filename)
            render = getattr(self, f"render_{filetype}")
            content = render(filename)
        return content

    def render_pdf(self, filename):
        try:
            doc = fitz.open(filename)
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            return pix.pil_tobytes(format="PNG")
        except Exception as e:
            logger.warning(f"Cound not generate thumbnail for {filename}: {e}")
            return None

    def preferred_crop_centering(self, filename):
        return self.CROP_CENTERING.get(self._get_filetype(filename))

    def _get_filetype(self, filname):
        return os.path.splitext(filname)[1][1:]


doc_renderer = DocumentRenderer()


@app.task(
    bind=True,
    name="geonode.documents.tasks.create_document_thumbnail",
    queue="geonode",
    expires=30,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False,
)
def create_document_thumbnail(self, object_id):
    """
    Create thumbnail for a document.
    """
    logger.debug(f"Generating thumbnail for document #{object_id}.")

    default_storage_manager = StorageManager()

    try:
        document = Document.objects.get(id=object_id)
    except Document.DoesNotExist:
        logger.error(f"Document #{object_id} does not exist.")
        raise

    image_file = None
    thumbnail_content = None
    remove_tmp_file = False
    centering = (0.5, 0.5)

    doc_path = None

    # get asset of the resource
    asset = get_default_asset(document)
    if not asset and not document.doc_url:
        raise Exception("Document has neither an associated Asset nor a link, cannot generate thumbnail")

    if asset:
        handler = asset_handler_registry.get_handler(asset)
        asset_storage_manager = handler.get_storage_manager(asset)
        doc_path = asset_storage_manager.path(asset.location[0])
    elif document.doc_url:
        doc_path = document.doc_url
        remove_tmp_file = True
        asset_storage_manager = default_storage_manager

    if document.is_image:
        try:
            image_file = asset_storage_manager.open(doc_path)
        except Exception as e:
            logger.debug(f"Could not generate thumbnail from remote document {document.doc_url}: {e}")

        if image_file:
            try:
                image = Image.open(image_file)
                with io.BytesIO() as output:
                    image.save(output, format="PNG")
                    thumbnail_content = output.getvalue()
                    output.close()
            except Exception as e:
                logger.debug(f"Could not generate thumbnail: {e}")
            finally:
                if image_file is not None:
                    image_file.close()
                    if remove_tmp_file:
                        default_storage_manager.delete(doc_path)

    elif doc_renderer.supports(doc_path):
        # in case it's a remote document we want to retrieve it first
        if document.doc_url:
            doc_path = default_storage_manager.open(doc_path).name
            remove_tmp_file = True
        try:
            thumbnail_content = doc_renderer.render(doc_path)
            preferred_centering = doc_renderer.preferred_crop_centering(doc_path)
            if preferred_centering is not None:
                centering = preferred_centering
        except Exception as e:
            print(e)
        finally:
            if remove_tmp_file:
                default_storage_manager.delete(doc_path)
    if not thumbnail_content:
        logger.warning(f"Thumbnail for document #{object_id} empty.")
        ResourceBase.objects.filter(id=document.id).update(thumbnail_url=None)
    else:
        filename = f"document-{document.uuid}-thumb.jpg"
        document.save_thumbnail(filename, thumbnail_content, centering=centering)
        logger.debug(f"Thumbnail for document #{object_id} created.")


@app.task(
    bind=True,
    name="geonode.documents.tasks.delete_orphaned_document_files",
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
def delete_orphaned_document_files(self):
    from geonode.documents.utils import delete_orphaned_document_files

    delete_orphaned_document_files()


@app.task(
    bind=True,
    name="geonode.documents.tasks.delete_orphaned_thumbnails",
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
def delete_orphaned_thumbnails(self):
    from geonode.base.utils import delete_orphaned_thumbs

    delete_orphaned_thumbs()
