# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import fileinput
import glob
import os
import re
import shutil
import subprocess
import signal
import sys
import time
import urllib
import urllib2
import zipfile
from urlparse import urlparse

import yaml
from paver.easy import (BuildFailure, call_task, cmdopts, info, needs, options,
                        path, sh, task)
from setuptools.command import easy_install

try:
    from geonode.settings import GEONODE_APPS
except BaseException:
    # probably trying to run install_win_deps.
    pass

try:
    from paver.path import pushd
except ImportError:
    from paver.easy import pushd

from geonode.settings import OGC_SERVER, INSTALLED_APPS

assert sys.version_info >= (2, 6), \
    SystemError("GeoNode Build requires python 2.6 or better")

dev_config = None
with open("dev_config.yml", 'r') as f:
    dev_config = yaml.load(f)


def grab(src, dest, name):
    download = True
    if not dest.exists():
        print 'Downloading %s' % name
    elif not zipfile.is_zipfile(dest):
        print 'Downloading %s (corrupt file)' % name
    else:
        download = False
    if download:
        if str(src).startswith("file://"):
            src2 = src[7:]
            if not os.path.exists(src2):
                print "Source location (%s) does not exist" % str(src2)
            else:
                print "Copying local file from %s" % str(src2)
                shutil.copyfile(str(src2), str(dest))
        else:
            urllib.urlretrieve(str(src), str(dest))


@task
@cmdopts([
    ('geoserver=', 'g', 'The location of the geoserver build (.war file).'),
    ('jetty=', 'j', 'The location of the Jetty Runner (.jar file).'),
])
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    # only start if using Geoserver backend
    if 'geonode.geoserver' not in INSTALLED_APPS:
        return

    download_dir = path('downloaded')
    if not download_dir.exists():
        download_dir.makedirs()

    geoserver_dir = path('geoserver')

    geoserver_bin = download_dir / \
        os.path.basename(dev_config['GEOSERVER_URL'])
    jetty_runner = download_dir / \
        os.path.basename(dev_config['JETTY_RUNNER_URL'])

    grab(
        options.get(
            'geoserver',
            dev_config['GEOSERVER_URL']),
        geoserver_bin,
        "geoserver binary")
    grab(
        options.get(
            'jetty',
            dev_config['JETTY_RUNNER_URL']),
        jetty_runner,
        "jetty runner")

    if not geoserver_dir.exists():
        geoserver_dir.makedirs()

        webapp_dir = geoserver_dir / 'geoserver'
        if not webapp_dir:
            webapp_dir.makedirs()

        print 'extracting geoserver'
        z = zipfile.ZipFile(geoserver_bin, "r")
        z.extractall(webapp_dir)

    _install_data_dir()


@task
def setup_qgis_server(options):
    """Prepare a testing instance of QGIS Server."""
    # only start if using QGIS Server backend
    if 'geonode.qgis_server' not in INSTALLED_APPS:
        return

    # QGIS Server testing instance run on top of docker
    try:
        sh('scripts/misc/docker_check.sh')
    except BaseException:
        info("You need to have docker and docker-compose installed.")
        return

    info('Docker and docker-compose were installed.')
    info('Proceeded to setup QGIS Server.')
    info('Create QGIS Server related folder.')

    try:
        os.makedirs('geonode/qgis_layer')
    except BaseException:
        pass

    try:
        os.makedirs('geonode/qgis_tiles')
    except BaseException:
        pass

    all_permission = 0o777
    os.chmod('geonode/qgis_layer', all_permission)
    stat = os.stat('geonode/qgis_layer')
    info('Mode : %o' % stat.st_mode)
    os.chmod('geonode/qgis_tiles', all_permission)
    stat = os.stat('geonode/qgis_tiles')
    info('Mode : %o' % stat.st_mode)

    info('QGIS Server related folder successfully setup.')


def _install_data_dir():
    target_data_dir = path('geoserver/data')
    if target_data_dir.exists():
        target_data_dir.rmtree()

    original_data_dir = path('geoserver/geoserver/data')
    justcopy(original_data_dir, target_data_dir)

    try:
        config = path(
            'geoserver/data/global.xml')
        with open(config) as f:
            xml = f.read()
            m = re.search('proxyBaseUrl>([^<]+)', xml)
            xml = xml[:m.start(1)] + \
                "http://localhost:8080/geoserver" + xml[m.end(1):]
            with open(config, 'w') as f:
                f.write(xml)
    except Exception as e:
        print(e)

    try:
        config = path(
            'geoserver/data/security/filter/geonode-oauth2/config.xml')
        with open(config) as f:
            xml = f.read()
            m = re.search('accessTokenUri>([^<]+)', xml)
            xml = xml[:m.start(1)] + \
                "http://localhost:8000/o/token/" + xml[m.end(1):]
            m = re.search('userAuthorizationUri>([^<]+)', xml)
            xml = xml[:m.start(
                1)] + "http://localhost:8000/o/authorize/" + xml[m.end(1):]
            m = re.search('redirectUri>([^<]+)', xml)
            xml = xml[:m.start(
                1)] + "http://localhost:8080/geoserver/index.html" + xml[m.end(1):]
            m = re.search('checkTokenEndpointUrl>([^<]+)', xml)
            xml = xml[:m.start(
                1)] + "http://localhost:8000/api/o/v4/tokeninfo/" + xml[m.end(1):]
            m = re.search('logoutUri>([^<]+)', xml)
            xml = xml[:m.start(
                1)] + "http://localhost:8000/account/logout/" + xml[m.end(1):]
            with open(config, 'w') as f:
                f.write(xml)
    except Exception as e:
        print(e)

    try:
        config = path(
            'geoserver/data/security/role/geonode REST role service/config.xml')
        with open(config) as f:
            xml = f.read()
            m = re.search('baseUrl>([^<]+)', xml)
            xml = xml[:m.start(1)] + "http://localhost:8000" + xml[m.end(1):]
            with open(config, 'w') as f:
                f.write(xml)
    except Exception as e:
        print(e)


@task
def static(options):
    with pushd('geonode/static'):
        sh('grunt production')


@task
@needs([
    'setup_geoserver',
    'setup_qgis_server',
])
def setup(options):
    """Get dependencies and prepare a GeoNode development environment."""

    updategeoip(options)
    info(('GeoNode development environment successfully set up.'
          'If you have not set up an administrative account,'
          ' please do so now. Use "paver start" to start up the server.'))


def grab_winfiles(url, dest, packagename):
    # Add headers
    headers = {'User-Agent': 'Mozilla 5.10'}
    request = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(request)
    with open(dest, 'wb') as writefile:
        writefile.write(response.read())


@task
def win_install_deps(options):
    """
    Install all Windows Binary automatically
    This can be removed as wheels become available for these packages
    """
    download_dir = path('downloaded').abspath()
    if not download_dir.exists():
        download_dir.makedirs()
    win_packages = {
        # required by transifex-client
        "Py2exe": dev_config['WINDOWS']['py2exe'],
        "Nose": dev_config['WINDOWS']['nose'],
        # the wheel 1.9.4 installs but pycsw wants 1.9.3, which fails to compile
        # when pycsw bumps their pyproj to 1.9.4 this can be removed.
        "PyProj": dev_config['WINDOWS']['pyproj'],
        "lXML": dev_config['WINDOWS']['lxml']
    }
    failed = False
    for package, url in win_packages.iteritems():
        tempfile = download_dir / os.path.basename(url)
        print "Installing file ... " + tempfile
        grab_winfiles(url, tempfile, package)
        try:
            easy_install.main([tempfile])
        except Exception as e:
            failed = True
            print "install failed with error: ", e
        os.remove(tempfile)
    if failed and sys.maxsize > 2**32:
        print "64bit architecture is not currently supported"
        print "try finding the 64 binaries for py2exe, nose, and pyproj"
    elif failed:
        print "install failed for py2exe, nose, and/or pyproj"
    else:
        print "Windows dependencies now complete.  Run pip install -e geonode --use-mirrors"


@cmdopts([
    ('version=', 'v', 'Legacy GeoNode version of the existing database.')
])
@task
def upgradedb(options):
    """
    Add 'fake' data migrations for existing tables from legacy GeoNode versions
    """
    version = options.get('version')
    if version in ['1.1', '1.2']:
        sh("python manage.py migrate maps 0001 --fake")
        sh("python manage.py migrate avatar 0001 --fake")
    elif version is None:
        print "Please specify your GeoNode version"
    else:
        print "Upgrades from version %s are not yet supported." % version


@task
def updategeoip(options):
    """
    Update geoip db
    """
    settings = options.get('settings', '')
    if settings:
        settings = 'DJANGO_SETTINGS_MODULE=%s' % settings

    sh("%s python manage.py updategeoip -o" % settings)


@task
@cmdopts([
    ('settings', 's', 'Specify custom DJANGO_SETTINGS_MODULE')
])
def sync(options):
    """
    Run the migrate and migrate management commands to create and migrate a DB
    """
    settings = options.get('settings', '')
    if settings:
        settings = 'DJANGO_SETTINGS_MODULE=%s' % settings

    sh("%s python manage.py makemigrations --noinput" % settings)
    sh("%s python manage.py migrate --noinput" % settings)
    sh("%s python manage.py loaddata sample_admin.json" % settings)
    sh("%s python manage.py loaddata geonode/base/fixtures/default_oauth_apps.json" % settings)
    sh("%s python manage.py loaddata geonode/base/fixtures/initial_data.json" % settings)


@task
def package(options):
    """
    Creates a tarball to use for building the system elsewhere
    """
    import tarfile
    import geonode

    version = geonode.get_version()
    # Use GeoNode's version for the package name.
    pkgname = 'GeoNode-%s-all' % version

    # Create the output directory.
    out_pkg = path(pkgname)
    out_pkg_tar = path("%s.tar.gz" % pkgname)

    # Create a distribution in zip format for the geonode python package.
    dist_dir = path('dist')
    dist_dir.rmtree()
    sh('python setup.py sdist --formats=zip')

    with pushd('package'):

        # Delete old tar files in that directory
        for f in glob.glob('GeoNode*.tar.gz'):
            old_package = path(f)
            if old_package != out_pkg_tar:
                old_package.remove()

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

        geonode_dist = path('..') / 'dist' / 'GeoNode-%s.zip' % version
        justcopy(geonode_dist, out_pkg)

        # Create a tar file with all files in the output package folder.
        tar = tarfile.open(out_pkg_tar, "w:gz")
        for file in out_pkg.walkfiles():
            tar.add(file)

        # Add the README with the license and important links to documentation.
        tar.add('README', arcname=('%s/README.rst' % out_pkg))
        tar.close()

        # Remove all the files in the temporary output package directory.
        out_pkg.rmtree()

    # Report the info about the new package.
    info("%s created" % out_pkg_tar.abspath())


@task
@needs(['start_geoserver',
        'start_qgis_server',
        'start_django'])
@cmdopts([
    ('bind=', 'b', 'Bind server to provided IP address and port number.'),
    ('java_path=', 'j', 'Full path to java install for Windows'),
    ('foreground', 'f', 'Do not run in background but in foreground'),
    ('settings', 's', 'Specify custom DJANGO_SETTINGS_MODULE')
], share_with=['start_django', 'start_geoserver'])
def start():
    """
    Start GeoNode (Django, GeoServer & Client)
    """
    call_task('start_messaging')

    info("GeoNode is now available.")


@task
def stop_django():
    """
    Stop the GeoNode Django application
    """
    kill('python', 'runserver')
    kill('python', 'runmessaging')


@task
def stop_geoserver():
    """
    Stop GeoServer
    """
    # only start if using Geoserver backend
    if 'geonode.geoserver' not in INSTALLED_APPS:
        return
    kill('java', 'geoserver')

    # Kill process.
    try:
        # proc = subprocess.Popen("ps -ef | grep -i -e '[j]ava\|geoserver' | awk '{print $2}'",
        proc = subprocess.Popen("ps -ef | grep -i -e 'geoserver' | awk '{print $2}'",
                                shell=True,
                                stdout=subprocess.PIPE)
        for pid in proc.stdout:
            info('Stopping geoserver (process number %s)' % int(pid))
            os.kill(int(pid), signal.SIGKILL)
            os.kill(int(pid), 9)
            sh('sleep 30')
            # Check if the process that we killed is alive.
            try:
               os.kill(int(pid), 0)
               # raise Exception("""wasn't able to kill the process\nHINT:use signal.SIGKILL or signal.SIGABORT""")
            except OSError as ex:
               continue
    except Exception as e:
        info(e)


@task
@cmdopts([
    ('qgis_server_port=', 'p', 'The port of the QGIS Server instance.')
])
def stop_qgis_server():
    """
    Stop QGIS Server Backend.
    """
    # only start if using QGIS Server backend
    if 'geonode.qgis_server' not in INSTALLED_APPS:
        return
    port = options.get('qgis_server_port', '9000')

    sh(
        'docker-compose -f docker-compose-qgis-server.yml down',
        env={
            'GEONODE_PROJECT_PATH': os.getcwd(),
            'QGIS_SERVER_PORT': port
        })


@task
@needs([
    'stop_geoserver',
    'stop_qgis_server'
])
def stop():
    """
    Stop GeoNode
    """
    # windows needs to stop the geoserver first b/c we can't tell which python
    # is running, so we kill everything
    info("Stopping GeoNode ...")
    stop_django()


@cmdopts([
    ('bind=', 'b', 'Bind server to provided IP address and port number.')
])
@task
def start_django():
    """
    Start the GeoNode Django application
    """
    settings = options.get('settings', '')
    if settings:
        settings = 'DJANGO_SETTINGS_MODULE=%s' % settings
    bind = options.get('bind', '0.0.0.0:8000')
    foreground = '' if options.get('foreground', False) else '&'
    sh('%s python manage.py runserver %s %s' % (settings, bind, foreground))


def start_messaging():
    """
    Start the GeoNode messaging server
    """
    settings = options.get('settings', '')
    if settings:
        settings = 'DJANGO_SETTINGS_MODULE=%s' % settings
    foreground = '' if options.get('foreground', False) else '&'
    sh('%s python manage.py runmessaging %s' % (settings, foreground))


@cmdopts([
    ('java_path=', 'j', 'Full path to java install for Windows')
])
@task
def start_geoserver(options):
    """
    Start GeoServer with GeoNode extensions
    """
    # only start if using Geoserver backend
    if 'geonode.geoserver' not in INSTALLED_APPS:
        return

    GEOSERVER_BASE_URL = OGC_SERVER['default']['LOCATION']
    url = GEOSERVER_BASE_URL

    if urlparse(GEOSERVER_BASE_URL).hostname != 'localhost':
        print "Warning: OGC_SERVER['default']['LOCATION'] hostname is not equal to 'localhost'"

    if not GEOSERVER_BASE_URL.endswith('/'):
        print "Error: OGC_SERVER['default']['LOCATION'] does not end with a '/'"
        sys.exit(1)

    download_dir = path('downloaded').abspath()
    jetty_runner = download_dir / \
        os.path.basename(dev_config['JETTY_RUNNER_URL'])
    data_dir = path('geoserver/data').abspath()
    geofence_dir = path('geoserver/data/geofence').abspath()
    web_app = path('geoserver/geoserver').abspath()
    log_file = path('geoserver/jetty.log').abspath()
    config = path('scripts/misc/jetty-runner.xml').abspath()
    jetty_port = urlparse(GEOSERVER_BASE_URL).port

    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_free = True
    try:
        s.bind(("127.0.0.1", jetty_port))
    except socket.error as e:
        socket_free = False
        if e.errno == 98:
            info('Port %s is already in use' % jetty_port)
        else:
            info('Something else raised the socket.error exception while checking port %s' % jetty_port)
            print(e)
    finally:
        s.close()

    if socket_free:
        # @todo - we should not have set workdir to the datadir but a bug in geoserver
        # prevents geonode security from initializing correctly otherwise
        with pushd(data_dir):
            javapath = "java"
            loggernullpath = os.devnull

            # checking if our loggernullpath exists and if not, reset it to
            # something manageable
            if loggernullpath == "nul":
                try:
                    open("../../downloaded/null.txt", 'w+').close()
                except IOError as e:
                    print "Chances are that you have Geoserver currently running.  You \
                            can either stop all servers with paver stop or start only \
                            the django application with paver start_django."
                    sys.exit(1)
                loggernullpath = "../../downloaded/null.txt"

            try:
                sh(('java -version'))
            except BaseException:
                print "Java was not found in your path.  Trying some other options: "
                javapath_opt = None
                if os.environ.get('JAVA_HOME', None):
                    print "Using the JAVA_HOME environment variable"
                    javapath_opt = os.path.join(os.path.abspath(
                        os.environ['JAVA_HOME']), "bin", "java.exe")
                elif options.get('java_path'):
                    javapath_opt = options.get('java_path')
                else:
                    print "Paver cannot find java in the Windows Environment.  \
                    Please provide the --java_path flag with your full path to \
                    java.exe e.g. --java_path=C:/path/to/java/bin/java.exe"
                    sys.exit(1)
                # if there are spaces
                javapath = 'START /B "" "' + javapath_opt + '"'

            sh((
                '%(javapath)s -Xms512m -Xmx1024m -server -XX:+UseConcMarkSweepGC -XX:MaxPermSize=256m'
                ' -DGEOSERVER_DATA_DIR=%(data_dir)s'
                ' -Dgeofence.dir=%(geofence_dir)s'
                # ' -Dgeofence-ovr=geofence-datasource-ovr.properties'
                # workaround for JAI sealed jar issue and jetty classloader
                # ' -Dorg.eclipse.jetty.server.webapp.parentLoaderPriority=true'
                ' -jar %(jetty_runner)s'
                ' --port %(jetty_port)i'
                ' --log %(log_file)s'
                ' %(config)s'
                ' > %(loggernullpath)s &' % locals()
            ))

        info('Starting GeoServer on %s' % url)

    # wait for GeoServer to start
    started = waitfor(url)
    info('The logs are available at %s' % log_file)

    if not started:
        # If applications did not start in time we will give the user a chance
        # to inspect them and stop them manually.
        info(('GeoServer never started properly or timed out.'
              'It may still be running in the background.'))
        sys.exit(1)


@task
@cmdopts([
    ('qgis_server_port=', 'p', 'The port of the QGIS Server instance.')
])
def start_qgis_server():
    """Start QGIS Server instance with GeoNode related plugins."""
    # only start if using QGIS Serrver backend
    if 'geonode.qgis_server' not in INSTALLED_APPS:
        return
    info('Starting up QGIS Server...')

    port = options.get('qgis_server_port', '9000')

    sh(
        'docker-compose -f docker-compose-qgis-server.yml up -d qgis-server',
        env={
            'GEONODE_PROJECT_PATH': os.getcwd(),
            'QGIS_SERVER_PORT': port
        })
    info('QGIS Server is up.')


@task
def test(options):
    """
    Run GeoNode's Unit Test Suite
    """
    sh("%s manage.py test %s.tests --noinput" % (options.get('prefix'),
                                                 '.tests '.join(GEONODE_APPS)))


@task
def test_javascript(options):
    with pushd('geonode/static/geonode'):
        sh('./run-tests.sh')


@task
@cmdopts([
    ('name=', 'n', 'Run specific tests.'),
    ('settings', 's', 'Specify custom DJANGO_SETTINGS_MODULE')
])
def test_integration(options):
    """
    Run GeoNode's Integration test suite against the external apps
    """
    call_task('stop_geoserver')
    _reset()
    # Start GeoServer
    call_task('start_geoserver')
    info("GeoNode is now available, running the tests now.")

    name = options.get('name', 'geonode.tests.integration')
    settings = options.get('settings', '')
    if not settings and name == 'geonode.upload.tests.integration':
        settings = 'geonode.upload.tests.test_settings'

    success = False
    try:
        if name == 'geonode.tests.csw':
            call_task('sync', options={'settings': settings})
            call_task('start', options={'settings': settings})
            sh('sleep 30')
            call_task('setup_data', options={'settings': settings})

        settings = 'DJANGO_SETTINGS_MODULE=%s' % settings if settings else ''

        if name == 'geonode.upload.tests.integration':
            sh("%s python manage.py makemigrations --noinput" % settings)
            sh("%s python manage.py migrate --noinput" % settings)
            sh("%s python manage.py loaddata sample_admin.json" % settings)
            sh("%s python manage.py loaddata geonode/base/fixtures/default_oauth_apps.json" % settings)
            sh("%s python manage.py loaddata geonode/base/fixtures/initial_data.json" % settings)
            call_task('start_geoserver')
            bind = options.get('bind', '0.0.0.0:8000')
            foreground = '' if options.get('foreground', False) else '&'
            sh('%s python manage.py runmessaging %s' % (settings, foreground))
            sh('%s python manage.py runserver %s %s' % (settings, bind, foreground))
            sh('sleep 30')
            settings = 'REUSE_DB=1 %s' % settings

        sh(('%s python manage.py test %s'
            ' --noinput --liveserver=0.0.0.0:8000' % (settings, name)))

    except BuildFailure as e:
        info('Tests failed! %s' % str(e))
    else:
        success = True
    finally:
        # don't use call task here - it won't run since it already has
        stop()

    call_task('stop_geoserver')
    _reset()
    if not success:
        sys.exit(1)


@task
@cmdopts([
    ('coverage', 'c', 'use this flag to generate coverage during test runs')
])
def run_tests(options):
    """
    Executes the entire test suite.
    """
    if options.get('coverage'):
        prefix = 'coverage run --branch --source=geonode'
    else:
        prefix = 'python'
    sh('%s manage.py test geonode.tests.smoke' % prefix)
    call_task('test', options={'prefix': prefix})
    call_task('test_integration')
    call_task('test_integration', options={'name': 'geonode.tests.csw'})

    # only start if using Geoserver backend
    if 'geonode.geoserver' in INSTALLED_APPS:
        call_task('test_integration',
                  options={'name': 'geonode.upload.tests.integration',
                           'settings': 'geonode.upload.tests.test_settings'})

    sh('flake8 geonode')


@task
@needs(['stop'])
def reset():
    """
    Reset a development environment (Database, GeoServer & Catalogue)
    """
    _reset()


def _reset():
    sh("rm -rf geonode/development.db")
    sh("rm -rf geonode/uploaded/*")
    _install_data_dir()


@needs(['reset'])
def reset_hard():
    """
    Reset a development environment (Database, GeoServer & Catalogue)
    """
    sh("git clean -dxf")


@task
@cmdopts([
    ('type=', 't', 'Import specific data type ("vector", "raster", "time")'),
    ('settings', 's', 'Specify custom DJANGO_SETTINGS_MODULE')
])
def setup_data():
    """
    Import sample data (from gisdata package) into GeoNode
    """
    import gisdata

    ctype = options.get('type', None)

    data_dir = gisdata.GOOD_DATA

    if ctype in ['vector', 'raster', 'time']:
        data_dir = os.path.join(gisdata.GOOD_DATA, ctype)

    settings = options.get('settings', '')
    if settings:
        settings = 'DJANGO_SETTINGS_MODULE=%s' % settings

    sh("%s python manage.py importlayers %s -v2" % (settings, data_dir))


@needs(['package'])
@cmdopts([
    ('key=', 'k', 'The GPG key to sign the package'),
    ('ppa=', 'p', 'PPA this package should be published to.'),
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

    version, simple_version = versions()

    info('Creating package for GeoNode version %s' % version)

    # Get rid of any uncommitted changes to debian/changelog
    info('Getting rid of any uncommitted changes in debian/changelog')
    sh('git checkout package/debian/changelog')

    # Workaround for git-dch bug
    # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=594580
    sh('ln -s %s %s' % (os.path.realpath('.git'), os.path.realpath('package')))

    with pushd('package'):

        # Install requirements
        # sh('sudo apt-get -y install debhelper devscripts git-buildpackage')

        sh(('git-dch --spawn-editor=snapshot --git-author --new-version=%s'
            ' --id-length=6 --ignore-branch --release' % (simple_version)))
        # In case you publish from Ubuntu Xenial (git-dch is removed from upstream)
        #  use the following line instead:
        # sh(('gbp dch --spawn-editor=snapshot --git-author --new-version=%s'
        #    ' --id-length=6 --ignore-branch --release' % (simple_version)))

        deb_changelog = path('debian') / 'changelog'
        for line in fileinput.input([deb_changelog], inplace=True):
            print line.replace("urgency=medium", "urgency=high"),

        # Revert workaround for git-dhc bug
        sh('rm -rf .git')

        if key is None and ppa is None:
            # A local installable package
            sh('debuild -uc -us -A')
        elif key is None and ppa is not None:
                # A sources package, signed by daemon
            sh('debuild -S')
        elif key is not None and ppa is None:
            # A signed installable package
            sh('debuild -k%s -A' % key)
        elif key is not None and ppa is not None:
            # A signed, source package
            sh('debuild -k%s -S' % key)

    if ppa is not None:
        sh('dput ppa:%s geonode_%s_source.changes' % (ppa, simple_version))


@task
def publish():
    if 'GPG_KEY_GEONODE' in os.environ:
        key = os.environ['GPG_KEY_GEONODE']
    else:
        print "You need to set the GPG_KEY_GEONODE environment variable"
        return

    call_task('deb', options={
        'key': key,
        'ppa': 'geonode/testing',
    })

    version, simple_version = versions()
    sh('git add package/debian/changelog')
    sh('git commit -m "Updated changelog for version %s"' % version)
    sh('git tag %s' % version)
    sh('git push origin %s' % version)
    sh('git tag debian/%s' % simple_version)
    sh('git push origin debian/%s' % simple_version)
    sh('git push origin master')
    sh('python setup.py sdist upload -r pypi')


def versions():
    import geonode
    from geonode.version import get_git_changeset
    raw_version = geonode.__version__
    version = geonode.get_version()
    timestamp = get_git_changeset()

    major, minor, revision, stage, edition = raw_version

    branch = 'dev'

    if stage == 'final':
        stage = 'thefinal'

    if stage == 'unstable':
        tail = '%s%s' % (branch, timestamp)
    else:
        tail = '%s%s' % (stage, edition)

    simple_version = '%s.%s.%s+%s' % (major, minor, revision, tail)
    return version, simple_version


def kill(arg1, arg2):
    """Stops a proces that contains arg1 and is filtered by arg2
    """
    from subprocess import Popen, PIPE

    # Wait until ready
    t0 = time.time()
    # Wait no more than these many seconds
    time_out = 30
    running = True

    while running and time.time() - t0 < time_out:
        if os.name == 'nt':
            p = Popen('tasklist | find "%s"' % arg1, shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)
        else:
            p = Popen('ps aux | grep %s' % arg1, shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

        lines = p.stdout.readlines()

        running = False
        for line in lines:
            # this kills all java.exe and python including self in windows
            if ('%s' %
                arg2 in line) or (os.name == 'nt' and '%s' %
                                  arg1 in line):
                running = True

                # Get pid
                fields = line.strip().split()

                info('Stopping %s (process number %s)' % (arg1, fields[1]))
                if os.name == 'nt':
                    kill = 'taskkill /F /PID "%s"' % fields[1]
                else:
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
        except IOError:
            pass
        else:
            if resp.getcode() == 200:
                started = True
                break
        time.sleep(1)
    return started


def _copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def justcopy(origin, target):
    if os.path.isdir(origin):
        shutil.rmtree(target, ignore_errors=True)
        _copytree(origin, target)
    elif os.path.isfile(origin):
        if not os.path.exists(target):
            os.makedirs(target)
        shutil.copy(origin, target)
