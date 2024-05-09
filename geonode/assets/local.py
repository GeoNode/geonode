import datetime
import logging
import os

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django_downloadview import DownloadResponse

from geonode.assets.handlers import asset_handler_registry, AssetHandlerInterface, AssetDownloadHandlerInterface
from geonode.assets.models import LocalAsset
from geonode.storage.manager import DefaultStorageManager, StorageManager
from geonode.utils import build_absolute_uri


logger = logging.getLogger(__name__)

_asset_storage_manager = StorageManager(
    concrete_storage_manager=DefaultStorageManager(location=os.path.dirname(settings.ASSETS_ROOT))
)


class LocalAssetHandler(AssetHandlerInterface):
    @staticmethod
    def handled_asset_class():
        return LocalAsset

    def get_download_handler(self, asset):
        return LocalAssetDownloadHandler()

    def get_storage_manager(self, asset):
        return _asset_storage_manager

    def create(self, title, description, type, owner, files=None, clone_files=False, *args, **kwargs):
        if not files:
            raise ValueError("File(s) expected")

        if clone_files:
            prefix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            files = _asset_storage_manager.copy_files_list(files, dir=settings.ASSETS_ROOT, dir_prefix=prefix)
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
        """
        Removes the files related to an Asset.
        Only files within the Assets directory are removed
        """
        removed_dir = set()
        for file in asset.location:
            is_managed = self._is_file_managed(file)
            if is_managed:
                logger.info(f"Removing asset file {file}")
                _asset_storage_manager.delete(file)
                removed_dir.add(os.path.dirname(file))
            else:
                logger.info(f"Not removing asset file outside asset directory {file}")

        # TODO: in case of subdirs, make sure that all the tree is removed in the proper order
        for dir in removed_dir:
            if not os.path.exists(dir):
                logger.warning(f"Trying to remove not existing asset directory {dir}")
                continue
            if not os.listdir(dir):
                logger.info(f"Removing empty asset directory {dir}")
                os.rmdir(dir)

    def replace_data(self, asset: LocalAsset, files: list):
        self.remove_data(asset)
        asset.location = files
        asset.save()

    def clone(self, source: LocalAsset) -> LocalAsset:
        # get a new asset instance to be edited and stored back
        asset = LocalAsset.objects.get(pk=source.pk)
        # only copy files if they are managed
        if self._are_files_managed(asset.location):
            asset.location = _asset_storage_manager.copy_files_list(
                asset.location, dir=settings.ASSETS_ROOT, dir_prefix=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            )
        # it's a polymorphic object, we need to null both IDs
        # https://django-polymorphic.readthedocs.io/en/stable/advanced.html#copying-polymorphic-objects
        asset.pk = None
        asset.id = None
        asset.save()
        asset.refresh_from_db()
        return asset

    def create_download_url(self, asset) -> str:
        return build_absolute_uri(reverse("assets-download", args=(asset.pk,)))

    def create_link_url(self, asset) -> str:
        return build_absolute_uri(reverse("assets-link", args=(asset.pk,)))

    def _is_file_managed(self, file) -> bool:
        assets_root = os.path.normpath(settings.ASSETS_ROOT)
        return file.startswith(assets_root)

    def _are_files_managed(self, files: list) -> bool:
        """
        :param files: files to be checked
        :return: True if all files are managed, False is no file is managed
        :raise: ValueError if both managed and unmanaged files are in the list
        """
        managed = unmanaged = None
        for file in files:
            if self._is_file_managed(file):
                managed = True
            else:
                unmanaged = True
            if managed and unmanaged:
                logger.error(f"Both managed and unmanaged files are present: {files}")
                raise ValueError("Both managed and unmanaged files are present")

        return bool(managed)


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

        if _asset_storage_manager.exists(file0):
            logger.info(f"Returning file {file0} with name {outname}")

            return DownloadResponse(
                _asset_storage_manager.open(file0).file,
                basename=f"{outname}",
                attachment=attachment,
            )
        else:
            logger.warning(f"Internal file {file0} not found for asset  {asset.id}")
            return HttpResponse(f"Internal file not found for asset {asset.id}", status=500)


asset_handler_registry.register(LocalAssetHandler)
