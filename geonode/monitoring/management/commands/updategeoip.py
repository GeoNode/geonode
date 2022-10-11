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
import os
import logging
import gzip
import tarfile

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_noop as _

logger = logging.getLogger(__name__)

URL = 'https://build.geo-solutions.it/geonode/geoserver/latest/GeoLite2-City.tar.gz'
OLD_FORMAT = False


class Command(BaseCommand):
    """
    Update GeoIP database
    """

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', dest='file', default=settings.GEOIP_PATH,
                            help=_(f"Write result to file, default GEOIP_PATH: {settings.GEOIP_PATH}"))
        parser.add_argument('-u', '--url', dest='url', default=URL,
                            help=_("Fetch database from specific url. If nothing provided, default {} will be used"))
        parser.add_argument('-o', '--overwrite', dest='overwrite', action='store_true', default=False,
                            help=_("Overwrite file if exists"))

    def handle(self, *args, **options):
        # Exit early if MONITORING_ENABLED=False
        if not settings.MONITORING_ENABLED or not URL:
            return

        fname = options['file']
        if not options['overwrite'] and os.path.exists(fname):
            logger.warning("File exists, won't overwrite %s", fname)
            return

        from tqdm import tqdm
        import requests
        import math
        # Streaming, so we can iterate over the response.
        r = requests.get(options['url'], stream=True, timeout=10, verify=False)
        # Total size in bytes.
        total_size = int(r.headers.get('content-length', 0))
        logger.info("Requesting %s", options['url'])
        block_size = 1024
        wrote = 0
        with open('output.bin', 'wb') as f:
            for data in tqdm(r.iter_content(block_size), total=math.ceil(total_size // block_size), unit='KB', unit_scale=False):  # noqa
                wrote = wrote + len(data)
                f.write(data)
        logger.info(f" total_size [{total_size}] / wrote [{wrote}] ")
        if total_size != 0 and wrote != total_size:
            logger.info("ERROR, something went wrong")
        else:
            if OLD_FORMAT:
                self.handle_old_format(open('output.bin', 'rb'), fname)
            else:
                self.handle_new_format(open('output.bin', 'rb'), fname)
        try:
            # Cleaning up
            os.remove('output.bin')
        except OSError:
            pass

    def handle_new_format(self, f, fname):
        try:
            with tarfile.open(fileobj=f) as zfile:
                members = zfile.getmembers()
                for m in members:
                    if m.name.endswith('GeoLite2-City.mmdb'):
                        with open(fname, 'wb') as tofile:
                            try:
                                fromfile = zfile.extractfile(m)
                                logger.info("Writing to %s", fname)
                                tofile.write(fromfile.read())
                            except Exception as err:
                                logger.error("Cannot extract %s and write to %s: %s", m, fname, err, exc_info=err)
                                try:
                                    os.remove(fname)
                                except OSError:
                                    logger.debug("Could not delete file %s", fname)
                        return
        except Exception as err:
            logger.error("Cannot process %s: %s", f, err, exc_info=err)

    def handle_old_format(self, f, fname):
        try:
            with gzip.GzipFile(fileobj=f) as zfile:
                logger.info("Writing to %s", fname)
                with open(fname, 'wb') as tofile:
                    try:
                        tofile.write(zfile.read())
                    except Exception as err:
                        logger.error("Cannot extract %s and write to %s: %s", f, fname, err, exc_info=err)
                        try:
                            os.remove(fname)
                        except OSError:
                            logger.debug(f'Could not delete file {fname}')
        except Exception as err:
            logger.error("Cannot process %s: %s", f, err, exc_info=err)
