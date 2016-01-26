from django.db.models import signals

from geonode.base.models import ResourceBase
from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer

from geonode.qgis_server.signals import qgis_server_pre_save
from geonode.qgis_server.signals import qgis_server_pre_delete
from geonode.qgis_server.signals import qgis_server_post_save
from geonode.qgis_server.signals import qgis_server_pre_save_maplayer
from geonode.qgis_server.signals import qgis_server_post_save_map

signals.post_save.connect(qgis_server_post_save, sender=ResourceBase)
signals.pre_save.connect(qgis_server_pre_save, sender=Layer)
signals.pre_delete.connect(qgis_server_pre_delete, sender=Layer)
signals.post_save.connect(qgis_server_post_save, sender=Layer)
signals.pre_save.connect(qgis_server_pre_save_maplayer, sender=MapLayer)
signals.post_save.connect(qgis_server_post_save_map, sender=Map)
