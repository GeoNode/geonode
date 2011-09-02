from setuptools import setup, find_packages
import pkg_resources
import sys, os

name='GeoNodePy'
version = "1.1"
req = pkg_resources.Requirement.parse(name)

setup(name=name,
      version=version,
      description="Application for serving and sharing geospatial data",
      long_description=open('README.rst').read(),
      classifiers=[
        "Development Status :: 1 - Planning" ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='GeoNode Developers',
      author_email='dev@geonode.org',
      url='http://geonode.org',
      license='GPL',
      packages = find_packages(),
      include_package_data=True,
      install_requires = [
          "gsconfig.py",
          "OWSLib>0.3.1",
          "Django>=1.1",
          "ReportLab",
          "PIL",
          "simplejson",
          "django-extensions",
          "httplib2"
      ],
      zip_safe=False,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )


