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
from django.conf import settings
from kombu import pools
from kombu import BrokerConnection

connections = pools.Connections(limit=100)
producers = pools.Producers(limit=connections.limit)

# run in-memory if broker is not available
# see producer code for synchronous queue
url = getattr(settings, 'BROKER_URL', 'memory://')
task_serializer = getattr(settings, 'CELERY_TASK_SERIALIZER', 'pickle')
broker_transport_options = getattr(settings, 'BROKER_TRANSPORT_OPTIONS', {'socket_timeout': 10})
broker_socket_timeout = getattr(broker_transport_options, 'socket_timeout', 10)
connection = BrokerConnection(url, connect_timeout=broker_socket_timeout)
