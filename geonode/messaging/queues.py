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
