# -*- coding: utf-8 -*-
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

from kombu import Exchange, Queue

geonode_exchange = Exchange("geonode", type="topic", durable=False)

queue_all_events = Queue("broadcast", geonode_exchange, routing_key="#")
queue_email_events = Queue("email.events", geonode_exchange, routing_key="email")
queue_geoserver = Queue("all.geoserver", geonode_exchange, routing_key="geoserver.#")
queue_geoserver_catalog = Queue("geoserver.catalog", geonode_exchange, routing_key="geoserver.catalog")
queue_geoserver_data = Queue("geoserver.data", geonode_exchange, routing_key="geoserver.catalog")
queue_geoserver_events = Queue("geoserver.events", geonode_exchange, routing_key="geonode.geoserver")
queue_notifications_events = Queue("notifications.events", geonode_exchange, routing_key="notifications")
queue_layer_viewers = Queue("geonode.layer.viewer", geonode_exchange, routing_key="geonode.viewer")
