from __future__ import with_statement

from django.conf import settings
from kombu import BrokerConnection
from kombu.common import maybe_declare
from kombu.pools import producers
from queues import queue_email_events, queue_geoserver_events,\
                   queue_notifications_events, queue_layer_viewers


connection = BrokerConnection(settings.BROKER_URL)


def send_email_producer(layer_uuid, user_id):
    with producers[connection].acquire(block=True) as producer:
        maybe_declare(queue_email_events, producer.channel)
        payload = {
            "layer_uuid": layer_uuid,
            "user_id": user_id

        }
        producer.publish(
            payload,
            exchange='geonode',
            serializer='json',
            routing_key='email'
        )


def geoserver_upload_layer(payload):
    with producers[connection].acquire(block=True) as producer:
        maybe_declare(queue_geoserver_events, producer.channel)
        producer.publish(
            payload,
            exchange='geonode',
            serializer='json',
            routing_key='geonode.geoserver'
        )


def notifications_send(payload, created=None):
    with producers[connection].acquire(block=True) as producer:
        maybe_declare(queue_notifications_events, producer.channel)
        payload['created'] = created
        producer.publish(
            payload,
            exchange='geonode',
            serializer='json',
            routing_key='notifications'
        )


def viewing_layer(user, owner, layer_id):
    with producers[connection].acquire(block=True) as producer:
        maybe_declare(queue_layer_viewers, producer.channel)

        payload = {"viewer": user,
                   "owner_layer": owner,
                   "layer_id": layer_id}
        producer.publish(
            payload,
            exchange='geonode',
            serializer='json',
            routing_key='geonode.viewer'
        )
