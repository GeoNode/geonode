#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from django.db.models import signals
from geonode.layers.models import Layer, Link
from geonode.catalogue import get_catalogue


logger = logging.getLogger(__name__)

def catalogue_pre_delete(instance, sender, **kwargs):
    """Removes the layer from the catalogue
    """
    catalogue = get_catalogue()
    catalogue.remove_record(instance.uuid)



def catalogue_post_save(instance, sender, **kwargs):
    """Get information from catalogue
    """
    try:
        catalogue = get_catalogue()
        catalogue.create_record(instance)
        record = catalogue.get_record(instance.uuid)
    except EnvironmentError, e:
        msg = ('Could not connect to catalogue'
               'to save information for layer "%s"' % (instance.name)
              )
        if e.reason.errno == errno.ECONNREFUSED:
            logger.warn(msg, e)
            return
        else:
            raise e

    # Create the different metadata links with the available formats
    for mime, name, metadata_url in record.links['metadata']:
        instance.link_set.get_or_create(url=metadata_url,
                         defaults=dict(
                           name=name,
                           extension='xml',
                           mime=mime,
                           link_type='metadata',
                          )
                         )



def catalogue_pre_save(instance, sender, **kwargs):
    """Send information to catalogue
    """
    record = None
    try:
        catalogue = get_catalogue()
        record = catalogue.get_record(instance.uuid)
    except EnvironmentError, e:
        msg = ('Could not connect to catalogue'
               'to save information for layer "%s"' % (instance.name)
              )
        if e.reason.errno == errno.ECONNREFUSED:
            logger.warn(msg, e)
        else:
            raise e

    if record is None:
        return

    # Fill in the url for the catalogue
    if hasattr(record.distribution, 'online'):
        onlineresources = [r for r in record.distribution.online if r.protocol == "WWW:LINK-1.0-http--link"]
        if len(onlineresources) == 1:
            res = onlineresources[0]
            instance.distribution_url = res.url
            instance.distribution_description = res.description

signals.pre_save.connect(catalogue_pre_save, sender=Layer)
signals.post_save.connect(catalogue_post_save, sender=Layer)
signals.pre_delete.connect(catalogue_pre_delete, sender=Layer)
