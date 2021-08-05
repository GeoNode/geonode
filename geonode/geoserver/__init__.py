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

import logging
from django.conf import settings
from django.utils.translation import ugettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase


logger = logging.getLogger(__name__)


def run_setup_hooks(*args, **kwargs):

    from django.db.models import signals

    from geonode.base.models import ResourceBase
    from geonode.layers.models import Layer
    from geonode.maps.models import Map, MapLayer

    from geonode.geoserver.signals import geoserver_pre_save
    from geonode.geoserver.signals import geoserver_pre_delete
    from geonode.geoserver.signals import geoserver_post_save
    from geonode.geoserver.signals import geoserver_post_save_map
    from geonode.geoserver.signals import geoserver_pre_save_maplayer

    signals.post_save.connect(geoserver_post_save, sender=ResourceBase)
    signals.pre_save.connect(geoserver_pre_save, sender=Layer)
    signals.pre_delete.connect(geoserver_pre_delete, sender=Layer)
    signals.post_save.connect(geoserver_post_save, sender=Layer)
    signals.pre_save.connect(geoserver_pre_save_maplayer, sender=MapLayer)
    signals.post_save.connect(geoserver_post_save_map, sender=Map)


def set_resource_links(*args, **kwargs):

    from geonode.utils import set_resource_default_links
    from geonode.catalogue.models import catalogue_post_save
    from geonode.layers.models import Layer

    if settings.UPDATE_RESOURCE_LINKS_AT_MIGRATE:
        _all_layers = Layer.objects.all()
        for index, layer in enumerate(_all_layers, start=1):
            _lyr_name = layer.name
            message = f"[{index} / {len(_all_layers)}] Updating Layer [{_lyr_name}] ..."
            logger.debug(message)
            try:
                set_resource_default_links(layer, layer)
                catalogue_post_save(instance=layer, sender=layer.__class__)
            except Exception:
                logger.exception(
                    f"[ERROR] Layer [{_lyr_name}] couldn't be updated"
                )


class GeoserverAppConfig(NotificationsAppConfigBase):
    name = 'geonode.geoserver'
    NOTIFICATIONS = (("layer_uploaded", _("Layer Uploaded"), _("A layer was uploaded"),),
                     ("layer_comment", _("Comment on Layer"), _("A layer was commented on"),),
                     ("layer_rated", _("Rating for Layer"), _("A rating was given to a layer"),),
                     )

    def ready(self):
        super().ready()
        run_setup_hooks()
        # Connect the post_migrate signal with the _set_resource_links
        # method to update links for each resource
        from django.db.models import signals
        signals.post_migrate.connect(set_resource_links, sender=self)


default_app_config = 'geonode.geoserver.GeoserverAppConfig'

BACKEND_PACKAGE = 'geonode.geoserver'
