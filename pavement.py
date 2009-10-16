from __future__ import with_statement
import os
from os.path import join
from paver import svn
from paver.easy import *
from paver.path25 import pushd
from paver.setuputils import setup, find_package_data
from paver.easy import options
import pkg_resources
from setuptools import find_packages
from shutil import copy, copytree
import sys
import zipfile


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
        info("oSkipping download. 'rm bundle  %s' if you need a fresh download. " %bundle)

@task
def install_25_deps(options):
    """Fetch python 2_5-specific dependencies (not maintained)"""
    pass
    
@task
def post_bootstrap(options):
    # installs the current package
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
        with pushd(gs):
            sh('mvn install')
            sh("mvn install:install-file -DgroupId=org.geoserver -DartifactId=geoserver -Dversion=2.0-SNAPSHOT -Dpackaging=war -Dfile=web/app/target/geoserver.war")
    

@task
def setup_gs_data(options):
    """Fetch a data directory to use with GeoServer for testing."""
    from urlgrabber.grabber import urlgrab
    from urlgrabber.progress import text_progress_meter
    src_url = "http://capra.opengeo.org/dev-data/geonode-geoserver-data.zip"
    path("work").mkdir()
    dst_url = "work/geonode-geoserver-data.zip"
    urlgrab(src_url, dst_url, progress_obj=text_progress_meter())
    path(gs_data).rmtree()
    unzip_file(dst_url, gs_data)

@task
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    if not path(gs_data).exists():
        call_task('setup_gs_data')
    if not (path('src') / gs).exists():
        call_task('checkout_geoserver')
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
@needs('concat_js', 'capra_js')
def package_client(options):
    """Package compressed client resources (JavaScript, CSS, images)."""

    zip = zipfile.ZipFile("build/geonode-client.zip",'w') #create zip in write mode
    with pushd('src/geonode-client/build/'):
        for file in path("geonode-client/").walkfiles():
            print(file)
            zip.write(file)
    
    with pushd('src/capra-client/build/'):
        for file in path("capra-client/").walkfiles():
            print(file)
            zip.write(file)

    zip.close()


@task
@needs('checkout_geoserver', 'setup_geoserver')
def package_geoserver(options):
    """Package GeoServer WAR file with appropriate extensions."""
    copy('src/geonode-geoserver-ext/target/geoserver-geonode-dev.war', 'build/')
    

@task
@needs('install_deps')
def package_webapp(options):
    """Package (Python, Django) web application and dependencies."""
    sh("pip bundle -r shared/core-libs.txt build/geonode-webapp.bundle geonode capra")    


def unzip_file(src, dest): 
    zip = zipfile.ZipFile(src)
    if not path(dest).exists():
        os.makedirs(dest)
    for name in zip.namelist():
        if name.endswith("/"):
            os.mkdir(join(dest, name))
        else:
            parent, file = os.path.split(name)
            parent = join(dest, parent)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            out = open(join(parent,file), 'wb')
            out.write(zip.read(name))
            out.close()

# set up supervisor?

if ALL_TASKS_LOADED:
    @task
    @needs('generate_setup', 'minilib', 'setuptools.command.sdist')
    def sdist():
        """Overrides sdist to make sure that our setup.py is generated."""
