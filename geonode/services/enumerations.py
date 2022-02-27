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

HARVESTER_TYPES = {
    'WMS': 'geonode.harvesting.harvesters.wms.OgcWmsHarvester',
    'GN_WMS': 'geonode.harvesting.harvesters.geonodeharvester.GeonodeUnifiedHarvesterWorker',
    'REST_MAP': 'geonode.harvesting.harvesters.arcgis.ArcgisHarvesterWorker',
    'REST_IMG': 'geonode.harvesting.harvesters.arcgis.ArcgisHarvesterWorker',
}

QUEUED = "QUEUED"
IN_PROCESS = "IN_PROCESS"
PROCESSED = "PROCESSED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"
