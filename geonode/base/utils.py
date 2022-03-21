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
import re
import json
import logging
from schema import Schema
from dateutil.parser import isoparse
from datetime import datetime, timedelta

# Django functionality
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# Geonode functionality
from guardian.shortcuts import get_objects_for_user

from geonode.layers.models import Dataset
from geonode.base.models import ResourceBase, Link, Configuration
from geonode.thumbs.utils import (
    get_thumbs,
    remove_thumb)
from geonode.utils import get_legend_url
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    BASIC_MANAGE_PERMISSIONS)

logger = logging.getLogger('geonode.base.utils')

_names = ['Zipped Shapefile', 'Zipped', 'Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
          'GeoJSON', 'Excel', 'Legend', 'GeoTIFF', 'GZIP', 'Original Dataset',
          'ESRI Shapefile', 'View in Google Earth', 'KML', 'KMZ', 'Atom', 'DIF',
          'Dublin Core', 'ebRIM', 'FGDC', 'ISO', 'ISO with XSL']

thumb_filename_regex = re.compile(
    r"^(document|map|layer|dataset|geoapp)-([a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12})-thumb-([a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12})\.png$")


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

    if isinstance(resource, Dataset):
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


class OwnerRightsRequestViewUtils:

    @staticmethod
    def get_message_recipients(owner):
        User = get_user_model()
        allowed_users = User.objects.none()
        if OwnerRightsRequestViewUtils.is_admin_moderate_mode():
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
    def is_group_private_mode():
        return settings.GROUP_PRIVATE_RESOURCES

    @staticmethod
    def is_manager_publish_mode():
        return settings.RESOURCE_PUBLISHING

    @staticmethod
    def is_admin_moderate_mode():
        return settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_auto_publishing_workflow():
        """
          **AUTO PUBLISHING**
            - `RESOURCE_PUBLISHING = False`
            - `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource:
              - OWNER gets all the owner permissions (publish resource included)
              - ANONYMOUS can view and download
            - No change to the Group Manager is applied
        """
        return not settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_simple_publishing_workflow():
        """
          **SIMPLE PUBLISHING**
            - `RESOURCE_PUBLISHING = True` (Autopublishing is disabled)
            - `ADMIN_MODERATE_UPLOADS = False`

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` EXCLUDED)
              - Group MEMBERS of the user's groups will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the *resource's group* will get the owner permissions (`publish_resource` EXCLUDED)
              - Group MEMBERS of the *resource's group* will get the `view_resourcebase`, `download_resourcebase` permission
        """
        return settings.RESOURCE_PUBLISHING and not settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_advanced_workflow():
        """
          **ADVANCED WORKFLOW**
            - `RESOURCE_PUBLISHING = True`
            - `ADMIN_MODERATE_UPLOADS = True`

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the user's groups will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can not view and download if the resource is not published

            - When resource has a group assigned:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` EXCLUDED)
              - Group MANAGERS of the resource's group will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the resource's group will get the `view_resourcebase`, `download_resourcebase` permission
        """
        return settings.RESOURCE_PUBLISHING and settings.ADMIN_MODERATE_UPLOADS

    @staticmethod
    def is_simplified_workflow():
        """
          **SIMPLIFIED WORKFLOW**
            - `RESOURCE_PUBLISHING = False`
            - `ADMIN_MODERATE_UPLOADS = True`

            - **NOTE**: Is it even possibile? when the resource is automatically published, can it be un-published?
            If this combination is not allowed, we should either stop the process when reading the settings or log a warning and force a safe combination.

            - When user creates a resource:
              - OWNER gets all the owner permissions (`publish_resource` and `change_resourcebase_permissions` INCLUDED)
              - Group MANAGERS of the user's groups will get the owner permissions (`publish_resource` INCLUDED)
              - Group MEMBERS of the user's group will get the `view_resourcebase`, `download_resourcebase` permission
              - ANONYMOUS can view and download
        """
        return not settings.RESOURCE_PUBLISHING and settings.ADMIN_MODERATE_UPLOADS


class ManageResourceOwnerPermissions:

    READ_ONLY_PERMS = VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS
    MANAGER_PERMS = VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS + BASIC_MANAGE_PERMISSIONS

    def __init__(self, user, group, role):
        self.user = user
        self.group = group
        self.role = role

    def set_owner_permissions_according_to_workflow(self):
        if not OwnerRightsRequestViewUtils.is_auto_publishing_workflow():
            if self.role and self.role == "manager":
                self._handle_perms(perms=self.MANAGER_PERMS)
            else:
                self._handle_perms(perms=self.READ_ONLY_PERMS)

    def _handle_perms(self, perms=None):
        '''
        Internally the set_permissions function will automatically handle the permissions
        that needs to be assigned to re resource.
        Background at: https://github.com/GeoNode/geonode/pull/8145
        If the user is demoted, we assign by default at least the view and the download permission
        to the resource
        '''
        queryset = (
            get_objects_for_user(
                self.user,
                ["base.view_resourcebase", "base.change_resourcebase"],
                any_perm=True)
            .filter(group=self.group.group)
            .exclude(owner=self.user)
        )
        # A.F.: By including 'self.group.resources()' here, we will look also for resources
        #       having permissions related to the current 'group' and not only the ones assigned
        #       to the 'group' through the metadata settings.
        # _resources = set([_r for _r in queryset.iterator()] + [_r for _r in self.group.resources()])
        _resources = queryset.iterator()
        for _r in _resources:
            perm_spec = _r.get_all_level_info()
            if perms:
                if "users" not in perm_spec:
                    perm_spec["users"] = {}
                perm_spec["users"][self.user] = perms
            # Let's the ResourceManager finally decide which are the correct security settings to apply
            _r.set_permissions(perm_spec)


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
