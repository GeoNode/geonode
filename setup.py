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
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import os
import sys

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils not to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
geonode_dir = 'geonode'

for dirpath, dirnames, filenames in os.walk(geonode_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])


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
      packages=packages,
      data_files=data_files,
      install_requires=[
        ## The commented name next to the package
        ## is the Ubuntu 14.04 package that provides it.

        ## Apps with official Ubuntu 14.04 packages

        # native dependencies
        "pillow", # python-pillow
        "lxml", # python-lxml
        # "psycopg2==2.4.5", # python-psycopg2
        "Django==1.6.10", # python-django

        # Other
        "beautifulsoup4==4.2.1", # python-bs4
        "MultipartPostHandler==0.1.0", # python-multipartposthandler
        "httplib2==0.8", # python-httplib2
        "transifex-client==0.10", # transifex-client
        "Paver==1.2.1", # python-paver
        "nose <=1.0, <=1.3.1", # python-nose
        "django-nose==1.2", # python-django-nose
        "awesome-slugify==1.6.2",

        # Django Apps
        "django-pagination >=1.0.5, <=1.0.7", # python-django-pagination
        "django-jsonfield==0.9.12", # python-django-jsonfield
        "django-extensions==1.2.5", # python-django-extensions
        "django-taggit==0.12", # python-django-taggit
        "django-mptt==0.6.1", # django-mptt
        "django-guardian==1.2.0", #django-guardian
        # "django-admin-bootstrapped==1.6.5", #django-admin-bootstrapped

        ## Apps with packages provided in GeoNode's PPA on Launchpad.
        "pinax-theme-bootstrap==3.0a11",
        "pinax-theme-bootstrap-account==1.0b2",
        "django-forms-bootstrap==3.0.1",
        "django-friendly-tag-loader==1.1",
        "django-activity-stream==0.4.5beta1",
        "django-downloadview==1.2",
        "django-tastypie==0.11.0",
        "django-polymorphic==0.5.6",
        "django-leaflet==0.13.7",
        "django-autocomplete-light==1.4.14",
        "django-modeltranslation==0.8",

        # GeoNode org maintained apps.
        "django-geoexplorer==4.0.5",
        "geonode-user-messages==0.1.2",
        "geonode-avatar==2.1.4",
        "geonode-announcements==1.0.5",
        "geonode-agon-ratings==0.3.1",
        "geonode-user-accounts==1.0.10",
        "geonode-arcrest==10.2",
        "geonode-notification==1.1.1",
        "geonode-dialogos==0.4",
        "gsconfig==0.6.13",
        "gsimporter==0.1",
        "gisdata==0.5.4",

        # geopython dependencies
        "OWSLib==0.8.10",
        "pycsw==1.10.2",

        # haystack/elasticsearch, uncomment to use
        "django-haystack==2.1.0",
        "pyelasticsearch==0.6.1",
        "celery==3.1.17",
        "django-celery==3.1.16",

        # datetimepicker widget
        "django-bootstrap3-datetimepicker==2.2.3",
        "flake8==2.3.0",
        "pep8==1.6.2"
        ],
      zip_safe=False,
      )
