# -*- coding: utf-8 -*-
import httplib2
from urlparse import urlparse
from django.conf import settings
from owslib.wms import WebMapService
from owslib.csw import CatalogueServiceWeb

_wms = None
_csw = None
_user, _password = settings.GEOSERVER_CREDENTIALS

def get_wms():
    global _wms
    wms_url = settings.GEOSERVER_BASE_URL + "wms?request=GetCapabilities&version=1.1.0"
    netloc = urlparse(wms_url).netloc
    http = httplib2.Http()
    http.add_credentials(_user, _password)
    http.authorizations.append(
        httplib2.BasicAuthentication(
            (_user, _password),
                netloc,
                wms_url,
                {},
                None,
                None,
                http
            )
        )
    body = http.request(wms_url)[1]
    _wms = WebMapService(wms_url, xml=body)

def get_csw():
    global _csw
    csw_url = "%ssrv/en/csw" % settings.GEONETWORK_BASE_URL
    _csw = CatalogueServiceWeb(csw_url)
    return _csw

def bbox_to_wkt(x0, x1, y0, y1, srid="4326"):
    return 'SRID=%s;POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))' % (srid,
                            x0, y0, x0, y1, x1, y1, x1, y0, x0, y0)
