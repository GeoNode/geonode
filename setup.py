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
        # native dependencies
        "pillow",
        "lxml",
        # python dependencies
        "gsconfig==0.6.7",
        "OWSLib==0.7.2",
        "Django==1.5.5",
        # Django Apps
        "pinax-theme-bootstrap==3.0a11",
        "pinax-theme-bootstrap-account==1.0b2",
        "django-user-accounts==1.0b14",
        "django-forms-bootstrap==2.0.3.post1",
        "django-pagination==1.0.7",
        "django-jsonfield==0.9.10",
        "django-friendly-tag-loader==1.1",
        "django-taggit==0.10a1",
        "django-taggit-templatetags",
        "django-geoexplorer==4.0.2",
        "django-notification==1.0",
        "django-announcements==1.0.2",
        "django-activity-stream==0.4.4",
        "django-extensions",
        "user-messages==0.1.1",
        "geonode-avatar==2.1.1",
        "dialogos==0.2",
        "agon-ratings==0.2",
        "South==0.7.3",
        "django-downloadview==1.2",
        #catalogue
        "pycsw==1.6.4",
        # setup
        "Paver",
        # sample and test data / metadata
        "gisdata==0.5.4",
        # testing
        "django-nose",
        "nose>=1.0",
        "beautifulsoup4",
        "MultipartPostHandler",
        # translation
        "transifex-client",
        ],
      zip_safe=False,
      )
