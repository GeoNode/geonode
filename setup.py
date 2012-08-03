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

from setuptools import setup

setup(name='GeoNode',
      version=__import__('geonode').get_version(),
      description="Application for serving and sharing geospatial data",
      long_description=open('README.rst').read(),
      classifiers=[
        "Development Status :: 1 - Planning"],
      keywords='',
      author='GeoNode Developers',
      author_email='dev@geonode.org',
      url='http://geonode.org',
      license='GPL',
      packages=['geonode',
                'geonode.maps',
                'geonode.security',
                'geonode.proxy',
                ],
      package_dir={'geonode': 'geonode'},
      package_data={'geonode': ['geonode/static/*']},
      install_requires=[
        # native dependencies
        "PIL",
        "lxml==2.3",
        # python dependencies
        "gsconfig==0.6",
        "OWSLib==0.5.0",
        "Django==1.4",
        "django-extensions==0.8",
        "httplib2>=0.7",
        "django-registration==0.8",
        "django-profiles==0.2",
        "django-avatar==1.0.4",
        "agon-ratings==0.2",
        "django-taggit==0.9.3", 
        "dialogos==0.1",
        "South==0.7.3",
        "django-forms-bootstrap==2.0.3.post1",
        # setup
        "Paver",
        # we use paste as an development server
        "paste>=1.3",
        "PasteDeploy",
        "pastescript",
        # assembling javascript
        "jstools==0.6",
        # sample and test data
        "gisdata==0.3.8",
        # document generator
        "Sphinx==1.1.3",
        # testing
        "django-nose",
        "nose>=1.0",
        "mock",
        ],
      zip_safe=False,
      entry_points="""\
      [paste.app_factory]
      main = geonode:main
      """,
      )
