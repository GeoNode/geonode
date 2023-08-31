#########################################################################
#
# Copyright (C) 2023 OSGeo
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

import re
import logging
import traceback

from geonode.base.models import Region
from django.contrib.gis.geos import GEOSGeometry

logger = logging.getLogger(__name__)


# A metadata storer that assigns regions to a resource on the base of spatial predicates
def spatial_predicate_region_assignor(instance, *args, **kwargs):
    def _get_poly_from_instance(instance):
        srid1, wkt1 = instance.geographic_bounding_box.split(";")
        srid1 = re.findall(r"\d+", srid1)
        poly1 = GEOSGeometry(wkt1, srid=int(srid1[0]))
        poly1.transform(4326)
        return poly1

    if not instance.regions or instance.regions.count() == 0:
        poly1 = _get_poly_from_instance(instance)

        queryset = Region.objects.all().order_by("name")
        global_regions = []
        regions_to_add = []
        for region in queryset:
            try:
                if region.is_assignable_to_geom(poly1):
                    regions_to_add.append(region)
                if region.level == 0 and region.parent is None:
                    global_regions.append(region)
            except Exception:
                tb = traceback.format_exc()
                if tb:
                    logger.debug(tb)
        if regions_to_add or global_regions:
            if regions_to_add:
                instance.regions.add(*regions_to_add)
            else:
                instance.regions.add(*global_regions)
    return instance
