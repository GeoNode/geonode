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
import tarfile
import urllib2 as urllib
import traceback

from six import StringIO

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_noop as _

logger = logging.getLogger(__name__)

try:
    from django.contrib.gis.geoip2 import GeoIP2 as GeoIP
    URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz'
    OLD_FORMAT = False
except ImportError:
    from django.contrib.gis.geoip import GeoIP
    URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'
    OLD_FORMAT = True


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
            logger.warning("File exists, won't overwrite %s", fname)
            return
        logger.info("Requesting %s", options['url'])

        r = urllib.urlopen(options['url'], timeout=10.0)

        if OLD_FORMAT:
            self.handle_old_format(r, fname)
        else:
            self.handle_new_format(r, fname)


    def handle_new_format(self, r, fname):
        try:
            data = StringIO(r.read())
            with tarfile.open(fileobj=data) as zfile:
                members = zfile.getmembers()
                for m in members:
                    if m.name.endswith('GeoLite2-City.mmdb'):
                        with open(fname, 'wb') as tofile:
                            try:
                                fromfile = zfile.extractfile(m)
                                logger.info("Writing to %s", fname)
                                tofile.write(fromfile.read())
                            except Exception, err:
                                logger.error("Cannot extract %s and write to %s: %s", m, fname, err, exc_info=err) 
                                try:
                                    os.remove(fname)
                                except OSError:
                                    logger.debug("Could not delete file %s", fname)
                        return
        except Exception, err:
            logger.error("Cannot process %s: %s", r, err, exc_info=err)


    def handle_old_format(self, r, fname):
        try:
            data = StringIO(r.read())
            with gzip.GzipFile(fileobj=data) as zfile:
                logger.info("Writing to %s", fname)
                try:
                    os.remove(fname)
                except OSError:
                    logger.debug('Could not delete file %s' % fname)
                with open(fname, 'wb') as tofile:
                    try:
                        tofile.write(zfile.read())
                    except:
                        tb = traceback.format_exc()
                        logger.error(tb)

                        try:
                            os.remove(fname)
                        except OSError:
                            logger.debug('Could not delete file %s' % fname)
        except:
            tb = traceback.format_exc()
            logger.error(tb)
