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

from distutils.core import setup
from setuptools import find_packages
import os

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
        "Pillow<=3.3.1",  # python-imaging (3.1.2)
        "lxml<=3.6.2",  # python-lxml (3.5.0)
        "psycopg2<=2.7.3.1",  # python-psycopg2 (2.6.1)
        "Django<1.9a0",  # python-django (1.8.7)

        # Other
        "amqp<=2.2.2",
        "anyjson<=0.3.3",
        "PyYAML<=3.12",
        "beautifulsoup4<=4.4.1",  # python-bs4 (4.4.1)
        "billiard<=3.5.0.3",
        "MultipartPostHandler<=0.1.0",  # python-multipartposthandler (0.1.0)
        "httplib2<=0.10.3",  # python-httplib2 (0.9.1, 0.9.2 in our ppa)
        "transifex-client<=0.12.4",  # transifex-client (0.11.1)
        "Paver<=1.2.4",  # python-paver (1.2.4)
        "Unidecode<=0.4.19",
        "django-nose<=1.4.5",  # python-django-nose (1.4.3)
        "nose<=1.3.7",  # python-nose (1.3.7)
        "awesome-slugify<=1.6.5",
        "django-floppyforms<=1.7.0",
        "certifi<=2017.7.27.1",
        "chardet<=3.0.4",
        "decorator<=4.1.2",
        "celery>4.0a0c,<=4.1.0",  # python-celery (3.1.20)
        # "django-celery==3.1.17",  # python-django-celery (3.1.17)
        "certifi<=2017.7.27.1",
        "autoflake<=0.7",
        "flake8<=2.5.4",  # python-flake8 (2.5.4)
        "pyflakes<=1.6.0",
        "pep8<=1.7.0",  # python-pep8 (1.7.0)
        "boto<=2.38.0",  # python-boto (2.38.0)
        "six<1.11.0",  # https://github.com/benjaminp/six/issues/210
        "diff-match-patch<=20121119",

        # Django Apps
        "django-pagination>=1.0.5,<=1.0.7",  # python-django-pagination (1.0.7)
        "django-extensions>=1.2.5,<=1.6.1",  # python-django-extensions (1.5.9)
        "django-jsonfield<=1.0.1",  # python-django-jsonfield (0.9.15, 1.0.1 in our ppa)
        "django-jsonfield-compat<=0.4.4",
        "django-leaflet<=0.22.0",
        "django-taggit<=0.22.1",  # python-django-taggit (0.18.0)
        "django-mptt<=0.8.7",  # django-mptt (0.8.0, 0.8.6 in our ppa)
        "django-treebeard<=4.1.2",  # django-treebeard (4.0)
        "django-guardian<=1.4.9",  # django-guardian (1.4.1)
        "django-downloadview<=1.8",  # python-django-downloadview (1.8)
        "django-polymorphic<=1.3",  # python-django-polymorphic (0.8.1) FIXME
        "django-reversion<=2.0.10",
        "django-suit<=0.2.15",
        "django-tastypie<=0.14.0",  # python-django-tastypie (0.12.0, 0.12.2 in our ppa)
        "django-oauth-toolkit>=0.10.0,<1.0",  # python-django-oauth-toolkit (0.10.0)
        "oauthlib<=2.0.2",

        # geopython dependencies
        "pyproj>=1.9.5,<=1.9.5.1",  # python-pyproj (1.9.5)
        "OWSLib>=0.10.3,<=0.15.0",  # python-owslib (0.10.3) FIXME
        "pycsw>=1.10.1,<=2.0.3",  # python-pycsw (1.10.1, 2.0.0 in ppa) FIXME
        "%s" % shapely_dep,  # python-shapely (1.5.13)


        # # Apps with packages provided in GeoNode's PPA on Launchpad.

        # Django Apps
        "awesome-slugify<=1.6.5",
        "dj-database-url<=0.4.2",
        "Pinax<=0.9a2",
        # pinax-comments==0.1.1
        "pinax-notifications<=4.0.0",
        # pinax-ratings==2.0.0
        "pinax-theme-bootstrap<=8.0.1",
        "django-bootstrap-form<=3.3",
        "django-forms-bootstrap<=3.1.0",
        "django-friendly-tag-loader<=1.2.1",
        "django-activity-stream<=0.6.4",
        "django-appconf<=1.0.2",
        "django-autocomplete-light>=2.3.3,<3.0a0",
        "django-autofixture<=0.12.1",
        "django-autoslug<=1.9.3",
        "django-braces<=1.11.0",
        "django-geonode-client<=0.0.15",
        "django-modeltranslation>=0.11,<=0.12.1",  # python-django-modeltranslation (0.11 Debian)
        "django-import-export<=0.5.1",
        "django-utils<=0.0.2",

        # GeoNode org maintained apps.
        "django-geoexplorer>=4.0.0,<5.0",
        "geonode-user-messages<=0.1.8",  # (0.1.3 in ppa) FIXME
        "geonode-avatar<=2.1.6",  # (2.1.5 in ppa) FIXME
        "geonode-announcements<=1.0.8",
        "geonode-agon-ratings<=0.3.5",  # (0.3.1 in ppa) FIXME

        # we can't use django-user-account until upstream merge changes for geonode.
        # this is temporary solution
        # "django-user-accounts==2.0.2dev",
        # django-user-accounts==2.0.2
        # we can't use django-user-account until upstream merge changes for geonode.
        # this is temporary solution
        # git+git://github.com/cezio/django-user-accounts@252_255_mixed#egg=django-user-accounts-2.0.2dev
        # updated to https://github.com/geosolutions-it/geonode-user-accounts.git
        "geonode-user-accounts>=1.0.13",

        "geonode-arcrest>=10.0",
        "geonode-dialogos>=0.5",
        "gsconfig<2.0.0",  # (1.0.3 in ppa) FIXME
        "gsimporter<=1.0.0",  # (0.1 in ppa) FIXME
        "gisdata>=0.5.4",

        # haystack/elasticsearch, uncomment to use
        "django-haystack<=2.6.0",  # missing from ppa FIXME
        "elasticsearch<=2.4.0",
        "pyelasticsearch<=0.6.1",

        # datetimepicker widget
        "django-bootstrap3-datetimepicker<=2.2.3",

        # AWS S3 dependencies
        "django-storages<=1.6.5",

        # Contribs
        "et-xmlfile<=1.0.1",
        "unicodecsv<=0.14.1",
        "urllib3<=1.22",
        "vine<=1.1.4",
        "xlrd<=1.1.0",
        "xlwt<=1.3.0",
        "xmltodict<=0.9.2",
        "funcsigs<=1.0.2",
        "geolinks<=0.2.0",
        "idna<=2.6",
        "ipaddress<=1.0.18",
        "jdcal<=1.3",
        "kombu<=4.1.0",
        "mccabe<=0.4.0",
        "mock<=2.0.0",
        "numpy<=1.13.1",
        "odfpy<=1.3.5",
        "openpyxl<=2.4.8",
        "pbr<=3.1.1",
        "python-dateutil<=2.6.1",
        "python-gnupg<=0.4.1",
        "python-mimeparse<=1.6.0",
        "pytz<=2017.2",
        "regex<=2016.7.21",
        "requests<=2.18.4",
        "simplejson<=3.11.1",
        "tablib<=0.12.1",

        # tests
        "coverage<=4.4.1",
        "factory-boy<=2.9.2",
        "Faker<=0.8.4",
        # "WeasyPrint",
        "user-agents",
        "xmljson",
        'psutil',
        'django-cors-headers',
        'django-multi-email-field',
      ],
      zip_safe=False
      )
