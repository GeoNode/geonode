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
    shapely_dep = "Shapely>=1.5.13"

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
        "pillow>=3.1.1",  # python-imaging (3.1.2)
        "lxml>=3.4.4",  # python-lxml (3.5.0)
        "psycopg2>=2.4.5",  # python-psycopg2 (2.6.1)
        "Django >=1.8.7, < 1.9a0",  # python-django (1.8.7)

        # Other
        "pyyaml>=3.11",
        "beautifulsoup4>=4.2.1",  # python-bs4 (4.4.1)
        "MultipartPostHandler>=0.1.0",  # python-multipartposthandler (0.1.0)
        "httplib2>=0.9.2",  # python-httplib2 (0.9.1, 0.9.2 in our ppa)
        "transifex-client>=0.10",  # transifex-client (0.11.1)
        "Paver>=1.2.1",  # python-paver (1.2.1)
        "nose>=1.3.1",  # python-nose (1.3.7)
        "django-nose>=1.4",  # python-django-nose (1.4.3)
        "celery>=3.1.18,<4.0a0",  # python-celery (3.1.20)
        "django-celery>=3.1.16",  # python-django-celery (3.1.17)
        "flake8>=2.3.0",  # python-flake8 (2.5.4)
        "pep8>=1.6.2",  # python-pep8 (1.7.0)
        "boto>=2.38.0",  # python-boto (2.38.0)

        # Django Apps
        "django-pagination >=1.0.5, <=1.0.7",  # python-django-pagination (1.0.7)
        "django-extensions>=1.2.5",  # python-django-extensions (1.5.9)
        "django-jsonfield>=0.9.16",  # python-django-jsonfield (0.9.15, 1.0.1 in our ppa)
        "django-taggit>=0.21.0",  # python-django-taggit (0.18.0)
        "django-mptt>=0.8.6",  # django-mptt (0.8.0, 0.8.6 in our ppa)
        "django-treebeard>=3.0",  # django-treebeard (4.0)
        "django-guardian>=1.4.1",  # django-guardian (1.4.1)
        "django-downloadview>=1.2",  # python-django-downloadview (1.8)
        "django-polymorphic>=0.9.2",  # python-django-polymorphic (0.8.1) FIXME
        "django-tastypie>=0.12.2, <=0.13.1",  # python-django-tastypie (0.12.0, 0.12.2 in our ppa)
        "django-oauth-toolkit>=0.10.0, <1.0",  # python-django-oauth-toolkit (0.10.0)
        "oauthlib==2.0.1",

        # geopython dependencies
        "pyproj>=1.9.3",  # python-pyproj (1.9.5)
        "OWSLib>=0.11.0",  # python-owslib (0.10.3) FIXME
        "pycsw>=2.0.2",  # python-pycsw (1.10.1, 2.0.0 in ppa) FIXME
        "%s" % shapely_dep,  # python-shapely (1.5.13)


        # # Apps with packages provided in GeoNode's PPA on Launchpad.

        # Django Apps
        "awesome-slugify>=1.6.2",
        "dj-database-url >=0.4.0",
        "pinax-theme-bootstrap>=3.0a11",
        "pinax-theme-bootstrap-account>=1.0b2",
        "django-forms-bootstrap>=3.0.1",
        "django-friendly-tag-loader>=1.2.1",
        "django-activity-stream>=0.6.1",
        "django-leaflet>=0.13.7",
        "django-autocomplete-light>=2.3.3, <3.0a0",
        "django-modeltranslation>=0.11",  # python-django-modeltranslation (0.11 Debian)

        # GeoNode org maintained apps.
        "django-geoexplorer>=4.0.5",
        "geonode-user-messages>=0.1.4",  # (0.1.3 in ppa) FIXME
        "geonode-avatar>=2.1.6",  # (2.1.5 in ppa) FIXME
        "geonode-announcements>=1.0.8",
        "geonode-agon-ratings>=0.3.5",  # (0.3.1 in ppa) FIXME
        "geonode-user-accounts>=1.0.13",  # (1.0.11 in ppa) FIXME
        "geonode-arcrest>=10.2",
        "geonode-notification>=1.1.1",
        "geonode-dialogos>=0.5",
        "gsconfig>=1.0.6",  # (1.0.3 in ppa) FIXME
        "gsimporter>=1.0.0",  # (0.1 in ppa) FIXME
        "gisdata>=0.5.4",

        # haystack/elasticsearch, uncomment to use
        "django-haystack>=2.4.1",  # missing from ppa FIXME
        "elasticsearch>=2.4.0",
        "pyelasticsearch>=0.6.1",

        # datetimepicker widget
        "django-bootstrap3-datetimepicker>=2.2.3",

        # AWS S3 dependencies
        "django-storages>=1.1.8"
        ],
      zip_safe=False,
      )
