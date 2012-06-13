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
        # setup
        "Paver",
        # native dependencies
        "PIL",
        "lxml",
        # python dependencies
        #"OWSLib==0.4.0",
        "Django==1.4",
        "django-extensions==0.8",
        "httplib2==0.7.4",
        "django-registration==0.8",
        "django-profiles==0.2",
        "django-avatar==1.0.4",
        "agon-ratings==0.2",
        "django-taggit==0.9.3",
        "South==0.7.3",
        "django-forms-bootstrap==2.0.3.post1",
        "gsconfig==0.5.4",
        # we use paste as an development server
        "pastescript",
        # assembling javascript
        "jstools==0.6",
        # sample and test data
        "gisdata==0.3.8",
        # document generator
        "Sphinx==1.1.3",
        # testing
        "django-nose",
        "nose",
        "nose-cover3",
        "coverage==3.4",
        "nosexcover",
        "mock",
        ],
      zip_safe=False,
      entry_points="""\
      [paste.app_factory]
      main = geonode:main
      """,
      )
