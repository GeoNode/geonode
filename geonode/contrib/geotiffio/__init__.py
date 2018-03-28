from urllib import quote
from urllib import urlencode

from django.conf import settings


def create_geotiff_io_url(layer, access_token):

    # check if layer is a raster
    if layer.storeType == 'coverageStore':

        params = [
            ("service", "WCS"),
            ("format", "image/tiff"),
            ("request", "GetCoverage"),
            ("srs", "EPSG:4326"),
            ("version", "2.0.1"),
            ("coverageid", "geonode:" + layer.name)
        ]

        if access_token:
            params.append(("access_token", access_token))

        url_to_geotiff = settings.GEOSERVER_PUBLIC_LOCATION + "wcs?" + urlencode(params)

        return settings.GEOTIFF_IO_BASE_URL + "?url=" + quote(url_to_geotiff)
