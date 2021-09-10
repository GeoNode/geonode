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

import traceback
import logging

from lxml import etree
from owslib.etree import etree as dlxml

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied
from django.views.decorators.clickjacking import xframe_options_exempt

from geonode.utils import resolve_object
from geonode.catalogue import get_catalogue
from geonode.base.models import ResourceBase

logger = logging.getLogger(__name__)


@xframe_options_exempt
def prefix_xsl_line(req, id):
    # if the layer is in the catalogue, try to get the distribution urls
    # that cannot be precalculated.
    resource = None
    try:
        resource = get_object_or_404(ResourceBase, pk=id)
        query = {
            'id': resource.get_real_instance().id
        }
        resource = resolve_object(
            req,
            resource.get_real_instance_class(),
            query,
            permission='base.view_resourcebase',
            permission_msg=_("You are not permitted to view this resource"))
        catalogue = get_catalogue()
        record = catalogue.get_record(resource.uuid)
        if record:
            logger.debug(record.xml)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        logger.debug(traceback.format_exc())
        msg = f'Could not connect to catalogue to save information for dataset "{str(resource)}"'
        return HttpResponse(msg, status=404)

    try:
        # generate an XML document (GeoNode's default is ISO)
        if resource.metadata_uploaded and resource.metadata_uploaded_preserve:
            md_doc = etree.tostring(dlxml.fromstring(resource.metadata_xml))
        else:
            md_doc = catalogue.catalogue.csw_gen_xml(resource, settings.CATALOG_METADATA_TEMPLATE)
        xml = md_doc
    except Exception:
        logger.debug(traceback.format_exc())
        return HttpResponse(
            "Resource Metadata not available!"
        )
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    xsl_static = getattr(settings, 'CATALOG_METADATA_XSL', '/static/metadataxsl/metadata.xsl')
    xsl_path = f'{site_url}{xsl_static}'
    xsl_line = f'<?xml-stylesheet type="text/xsl" href="{xsl_path}"?>'

    return HttpResponse(
        xsl_line + xml,
        content_type="text/xml"
    )
