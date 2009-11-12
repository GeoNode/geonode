from __future__ import with_statement
from paver import svn
from paver.easy import *
from paver.easy import options
from paver.path25 import pushd
from paver.setuputils import setup, find_package_data
from setuptools import find_packages
import shutil
import functools
import os
import sys
import paver.doctools
import paver.misctasks
import pkg_resources
from shutil import copy, copytree, move
import sys
import zipfile

try:
    from paver.virtual import bootstrap
except ImportError, e:
    info("VirtualEnv must be installed to enable 'paver bootstrap'. If you need this command, run: pip install virtualenv")

assert sys.version_info[0] >= 2 and sys.version_info[1] >= 6, SystemError("GeoNode Build require python 2.6.2 or better")

#build_dir = path('./build/')
build_dir = path('./package') #@@ confusing, rename

options(
    minilib=Bunch(extra_files=['virtual', 'doctools', 'misctasks']),
    sphinx=Bunch(
      docroot='docs',
      builddir="_build",
      sourcedir=""
      ),
    virtualenv=Bunch(
      packages_to_install=['pip', 'urlgrabber', 'jstools'],
      dest_dir='./',
      install_paver=True,
      script_name='bootstrap.py',
      paver_command_line='post_bootstrap'
      ),
    deploy=Bunch(
      pavement=path('shared/deployment_pavement.py'),
      req_file=path('shared/deploy-libs.txt'),
      packages_to_install=['pip'],
      dest_dir='./',
      out_dir=build_dir,
      install_paver=True,
      script_name=build_dir / 'bootstrap.py',
      paver_command_line='post_bootstrap'      
    )
)

venv = os.environ.get('VIRTUAL_ENV')
bundle = path('shared/geonode.pybundle')

dl_cache = "--download-cache=./build"

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
        pip_install("-r shared/%s" % corelibs)

# put bundle on atlas or capra
# download it, then install

@task
def bundle_deps(options):
    """
    Create a pybundle of all python dependencies.  If created, this
    will be the default for installing python deps.
    """
    pip_bundle("-r shared/core-libs.txt %s" %bundle)

@task
@needs(['download_bundle'])
def install_bundle(options):
    """
    Installs a bundle of dependencies located at %s.
    """ %bundle
    
    info('install the bundle')
    pip_install(bundle)

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
    """installs the current package"""
    if sys.platform == 'win32':
        bin = "Scripts"
    else:
        bin = "bin"
    pip = path(bin) / "pip"
    sh('%s install -e %s' %(pip, path("src/GeoNodePy")))

gs = "geoserver-build"
gs_data = "gs-data"

#@@ Move svn urls out to a config file

@task
@needs('checkout_geoserver')
def install_geoserver(options):
    """Fetch GeoServer sources from SVN in order to compile our extension."""
    with pushd(path('src') / gs):
        sh('mvn install')
        sh("mvn install:install-file -DgroupId=org.geoserver -DartifactId=geoserver -Dversion=2.1-SNAPSHOT -Dpackaging=war -Dfile=web/app/target/geoserver.war")

@task
def setup_gs_data(options):
    """Fetch a data directory to use with GeoServer for testing."""
    from urlgrabber.grabber import urlgrab
    from urlgrabber.progress import text_progress_meter
    src_url = "http://capra.opengeo.org/dev-data/geonode-geoserver-data.zip"
    shared = path("./shared")
    if not shared.exists():
        shared.mkdir()
    dst_url = shared / "geonode-geoserver-data.zip"
    if not dst_url.exists() or getattr(options, 'clean', False):
        urlgrab(src_url, dst_url, progress_obj=text_progress_meter())
        path(gs_data).rmtree()
        unzip_file(dst_url, gs_data)

@task
def checkout_geoserver(options):
    if not (path('src') / gs).exists():
        with pushd('src'):
            svn.checkout("http://svn.codehaus.org/geoserver/trunk/src",  gs)

@task
@needs('checkout_geoserver')
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    if not path(gs_data).exists():
        call_task('setup_gs_data')
    with pushd('src/geoserver-geonode-ext'):
        sh("mvn install")

#@task
#def rebuild_gs(options):
#    with pushd('src/geoserver-build'):
#        sh("svn up")
#        sh("mvn clean")
#        sh("mvn install")

#@task
#def rebuild_gs_ext(options):
#    with pushd('src/geoserver-geonode-ext'):
#        sh("mvn clean")
#        sh("mvn install")

@task
@needs(['install_deps','setup_geoserver', 'build_js'])
def build(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    info('If this is your first build: django-admin.py syncdb --settings=geonode.settings\n'\
         'to start node: django-admin.py runserver --settings=geonode.settings\n'\
         'to start geoserver: cd src/geoserver-geonode-ext/; mvn jetty:run-war') #@@ replace with something real


@task
@needs(['concat_js','capra_js'])
def build_js(options):
    """
    Concatenate and compress application client javascript
    """
    info('GeoNode Client Javascript is done building')


@task
def concat_js(options):
    """Compress the JavaScript resources used by the base GeoNode site."""
    with pushd('src/geonode-client/build/'):
       path("geonode-client").rmtree()
       os.makedirs("geonode-client/gx")
       sh("svn export ../externals/geoext/resources geonode-client/gx/theme")
       os.makedirs("geonode-client/ol") #need to split this off b/c of dumb hard coded OL paths
       sh("svn export ../externals/openlayers/theme geonode-client/ol/theme")
       os.makedirs("geonode-client/gn")
       sh("svn export ../src/theme/ geonode-client/gn/theme/")

       sh("jsbuild -o geonode-client/ all.cfg") 
       move("geonode-client/OpenLayers.js","geonode-client/ol/")
       move("geonode-client/GeoExt.js","geonode-client/gx/")
       move("geonode-client/GeoNode.js","geonode-client/gn/")
       move("geonode-client/ux.js","geonode-client/gn/")


@task
def capra_js(options):
    """Compress the JavaScript resources used by the CAPRA GeoNode extensions."""
    with pushd('src/capra-client/build/'):
       path("capra-client").rmtree()
       path("capra-client/").makedirs()
       sh("jsbuild -o capra-client/ all.cfg") 

@task
def build_dir(options):
    if not options.deploy.out_dir.exists():
        options.deploy.out_dir.mkdir()

@task
@needs('build_dir', 'concat_js', 'capra_js')
def package_client(options):
    """
    Package compressed client resources (JavaScript, CSS, images).
    """
    build_dir = options.deploy.out_dir
    zip = zipfile.ZipFile(build_dir / 'geonode-client.zip','w') #create zip in write mode

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
@needs('build_dir', 'setup_geoserver')
def package_geoserver(options):
    """Package GeoServer WAR file with appropriate extensions."""
    path('src/geoserver-geonode-ext/target/geoserver-geonode-dev.war').copy(options.deploy.out_dir)


deploy_req_txt = """
# NOTE... this file is generated
-r %(venv)s/shared/core-libs.txt
-e %(venv)s/src/GeoNodePy
""" %locals()


@task
@needs('build_dir')
def package_webapp(options):
    """Package (Python, Django) web application and dependencies."""
    with pushd('src/GeoNodePy'):
        import pdb;pdb.set_trace()
        sh('python setup.py egg_info sdist')

    import pkg_resources
    pkg_resources.get_distribution('GeoNodePy')        
        
    req_file = options.deploy.req_file
    req_file.write_text(deploy_req_txt)
    pip_bundle("-r %s %s/geonode-webapp.pybundle" %(req_file, options.deploy.out_dir))



@task
@needs('package_geoserver','package_webapp', 'package_client', 'package_bootstrap')
def package_all(options):
    info('all is packaged, ready to deploy')


def unzip_file(src, dest):
    zip = zipfile.ZipFile(src)
    if not path(dest).exists():
        path(dest).makedirs()
        
    for name in zip.namelist():
        if name.endswith("/"):
            (path(dest) / name).makedirs()
        else:
            parent, file = path(name).splitpath()
            parent = path(dest) / parent
            if parent and not parent.isdir():
                path(parent).makedirs()
            out = open(path(parent) / file, 'wb')
            out.write(zip.read(name))
            out.close()


@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""

def pip(*args):
    try:
        pkg_resources.require('pip>=0.6')
    except :
        error("**ATTENTION**: Update your 'pip' to at least 0.6")
        raise
    sh("pip " + " ".join(args))

pip_install = functools.partial(pip, 'install', dl_cache)
pip_bundle = functools.partial(pip, 'bundle', dl_cache)

if locals().has_key('bootstrap'):
    @task
    @needs('build_dir')
    def package_bootstrap(options):
        """Create a bootstrap script for deployment"""
        options.virtualenv = options.deploy
        call_task("paver.virtual.bootstrap")
