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
import errno
import logging

from django.conf import settings
from django.db.models import signals
from lxml import etree
from owslib.etree import etree as dlxml
from geonode.layers.models import Layer
from geonode.documents.models import Document
from geonode.catalogue import get_catalogue
from geonode.base.models import Link, ResourceBase


LOGGER = logging.getLogger(__name__)


def catalogue_pre_delete(instance, sender, **kwargs):
    """Removes the layer from the catalogue"""
    catalogue = get_catalogue()
    catalogue.remove_record(instance.uuid)


def catalogue_post_save(instance, sender, **kwargs):
    """Get information from catalogue"""
    _id = instance.resourcebase_ptr.id if hasattr(instance, 'resourcebase_ptr') else instance.id
    resources = ResourceBase.objects.filter(id=_id)

    # Update the Catalog
    try:
        catalogue = get_catalogue()
        catalogue.create_record(instance)
        record = catalogue.get_record(instance.uuid)
    except OSError as err:
        msg = f'Could not connect to catalogue to save information for layer "{instance.name}"'
        if err.errno == errno.ECONNREFUSED:
            LOGGER.warn(msg, err)
            return
        else:
            raise err

    if not record:
        msg = f'Metadata record for {instance.title} does not exist, check the catalogue signals.'
        LOGGER.warning(msg)
        return

    if not hasattr(record, 'links'):
        msg = f'Metadata record for {instance.title} should contain links.'
        raise Exception(msg)

    # Create the different metadata links with the available formats
    if resources.exists():
        for mime, name, metadata_url in record.links['metadata']:
            try:
                Link.objects.get_or_create(
                    resource=resources.get(),
                    url=metadata_url,
                    defaults=dict(
                        name=name,
                        extension='xml',
                        mime=mime,
                        link_type='metadata'
                    )
                )
            except Exception:
                _d = dict(name=name,
                          extension='xml',
                          mime=mime,
                          link_type='metadata')
                Link.objects.filter(
                    resource=resources.get(),
                    url=metadata_url,
                    extension='xml',
                    link_type='metadata').update(**_d)

    # generate an XML document (GeoNode's default is ISO)
    if instance.metadata_uploaded and instance.metadata_uploaded_preserve:
        md_doc = etree.tostring(dlxml.fromstring(instance.metadata_xml))
    else:
        md_doc = catalogue.catalogue.csw_gen_xml(instance, settings.CATALOG_METADATA_TEMPLATE)
    try:
        csw_anytext = catalogue.catalogue.csw_gen_anytext(md_doc)
    except Exception as e:
        LOGGER.exception(e)
        csw_anytext = ''

    resources.update(
        metadata_xml=md_doc,
        csw_wkt_geometry=instance.geographic_bounding_box,
        csw_anytext=csw_anytext)


if 'geonode.catalogue' in settings.INSTALLED_APPS:
    signals.post_save.connect(catalogue_post_save, sender=Layer)
    signals.pre_delete.connect(catalogue_pre_delete, sender=Layer)
    signals.post_save.connect(catalogue_post_save, sender=Document)
    signals.pre_delete.connect(catalogue_pre_delete, sender=Document)
