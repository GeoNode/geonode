from __future__ import with_statement
from paver.easy import *
from paver.path25 import pushd
from paver.setuputils import setup, find_package_data
from paver.easy import options
from setuptools import find_packages
import os
from shutil import copytree
from paver import svn
import pkg_resources


import os

try:
    # Optional tasks, only needed for development
    #from github.tools.task import *
    import paver.doctools
    import paver.virtual
    from paver.virtual import bootstrap
    import paver.misctasks
    ALL_TASKS_LOADED = True
except ImportError, e:
    info("some tasks could not not be imported.")
    debug(str(e))
    ALL_TASKS_LOADED = False

name='GeoNode'
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


options(
    minilib=Bunch(extra_files=['virtual', 'doctools']),
    sphinx=Bunch(
      docroot='docs',
      builddir="_build",
      sourcedir=""
      ),
    virtualenv=Bunch(
      packages_to_install=['pip'],
      dest_dir='./',
      install_paver=True,
      script_name='bootstrap.py',
      paver_command_line='post_bootstrap'
      ),
    )

options.setup.package_data=find_package_data(package='GeoNode',
                                             only_in_packages=False)

venv = os.environ.get('VIRTUAL_ENV')

@task
def install_deps(options):
    """Installs all the python deps from a requirments file"""
    bundle = path('shared/geonode.bundle')
    if bundle.exists():
        info('using to install python deps bundle')
        sh("pip install %s" %bundle)    
    else:
        info('installing from requirements file')
        sh("pip install -r shared/core-libs.txt")

# put bundle on atlas or capra
# download it, then install

@task
def bundle_deps(options):
    sh("pip bundle -r shared/geonode-requirments.txt shared/geonode.bundle")

def install_bundle(options):
    sh("pip install ./geonode.bundle")    


@task
def install_25_deps(options):
    """Fetch python 2_5-specific dependencies (not maintained)"""
    pass

    
@task
def post_bootstrap(options):
    # installs the current package
    import sys
    from os.path import join
    if sys.platform == 'win32':
        bin = "Scripts"
    else:
        bin = "bin"
    pip = join(bin, "pip")
    sh('%s install -e .' % pip)

gs = "geoserver-build"
gs_data = "gs-data"

#@@ Move svn urls out to a config file

@task
def checkout_geoserver(options):
    """Fetch GeoServer sources from SVN in order to compile our extension."""
    with pushd('src'):
        svn.checkout("http://svn.codehaus.org/geoserver/trunk/src",  gs)
    
@task
def setup_gs_data(options):
    """Fetch a data directory to use with GeoServer for testing."""
    path(gs_data).rmtree()
    svn.checkout("http://svn.codehaus.org/geoserver/trunk/data/minimal",  gs_data)
    
@task
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    if not path(gs_data).exists():
        call_task('setup_gs_data')
    if not (path('src') / gs).exists():
        call_task('checkout_geoserver')
    with pushd('src'):
        with pushd(gs):
            sh('mvn install')
            sh("mvn install:install-file -DgroupId=org.geoserver -DartifactId=geoserver -Dversion=2.0-SNAPSHOT -Dpackaging=war -Dfile=web/app/target/geoserver.war")
        with pushd('geonode-geoserver-ext'):
            sh("mvn install")

@task
@needs(['install_deps','setup_geoserver','concat_js','capra_js'])
def build(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    info('to start node: paster serve shared/dev-paste.ini\n'\
         'to start geoserver:mvn jetty:run-war -DGEOSERVER_DATA_DIR=/path/to/datadir/') #@@ replace with something real


@task
def concat_js():
    """Compress the JavaScript resources used by the base GeoNode site."""
    with pushd('src/geonode-client/build/'):
       path("geonode-client").rmtree()
       os.makedirs("geonode-client/script")
       copytree("../src/theme/", "geonode-client/theme/")
       copytree("../externals/openlayers/theme/default", "geonode-client/theme/ol/")
       copytree("../externals/geoext/resources", "geonode-client/theme/gx/")
       sh("jsbuild -o geonode-client/script/ all.cfg") 

@task
def capra_js():
    """Compress the JavaScript resources used by the CAPRA GeoNode extensions."""
    with pushd('src/capra-client/build/'):
       path("capra-client").rmtree()
       os.makedirs("capra-client/")
       sh("jsbuild -o capra-client/ all.cfg") 

# set up supervisor?


if ALL_TASKS_LOADED:
    @task
    @needs('generate_setup', 'minilib', 'setuptools.command.sdist')
    def sdist():
        """Overrides sdist to make sure that our setup.py is generated."""
