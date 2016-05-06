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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import signals

from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.documents.models import Document


ISO_XSL_NAME = 'ISO with XSL'

settings.DOWNLOAD_FORMATS_METADATA.append(ISO_XSL_NAME)


def xsl_post_save(instance, sender, **kwargs):
    """Add a link to the enriched ISO metadata
    """

    add_xsl_link(instance.resourcebase_ptr)


def add_xsl_link(resourcebase):
    """Add a link to the enriched ISO metadata
    """

    urlpath = reverse('prefix_xsl_line', args=[resourcebase.id])

    url = '{}{}'.format(settings.SITEURL, urlpath)

    link, created = Link.objects.get_or_create(
                        resource=resourcebase,
                        url=url,
                        defaults=dict(name=ISO_XSL_NAME,
                                      extension='xml',
                                      mime='text/xml',
                                      link_type='metadata'))
    return created


if 'geonode.catalogue' in settings.INSTALLED_APPS:
    signals.post_save.connect(xsl_post_save, sender=Layer)
    signals.post_save.connect(xsl_post_save, sender=Document)
    # TODO: maps as well?
