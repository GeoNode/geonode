# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings

from geonode.base.models import ResourceBase
from geonode.catalogue import get_catalogue


def prefix_xsl_line(req, id):
    resource = get_object_or_404(ResourceBase, pk=id)

    catalogue = get_catalogue()
    record = catalogue.get_record(resource.uuid)
    xml = record.xml

    xsl_path = '{}/static/metadataxsl/metadata.xsl'.format(settings.SITEURL)
    xsl_line = '<?xml-stylesheet type="text/xsl" href="{}"?>'.format(xsl_path)

    return HttpResponse(
        xsl_line + xml,
        content_type="text/xml"
    )
