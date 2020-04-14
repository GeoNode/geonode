# -*- coding: utf-8 -*-
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
import os
import logging
from dateutil.parser import isoparse
from datetime import datetime, timedelta

# Django functionality
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage as storage

# Geonode functionality
from guardian.shortcuts import get_perms, remove_perm, assign_perm

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, Link, Configuration
from geonode.geoserver.helpers import ogc_server_settings
from geonode.maps.models import Map
from geonode.services.models import Service

logger = logging.getLogger('geonode.base.utils')

_names = ['Zipped Shapefile', 'Zipped', 'Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
          'GeoJSON', 'Excel', 'Legend', 'GeoTIFF', 'GZIP', 'Original Dataset',
          'ESRI Shapefile', 'View in Google Earth', 'KML', 'KMZ', 'Atom', 'DIF',
          'Dublin Core', 'ebRIM', 'FGDC', 'ISO', 'ISO with XSL']


def delete_orphaned_thumbs():
    """
    Deletes orphaned thumbnails.
    """
    if isinstance(storage, FileSystemStorage):
        documents_path = os.path.join(settings.MEDIA_ROOT, 'thumbs')
    else:
        documents_path = os.path.join(settings.STATIC_ROOT, 'thumbs')
    if os.path.exists(documents_path):
        for filename in os.listdir(documents_path):
            fn = os.path.join(documents_path, filename)
            model = filename.split('-')[0]
            uuid = filename.replace(model, '').replace('-thumb.png', '')[1:]
            if ResourceBase.objects.filter(uuid=uuid).count() == 0:
                print('Removing orphan thumb %s' % fn)
                logger.debug('Removing orphan thumb %s' % fn)
                try:
                    os.remove(fn)
                except OSError:
                    print('Could not delete file %s' % fn)
                    logger.error('Could not delete file %s' % fn)


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
        legend_url_template = \
            ogc_server_settings.PUBLIC_LOCATION + \
            'ows?service=WMS&request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
            '{alternate}&STYLE={style_name}' + \
            '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'
        if layer.default_style and not layer.get_legend_url(style_name=layer.default_style.name):
            Link.objects.update_or_create(
                resource=layer.resourcebase_ptr,
                name='Legend',
                extension='png',
                url=legend_url_template.format(
                    alternate=layer.alternate,
                    style_name=layer.default_style.name),
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
    def get_message_recipients():
        User = get_user_model()
        allowed_users = User.objects.none()
        if OwnerRightsRequestViewUtils.is_admin_publish_mode():
            allowed_users |= User.objects.filter(is_superuser=True)
        return allowed_users

    @staticmethod
    def get_resource(resource_base):
        if resource_base.polymorphic_ctype.name == 'layer':
            return Layer.objects.get(pk=resource_base.pk)
        elif resource_base.polymorphic_ctype.name == 'document':
            return Document.objects.get(pk=resource_base.pk)
        elif resource_base.polymorphic_ctype.name == 'map':
            return Map.objects.get(pk=resource_base.pk)
        else:
            return Service.objects.get(pk=resource_base.pk)

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
            assign_perm(perm, self.resource.owner, self.resource.get_self_resource())

    def _restore_owner_permissions(self):

        for perm_list in self.resource.BASE_PERMISSIONS.values():
            for perm in perm_list:
                assign_perm(perm, self.resource.owner, self.resource.get_self_resource())

        for perm_list in self.resource.PERMISSIONS.values():
            for perm in perm_list:
                assign_perm(perm, self.resource.owner, self.resource)
