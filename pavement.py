from __future__ import with_statement
from os.path import join
from paver import svn
from paver.easy import *
from paver.easy import options
from paver.path25 import pushd
from paver.setuputils import setup, find_package_data
from setuptools import find_packages
from shutil import copytree
import os
import os
import paver.doctools
import paver.misctasks
import paver.virtual
import pkg_resources
import sys


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
    minilib=Bunch(extra_files=['virtual',
                               'doctools',
                               'misctasks']),
    sphinx=Bunch(
      docroot='docs',
      builddir="_build",
      sourcedir="./"
      ),
    # must hand install virtualenv to run paver bootstrap
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
bin = "bin"
if sys.platform == 'win32':
    bin = "Scripts"

bundle = path('shared/geonode.pybundle')

@task
def install_deps(options):
    """Installs all the python deps from a requirments file"""
    if bundle.exists():
        info('using to install python deps bundle')
        call_task('install_bundle')
    else:
        info('installing from requirements file')
        if sys.platform == 'win32':
            corelibs = "core-libs-win.txt"
        else:
            corelibs = "core-libs.txt"
        sh("pip install -r shared/%s" % corelibs)

# put bundle on atlas or capra
# download it, then install

@task
def bundle_deps(options):
    sh("pip bundle -r shared/core-libs.txt %s" %bundle)

@task
@needs(['download_bundle'])
def install_bundle(options):
    """
    Installs a bundle of dependencies located at %s.
    """ %bundle
    
    info('install the bundle')
    sh("pip install %s" %bundle)    

dlname = 'geonode.bundle'

@task
def download_bundle(options):
    """
    Downloads zipped bundle of python dependencies to %s. Does not overwrite.
    """ %bundle
    
    bpath = bundle.abspath()
    if not bundle.exists():
        with pushd('shared'):
            #sh('wget http://capra.opengeo.org/repo/%s.zip' %bundle.name)
            sh('wget http://capra.opengeo.org/repo/%s.zip' %dlname)
            path(dlname + '.zip').copy(bpath)
    else:
        info("Skipping download. 'rm bundle  %s' if you need a fresh download. " %bundle)


@task
def install_25_deps(options):
    """Fetch python 2_5-specific dependencies (not maintained)"""
    pass

    
@task
def post_bootstrap(options):
    # installs the current package
    sh('%s install -e .' %(path(bin) / "pip"))

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
    with pushd('src/geonode-geoserver-ext'):
        sh("mvn install")


@task
@needs(['install_deps','setup_geoserver', 'build_js'])
def build(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    info('to start node: django-admin runserver --settings=geonode.settings\n'\
         'to start geoserver: cd src/geonode-geoserver-ext/; mvn jetty:run-war') #@@ replace with something real


@task
@needs(['concat_js','capra_js'])
def build_js(options):
    info('GeoNode Client Javascript is done building')


@task
def concat_js(options):
    """Compress the JavaScript resources used by the base GeoNode site."""
    with pushd('src/geonode-client/build/'):
       path("geonode-client").rmtree()
       os.makedirs("geonode-client/script")
       sh("svn export ../src/theme/ geonode-client/theme/")
       sh("svn export ../externals/openlayers/theme/default geonode-client/theme/ol/")
       sh("svn export ../externals/geoext/resources geonode-client/theme/gx/")
       sh("jsbuild -o geonode-client/script/ all.cfg") 


@task
def capra_js(options):
    """Compress the JavaScript resources used by the CAPRA GeoNode extensions."""
    with pushd('src/capra-client/build/'):
       path("capra-client").rmtree()
       os.makedirs("capra-client/")
       sh("jsbuild -o capra-client/ all.cfg") 

@task
def install_sphinx_conditionally(options):
    """if no sphinx, install it"""
    try:
        import sphinx
    except ImportError:
        sh("%s install sphinx" %(path(bin) / 'pip'))

@task
@needs(['install_sphinx_conditionally'])
def html(options):
    call_task('paver.doctools.html')

@task
@needs('minilib', 'setuptools.command.sdist')
def sdist():
    """update minilib, run sdist"""
