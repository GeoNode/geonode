import logging
import os.path

from django.http import HttpResponse

from django.core.exceptions import PermissionDenied
from geonode.security.permissions import DOWNLOAD_PERMISSIONS
from geonode.assets.handlers import asset_handler_registry
from geonode.assets.models import Asset
from geonode.base.models import ResourceBase, Link
from geonode.security.utils import get_visible_resources


logger = logging.getLogger(__name__)


def get_perms_response(request, asset: Asset):
    user = request.user

    # quick check
    is_admin = user.is_superuser if user and user.is_authenticated else False
    if is_admin or user == asset.owner:
        logger.debug("Asset: access allowed by user")
        return None

    visibile_res = get_visible_resources(queryset=ResourceBase.objects.filter(link__asset=asset), user=request.user)

    logger.warning("TODO: implement permission check")
    if visibile_res.exists():
        if user.has_perm(DOWNLOAD_PERMISSIONS[0]):
            logger.debug("Asset: access allowed by Resource")
            return None
        raise PermissionDenied
    elif user and user.is_authenticated:
        return HttpResponse(status=403)
    else:
        return HttpResponse(status=401)


def get_default_asset(resource: ResourceBase, link_type=None) -> Asset or None:
    """
    Get the default asset for a ResourceBase.

    In this first implementation we select the first one --
    in the future there may be further flags to identify the preferred one
    """
    filters = {"link__resource": resource}
    if link_type:
        filters["link__link_type"] = link_type
    asset = Asset.objects.filter(**filters).first()
    return asset.get_real_instance() if asset else None


DEFAULT_TYPES = {"image": ["jpg", "jpeg", "gif", "png", "bmp", "svg"]}


def find_type(ext):
    return next((datatype for datatype, extensions in DEFAULT_TYPES.items() if ext.lower() in extensions), None)


def create_link(resource, asset, link_type=None, extension=None, name=None, mime=None, asset_handler=None, **kwargs):
    asset = asset.get_real_instance()
    asset_handler = asset_handler or asset_handler_registry.get_handler(asset)

    if not link_type or not extension or not name:
        fallback_name, fallback_ext = (
            os.path.splitext(os.path.basename(asset.location[0])) if len(asset.location) else (None, None)
        )
        if fallback_ext:
            fallback_ext = fallback_ext.lstrip(".")
        link_type = link_type or find_type(fallback_ext) if fallback_ext else None

    link = Link(
        resource=resource,
        asset=asset,
        url=asset_handler.create_link_url(asset),
        extension=extension or fallback_ext or "Unknown",
        link_type=link_type or "data",
        name=name or fallback_name or asset.title,
        mime=mime or "",
    )
    link.save()
    return link


def create_asset_and_link(
    resource,
    owner,
    files: list,
    handler=None,
    title=None,
    description=None,
    link_type=None,
    extension=None,
    asset_type=None,
    mime=None,
    clone_files: bool = True,
) -> tuple[Asset, Link]:

    asset_handler = handler or asset_handler_registry.get_default_handler()
    asset = link = None
    try:
        default_title, default_ext = os.path.splitext(next(f for f in files)) if len(files) else (None, None)
        if default_ext:
            default_ext = default_ext.lstrip(".")
        link_type = link_type or find_type(default_ext) if default_ext else None

        asset = asset_handler.create(
            title=title or default_title or "Unknown",
            description=description or asset_type or "Unknown",
            type=asset_type or "Unknown",
            owner=owner,
            files=files,
            clone_files=clone_files,
        )

        link = create_link(
            resource,
            asset,
            asset_handler=asset_handler,
            link_type=link_type,
            extension=extension,
            name=title,
            mime=mime,
        )

        return asset, link
    except Exception as e:
        logger.error(f"Error creating Asset for resource {resource}: {e}", exc_info=e)
        rollback_asset_and_link(asset, link)
        raise Exception(f"Error creating asset: {e}")


def create_asset_and_link_dict(resource, values: dict, clone_files=True):
    return create_asset_and_link(
        resource,
        values["owner"],
        values["files"],
        title=values.pop("data_title", None),
        description=values.pop("description", None),
        link_type=values.pop("link_type", None),
        extension=values.pop("extension", None),
        asset_type=values.pop("data_type", None),
        clone_files=clone_files,
    )


def copy_assets_and_links(resource, target=None) -> list:
    assets_and_links = []
    links_with_assets = Link.objects.filter(resource=resource, asset__isnull=False).prefetch_related("asset")

    for link in links_with_assets:
        link.asset = asset_handler_registry.get_handler(link.asset).clone(link.asset)
        link.pk = None
        link.resource = target
        link.save()
        assets_and_links.append((link.asset, link))
    return assets_and_links


def rollback_asset_and_link(asset, link):
    try:
        if link:
            link.delete()
        if asset:
            asset.delete()  # TODO: make sure we are only deleting from DB and not also the stored data
    except Exception as e:
        logger.error(f"Could not rollback asset[{asset}] and link[{link}]", exc_info=e)
