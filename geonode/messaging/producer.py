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

import logging
import traceback

from decorator import decorator
from kombu import BrokerConnection
from kombu.common import maybe_declare
from .queues import (
    queue_email_events,
    queue_geoserver_events,
    queue_notifications_events,
    queue_dataset_viewers
)

from . import (url,
               producers,
               connection,
               broker_socket_timeout,
               task_serializer)
from .consumer import Consumer

logger = logging.getLogger(__name__)

LOCAL_STARTED = False


@decorator
def sync_if_local_memory(func, *args, **kwargs):
    """
    Runs locally, synchronous if connection is memory://
    This will create in-memory transport if messaging is
    not configured.

    This allows to run synchronous queue in deployments
    which don't have external broker deployed
    """
    try:
        return func(*args, **kwargs)
    finally:
        connection = BrokerConnection(url, connect_timeout=broker_socket_timeout)
        if getattr(connection.connection, 'driver_name', None) == 'memory':
            # hack explained:
            # when using memory://, first run usually contains only message for
            # specific queue. Subsequent runs will deliver the same message
            # in topic queue and broadcast one, which is weird.
            # that's why for first run we stop after first message, and then after
            # two (so we catch topic and broadcast)
            # This may change in the future
            global LOCAL_STARTED
            max_messages = 1 if not LOCAL_STARTED else 2
            LOCAL_STARTED = True
            worker = Consumer(connection, max_messages)
            try:
                worker.run(timeout=broker_socket_timeout)
            except Exception:
                tb = traceback.format_exc()
                msg = f"Exception while publishing message: {tb}"
                logger.error(msg)
                raise Exception(msg)
        elif not getattr(connection.connection, 'driver_name', None):
            msg = f"Exception while getting connection to {url}"
            logger.error(msg)
            raise Exception(msg)


@sync_if_local_memory
def send_email_producer(dataset_uuid, user_id):
    with producers[connection].acquire(block=True, timeout=broker_socket_timeout) as producer:
        maybe_declare(queue_email_events, producer.channel)
        payload = {
            "dataset_uuid": dataset_uuid,
            "user_id": user_id
        }
        producer.publish(
            payload,
            exchange='geonode',
            serializer=task_serializer,
            routing_key='email',
            timeout=broker_socket_timeout
        )
        producer.release()


@sync_if_local_memory
def geoserver_upload_dataset(payload):
    with producers[connection].acquire(block=True, timeout=broker_socket_timeout) as producer:
        maybe_declare(queue_geoserver_events, producer.channel)
        producer.publish(
            payload,
            exchange='geonode',
            serializer=task_serializer,
            routing_key='geonode.geoserver',
            timeout=broker_socket_timeout
        )
        producer.release()


@sync_if_local_memory
def notifications_send(payload, created=None):
    with producers[connection].acquire(block=True, timeout=broker_socket_timeout) as producer:
        maybe_declare(queue_notifications_events, producer.channel)
        payload['created'] = created
        producer.publish(
            payload,
            exchange='geonode',
            serializer=task_serializer,
            routing_key='notifications',
            timeout=broker_socket_timeout
        )
        producer.release()


@sync_if_local_memory
def viewing_dataset(user, owner, dataset_id):
    with producers[connection].acquire(block=True, timeout=broker_socket_timeout) as producer:
        maybe_declare(queue_dataset_viewers, producer.channel)
        payload = {"viewer": user,
                   "owner_dataset": owner,
                   "dataset_id": dataset_id}
        producer.publish(
            payload,
            exchange='geonode',
            serializer=task_serializer,
            routing_key='geonode.viewer',
            timeout=broker_socket_timeout
        )
        producer.release()
