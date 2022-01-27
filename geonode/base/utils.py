#########################################################################
#
# Copyright (C) 2016 OSGeo
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

"""Utilities for managing GeoNode base models
"""

# Standard Modules
import json
import re
import logging
from urllib.parse import urljoin

from dateutil.parser import isoparse
from datetime import datetime, timedelta

# Django functionality
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
# Geonode functionality
from guardian.shortcuts import get_perms, remove_perm, assign_perm

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, Link, Configuration
from geonode.thumbs.utils import (
    get_thumbs,
    remove_thumb)
from geonode.utils import get_legend_url
from schema import Schema

logger = logging.getLogger('geonode.base.utils')

_names = ['Zipped Shapefile', 'Zipped', 'Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
          'GeoJSON', 'Excel', 'Legend', 'GeoTIFF', 'GZIP', 'Original Dataset',
          'ESRI Shapefile', 'View in Google Earth', 'KML', 'KMZ', 'Atom', 'DIF',
          'Dublin Core', 'ebRIM', 'FGDC', 'ISO', 'ISO with XSL']

thumb_filename_regex = re.compile(
    r"^(document|map|layer)-([a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12})-thumb-([a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12})\.png$")


def get_thumb_uuid(filename):
    """Fetches the UUID associated with the given thumbnail file"""
    result = thumb_filename_regex.search(filename)
    uuid = result.group(2) if result else None

    return uuid


def delete_orphaned_thumbs():
    """
    Deletes orphaned thumbnails.
    """
    deleted = []
    thumb_uuids = {get_thumb_uuid(filename): filename for filename in get_thumbs()}
    db_uuids = ResourceBase.objects.filter(uuid__in=thumb_uuids.keys()).values_list("uuid", flat=True)
    orphaned_uuids = set(thumb_uuids.keys()) - set(db_uuids)
    orphaned_thumbs = (thumb_uuids[uuid] for uuid in orphaned_uuids if uuid is not None)

    for filename in orphaned_thumbs:
        try:
            remove_thumb(filename)
            deleted.append(filename)
        except NotImplementedError as e:
            logger.error(f"Failed to delete orphaned thumbnail '{filename}': {e}")

    return deleted


def remove_duplicate_links(resource):
    """
    Makes a scan of Links related to the resource and removes the duplicates.
    It also regenerates the Legend link in case this is missing for some reason.
    """
    for _n in _names:
        _links = Link.objects.filter(resource__id=resource.id, name=_n)
        _cnt = _links.count()
        while _cnt > 1:
            _links.last().delete()
            _cnt -= 1

    if isinstance(resource, Layer):
        # fixup Legend links
        layer = resource
        if layer.default_style and not layer.get_legend_url(style_name=layer.default_style.name):
            Link.objects.update_or_create(
                resource=layer.resourcebase_ptr,
                name='Legend',
                extension='png',
                url=get_legend_url(layer, layer.default_style.name),
                mime='image/png',
                link_type='image')


def configuration_session_cache(session):
    CONFIG_CACHE_TIMEOUT_SEC = 60

    _config = session.get('config')
    _now = datetime.utcnow()
    _dt = isoparse(_config.get('expiration')) if _config else _now
    if _config is None or _dt < _now:
        config = Configuration.load()
        _dt = _now + timedelta(seconds=CONFIG_CACHE_TIMEOUT_SEC)
        cached_config = {
            'configuration': {},
            'expiration': _dt.isoformat()
        }

        for field_name in ['read_only', 'maintenance']:
            cached_config['configuration'][field_name] = getattr(config, field_name)

        session['config'] = cached_config


def build_absolute_uri(url):
    if url and 'http' not in url:
        url = urljoin(settings.SITEURL, url)
    return url


class OwnerRightsRequestViewUtils:

    @staticmethod
    def get_message_recipients(owner):
        User = get_user_model()
        allowed_users = User.objects.none()
        if OwnerRightsRequestViewUtils.is_admin_publish_mode():
            allowed_users |= User.objects.filter(is_superuser=True).exclude(pk=owner.pk)
            try:
                from geonode.groups.models import GroupProfile
                groups = owner.groups.all()
                obj_group_managers = []
                for group in groups:
                    try:
                        group_profile = GroupProfile.objects.get(slug=group.name)
                        managers = group_profile.get_managers()
                        for manager in managers:
                            if manager not in obj_group_managers and not manager.is_superuser:
                                obj_group_managers.append(manager)
                    except GroupProfile.DoesNotExist:
                        pass
                allowed_users |= User.objects.filter(id__in=[_u.id for _u in obj_group_managers])
            except Exception:
                pass

        return allowed_users

    @staticmethod
    def get_resource(resource_base):
        return resource_base.get_real_instance()

    @staticmethod
    def is_admin_publish_mode():
        return settings.ADMIN_MODERATE_UPLOADS


class ManageResourceOwnerPermissions:
    def __init__(self, resource):
        self.resource = resource

    def set_owner_permissions_according_to_workflow(self):
        if self.resource.is_approved and OwnerRightsRequestViewUtils.is_admin_publish_mode():
            self._disable_owner_write_permissions()
        else:
            self._restore_owner_permissions()

    def _disable_owner_write_permissions(self):

        for perm in get_perms(self.resource.owner, self.resource.get_self_resource()):
            remove_perm(perm, self.resource.owner, self.resource.get_self_resource())

        for perm in get_perms(self.resource.owner, self.resource):
            remove_perm(perm, self.resource.owner, self.resource)

        for perm in self.resource.BASE_PERMISSIONS.get('read') + self.resource.BASE_PERMISSIONS.get('download'):
            if not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS:
                assign_perm(perm, self.resource.owner, self.resource.get_self_resource())
            elif perm not in {'change_resourcebase_permissions', 'publish_resourcebase'}:
                assign_perm(perm, self.resource.owner, self.resource.get_self_resource())

    def _restore_owner_permissions(self):

        for perm_list in self.resource.BASE_PERMISSIONS.values():
            for perm in perm_list:
                if not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS:
                    assign_perm(perm, self.resource.owner, self.resource.get_self_resource())
                elif perm not in {'change_resourcebase_permissions', 'publish_resourcebase'}:
                    assign_perm(perm, self.resource.owner, self.resource.get_self_resource())

        for perm_list in self.resource.PERMISSIONS.values():
            for perm in perm_list:
                if not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS:
                    assign_perm(perm, self.resource.owner, self.resource)
                elif perm not in {'change_resourcebase_permissions', 'publish_resourcebase'}:
                    assign_perm(perm, self.resource.owner, self.resource)


def validate_extra_metadata(data, instance):
    if not data:
        return data

    # starting validation of extra metadata passed via JSON
    # if schema for metadata validation is not defined, an error is raised
    resource_type = (
        instance.polymorphic_ctype.model
        if instance.polymorphic_ctype
        else instance.class_name.lower()
    )
    extra_metadata_validation_schema = settings.EXTRA_METADATA_SCHEMA.get(resource_type, None)
    if not extra_metadata_validation_schema:
        raise ValidationError(
            f"EXTRA_METADATA_SCHEMA validation schema is not available for resource {resource_type}"
        )
    # starting json structure validation. The Field can contain multiple metadata
    try:
        if isinstance(data, str):
            data = json.loads(data)
    except Exception:
        raise ValidationError("The value provided for the Extra metadata field is not a valid JSON")

    # looping on all the single metadata provided. If it doen't match the schema an error is raised
    for _index, _metadata in enumerate(data):
        try:
            Schema(extra_metadata_validation_schema).validate(_metadata)
        except Exception as e:
            raise ValidationError(f"{e} at index {_index} for input json: {json.dumps(_metadata)}")
    # conerted because in this case, we can store a well formated json instead of the user input
    return data
