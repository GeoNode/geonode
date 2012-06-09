from paver.easy import *
from paver.easy import options
from paver.path25 import pushd
import functools
import os
import sys
import time
from datetime import date
import socket
import ConfigParser
import paver.doctools
import paver.misctasks
import pkg_resources
import subprocess
import shutil
from shutil import move
import zipfile
import tarfile
import urllib
import glob
from subprocess import Popen, PIPE


OUTPUT_DIR = path(os.path.abspath('dist'))
BUNDLE = path(os.path.join(OUTPUT_DIR, 'geonode.pybundle'))


assert sys.version_info >= (2,6), \
       SystemError("GeoNode Build requires python 2.6 or better")


options(
    config=Bunch(
        package_dir = path('shared/package')
    ),
    sphinx=Bunch(
        docroot='docs',
        builddir="_build",
        sourcedir="source"
    ),
    deploy=Bunch(
        req_file=path('shared/package/requirements.txt'),
        packages_to_install=['pip'],
        dest_dir='./',
    ),
)

deploy_req_txt = """
# NOTE... this file is generated
-r requirements.txt
# this line installs GeoNode
.
""" % locals()


def grab(src, dest):
    from urllib import urlretrieve
    if not os.path.exists(dest):
        urlretrieve(str(src), str(dest))

@task
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    with pushd('geoserver-geonode-ext'):
        sh("mvn clean install -DskipTests")

@task
def setup_geonetwork(options):
    """Fetch the geonetwork.war to use with GeoServer for testing."""
    war_file = 'geonetwork.war'
    src_url = 'http://dev.geonode.org/dev-data/synth/%s' % war_file
    info("geonetwork url: %s" % src_url)
    # where to download the war files. If changed change also
    # geoserver-geonode-ext/jetty.xml accordingly

    build_path = path('build')
    if not build_path.exists():
        build_path.mkdir()

    dst_url = os.path.join(build_path, war_file)

    webapps = path("build/webapps")
    if not webapps.exists():
        webapps.mkdir()

    deployed_url = webapps / "geonetwork"

    if getattr(options, 'clean', False):
        deployed_url.rmtree()

    grab(src_url, dst_url)

    if not deployed_url.exists():
        zip_extractall(zipfile.ZipFile(dst_url), deployed_url)


@task
def setup_client(options):
    """
    Fetch geonode-client
    """
    sh('git submodule update --init')
    static = os.path.abspath("geonode/static/geonode")
    scripts_path = os.path.join(static, 'script')

    if not os.path.exists(scripts_path):
        os.makedirs(scripts_path)
    
    with pushd("geonode-client/"):
        sh("jsbuild buildjs.cfg -o %s" % scripts_path)
 
    resources = ((
           # Ext resources
           'externals/ext',
           'app/static/externals/ext'
           ),(
           'externals/gxp/theme',
           'app/static/externals/gxp/src/theme'
           ),(
           'externals/PrintPreview/resources',
           'app/static/externals/PrintPreview/resources'
           ),(
           'externals/geoext/resources',
           'app/static/externals/geoext/resources'
           ),(
           # OpenLayers resources
           'externals/openlayers/theme',
           'app/static/externals/openlayers/theme'
           ),(
           'externals/openlayers/img',
           'app/static/externals/openlayers/img'
           ),(
           'theme/ux/colorpicker',
           'app/static/script/ux/colorpicker/color-picker.ux.css'
           ),(
           'script/ux/colorpicker',
           'script/ux/colorpicker/picker.gif'
           ),(
           'script/ux/colorpicker',
           'app/static/script/ux/colorpicker/side_slider.jpg'
           ),(
           'script/ux/colorpicker',
           'app/static/script/ux/colorpicker/mask.png'
           ),(
           # GeoExt Resources
           'externals/geoext/resource',
           'app/static/externals/geoext/resources'
           ),(
           'theme/ux/fileuploadfield',
           'app/static/script/ux/fileuploadfield/css'
           ),(
           # gxp resources
           'externals/gxp/src/theme',
           'app/static/externals/gxp/src/theme'
    ))

    for t, o in resources:
        origin = os.path.join('geonode-client', o)
        target = os.path.join(static, t)
        if os.path.isdir(origin):
            shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(origin, target)
        elif os.path.isfile(origin):
            if not os.path.exists(target):
                os.makedirs(target)
            sh('cp %s %s' % (origin, target))

@task
@needs([
    'setup_geoserver',
    'setup_geonetwork',
    'setup_client',
])
def setup(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    sh('pip install -e .')
    info("""GeoNode development environment successfully set up.\nIf you have not set up an administrative account, please do so now.\nUse "paver host" to start up the server.""") 



@task
def syncdb(options):
    """
    Run the syncdb and migrate management commands to create and migrate a DB
    """
    sh("python manage.py syncdb --noinput")
    sh("python manage.py migrate --noinput")
    sh("python manage.py loaddata tests/integration/admin.fixture.json")


def package_dir(options):
    """
    Adds a packaging directory
    """
    if not os.path.exists(OUTPUT_DIR):
        OUTPUT_DIR.mkdir()


def package_geoserver(options):
    """Package GeoServer WAR file with appropriate extensions."""
    geoserver_target.copy(options.deploy.out_dir)


def package_geonetwork(options):
    """Package GeoNetwork WAR file for deployment."""
    geonetwork_target.copy(options.deploy.out_dir)


def package_webapp(options):
    """Package (Python, Django) web application and dependencies."""
    sh('python setup.py egg_info sdist')
        
    req_file = options.deploy.req_file
    req_file.write_text(deploy_req_txt)
    pip_bundle("-r %s %s/geonode-webapp.pybundle" % (req_file, options.deploy.out_dir))



def create_version_name():
    # we'll use the geonode version as our "official" version number
    # for now
    slug = "GeoNode-%s" % (
        pkg_resources.get_distribution('GeoNode').version,
    )

    return slug

@task
@cmdopts([
    ('name=', 'n', 'Release number or name'),
    ('append_to=', 'a', 'append to release name'),
    ('skip_packaging', 'y', 'Do not call package functions when creating a release'),
])
def release(options):
    """
    Creates a tarball to use for building the system elsewhere
    """

    if not hasattr(options, 'skip_packaging'):
        package_dir()
        package_geoserver()
        package_geonetwork()
        package_webapp()
    if hasattr(options, 'name'):
        pkgname = options.name
    else:
        pkgname = create_version_name()
        if hasattr(options, 'append_to'):
            pkgname += options.append_to

    with pushd('shared'):
        out_pkg = path(pkgname)
        out_pkg.rmtree()
        path('./package').copytree(out_pkg)

        tar = tarfile.open("%s.tar.gz" % out_pkg, "w:gz")
        for file in out_pkg.walkfiles():
            tar.add(file)
        tar.add('README.release.rst', arcname=('%s/README.rst' % out_pkg))
        tar.close()

        out_pkg.rmtree()
        info("%s.tar.gz created" % out_pkg.abspath())


@task
@needs(['start_geoserver',
        'syncdb',
        'setup_client',
        'start_django',])
def start():
    """
    Start the GeoNode app and all its constituent parts (Django, GeoServer & Client)
    """
    print 'Starting GeoNode on http://localhost:8000'


@task
@needs(['stop_django', 'stop_geoserver'])
def stop():
    """
    Stop GeoNode
    """
    print 'Stopped GeoNode'

@task
def start_django():
    """
    Start the GeoNode Django application (with paster)
    """
    sh('paster serve shared/dev-paste.ini --daemon')

@task
def stop_django():
    """
    Stop the GeoNode Django application (with paster)
    """
    kill('paster', 'project.paste')

@task
def start_geoserver():
    """
    Start GeoNode's Java apps (GeoServer with GeoNode extensions and GeoNetwork)
    """
    with pushd('geoserver-geonode-ext'):
        sh('./startup.sh &')

@task
def stop_geoserver():
    """
    Stop GeoNode's Java apps (GeoServer and GeoNetwork)
    """
    kill('jetty', 'java')

@task
def test(options):
    """
    Run GeoNode's Unit Test Suite
    """
    sh("python manage.py test geonode")

@task
def test_integration(options):
    """
    Run GeoNode's Integration test suite against the external apps
    """
    from time import sleep
    call_task('reset')
    call_task('start')
    #FIXME: Check the server is up instead of a blind sleep
    sleep(60)
    with pushd('tests/integration'):
        sh("python manage.py test")
    call_task('stop')

@task
@needs(['stop'])
def reset():
    """
    Reset a development environment (Database, GeoServer & GeoNetwork)
    """
    sh("rm -rf geonode/development.db")
    sh("rm -rf build/gs_data")
    # TODO: There should be a better way to clean out GeoNetworks data
    # Rather than just deleting the entire app
    sh("rm -rf build/webapps/geonetwork")
    setup_geonetwork()

@task
def setup_data():
    """
    Import sample data (from gisdata package) into GeoNode
    """
    import gisdata
    data_dir = gisdata.GOOD_DATA
    sh("python manage.py importlayers %s" % data_dir)




# Helper functions

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



# include patched versions of zipfile code
# to extract zipfile dirs in python 2.6.1 and below...

def zip_extractall(zf, path=None, members=None, pwd=None):
    if sys.version_info >= (2, 6, 2):
        zf.extractall(path=path, members=members, pwd=pwd)
    else:
        _zip_extractall(zf, path=path, members=members, pwd=pwd)

def _zip_extractall(zf, path=None, members=None, pwd=None):
    """Extract all members from the archive to the current working
       directory. `path' specifies a different directory to extract to.
       `members' is optional and must be a subset of the list returned
       by namelist().
    """
    if members is None:
        members = zf.namelist()

    for zipinfo in members:
        _zip_extract(zf, zipinfo, path, pwd)

def _zip_extract(zf, member, path=None, pwd=None):
    """Extract a member from the archive to the current working directory,
       using its full name. Its file information is extracted as accurately
       as possible. `member' may be a filename or a ZipInfo object. You can
       specify a different directory using `path'.
    """
    if not isinstance(member, zipfile.ZipInfo):
        member = zf.getinfo(member)

    if path is None:
        path = os.getcwd()
    
    return _zip_extract_member(zf, member, path, pwd)


def _zip_extract_member(zf, member, targetpath, pwd):
    """Extract the ZipInfo object 'member' to a physical
       file on the path targetpath.
    """
    # build the destination pathname, replacing
    # forward slashes to platform specific separators.
    # Strip trailing path separator, unless it represents the root.
    if (targetpath[-1:] in (os.path.sep, os.path.altsep)
        and len(os.path.splitdrive(targetpath)[1]) > 1):
        targetpath = targetpath[:-1]

    # don't include leading "/" from file name if present
    if member.filename[0] == '/':
        targetpath = os.path.join(targetpath, member.filename[1:])
    else:
        targetpath = os.path.join(targetpath, member.filename)

    targetpath = os.path.normpath(targetpath)

    # Create all upper directories if necessary.
    upperdirs = os.path.dirname(targetpath)
    if upperdirs and not os.path.exists(upperdirs):
        os.makedirs(upperdirs)

    if member.filename[-1] == '/':
        if not os.path.isdir(targetpath):
            os.mkdir(targetpath)
        return targetpath

    source = zf.open(member, pwd=pwd)
    target = file(targetpath, "wb")
    shutil.copyfileobj(source, target)
    source.close()
    target.close()

    return targetpath


def kill(arg1, arg2):
    """Stops a proces that contains arg1 and is filtered by arg2
    """

    # Wait until ready
    t0 = time.time()
    time_out = 30 # Wait no more than these many seconds
    running = True

    while running and time.time()-t0 < time_out:
        p = Popen('ps aux | grep %s' % arg1, shell=True,
              stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

        lines = p.stdout.readlines()

        running = False
        for line in lines:

            if '%s' % arg2 in line:
                running = True

                # Get pid
                fields = line.strip().split()

                print 'Stopping %s (process number %s)' % (arg1, fields[1])
                kill = 'kill -9 %s 2> /dev/null' % fields[1]
                os.system(kill)

        # Give it a little more time
        time.sleep(1)
    else:
        #print 'There are no process containing "%s" running' % arg1
        pass

    if running:
        raise Exception('Could not stop %s: '
                        'Running processes are\n%s'
                        % (arg1, '\n'.join([l.strip() for l in lines])))
