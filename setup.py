from setuptools import setup, find_packages

setup(name='GeoNode',
      version= __import__('geonode').get_version(),
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
          "gsconfig",
          "OWSLib==0.4.0",
          "Django>=1.1",
          "PIL",
          "django-extensions",
          "httplib2"
      ],
      zip_safe=False,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )


