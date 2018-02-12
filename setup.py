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

import os
from distutils.core import setup

from setuptools import find_packages

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if on_rtd:
    shapely_dep = "Shapely<1.5.13"
else:
    shapely_dep = "Shapely>=1.5.13,<1.6.dev0"

setup(name='GeoNode',
      version=__import__('geonode').get_version(),
      description="Application for serving and sharing geospatial data",
      long_description=open('README').read(),
      classifiers=[
          "Development Status :: 4 - Beta"],
      keywords='',
      author='GeoNode Developers',
      author_email='dev@geonode.org',
      url='http://geonode.org',
      license='GPL',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
            # # The commented name next to the package
            # # is the Ubuntu 16.04 package that provides it
            # # with version in parenthesis

            # # Apps with official Ubuntu 16.04 packages

            # native dependencies
            "Pillow<=3.3.1",  # python-imaging (3.1.2) - python-pillow (3.3.1 in our ppa)
            "lxml<=3.6.2",  # python-lxml (3.6.2 in our ppa)
            "psycopg2<=2.7.3.1",  # python-psycopg2 (2.7.3.1 in our ppa)
            "Django<1.9a0",  # python-django (1.8.18 in our ppa)

            # Other
            "amqp<=2.2.2",  # (python-amqp 2.2.2 in our ppa)
            "anyjson<=0.3.3",  # (python-anyjson 0.3.3 in our ppa)
            "PyYAML<=3.12",  # (python-pyyaml 3.12 in out ppa)
            "beautifulsoup4<=4.4.1",  # python-bs4 (4.4.1)
            "billiard<=3.5.0.3",  # (python-billiard 3.5.0.3 in our ppa)
            "MultipartPostHandler<=0.1.0",  # python-multipartposthandler (0.1.0)
            "httplib2<=0.10.3",  # python-httplib2 (0.10.3 in our ppa)
            "transifex-client<=0.12.4",  # transifex-client (0.11.1)
            "Paver<=1.2.4",  # python-paver (1.2.4)
            "Unidecode<=0.4.19",  # python-unidecode (0.04.19)
            "django-nose<=1.4.5",  # python-django-nose (1.4.5 in out ppa)
            "nose<=1.3.7",  # python-nose (1.3.7)
            "awesome-slugify<=1.6.5",  # python-awesome-slugify (1.6.5)
            "django-floppyforms<=1.7.0",  # python-django-floppyforms (1.6.0 in our ppa)
            "chardet<=3.0.4",  # python-chardet (3.0.4 in our ppa)
            "decorator<=4.1.2",  # python-decorator (4.1.2 in our ppa)
            "celery>4.0a0c,<=4.1.0",  # python-celery (4.1.0)
            "certifi<=2017.7.27.1",  # depends on python-elasticsearch
            "autoflake<=0.7",
            "flake8<=2.5.4",  # python-flake8 (2.5.4)
            "pyflakes<=1.6.0",
            "pep8<=1.7.0",  # python-pep8 (1.7.0)
            "boto<=2.38.0",  # python-boto (2.38.0)
            "six<1.11.0",  # https://github.com/benjaminp/six/issues/210 (1.10.0 in ppa) TODO
            "diff-match-patch<=20121119",  # (20121119 in ppa) TODO

            # Django Apps
            "django-pagination>=1.0.5,<=1.0.7",  # python-django-pagination (1.0.7)
            "django-extensions>=1.2.5,<=1.6.1",  # python-django-extensions (1.5.9) TODO
            "django-jsonfield<=1.0.1",  # python-django-jsonfield (0.9.15, 1.0.1 in our ppa)
            "django-jsonfield-compat<=0.4.4",  # python-django-jsonfield-compat (0.4.4 in our ppa)
            "django-leaflet<=0.22.0",  # python-django-leaflet (0.19.0 in our ppa) TODO
            "django-taggit<=0.22.1",  # python-django-taggit (0.18.0)
            "django-mptt<=0.8.7",  # django-mptt (0.8.0, 0.8.6 in our ppa) FIXME
            "django-treebeard<=4.1.2",  # django-treebeard (4.0) FIXME
            "django-guardian<=1.4.9",  # django-guardian (1.4.1) FIXME
            "django-downloadview<=1.8",  # python-django-downloadview (1.8)
            "django-polymorphic<=1.3",  # python-django-polymorphic (1.3)
            "django-reversion<=2.0.10",  # python-django-reversion (1.10.0) FIXME
            "django-suit<=0.2.15",  # python-django-suit (0.2.15 in our ppa)
            "django-tastypie<=0.14.0",  # python-django-tastypie (0.12.0, 0.12.2, 0.13.3 in our ppa) FIXME
            "django-invitations==1.9.1",  # python-django-invitations (1.9.1 in our ppa)
            "django-oauth-toolkit>=0.10.0,<1.0",  # python-django-oauth-toolkit (0.12.0 in our ppa)
            "oauthlib<=2.0.2",  # python-oauthlib (2.0.2 in our ppa)

            # geopython dependencies
            "pyproj>=1.9.5,<=1.9.5.1",  # python-pyproj (1.9.5.1)
            "OWSLib>=0.10.3,<=0.15.0",  # python-owslib (0.15.0 in our ppa)
            "pycsw>=1.10.1,<=2.0.3",  # python-pycsw (1.10.1, 2.0.0, 2.0.3 in our ppa)
            "%s" % shapely_dep,  # python-shapely (1.5.13)

            # # Apps with packages provided in GeoNode's PPA on Launchpad.

            # Django Apps
            "dj-database-url<=0.4.2",  # , python-dj-database-url (0.4.1 in ppa)
            "Pinax<=0.9a2",  # python-pinax (0.9a2 in our ppa)
            # pinax-comments==0.1.1
            "pinax-notifications==4.1.0",  # (4.0.0 in ppa) FIXME
            "pinax-theme-bootstrap<=8.0.1",  # python-pinax-theme-bootstrap (8.0.1 in our ppa)
            "django-forms-bootstrap<=3.1.0",  # python-django-forms-bootstrap (3.1.0 in our ppa)
            "django-friendly-tag-loader<=1.2.1",  # python-django-friendly-tag-loader (1.2.1 in our ppa)
            "django-allauth<=0.34.0",  # TODO
            "django-activity-stream<=0.6.4",  # python-django-activity-stream (0.6.3 in ppa) FIXME
            "django-appconf<=1.0.2",  # (1.0.2 in ppa)
            "django-autocomplete-light>=2.3.3,<3.0a0",  # (2.3.3.1 in ppa)
            "django-autofixture<=0.12.1",  # python-django-autofixture (0.12.1 in our ppa)
            "django-autoslug<=1.9.3",  # python-django-autoslug (1.9.3 in our ppa)
            "django-braces<=1.12.0",  # pytnon-django-braces (1.12.0 in our ppa)
            "django-geonode-client<=1.0.0",  # python-django-geonode-client (1.0.0 in our ppa)
            "django-modeltranslation>=0.11,<=0.12.1",  # python-django-modeltranslation (0.12 Debian)
            "django-import-export<=0.5.1",  # missing from ppa FIXME
            "django-utils<=0.0.2",  # missing from ppa FIXME

            # GeoNode org maintained apps.
            "django-geoexplorer>=4.0.0,<5.0",  # python-django-geoexplorer (4.0.37 in our ppa) FIXME
            "geonode-user-messages<=0.1.12",  # python-geonode-user-messages (0.1.11 in our ppa) FIXME
            "geonode-avatar<=2.1.6",  # python-geonode-avatar (2.1.6 in our ppa)
            "geonode-announcements<=1.0.9",  # python-geonode-announcements (1.0.9 in our ppa)
            "geonode-agon-ratings<=0.3.5",  # python-geonode-agon-ratings (0.3.5 in our ppa)
            "geonode-arcrest>=10.0",  # python-geonode-arcrest (10.2 in our ppa)
            "geonode-dialogos>=0.5",  # python-geonode-dialogos (0.7 in our ppa)
            "gsconfig<2.0.0",  # python-gsconfig (1.0.8 in our ppa)
            "gn-gsimporter<2.0.0",  # python-gn-gsimporter (1.0.2 in our ppa)
            "gisdata>=0.5.4",  # python-gisdata (0.5.4 in our ppa)

            # haystack/elasticsearch, uncomment to use
            "django-haystack<=2.6.0",  # (2.4.1 in ppa) FIXME
            "elasticsearch<=2.4.0",  # (2.4.0 in ppa)
            "pyelasticsearch<=0.6.1",

            # datetimepicker widget
            "django-bootstrap3-datetimepicker<=2.2.3",  # (2.2.3 in ppa)

            # AWS S3 dependencies
            "django-storages<=1.6.5",  # python-django-storages (1.6.5 in our ppa)

            # DJango Caches
            "python-memcached<=1.59",  # missing from ppa FIXME

            # Contribs
            "et-xmlfile<=1.0.1",  # python-et-xmlfile (1.0.1 in our ppa)
            "unicodecsv<=0.14.1",  # python-unicodecsv (0.14.1 in our ppa)
            "urllib3<=1.22",
            "vine<=1.1.4",  # (1.1.4 in our ppa)
            "xlrd<=1.1.0",  # (0.9.4 in ppa) FIXME
            "xlwt<=1.3.0",  # (0.7.5 in ppa) FIXME
            "xmltodict<=0.9.2",  # (0.9.2 in ppa)
            "funcsigs<=1.0.2",  # (0.4 in ppa) FIXME
            "geolinks<=0.2.0",  # python-geolinks (0.2.0 in ppa)
            "idna<=2.6",  # (2.0 in ppa) FIXME
            "ipaddress<=1.0.18",  # (1.0.16 in ppa) FIXME
            "jdcal<=1.3",  # (1.0 in ppa) FIXME
            "kombu<=4.1.0",  # python-kombu (4.1.0 in our ppa)
            "mccabe<=0.4.0",  # (0.2.1 in ppa) FIXME
            "mock<=2.0.0",  # (1.3.0 in ppa) FIXME
            "numpy<=1.13.1",  # (1.11.0 in ppa) FIXME
            "odfpy<=1.3.5",  # python-odfpy (1.3.6 in our ppa)
            "openpyxl<=2.4.8",  # (2.3.0 in ppa) FIXME
            "pbr<=3.1.1",  # (1.8.0 in ppa) FIXME
            "python-dateutil<=2.6.1",  # (2.4.2 in ppa) FIXME
            "python-gnupg<=0.4.1",  # (0.3.8 in ppa) FIXME
            "python-mimeparse<=1.6.0",  # (0.1.4 in ppa) FIXME
            "pytz<=2017.2",  # python-pytz (2017.3 in our ppa)
            "regex<=2016.7.21",  # (0.1.20160110 in ppa)
            "requests<=2.18.4",
            "simplejson<=3.11.1",  # (3.8.1 in ppa) FIXME
            "tablib<=0.12.1",  # (0.9.11 in ppa) FIXME

            "psutil",  # (3.4.2 in ppa) FIXME
            "django-cors-headers",  # python-django-cors-headers (2.1.0 in our ppa)
            "django-multi-email-field",  # python-django-multi-email-field (0.5.1 in our ppa)
            # "WeasyPrint",
            "user-agents",  # python-user-agents (1.1.0 in our ppa)
            "xmljson",  # python-xmljson (0.1.9 in our ppa)

            # tests
            "coverage<=4.4.1",
            "factory-boy<=2.9.2",
            "Faker<=0.8.4",
            "pytest",
            "pytest-bdd<=2.5.0",  # latest requires six>=1.11.0
            "pytest-splinter",
      ],
      zip_safe=False
      )
