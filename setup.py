from distutils.core import setup

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
      packages = ['geonode',
                  'geonode.maps',
                  'geonode.security',
                  'geonode.proxy',
                  ],
      package_dir = {'geonode': 'geonode'},
      package_data = {'geonode': ['geonode/static/*']},
      install_requires = [
        # setup
        "Paver==1.0.5",
        # native dependencies
        # Better packaged PIL replacement
        "Pillow==1.7.7",
        "lxml",
        # python dependencies
        "OWSLib==0.4.0",
        "Django==1.4",
        "django-extensions==0.8",
        "httplib2==0.7.4",
        "gsconfig==0.5.4",
        "django-registration==0.8",
        "django-profiles==0.2",
        "django-avatar==1.0.4",
        "agon-ratings==0.2",
        "django-taggit==0.9.3",
        "South==0.7.3",
        "django-forms-bootstrap==2.0.3.post1",
        ],
      zip_safe=False,
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
