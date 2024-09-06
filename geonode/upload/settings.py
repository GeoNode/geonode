import os

"""
main settings to handle the celery rate
"""
IMPORTER_GLOBAL_RATE_LIMIT = os.getenv("IMPORTER_GLOBAL_RATE_LIMIT", 5)
IMPORTER_PUBLISHING_RATE_LIMIT = os.getenv("IMPORTER_PUBLISHING_RATE_LIMIT", 5)
IMPORTER_RESOURCE_CREATION_RATE_LIMIT = os.getenv("IMPORTER_RESOURCE_CREATION_RATE_LIMIT", 10)
IMPORTER_RESOURCE_COPY_RATE_LIMIT = os.getenv("IMPORTER_RESOURCE_COPY_RATE_LIMIT", 10)

SYSTEM_HANDLERS = [
    "geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
    "geonode.upload.handlers.geojson.handler.GeoJsonFileHandler",
    "geonode.upload.handlers.shapefile.handler.ShapeFileHandler",
    "geonode.upload.handlers.kml.handler.KMLFileHandler",
    "geonode.upload.handlers.csv.handler.CSVFileHandler",
    "geonode.upload.handlers.geotiff.handler.GeoTiffFileHandler",
    "geonode.upload.handlers.xml.handler.XMLFileHandler",
    "geonode.upload.handlers.sld.handler.SLDFileHandler",
    "geonode.upload.handlers.tiles3d.handler.Tiles3DFileHandler",
    "geonode.upload.handlers.remote.tiles3d.RemoteTiles3DResourceHandler",
    "geonode.upload.handlers.remote.wms.RemoteWMSResourceHandler",
]
