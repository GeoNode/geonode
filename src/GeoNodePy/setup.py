from setuptools import setup, find_packages
import sys, os

version = '0.1'

name='GeoNodePy'
version = "1.0.1"

setup(name=name,
      version=version,
      description="Application for serving and sharing geospatial data",
      long_description=""" """,
      classifiers=[
        "Development Status :: 1 - Planning" ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='GeoNode Developers',
      author_email='dev@geonode.org',
      url='http://geonode.org',
      license='GPL',
      packages = ['capra', 'geonode',],
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=False,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )


