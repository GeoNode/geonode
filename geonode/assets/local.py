import datetime
import logging
import os

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django_downloadview import DownloadResponse

from geonode.assets.handlers import asset_handler_registry, AssetHandlerInterface, AssetDownloadHandlerInterface
from geonode.assets.models import LocalAsset
from geonode.storage.manager import storage_manager
from geonode.utils import build_absolute_uri


logger = logging.getLogger(__name__)


class LocalAssetHandler(AssetHandlerInterface):
    @staticmethod
    def handled_asset_class():
        return LocalAsset

    def get_download_handler(self, asset):
        return LocalAssetDownloadHandler()

    def get_storage_manager(self, asset):
        return storage_manager

    def create(self, title, description, type, owner, files=None, clone_files=False, *args, **kwargs):
        if not files:
            raise ValueError("File(s) expected")

        if clone_files:
            prefix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            files = storage_manager.copy_files_list(files, dir=settings.ASSETS_ROOT, dir_prefix=prefix)
            # TODO: please note the copy_files_list will make flat any directory structure

        asset = LocalAsset(
            title=title,
            description=description,
            type=type,
            owner=owner,
            created=datetime.datetime.now(),
            location=files,
        )
        asset.save()
        return asset

    def remove_data(self, asset: LocalAsset):
        removed_dir = set()
        for file in asset.location:
            if file.startswith(settings.ASSETS_ROOT):
                logger.info(f"Removing asset file {file}")
                storage_manager.delete(file)
                removed_dir.add(os.path.dirname(file))
            else:
                logger.info(f"Not removing asset file outside asset directory {file}")

        for dir in removed_dir:
            if not os.listdir(dir):
                logger.info(f"Removing empty asset directory {dir}")
                os.remove(dir)

    def replace_data(self, asset: LocalAsset, files: list):
        self.remove_data(asset)
        asset.location = files
        asset.save()

    def clone(self, asset: LocalAsset) -> LocalAsset:
        prefix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        asset.location = storage_manager.copy_files_list(asset.location, dir=settings.ASSETS_ROOT, dir_prefix=prefix)
        asset.pk = None
        asset.save()
        return asset

    def create_download_url(self, asset) -> str:
        return build_absolute_uri(reverse("assets-download", args=(asset.pk,)))

    def create_link_url(self, asset) -> str:
        return build_absolute_uri(reverse("assets-link", args=(asset.pk,)))


class LocalAssetDownloadHandler(AssetDownloadHandlerInterface):

    def create_response(self, asset: LocalAsset, attachment: bool = False, basename=None) -> HttpResponse:
        if not asset.location:
            return HttpResponse("Asset does not contain any data", status=500)

        if len(asset.location) > 1:
            logger.warning("TODO: Asset contains more than one file. Download needs to be implemented")

        file0 = asset.location[0]
        filename = os.path.basename(file0)
        orig_base, ext = os.path.splitext(filename)
        outname = f"{basename or orig_base}{ext}"

        if storage_manager.exists(file0):
            logger.info(f"Returning file {file0} with name {outname}")

            return DownloadResponse(
                storage_manager.open(file0).file,
                basename=f"{outname}",
                attachment=attachment,
            )
        else:
            logger.warning(f"Internal file {file0} not found for asset  {asset.id}")
            return HttpResponse(f"Internal file not found for asset {asset.id}", status=500)


asset_handler_registry.register(LocalAssetHandler)
