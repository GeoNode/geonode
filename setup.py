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
    shapely_dep = "Shapely==1.5.17"

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
        "pillow==3.3.1",  # python-imaging (3.1.2)
        "lxml==3.6.2",  # python-lxml (3.5.0)
        "psycopg2==2.7.3",  # python-psycopg2 (2.6.1)
        "Django>=1.8.7,<1.9a0",  # python-django (1.8.7)

        # Other
        "pyyaml==3.11",
        "beautifulsoup4==4.4.1",  # python-bs4 (4.4.1)
        "MultipartPostHandler==0.1.0",  # python-multipartposthandler (0.1.0)
        "httplib2==0.10.3",  # python-httplib2 (0.9.1, 0.9.2 in our ppa)
        "transifex-client<=0.12.4",  # transifex-client (0.11.1)
        "Paver==1.2.4",  # python-paver (1.2.4)
        "nose==1.3.7",  # python-nose (1.3.7)
        "django-nose==1.4.4",  # python-django-nose (1.4.3)
        "awesome-slugify==1.6.2",
        "django-floppyforms==1.7.0",
        "celery>=3.1.18,<4.0a0",  # python-celery (3.1.20)
        "django-celery==3.1.17",  # python-django-celery (3.1.17)
        "flake8<=2.5.4",  # python-flake8 (2.5.4)
        "pyflakes<=1.6.0",
        "pep8<=1.7.0",  # python-pep8 (1.7.0)
        "boto==2.38.0",  # python-boto (2.38.0)

        # Django Apps
        "django-pagination>=1.0.5,<=1.0.7",  # python-django-pagination (1.0.7)
        "django-extensions>=1.2.5",  # python-django-extensions (1.5.9)
        "django-jsonfield==1.0.1",  # python-django-jsonfield (0.9.15, 1.0.1 in our ppa)
        "django-jsonfield-compat==0.4.4",
        "django-taggit==0.21.0",  # python-django-taggit (0.18.0)
        "django-mptt==0.8.6",  # django-mptt (0.8.0, 0.8.6 in our ppa)
        "django-treebeard==4.0",  # django-treebeard (4.0)
        "django-guardian==1.4.6",  # django-guardian (1.4.1)
        "django-downloadview==1.8",  # python-django-downloadview (1.8)
        "django-polymorphic==1.3",  # python-django-polymorphic (0.8.1) FIXME
        "django-tastypie==0.14.0",  # python-django-tastypie (0.12.0, 0.12.2 in our ppa)
        "django-oauth-toolkit>=0.10.0,<1.0",  # python-django-oauth-toolkit (0.10.0)
        "oauthlib==2.0.2",

        # geopython dependencies
        "pyproj==1.9.5.1",  # python-pyproj (1.9.5)
        # we can't use OWSLib 0.14 until upstream merge changes for geonode.
        # this is temporary solution
        "OWSLib==0.14-dev",  # python-owslib (0.10.3) FIXME
        "pycsw==2.0.3",  # python-pycsw (1.10.1, 2.0.0 in ppa) FIXME
        "%s" % shapely_dep,  # python-shapely (1.5.13)


        # # Apps with packages provided in GeoNode's PPA on Launchpad.

        # Django Apps
        "awesome-slugify==1.6.5",
        "dj-database-url==0.4.2",
        "pinax-theme-bootstrap==3.0a11",
        "django-forms-bootstrap==3.1.0",
        "django-friendly-tag-loader==1.2.1",
        "django-activity-stream==0.6.4",
        "django-leaflet==0.22.0",
        "django-autocomplete-light>=2.3.3,<3.0a0",
        "django-modeltranslation>=0.11,<0.12.1",  # python-django-modeltranslation (0.11 Debian)

        # GeoNode org maintained apps.
        "django-geoexplorer<=4.0.11",
        "geonode-user-messages==0.1.6",  # (0.1.3 in ppa) FIXME
        "geonode-avatar==2.1.6",  # (2.1.5 in ppa) FIXME
        "geonode-announcements==1.0.8",
        "geonode-agon-ratings==0.3.5",  # (0.3.1 in ppa) FIXME
        "pinax-notifications<4.0",
        "django-user-accounts==2.0.2dev",
        # we can't use django-user-account until upstream merge changes for geonode.
        # this is temporary solution
        "geonode-arcrest>=10.2",
        "geonode-dialogos>=0.5",
        "gsconfig==1.0.6",  # (1.0.3 in ppa) FIXME
        "gsimporter==1.0.0",  # (0.1 in ppa) FIXME
        "gisdata==0.5.4",

        # haystack/elasticsearch, uncomment to use
        "django-haystack==2.6.0",  # missing from ppa FIXME
        "elasticsearch==2.4.0",
        "pyelasticsearch==0.6.1",

        # datetimepicker widget
        "django-bootstrap3-datetimepicker==2.2.3",

        # AWS S3 dependencies
        "django-storages==1.6.5",

        # Contribs
        "xlrd==1.0.0",
        # tests
        "factory_boy",
        # "WeasyPrint",

        ],
      zip_safe=False,
      dependency_links=[
        'https://github.com/cezio/django-user-accounts/archive/252_255_mixed.zip#egg=django-user-accounts-2.0.2dev'
      ]
      )
