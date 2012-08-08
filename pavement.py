#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import os
import sys
import time

import pkg_resources
import shutil
import zipfile
import tarfile

import urllib
from urllib import urlretrieve
from subprocess import Popen, PIPE

from paver.easy import *
from paver.easy import options
from paver.path25 import pushd



assert sys.version_info >= (2,6), \
       SystemError("GeoNode Build requires python 2.6 or better")


options(
    sphinx=Bunch(
        docroot='docs',
        builddir="_build",
        sourcedir="source"
    ),
)

def grab(src, dest):
    urlretrieve(str(src), str(dest))

@task
@cmdopts([
  ('fast', 'f', 'Fast. Skip some operations for speed.'),
])
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    fast = options.get('fast', False)

    with pushd('geoserver-geonode-ext'):
        if fast:
            sh('mvn install -DskipTests')
        else:
            sh("mvn clean install jetty:stop")

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
           ), (
           # GeoExplorer resources
           'theme/app',
           'app/static/theme/app'
    ))

    for t, o in resources:
        origin = os.path.join('geonode-client', o)
        target = os.path.join(static, t)
        justcopy(origin, target)

@task
@needs([
    'setup_geoserver',
    'setup_client',
])
def setup(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    #FIXME(Ariel): Delete this once the last requirement is available in pypi
    sh('pip install -r requirements.txt')
    # Needed to re-install in dev mode  after a git clean, better safe than sorry.
    sh('pip install -e .')

    info("""GeoNode development environment successfully set up.\nIf you have not set up an administrative account, please do so now.\nUse "paver start" to start up the server.""") 


@task
def sync(options):
    """
    Run the syncdb and migrate management commands to create and migrate a DB
    """
    sh("python manage.py syncdb --noinput")
    sh("python manage.py migrate --noinput")
    sh("python manage.py loaddata sample_admin.json")



@task
def package(options):
    """
    Creates a tarball to use for building the system elsewhere
    """
    version = pkg_resources.get_distribution('GeoNode').version,
    # Use GeoNode's version for the package name.
    pkgname = 'GeoNode-%s-all' % version

    # Create the output directory.
    out_pkg = path(pkgname)

    # Clean anything that is in the outout package tree.
    out_pkg.rmtree()
    # And copy the default files from the package folder.
    path('./package').copytree(out_pkg)

    # Package Geoserver's war.
    geoserver_target = path('geoserver-geonode-ext/target/geoserver.war')
    geoserver_target.copy(out_pkg)

    # Package (Python, Django) web application and dependencies.

    # Create a new requirements file, only to be able to install the GeoNode
    # python package along with all the other dependencies.
    req_file = path('package_requirements.txt')
    req_file.write_text('-r requirements.txt')

    # Create a distribution in zip format for the geonode python package.
    sh('python setup.py sdist --format=zip')
    # Write path to released zip file to requirements.txt, by default
    # the command below puts it in the 'dist' folder
    req_file.write_text(os.path.join('dist', 'GeoNode-%s.zip' % version))

    # Bundle all the dependencies in a zip-lib package called a pybundle.
    bundle = os.path.join(out_pkg, 'geonode-webapp.pybundle')
    sh('pip bundle -r %s %s' % (req_file, bundle))

    # Remove the requirements file used to create the pybundle.
    req_file.remove()

    # Create a tar file with all the information in the output package folder.
    tar = tarfile.open("%s.tar.gz" % out_pkg, "w:gz")
    for file in out_pkg.walkfiles():
        tar.add(file)

    # Add the README with the license and important links to documentation.
    tar.add('./package/README', arcname=('%s/README.rst' % out_pkg))
    tar.close()

    # Remove all the files in the temporary output package directory.
    out_pkg.rmtree()

    # Report the info about the new package.
    info("%s.tar.gz created" % out_pkg.abspath())


@task
@needs(['start_geoserver',
        'sync',
        'start_django',])
def start():
    """
    Start the GeoNode app and all its constituent parts (Django, GeoServer & Client)
    """
    print "GeoNode is now available."


def stop_django():
    """
    Stop the GeoNode Django application
    """
    kill('python', 'runserver')


def stop_geoserver():
    """
    Stop GeoServer
    """
    kill('jetty', 'java')


@task
def stop():
    """
    Stop GeoNode
    """
    print "Stopping GeoNode ..."
    stop_django()
    stop_geoserver()


@task
def start_django():
    """
    Start the GeoNode Django application
    """
    sh('python manage.py runserver &')


@task
def start_geoserver(options):
    """
    Start GeoNode's Java apps (GeoServer with GeoNode extensions and GeoNetwork)
    """

    from geonode.settings import GEOSERVER_BASE_URL

    with pushd('geoserver-geonode-ext'):
        sh('MAVEN_OPTS="-Xmx512m -XX:MaxPermSize=256m" mvn jetty:run > /dev/null &')
 
    print 'Starting GeoServer on %s' % GEOSERVER_BASE_URL
    # wait for GeoServer to start
    started = waitfor(GEOSERVER_BASE_URL)
    if not started:
        # If applications did not start in time we will give the user a chance
        # to inspect them and stop them manually.
        print "GeoServer never started properly or timed out. It may still be running in the background."
        print "The logs are available at geoserver-geonode-ext/jetty.log"
        sys.exit(1)
 


@task
def test(options):
    """
    Run GeoNode's Unit Test Suite
    """
    sh("python manage.py test geonode --noinput")


@task
@needs(['reset',])
def test_integration(options):
    """
    Run GeoNode's Integration test suite against the external apps
    """

    # Start GeoServer
    call_task('start_geoserver') 
    print "GeoNode is now available, running the tests now."

    success = False
    try:
        sh('python manage.py test geonode.tests.integration --noinput --liveserver=localhost:8000')
    except BuildFailure, e:
        print 'Tests failed! %s' % str(e)
    else:
        success = True
    finally:
        # don't use call task here - it won't run since it already has
        stop_django()
        stop_geoserver()

    if not success:
        sys.exit(1)


@task
@needs(['stop'])
def reset():
    """
    Reset a development environment (Database, GeoServer & GeoNetwork)
    """
    sh("rm -rf geonode/development.db")
    # Reset data dir
    sh('git clean -xdf geoserver-geonode-ext/src/main/webapp/data')
    sh('git checkout geoserver-geonode-ext/src/main/webapp/data')


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


def waitfor(url, timeout=300):
    started = False
    for a in xrange(timeout):
        try:
            resp = urllib.urlopen(url)
        except IOError, e:
            pass
        else:
            if resp.getcode() == 200:
                started = True
                break 
        time.sleep(1)
    return started


def justcopy(origin, target):
    if os.path.isdir(origin):
         shutil.rmtree(target, ignore_errors=True)
         shutil.copytree(origin, target)
    elif os.path.isfile(origin):
        if not os.path.exists(target):
            os.makedirs(target)
        shutil.copy(origin, target)
