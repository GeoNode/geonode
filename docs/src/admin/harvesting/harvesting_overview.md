# Harvesting resources from remote services

GeoNode is able to harvest resource metadata from multiple remote services.

Harvesting is the process by which a metadata catalogue, *i.e.* GeoNode, is able to connect to other remote catalogues and retrieve information about their resources. This process is usually performed periodically, in order to keep the local catalogue in sync with the remote.

When appropriately configured, GeoNode will contact the remote service, extract a list of relevant resources that can be harvested, and create local resources for each remote resource. It will also keep the resources synchronized with the remote service by periodically updating them.

Out of the box, GeoNode ships with support for harvesting from:

1. [Other remote GeoNode instances](harvester_workers.md#geonode-harvester-worker)
2. [OGC WMS servers](harvester_workers.md#wms-harvester-worker)
3. [ArcGIS REST services](harvester_workers.md#arcgis-rest-services-harvester-worker)

Adding support for [additional harvesting sources](harvester_workers.md#creating-new-harvesting-workers) is also possible.
