import datetime
import logging
import os
import shutil

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.urls import reverse
from django_downloadview import DownloadResponse
from zipstream import ZipStream

from geonode.assets.handlers import asset_handler_registry, AssetHandlerInterface, AssetDownloadHandlerInterface
from geonode.assets.models import LocalAsset
from geonode.storage.manager import DefaultStorageManager, StorageManager
from geonode.utils import build_absolute_uri, mkdtemp

logger = logging.getLogger(__name__)

_asset_storage_manager = StorageManager(
    concrete_storage_manager=DefaultStorageManager(location=os.path.dirname(settings.ASSETS_ROOT))
)


class DefaultLocalLinkUrlHandler:
    def get_link_url(self, asset: LocalAsset):
        return build_absolute_uri(reverse("assets-link", args=(asset.pk,)))


class IndexLocalLinkUrlHandler:
    def get_link_url(self, asset: LocalAsset):
        asset = asset.get_real_instance()
        if not isinstance(asset, LocalAsset):
            raise TypeError("Only localasset are allowed")
        return build_absolute_uri(reverse("assets-link", args=(asset.pk,))) + f"/{os.path.basename(asset.location[0])}"


class LocalAssetHandler(AssetHandlerInterface):

    link_url_handlers = {"3dtiles": IndexLocalLinkUrlHandler()}

    @staticmethod
    def handled_asset_class():
        return LocalAsset

    def get_download_handler(self, asset=None):
        return LocalAssetDownloadHandler()

    def get_storage_manager(self, asset):
        return _asset_storage_manager

    def get_link_url_handler(self, asset):
        return self.link_url_handlers.get(asset.type, None) or DefaultLocalLinkUrlHandler()

    def _create_asset_dir(self):
        return os.path.normpath(
            mkdtemp(dir=settings.ASSETS_ROOT, prefix=datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        )

    def create(self, title, description, type, owner, files=None, clone_files=False, *args, **kwargs):
        if not files:
            raise ValueError("File(s) expected")

        if clone_files:
            files = self._copy_data(files)

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
        asset = self.__force_real_instance(asset)
        if self._are_files_managed(asset):
            logger.info(f"Removing files for asset {asset.pk}")
            base = self._get_managed_dir(asset)
            logger.info(f"Removing asset path {base} for asset {asset.pk}")
            shutil.rmtree(base)
        else:
            logger.info(f"Not removing unmanaged files for asset {asset.pk}")

    def replace_data(self, asset: LocalAsset, files: list):
        asset = self.__force_real_instance(asset)
        self.remove_data(asset)
        asset.location = files
        asset.save()

    def _copy_data(self, files):
        new_path = self._create_asset_dir()
        logger.info(f"Copying asset data from {files} into {new_path}")
        new_files = []
        for file in files:
            if os.path.isdir(file):
                dst = os.path.join(new_path, os.path.basename(file))
                logging.info(f"Copying into {dst} directory {file}")
                new_dir = shutil.copytree(file, dst)
                new_files.append(new_dir)
            elif os.path.isfile(file):
                logging.info(f"Copying into {new_path} file {os.path.basename(file)}")
                new_file = shutil.copy2(file, new_path)
                new_files.append(new_file)
            else:
                logger.warning(f"Not copying path {file}")

        return new_files

    def _clone_data(self, source_dir):
        new_path = self._create_asset_dir()
        logger.info(f"Cloning asset data from {source_dir} into {new_path}")

        if settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS is not None:
            # value is always set by default as None
            # https://docs.djangoproject.com/en/3.2/ref/settings/#file-upload-directory-permissions
            os.chmod(new_path, settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS)

        shutil.copytree(source_dir, new_path, dirs_exist_ok=True)

        return new_path

    def clone(self, source: LocalAsset) -> LocalAsset:
        # get a new asset instance to be edited and stored back
        source = self.__force_real_instance(source)
        asset = LocalAsset.objects.get(pk=source.pk)

        # only copy files if they are managed
        if self._are_files_managed(asset):
            base = self._get_managed_dir(asset)
            cloned = self._clone_data(base)
            asset.location = [os.path.normpath(file).replace(base, cloned) for file in asset.location]

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
        return self.get_link_url_handler(asset).get_link_url(asset)

    @classmethod
    def _is_file_managed(cls, file) -> bool:
        assets_root = os.path.join(os.path.normpath(settings.ASSETS_ROOT), "")
        return file.startswith(assets_root)

    @classmethod
    def _are_files_managed(cls, asset: LocalAsset) -> bool:
        """
        :param asset: asset pointing to the files to be checked
        :return: True if all files are managed, False is no file is managed
        :raise: ValueError if both managed and unmanaged files are in the list
        """
        managed = unmanaged = None
        for file in asset.location:
            if cls._is_file_managed(file):
                managed = True
            else:
                unmanaged = True
            if managed and unmanaged:
                logger.error(f"Both managed and unmanaged files are present on Asset {asset.pk}: {asset.location}")
                raise ValueError("Both managed and unmanaged files are present")

        return bool(managed)

    @classmethod
    def _get_managed_dir(cls, asset):
        if not asset.location:
            raise ValueError("Asset does not have any associated file")

        assets_root = os.path.normpath(settings.ASSETS_ROOT)
        base_common = None

        for file in asset.location:
            if not cls._is_file_managed(file):
                raise ValueError("Asset is unmanaged")

            norm_file = os.path.normpath(file)
            relative = norm_file.removeprefix(assets_root)
            base = os.path.split(relative)[0].lstrip("/")

            if base_common:
                if base_common != base:
                    raise ValueError(f"Mismatching base dir in asset files - Asset {asset.pk}")
            else:
                base_common = base

        managed_dir = os.path.join(assets_root, base_common)

        if not os.path.exists(managed_dir):
            raise ValueError(f"Common dir '{managed_dir}' does not exist - Asset {asset.pk}")

        if not os.path.isdir(managed_dir):
            raise ValueError(f"Common dir '{managed_dir}' does not seem to be a directory - Asset {asset.pk}")

        if assets_root == managed_dir:  # dunno if this can ever happen, but better safe than sorry
            raise ValueError(f"Common dir '{managed_dir}' matches the whole Assets dir - Asset {asset.pk}")

        return managed_dir

    @classmethod
    def __force_real_instance(cls, asset):
        asset = asset.get_real_instance()
        if not isinstance(asset, LocalAsset):
            raise TypeError(f"Real instance of asset {asset} is not {cls.handled_asset_class()}")
        return asset


class LocalAssetDownloadHandler(AssetDownloadHandlerInterface):

    def create_response(
        self, asset: LocalAsset, attachment: bool = False, basename: str = None, path: str = None
    ) -> HttpResponse:
        asset = asset.get_real_instance()
        if not isinstance(asset, LocalAsset):
            raise TypeError("Only localasset are allowed")
        if not asset.location:
            return HttpResponse("Asset does not contain any data", status=500)

        if len(asset.location) > 1:
            logger.warning("TODO: Asset contains more than one file. Download needs to be implemented")

        file0 = asset.location[0]
        if not path:  # use the file definition
            if not os.path.isfile(file0):
                logger.warning(f"Default file {file0} not found for asset {asset.id}")
                return HttpResponse(f"Default file not found for asset {asset.id}", status=400)
            localfile = file0

        else:  # a specific file is requested
            if "/../" in path:  # we may want to improve fraudolent request detection
                logger.warning(f"Tentative path traversal for asset {asset.id}")
                return HttpResponse(f"File not found for asset {asset.id}", status=400)

            if os.path.isfile(file0):
                dir0 = os.path.dirname(file0)
            elif os.path.isdir(file0):
                dir0 = file0
            else:
                return HttpResponse(f"Unexpected internal location '{file0}' for asset {asset.id}", status=500)

            localfile = os.path.join(dir0, path)
            logger.debug(f"Requested path {dir0} + {path}")

        if os.path.isfile(localfile):
            filename = os.path.basename(localfile)
            orig_base, ext = os.path.splitext(filename)
            outname = f"{basename or orig_base or 'file'}{ext}"
            match attachment:
                case True:
                    logger.info(f"Zipping file '{localfile}' with name '{orig_base}'")
                    zs = ZipStream(sized=True).from_path(LocalAssetHandler._get_managed_dir(asset), arcname="/")
                    # closing zip for all contents to be written
                    return StreamingHttpResponse(
                        zs,
                        content_type="application/zip",
                        headers={
                            "Content-Disposition": f"attachment; filename={orig_base}.zip",
                            "Content-Length": len(zs),
                            "Last-Modified": zs.last_modified,
                        },
                    )
                case False:
                    logger.info(f"Returning file '{localfile}' with name '{outname}'")
                    return DownloadResponse(
                        _asset_storage_manager.open(localfile).file, basename=f"{outname}", attachment=False
                    )
        else:
            logger.warning(f"Internal file {localfile} not found for asset {asset.id}")
            return HttpResponse(f"Internal file not found for asset {asset.id}", status=404 if path else 500)


asset_handler_registry.register(LocalAssetHandler)
