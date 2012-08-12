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
import urllib

from paver.easy import task, options, cmdopts, needs
from paver.easy import path, sh, pushd, info, call_task


assert sys.version_info >= (2,6,2), \
       SystemError("GeoNode Build requires python 2.6.2 or better")


def grab(src, dest):
    urllib.urlretrieve(str(src), str(dest))

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
def setup_client(options):
    """
    Fetch geonode-client
    """
    sh('git submodule update --init')
    here = os.path.abspath('.')
    static = path(here) / 'geonode' / 'static' / 'geonode'
    scripts_path = path(static) / 'script'

    if not scripts_path.exists():
        scripts_path.makedirs()
    
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
        origin = path('geonode-client') / o
        target = path(static) / t
        justcopy(origin, target)

@task
@needs([
    'setup_geoserver',
    'setup_client',
])
def setup(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
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
    import pkg_resources
    import tarfile
    import geonode

    version = geonode.get_version()
    # Use GeoNode's version for the package name.
    pkgname = 'GeoNode-%s-all' % version

    # Create the output directory.
    out_pkg = path(pkgname)
    out_pkg_tar = path("%s.tar.gz" % pkgname)

    # Create a distribution in zip format for the geonode python package.
    sh('python setup.py sdist --format=zip')

    with pushd('package'):
        if out_pkg_tar.exists():
            info('There is already a package for version %s' % version)
            return

        # Clean anything that is in the oupout package tree.
        out_pkg.rmtree()
        out_pkg.makedirs()

        support_folder = path('support')
        install_file = path('install.sh')

        # And copy the default files from the package folder.
        justcopy(support_folder, out_pkg / 'support')
        justcopy(install_file, out_pkg)


        # Package Geoserver's war.
        geoserver_target = path('../geoserver-geonode-ext/target/geoserver.war')
        geoserver_target.copy(out_pkg)

        # Package (Python, Django) web application and dependencies.
        # Bundle all the dependencies in a zip-lib package called a pybundle.
        bundle = out_pkg / 'geonode-webapp.pybundle'
        geonode_dist = path('..') / 'dist' / 'GeoNode-%s.zip' % version
        sh('pip bundle %s %s' % (bundle, geonode_dist))

        # Create a tar file with all the information in the output package folder.
        tar = tarfile.open(out_pkg_tar, "w:gz")
        for file in out_pkg.walkfiles():
            tar.add(file)

        # Add the README with the license and important links to documentation.
        tar.add('README', arcname=('%s/README.rst' % out_pkg))
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
    info("GeoNode is now available.")


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
    info("Stopping GeoNode ...")
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
    Start GeoServer with GeoNode extensions
    """

    from geonode.settings import GEOSERVER_BASE_URL

    with pushd('geoserver-geonode-ext'):
        sh('MAVEN_OPTS="-Xmx512m -XX:MaxPermSize=256m" mvn jetty:run > /dev/null &')
 
    info('Starting GeoServer on %s' % GEOSERVER_BASE_URL)
    # wait for GeoServer to start
    started = waitfor(GEOSERVER_BASE_URL)
    if not started:
        # If applications did not start in time we will give the user a chance
        # to inspect them and stop them manually.
        info("GeoServer never started properly or timed out. It may still be running in the background.")
        info("The logs are available at geoserver-geonode-ext/jetty.log")
        sys.exit(1)
 


@task
def test(options):
    """
    Run GeoNode's Unit Test Suite
    """
    sh("python manage.py test geonode --noinput")


@task
def test_integration(options):
    """
    Run GeoNode's Integration test suite against the external apps
    """
    _reset()
    # Start GeoServer
    call_task('start_geoserver') 
    info("GeoNode is now available, running the tests now.")

    success = False
    try:
        sh('python manage.py test geonode.tests.integration --noinput --liveserver=localhost:8000')
    except BuildFailure, e:
        info('Tests failed! %s' % str(e))
    else:
        success = True
    finally:
        # don't use call task here - it won't run since it already has
        stop_django()
        stop_geoserver()

    _reset()
    if not success:
        sys.exit(1)


@task
@needs(['stop'])
def reset():
    """
    Reset a development environment (Database, GeoServer & Catalogue)
    """
    _reset()

def _reset():
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
    sh("python manage.py importlayers %s -v2" % data_dir)

@needs(['package'])
@cmdopts([
  ('key=', 'k', 'The GPG key to sign the package'),
  ('ppa=', 'p', 'The name of the PPA where this package should be published to.'),
])
def deb(options):
    """
    Creates debian packages.

    Example uses:
        paver deb
        paver deb -k 12345
        paver deb -k 12345 -p geonode/testing
    """
    key = options.get('key', None)
    ppa = options.get('ppa', None)
    branch = options.get('branch', 'dev')

    import geonode
    from geonode.version import get_git_changeset
    raw_version = geonode.__version__
    version = geonode.get_version()
    timestamp = get_git_changeset()

    major, minor, revision, stage, edition = raw_version

    if stage == 'alpha' and edition == 0:
        tail = 'dev%s' % timestamp
    else:
        tail = '%s%s' % (stage, edition)

    simple_version = '%s.%s.%s+%s' % (major, minor, revision, tail)

    info('Creating package for GeoNode version %s' % version)

    with pushd('package'):
        # Get rid of any uncommitted changes to debian/changelog
        info('Getting rid of any uncommitted changes in debian/changelog')
        sh('git checkout debian/changelog')

        # Workaround for git-dhc bug
        # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=594580
        path('.git').makedirs()

        sh('git-dch --git-author --new-version=%s --id-length=6 --debian-branch=%s' % (simple_version, branch))

        # Rever workaround for git-dhc bug
        path('.git').rmtree()


        sh('sudo apt-get -y install debhelper devscripts git-buildpackage')

        if key is None:
            sh('debuild -uc -us -A')
        else:
            if ppa is None:
                sh('debuild -k%s -A' % key)
            else:
                sh('debuild -k%s -S' % key)
                sh('dput ppa:%s geonode_*.sources' % ppa)


def kill(arg1, arg2):
    """Stops a proces that contains arg1 and is filtered by arg2
    """
    from subprocess import Popen, PIPE

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

                info('Stopping %s (process number %s)' % (arg1, fields[1]))
                kill = 'kill -9 %s 2> /dev/null' % fields[1]
                os.system(kill)

        # Give it a little more time
        time.sleep(1)
    else:
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
    import shutil
    if os.path.isdir(origin):
         shutil.rmtree(target, ignore_errors=True)
         shutil.copytree(origin, target)
    elif os.path.isfile(origin):
        if not os.path.exists(target):
            os.makedirs(target)
        shutil.copy(origin, target)
