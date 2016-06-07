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
