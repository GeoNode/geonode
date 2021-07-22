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
import time
import json
from datetime import datetime

# from django.conf import settings
from kombu.mixins import ConsumerMixin
from geonode.security.views import send_email_consumer
from geonode.layers.views import dataset_view_counter
from geonode.layers.models import Dataset
from geonode.geoserver.helpers import gs_slurp

from .queues import (
    queue_email_events,
    queue_geoserver_events,
    queue_notifications_events,
    queue_all_events,
    queue_geoserver_catalog,
    queue_geoserver_data,
    queue_geoserver,
    queue_dataset_viewers
)

logger = logging.getLogger(__package__)


class Consumer(ConsumerMixin):

    def __init__(self, connection, messages_limit=None):
        self.last_message = None
        self.connection = connection
        self.messages_limit = messages_limit

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(queue_all_events,
                     callbacks=[self.on_message]),
            Consumer(queue_email_events,
                     callbacks=[self.on_email_messages]),
            Consumer(queue_geoserver_events,
                     callbacks=[self.on_geoserver_messages]),
            Consumer(queue_notifications_events,
                     callbacks=[self.on_notifications_messages]),
            Consumer(queue_geoserver_catalog,
                     callbacks=[self.on_geoserver_catalog]),
            Consumer(queue_geoserver_data,
                     callbacks=[self.on_geoserver_data]),
            Consumer(queue_geoserver,
                     callbacks=[self.on_geoserver_all]),
            Consumer(queue_dataset_viewers,
                     callbacks=[self.on_dataset_viewer]),
        ]

    def _check_message_limit(self):
        if self.messages_limit is not None:
            self.messages_limit -= 1
            if self.messages_limit < 1:
                self.should_stop = True
            return True

    def on_consume_end(self, connection, channel):
        super().on_consume_end(connection, channel)
        logger.debug("finished.")

    def on_message(self, body, message):
        logger.debug(f"broadcast: RECEIVED MSG - body: {body}")
        message.ack()
        self._check_message_limit()

    def on_email_messages(self, body, message):
        logger.debug(f"on_email_messages: RECEIVED MSG - body: {body}")
        dataset_uuid = body.get("dataset_uuid")
        user_id = body.get("user_id")
        send_email_consumer(dataset_uuid, user_id)
        # Not sure if we need to send ack on this fanout version.
        message.ack()
        logger.debug("on_email_messages: finished")
        self._check_message_limit()

    def on_geoserver_messages(self, body, message):
        logger.debug(f"on_geoserver_messages: RECEIVED MSG - body: {body}")
        # dataset_id = body.get("id")
        # try:
        #     layer = _wait_for_dataset(dataset_id)
        # except Dataset.DoesNotExist as err:
        #     logger.debug(err)
        #     return

        # geoserver_post_save_local(layer)

        # Not sure if we need to send ack on this fanout version.
        message.ack()
        logger.debug("on_geoserver_messages: finished")
        self._check_message_limit()

    def on_notifications_messages(self, body, message):
        logger.debug(f"on_notifications_message: RECEIVED MSG - body: {body}")
        body.get("id")
        body.get("app_label")
        body.get("model")
        body.get("created")
        # notification_post_save_resource2(instance_id, app_label, model, created)
        message.ack()
        logger.debug("on_notifications_message: finished")
        self._check_message_limit()

    def on_geoserver_all(self, body, message):
        logger.debug(f"on_geoserver_all: RECEIVED MSG - body: {body}")
        message.ack()
        logger.debug("on_geoserver_all: finished")
        # TODO:Adding consurmer's producers.
        self._check_message_limit()

    def on_geoserver_catalog(self, body, message):
        logger.debug(f"on_geoserver_catalog: RECEIVED MSG - body: {body}")
        try:
            _update_dataset_data(body, self.last_message)
            self.last_message = json.loads(body)
        except Exception:
            logger.debug(f"Could not encode message {body}")
        message.ack()
        logger.debug("on_geoserver_catalog: finished")
        self._check_message_limit()

    def on_geoserver_data(self, body, message):
        logger.debug(f"on_geoserver_data: RECEIVED MSG - body: {body}")
        try:
            _update_dataset_data(body, self.last_message)
            self.last_message = json.loads(body)
        except Exception:
            logger.debug(f"Could not encode message {body}")
        message.ack()
        logger.debug("on_geoserver_data: finished")
        self._check_message_limit()

    def on_consume_ready(self, connection, channel, consumers, **kwargs):
        logger.debug(">>> Ready:")
        logger.debug(connection)
        logger.debug(f"{len(consumers)} consumers:")
        for i, consumer in enumerate(consumers, start=1):
            logger.debug(f"{i} {consumer}")
        super().on_consume_ready(
            connection, channel, consumers, **kwargs)

    def on_dataset_viewer(self, body, message):
        logger.debug(f"on_dataset_viewer: RECEIVED MSG - body: {body}")
        viewer = body.get("viewer")
        # owner_dataset = body.get("owner_dataset")
        dataset_id = body.get("dataset_id")
        dataset_view_counter(dataset_id, viewer)

        # TODO Disabled for now. This should be handeld through Notifications
        # if settings.EMAIL_ENABLE:
        #     send_email_owner_on_view(owner_dataset, viewer, dataset_id)
        message.ack()
        logger.debug("on_dataset_viewer: finished")
        self._check_message_limit()


def _update_dataset_data(body, last_message):
    message = json.loads(body)
    workspace = message["source"]["workspace"] if "workspace" in message["source"] else None
    store = message["source"]["store"] if "store" in message["source"] else None
    filter = message["source"]["name"]

    update_dataset = False
    if not last_message:
        last_message = message
        update_dataset = True
    last_workspace = message["source"]["workspace"] if "workspace" in message["source"] else None
    last_store = message["source"]["store"] if "store" in message["source"] else None
    last_filter = last_message["source"]["name"]
    if (last_workspace, last_store, last_filter) != (workspace, store, filter):
        update_dataset = True
    else:
        timestamp_t1 = datetime.strptime(last_message["timestamp"], '%Y-%m-%dT%H:%MZ')
        timestamp_t2 = datetime.strptime(message["timestamp"], '%Y-%m-%dT%H:%MZ')
        timestamp_delta = timestamp_t2 - timestamp_t1
        if timestamp_t2 > timestamp_t1 and timestamp_delta.seconds > 60:
            update_dataset = True

    if update_dataset:
        gs_slurp(True, workspace=workspace, store=store, filter=filter, remove_deleted=True, execute_signals=True)


def _wait_for_dataset(dataset_id, num_attempts=5, wait_seconds=1):
    """Blocks execution while the Dataset instance is not found on the database

    This is a workaround for the fact that the
    ``geonode.geoserver.signals.geoserver_post_save_local`` function might
    try to access the layer's ``id`` parameter before the layer is done being
    saved in the database.

    """

    for current in range(1, num_attempts + 1):
        try:
            instance = Dataset.objects.get(id=dataset_id)
            logger.debug(
                f"Attempt {current}/{num_attempts} - Found layer in the "
                "database")
            break
        except Dataset.DoesNotExist:
            time.sleep(wait_seconds)
            logger.debug(
                f"Attempt {current}/{num_attempts} - Could not find layer "
                "instance")
    else:
        logger.debug(
            f"Reached maximum attempts and layer {dataset_id} is still not "
            "saved. Exiting...")
        raise Dataset.DoesNotExist
    return instance
