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

from django.utils.translation import ugettext_lazy as _


AUTO = "AUTO"
OWS = "OWS"
WMS = "WMS"
WFS = "WFS"
TMS = "TMS"
CSW = "CSW"
REST_MAP = "REST_MAP"
REST_IMG = "REST_IMG"
OGP = "OGP"
HGL = "HGL"
GN_WMS = "GN_WMS"
GN_CSW = "GN_CSW"

LOCAL = "L"
CASCADED = "C"
HARVESTED = "H"
INDEXED = "I"
LIVE = "X"
OPENGEOPORTAL = "O"

SERVICE_TYPES = (
    (AUTO, _('Auto-detect')),
    (OWS, _('Paired WMS/WFS/WCS')),
    (WMS, _('Web Map Service')),
    (CSW, _('Catalogue Service')),
    (REST_MAP, _('ArcGIS REST MapServer')),
    (REST_IMG, _('ArcGIS REST ImageServer')),
    (OGP, _('OpenGeoPortal')),
    (HGL, _('Harvard Geospatial Library')),
    (GN_WMS, _('GeoNode (Web Map Service)')),
    (GN_CSW, _('GeoNode (Catalogue Service)')),
)

GXP_PTYPES = {
    'AUTO': 'gxp_wmscsource',
    'OWS': 'gxp_wmscsource',
    'WMS': 'gxp_wmscsource',
    'WFS': 'gxp_wmscsource',
    'WCS': 'gxp_wmscsource',
    'REST_MAP': 'gxp_arcrestsource',
    'REST_IMG': 'gxp_arcrestsource',
    'HGL': 'gxp_hglsource',
    'GN_WMS': 'gxp_geonodecataloguesource',
}

QUEUED = "QUEUED"
IN_PROCESS = "IN_PROCESS"
PROCESSED = "PROCESSED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"
