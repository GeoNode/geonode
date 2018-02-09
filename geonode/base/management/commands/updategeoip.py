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
from __future__ import print_function
import os
import logging
import gzip
import urllib

from six import StringIO

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_noop as _

log = logging.getLogger(__name__)

URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'


class Command(BaseCommand):
    """
    Update GeoIP database
    """

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', dest='file', default=settings.GEOIP_PATH,
                            help=_("Write result to file, default GEOIP_PATH: {}".format(settings.GEOIP_PATH)))
        parser.add_argument('-u', '--url', dest='url', default=URL,
                            help=_("Fetch database from specific url. If nothing provided, default {} will be used"))
        parser.add_argument('-o', '--overwrite', dest='overwrite', action='store_true', default=False,
                            help=_("Overwrite file if exists"))

    def handle(self, *args, **options):
        fname = options['file']
        fbase = '.'.join(os.path.basename(options['url']).split('.')[:-1])
        if not options['overwrite'] and os.path.exists(fname):
            log.warning("File exists, won't overwrite %s", fname)
            return 
        log.info("Requesting %s", options['url'])
        r = urllib.urlopen(options['url'])
        data = StringIO(r.read())
        with gzip.GzipFile(fileobj=data) as zfile:
            log.info("Writing to %s", fname)
            with open(fname, 'wb') as tofile:
                tofile.write(zfile.read())
