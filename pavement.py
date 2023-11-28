#########################################################################
#
# Copyright (C) 2018 OSGeo
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
import pytz
import logging
import datetime
from dateutil.parser import parse as parsedate

from urllib.parse import urlparse
from urllib.request import urlopen, Request

import zipfile
from tqdm import tqdm
import requests
import math
import psutil

import yaml
from paver.easy import (
    BuildFailure,
    call_task,
    cmdopts,
    info,
    needs,
    path,
    sh,
    task,
)
from setuptools.command import easy_install

try:
    from paver.path import pushd
except ImportError:
    from paver.easy import pushd

from geonode.settings import (
    on_travis,
    core_tests,
    internal_apps_tests,
    integration_tests,
    integration_server_tests,
    integration_upload_tests,
    integration_monitoring_tests,
    integration_csw_tests,
    integration_bdd_tests,
    INSTALLED_APPS,
    GEONODE_CORE_APPS,
    GEONODE_INTERNAL_APPS,
    GEONODE_APPS,
    OGC_SERVER,
    ASYNC_SIGNALS,
    MONITORING_ENABLED,
    CELERY_BEAT_SCHEDULER,
)

try:
    from geonode.settings import TEST_RUNNER_KEEPDB, TEST_RUNNER_PARALLEL

    _keepdb = "--keepdb" if TEST_RUNNER_KEEPDB else ""
    _parallel = f"--parallel={TEST_RUNNER_PARALLEL}" if TEST_RUNNER_PARALLEL else ""
except Exception:
    _keepdb = ""
    _parallel = ""

assert sys.version_info >= (2, 6), SystemError("GeoNode Build requires python 2.6 or better")

dev_config = None
with open("dev_config.yml") as f:
    dev_config = yaml.load(f, Loader=yaml.Loader)


logger = logging.getLogger(__name__)


def grab(src, dest, name):
    src, dest, name = map(str, (src, dest, name))
    logger.info(f" src, dest, name --> {src} {dest} {name}")

    if not os.path.exists(dest):
        logger.info(f"Downloading {name}")
    elif not zipfile.is_zipfile(dest):
        logger.info(f"Downloading {name} (corrupt file)")
    elif not src.startswith("file://"):
        r = requests.head(src)
        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(dest))
        url_time = file_time
        for _k in ["last-modified", "Date"]:
            if _k in r.headers:
                url_time = r.headers[_k]
        url_date = parsedate(url_time)
        utc = pytz.utc
        url_date = url_date.replace(tzinfo=utc)
        file_time = file_time.replace(tzinfo=utc)
        if url_date < file_time:
            # Do not download if older than the local one
            return
        logger.info(f"Downloading updated {name}")

    # Local file does not exist or remote one is newer
    if src.startswith("file://"):
        src2 = src.replace("file://", "")
        if not os.path.exists(src2):
            logger.info(f"Source location ({src2}) does not exist")
        else:
            logger.info(f"Copying local file from {src2}")
            shutil.copyfile(src2, dest)
    else:
        # urlretrieve(str(src), str(dest))
        # Streaming, so we can iterate over the response.
        r = requests.get(src, stream=True, timeout=10, verify=False)
        # Total size in bytes.
        total_size = int(r.headers.get("content-length", 0))
        logger.info(f"Requesting {src}")
        block_size = 1024
        wrote = 0
        with open("output.bin", "wb") as f:
            for data in tqdm(
                r.iter_content(block_size), total=math.ceil(total_size // block_size), unit="KB", unit_scale=False
            ):
                wrote += len(data)
                f.write(data)
        logger.info(f" total_size [{total_size}] / wrote [{wrote}] ")
        if total_size != 0 and wrote != total_size:
            logger.error(
                f"ERROR, something went wrong. Data could not be written. Expected to write {wrote} but wrote {total_size} instead"
            )
        else:
            shutil.move("output.bin", dest)
        try:
            # Cleaning up
            os.remove("output.bin")
        except OSError:
            pass


@task
@cmdopts(
    [
        ("geoserver=", "g", "The location of the geoserver build (.war file)."),
        ("jetty=", "j", "The location of the Jetty Runner (.jar file)."),
        ("force_exec=", "", "Force GeoServer Setup."),
    ]
)
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    # only start if using Geoserver backend
    if "geonode.geoserver" not in INSTALLED_APPS:
        return
    if on_travis and not options.get("force_exec", False):
        """Will make use of the docker container for the Integration Tests"""
        return
    else:
        download_dir = path("downloaded")
        if not download_dir.exists():
            download_dir.makedirs()
        geoserver_dir = path("geoserver")
        geoserver_bin = download_dir / os.path.basename(urlparse(dev_config["GEOSERVER_URL"]).path)
        jetty_runner = download_dir / os.path.basename(urlparse(dev_config["JETTY_RUNNER_URL"]).path)
        geoserver_data = download_dir / os.path.basename(urlparse(dev_config["DATA_DIR_URL"]).path)
        grab(options.get("geoserver", dev_config["GEOSERVER_URL"]), geoserver_bin, "geoserver binary")
        grab(options.get("jetty", dev_config["JETTY_RUNNER_URL"]), jetty_runner, "jetty runner")
        grab(options.get("geoserver data", dev_config["DATA_DIR_URL"]), geoserver_data, "geoserver data-dir")

        if not geoserver_dir.exists():
            geoserver_dir.makedirs()

            webapp_dir = geoserver_dir / "geoserver"
            if not webapp_dir:
                webapp_dir.makedirs()

            logger.info("extracting geoserver")
            z = zipfile.ZipFile(geoserver_bin, "r")
            z.extractall(webapp_dir)

            logger.info("extracting geoserver data dir")
            z = zipfile.ZipFile(geoserver_data, "r")
            z.extractall(geoserver_dir)

        _configure_data_dir()


def _configure_data_dir():
    try:
        config = path("geoserver/data/global.xml")
        with open(config) as f:
            xml = f.read()
            m = re.search("proxyBaseUrl>([^<]+)", xml)
            xml = f"{xml[:m.start(1)]}http://localhost:8080/geoserver{xml[m.end(1):]}"
            with open(config, "w") as f:
                f.write(xml)
    except Exception as e:
        print(e)

    try:
        config = path("geoserver/data/security/filter/geonode-oauth2/config.xml")
        with open(config) as f:
            xml = f.read()
            m = re.search("accessTokenUri>([^<]+)", xml)
            xml = f"{xml[:m.start(1)]}http://localhost:8000/o/token/{xml[m.end(1):]}"
            m = re.search("userAuthorizationUri>([^<]+)", xml)
            xml = f"{xml[:m.start(1)]}http://localhost:8000/o/authorize/{xml[m.end(1):]}"
            m = re.search("redirectUri>([^<]+)", xml)
            xml = f"{xml[:m.start(1)]}http://localhost:8080/geoserver/index.html{xml[m.end(1):]}"
            m = re.search("checkTokenEndpointUrl>([^<]+)", xml)
            xml = f"{xml[:m.start(1)]}http://localhost:8000/api/o/v4/tokeninfo/{xml[m.end(1):]}"
            m = re.search("logoutUri>([^<]+)", xml)
            xml = f"{xml[:m.start(1)]}http://localhost:8000/account/logout/{xml[m.end(1):]}"
            with open(config, "w") as f:
                f.write(xml)
    except Exception as e:
        print(e)

    try:
        config = path("geoserver/data/security/role/geonode REST role service/config.xml")
        with open(config) as f:
            xml = f.read()
            m = re.search("baseUrl>([^<]+)", xml)
            xml = f"{xml[:m.start(1)]}http://localhost:8000{xml[m.end(1):]}"
            with open(config, "w") as f:
                f.write(xml)
    except Exception as e:
        print(e)


@task
def static(options):
    with pushd("geonode/static"):
        sh("grunt production")


@task
@needs(
    [
        "setup_geoserver",
    ]
)
def setup(options):
    """Get dependencies and prepare a GeoNode development environment."""
    info(
        "GeoNode development environment successfully set up."
        "If you have not set up an administrative account,"
        ' please do so now. Use "paver start" to start up the server.'
    )


def grab_winfiles(url, dest, packagename):
    # Add headers
    headers = {"User-Agent": "Mozilla 5.10"}
    request = Request(url, None, headers)
    response = urlopen(request)
    with open(dest, "wb") as writefile:
        writefile.write(response.read())


@task
def win_install_deps(options):
    """
    Install all Windows Binary automatically
    This can be removed as wheels become available for these packages
    """
    download_dir = path("downloaded").abspath()
    if not download_dir.exists():
        download_dir.makedirs()
    win_packages = {
        # required by transifex-client
        "Py2exe": dev_config["WINDOWS"]["py2exe"],
        # the wheel 1.9.4 installs but pycsw wants 1.9.3, which fails to compile
        # when pycsw bumps their pyproj to 1.9.4 this can be removed.
        "PyProj": dev_config["WINDOWS"]["pyproj"],
        "lXML": dev_config["WINDOWS"]["lxml"],
    }
    failed = False
    for package, url in win_packages.items():
        tempfile = download_dir / os.path.basename(url)
        logger.info(f"Installing file ... {tempfile}")
        grab_winfiles(url, tempfile, package)
        try:
            easy_install.main([tempfile])
        except Exception as e:
            failed = True
            logger.error("install failed with error: ", e)
        os.remove(tempfile)
    if failed and sys.maxsize > 2**32:
        logger.error("64bit architecture is not currently supported")
        logger.error("try finding the 64 binaries for py2exe, and pyproj")
    elif failed:
        logger.error("install failed for py2exe, and/or pyproj")
    else:
        print("Windows dependencies now complete.  Run pip install -e geonode --use-mirrors")


@task
@cmdopts([("version=", "v", "Legacy GeoNode version of the existing database.")])
def upgradedb(options):
    """
    Add 'fake' data migrations for existing tables from legacy GeoNode versions
    """
    version = options.get("version")
    if version in {"1.1", "1.2"}:
        sh("python -W ignore manage.py migrate maps 0001 --fake")
        sh("python -W ignore manage.py migrate avatar 0001 --fake")
    elif version is None:
        print("Please specify your GeoNode version")
    else:
        print(f"Upgrades from version {version} are not yet supported.")


@task
@cmdopts([("settings=", "s", "Specify custom DJANGO_SETTINGS_MODULE")])
def sync(options):
    """
    Run the migrate and migrate management commands to create and migrate a DB
    """
    settings = options.get("settings", "")
    if settings and "DJANGO_SETTINGS_MODULE" not in settings:
        settings = f"DJANGO_SETTINGS_MODULE={settings}"

    sh(f"{settings} python -W ignore manage.py makemigrations --noinput")
    sh(f"{settings} python -W ignore manage.py migrate --noinput")
    sh(f"{settings} python -W ignore manage.py loaddata sample_admin.json")
    sh(f"{settings} python -W ignore manage.py loaddata geonode/base/fixtures/default_oauth_apps.json")
    sh(f"{settings} python -W ignore manage.py loaddata geonode/base/fixtures/initial_data.json")
    sh(f"{settings} python -W ignore manage.py set_all_datasets_alternate")
    sh(f"{settings} python -W ignore manage.py collectstatic --noinput")


@task
def package(options):
    """
    Creates a tarball to use for building the system elsewhere
    """
    import tarfile
    import geonode

    version = geonode.get_version()
    # Use GeoNode's version for the package name.
    pkgname = f"GeoNode-{version}-all"

    # Create the output directory.
    out_pkg = path(pkgname)
    out_pkg_tar = path(f"{pkgname}.tar.gz")

    # Create a distribution in zip format for the geonode python package.
    dist_dir = path("dist")
    dist_dir.rmtree()
    sh("python setup.py sdist --formats=zip")

    with pushd("package"):
        # Delete old tar files in that directory
        for f in glob.glob("GeoNode*.tar.gz"):
            old_package = path(f)
            if old_package != out_pkg_tar:
                old_package.remove()

        if out_pkg_tar.exists():
            info(f"There is already a package for version {version}")
            return

        # Clean anything that is in the oupout package tree.
        out_pkg.rmtree()
        out_pkg.makedirs()

        support_folder = path("support")
        install_file = path("install.sh")

        # And copy the default files from the package folder.
        justcopy(support_folder, out_pkg / "support")
        justcopy(install_file, out_pkg)

        geonode_dist = path("..") / "dist" / f"GeoNode-{version}.zip"
        justcopy(geonode_dist, out_pkg)

        # Create a tar file with all files in the output package folder.
        tar = tarfile.open(out_pkg_tar, "w:gz")
        for file in out_pkg.walkfiles():
            tar.add(file)

        # Add the README with the license and important links to documentation.
        tar.add("README", arcname=f"{out_pkg}/README.rst")
        tar.close()

        # Remove all the files in the temporary output package directory.
        out_pkg.rmtree()

    # Report the info about the new package.
    info(f"{out_pkg_tar.abspath()} created")


@task
@needs(["start_geoserver", "start_django"])
@cmdopts(
    [
        ("bind=", "b", "Bind server to provided IP address and port number."),
        ("java_path=", "j", "Full path to java install for Windows"),
        ("foreground", "f", "Do not run in background but in foreground"),
        ("settings=", "s", "Specify custom DJANGO_SETTINGS_MODULE"),
    ],
    share_with=["start_django", "start_geoserver"],
)
def start(options):
    """
    Start GeoNode (Django, GeoServer & Client)
    """
    info("GeoNode is now available.")


@task
def stop_django(options):
    """
    Stop the GeoNode Django application
    """
    if ASYNC_SIGNALS:
        kill("python", "celery")
        kill("celery", "worker")
    kill("python", "runserver")
    kill("python", "runmessaging")


@task
@cmdopts([("force_exec=", "", "Force GeoServer Stop.")])
def stop_geoserver(options):
    """
    Stop GeoServer
    """
    # we use docker-compose for integration tests
    if on_travis and not options.get("force_exec", False):
        return

    # only start if using Geoserver backend
    if "geonode.geoserver" not in INSTALLED_APPS:
        return
    kill("java", "geoserver")

    # Kill process.
    try:
        # proc = subprocess.Popen("ps -ef | grep -i -e '[j]ava\|geoserver' |
        # awk '{print $2}'",
        proc = subprocess.Popen(
            "ps -ef | grep -i -e 'geoserver' | awk '{print $2}'", shell=True, stdout=subprocess.PIPE
        )
        for pid in map(int, proc.stdout):
            info(f"Stopping geoserver (process number {pid})")
            os.kill(pid, signal.SIGKILL)

            # Check if the process that we killed is alive.
            killed, alive = psutil.wait_procs([psutil.Process(pid=pid)], timeout=30)
            for p in alive:
                p.kill()
    except Exception as e:
        info(e)


@task
@needs(
    [
        "stop_geoserver",
    ]
)
def stop(options):
    """
    Stop GeoNode
    """
    # windows needs to stop the geoserver first b/c we can't tell which python
    # is running, so we kill everything
    info("Stopping GeoNode ...")
    stop_django(options)


@task
@cmdopts([("bind=", "b", "Bind server to provided IP address and port number.")])
def start_django(options):
    """
    Start the GeoNode Django application
    """
    settings = options.get("settings", "")
    if settings and "DJANGO_SETTINGS_MODULE" not in settings:
        settings = f"DJANGO_SETTINGS_MODULE={settings}"
    bind = options.get("bind", "0.0.0.0:8000")
    port = bind.split(":")[1]
    foreground = "" if options.get("foreground", False) else "&"
    sh(f"{settings} python -W ignore manage.py runserver {bind} {foreground}")

    if ASYNC_SIGNALS:
        sh(
            f"{settings} celery -A geonode.celery_app:app worker --autoscale=20,10 --without-gossip --without-mingle -Ofair -B -E \
            --statedb=/tmp/worker.state --scheduler={CELERY_BEAT_SCHEDULER} --loglevel=DEBUG \
            --concurrency=10 --max-tasks-per-child=10 -n worker1@%h -f celery.log {foreground}"
        )
        sh(f"{settings} python -W ignore manage.py runmessaging {foreground}")

    # wait for Django to start
    started = waitfor(f"http://localhost:{port}")
    if not started:
        info("Django never started properly or timed out.")
        sys.exit(1)


@task
def start_messaging(options):
    """
    Start the GeoNode messaging server
    """
    settings = options.get("settings", "")
    if settings and "DJANGO_SETTINGS_MODULE" not in settings:
        settings = f"DJANGO_SETTINGS_MODULE={settings}"
    foreground = "" if options.get("foreground", False) else "&"
    sh(f"{settings} python -W ignore manage.py runmessaging {foreground}")


@task
@cmdopts([("java_path=", "j", "Full path to java install for Windows"), ("force_exec=", "", "Force GeoServer Start.")])
def start_geoserver(options):
    """
    Start GeoServer with GeoNode extensions
    """
    # we use docker-compose for integration tests
    if on_travis and not options.get("force_exec", False):
        return

    # only start if using Geoserver backend
    if "geonode.geoserver" not in INSTALLED_APPS:
        return

    GEOSERVER_BASE_URL = OGC_SERVER["default"]["LOCATION"]
    url = GEOSERVER_BASE_URL

    if urlparse(GEOSERVER_BASE_URL).hostname != "localhost":
        logger.warning("Warning: OGC_SERVER['default']['LOCATION'] hostname is not equal to 'localhost'")

    if not GEOSERVER_BASE_URL.endswith("/"):
        logger.error("Error: OGC_SERVER['default']['LOCATION'] does not end with a '/'")
        sys.exit(1)

    download_dir = path("downloaded").abspath()
    jetty_runner = download_dir / os.path.basename(dev_config["JETTY_RUNNER_URL"])
    data_dir = path("geoserver/data").abspath()
    geofence_dir = path("geoserver/data/geofence").abspath()
    web_app = path("geoserver/geoserver").abspath()
    log_file = path("geoserver/jetty.log").abspath()
    config = path("scripts/misc/jetty-runner.xml").abspath()
    jetty_port = urlparse(GEOSERVER_BASE_URL).port

    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_free = True
    try:
        s.bind(("127.0.0.1", jetty_port))
    except OSError as e:
        socket_free = False
        if e.errno == 98:
            info(f"Port {jetty_port} is already in use")
        else:
            info(f"Something else raised the socket.error exception while checking port {jetty_port}")
            print(e)
    finally:
        s.close()

    if socket_free:
        # @todo - we should not have set workdir to the datadir but a bug in geoserver
        # prevents geonode security from initializing correctly otherwise
        with pushd(data_dir):
            javapath = "java"
            if on_travis:
                sh(
                    "sudo apt install -y openjdk-8-jre openjdk-8-jdk;"
                    " sudo update-java-alternatives --set java-1.8.0-openjdk-amd64;"
                    ' export JAVA_HOME=$(readlink -f /usr/bin/java | sed "s:bin/java::");'
                    " export PATH=$JAVA_HOME'bin/java':$PATH;"
                )
                # import subprocess
                # result = subprocess.run(['update-alternatives', '--list', 'java'], stdout=subprocess.PIPE)
                # javapath = result.stdout
                javapath = "/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java"
            loggernullpath = os.devnull

            # checking if our loggernullpath exists and if not, reset it to
            # something manageable
            if loggernullpath == "nul":
                try:
                    open("../../downloaded/null.txt", "w+").close()
                except OSError:
                    print(
                        "Chances are that you have Geoserver currently running. You "
                        "can either stop all servers with paver stop or start only "
                        "the django application with paver start_django."
                    )
                    sys.exit(1)
                loggernullpath = "../../downloaded/null.txt"

            try:
                sh(("%(javapath)s -version") % locals())
            except Exception:
                logger.warning("Java was not found in your path.  Trying some other options: ")
                javapath_opt = None
                if os.environ.get("JAVA_HOME", None):
                    logger.info("Using the JAVA_HOME environment variable")
                    javapath_opt = os.path.join(os.path.abspath(os.environ["JAVA_HOME"]), "bin", "java.exe")
                elif options.get("java_path"):
                    javapath_opt = options.get("java_path")
                else:
                    logger.critical(
                        "Paver cannot find java in the Windows Environment. "
                        "Please provide the --java_path flag with your full path to "
                        "java.exe e.g. --java_path=C:/path/to/java/bin/java.exe"
                    )
                    sys.exit(1)
                # if there are spaces
                javapath = f'START /B "" "{javapath_opt}"'

            sh(
                "%(javapath)s -Xms512m -Xmx2048m -server -Dgwc.context.suffix=gwc -XX:+UseConcMarkSweepGC -XX:MaxPermSize=512m"
                " -DGEOSERVER_DATA_DIR=%(data_dir)s"
                " -DGEOSERVER_CSRF_DISABLED=true"
                " -Dgeofence.dir=%(geofence_dir)s"
                " -Djava.awt.headless=true"
                # ' -Dgeofence-ovr=geofence-datasource-ovr.properties'
                # workaround for JAI sealed jar issue and jetty classloader
                # ' -Dorg.eclipse.jetty.server.webapp.parentLoaderPriority=true'
                " -jar %(jetty_runner)s"
                " --port %(jetty_port)i"
                " --log %(log_file)s"
                " %(config)s"
                " > %(loggernullpath)s &" % locals()
            )

        info(f"Starting GeoServer on {url}")

    # wait for GeoServer to start
    started = waitfor(url)
    info(f"The logs are available at {log_file}")

    if not started:
        # If applications did not start in time we will give the user a chance
        # to inspect them and stop them manually.
        info("GeoServer never started properly or timed out." "It may still be running in the background.")
        sys.exit(1)


@task
def test(options):
    """
    Run GeoNode's Unit Test Suite
    """
    if on_travis:
        if core_tests:
            _apps = GEONODE_CORE_APPS
        if internal_apps_tests:
            _apps = GEONODE_INTERNAL_APPS
    else:
        _apps = GEONODE_APPS

    _apps_to_test = []
    for _app in _apps:
        if _app and len(_app) > 0 and "geonode" in _app:
            _apps_to_test.append(_app)
    if MONITORING_ENABLED and "geonode.monitoring" in INSTALLED_APPS and "geonode.monitoring" not in _apps_to_test:
        _apps_to_test.append("geonode.monitoring")
    sh(
        f"{options.get('prefix')} manage.py test geonode.tests.smoke \
{('.tests '.join(_apps_to_test))}.tests --noinput {_keepdb} {_parallel}"
    )


@task
@cmdopts([("local=", "l", "Set to True if running bdd tests locally")])
def test_bdd(options):
    """
    Run GeoNode's BDD Test Suite
    """
    local = str2bool(options.get("local", "false"))
    if local:
        call_task("reset_hard")

    call_task("setup")
    call_task("sync")
    if local:
        sh("sleep 30")

    info("GeoNode is now available, running the bdd tests now.")
    sh("py.test")


@task
def test_javascript(options):
    with pushd("geonode/static/geonode"):
        sh("./run-tests.sh")


@task
@cmdopts(
    [
        ("name=", "n", "Run specific tests."),
        ("settings=", "s", "Specify custom DJANGO_SETTINGS_MODULE"),
        ("local=", "l", "Set to True if running bdd tests locally"),
    ]
)
def test_integration(options):
    """
    Run GeoNode's Integration test suite against the external apps
    """
    prefix = options.get("prefix")
    local = str2bool(options.get("local", "false"))
    if local:
        call_task("stop_geoserver")
        _reset()

    name = options.get("name", None)
    settings = options.get("settings", "")
    success = False
    try:
        call_task("setup", options={"settings": settings, "force_exec": True})

        if not settings:
            settings = "REUSE_DB=1 DJANGO_SETTINGS_MODULE=geonode.settings"

        if name and name in ("geonode.tests.csw", "geonode.tests.integration", "geonode.geoserver.tests.integration"):
            call_task("sync", options={"settings": settings})
            if local:
                call_task("start_geoserver", options={"settings": settings, "force_exec": True})
                call_task("start", options={"settings": settings})
            if integration_server_tests:
                call_task("setup_data", options={"settings": settings})
        elif "geonode.geoserver" in INSTALLED_APPS:
            if local:
                sh("cp geonode/upload/tests/test_settings.py geonode/")
                settings = "geonode.test_settings"
                sh(f"DJANGO_SETTINGS_MODULE={settings} python -W ignore manage.py " "makemigrations --noinput")
                sh(f"DJANGO_SETTINGS_MODULE={settings} python -W ignore manage.py " "migrate --noinput")
                sh(f"DJANGO_SETTINGS_MODULE={settings} python -W ignore manage.py " "loaddata sample_admin.json")
                sh(
                    f"DJANGO_SETTINGS_MODULE={settings} python -W ignore manage.py "
                    "loaddata geonode/base/fixtures/default_oauth_apps.json"
                )
                sh(
                    f"DJANGO_SETTINGS_MODULE={settings} python -W ignore manage.py "
                    "loaddata geonode/base/fixtures/initial_data.json"
                )
                call_task("start_geoserver")
                bind = options.get("bind", "0.0.0.0:8000")
                foreground = "" if options.get("foreground", False) else "&"
                sh(f"DJANGO_SETTINGS_MODULE={settings} python -W ignore manage.py runmessaging {foreground}")
                sh(f"DJANGO_SETTINGS_MODULE={settings} python -W ignore manage.py runserver {bind} {foreground}")
                sh("sleep 30")
                settings = f"REUSE_DB=1 DJANGO_SETTINGS_MODULE={settings}"
            else:
                call_task("sync", options={"settings": settings})

        live_server_option = ""
        info("Running the tests now...")
        sh(f"{settings} {prefix} manage.py test {name} -v 3 {_keepdb} --noinput {live_server_option}")

    except BuildFailure as e:
        info(f"Tests failed! {str(e)}")
    else:
        success = True
    finally:
        if local:
            stop(options)
            _reset()

    if not success:
        sys.exit(1)


@task
@needs(
    [
        "start_geoserver",
    ]
)
@cmdopts(
    [
        ("coverage", "c", "use this flag to generate coverage during test runs"),
        ("local=", "l", "Set to True if running tests locally"),
    ]
)
def run_tests(options):
    """
    Executes the entire test suite.
    """
    if options.get("coverage"):
        prefix = 'coverage run --branch --source=geonode \
--omit="*/__init__*,*/test*,*/wsgi*,*/version*,*/migrations*,\
*/search_indexes*,*/management/*,*/context_processors*,*/upload/*"'
    else:
        prefix = "python"
    local = options.get("local", "false")  # travis uses default to false

    if not integration_tests and not integration_csw_tests and not integration_bdd_tests:
        call_task("test", options={"prefix": prefix})
    elif integration_tests:
        if integration_upload_tests:
            call_task(
                "test_integration",
                options={"prefix": prefix, "name": "geonode.upload.tests.integration", "local": local},
            )
        elif integration_monitoring_tests:
            call_task(
                "test_integration",
                options={"prefix": prefix, "name": "geonode.monitoring.tests.integration", "local": local},
            )
        elif integration_csw_tests:
            call_task("test_integration", options={"prefix": prefix, "name": "geonode.tests.csw", "local": local})
        elif integration_bdd_tests:
            call_task("test_bdd", options={"local": local})
        elif integration_server_tests:
            call_task(
                "test_integration",
                options={"prefix": prefix, "name": "geonode.geoserver.tests.integration", "local": local},
            )
        else:
            call_task(
                "test_integration", options={"prefix": prefix, "name": "geonode.tests.integration", "local": local}
            )
    sh("flake8 geonode")


@task
@needs(["stop"])
def reset(options):
    """
    Reset a development environment (Database, GeoServer & Catalogue)
    """
    _reset()


def _reset():
    from geonode import settings

    path = os.path.join(settings.PROJECT_ROOT, "development.db")
    sh(f"rm -rf {path}")
    sh("rm -rf geonode/development.db")
    sh("rm -rf geonode/uploaded/*")
    _configure_data_dir()


@needs(["reset"])
def reset_hard(options):
    """
    Reset a development environment (Database, GeoServer & Catalogue)
    """
    sh("git clean -dxf")


@task
@cmdopts(
    [
        ("type=", "t", 'Import specific data type ("vector", "raster", "time")'),
        ("settings=", "s", "Specify custom DJANGO_SETTINGS_MODULE"),
    ]
)
def setup_data(options):
    """
    Import sample data (from gisdata package) into GeoNode
    """
    import gisdata

    ctype = options.get("type", None)

    data_dir = gisdata.GOOD_DATA

    if ctype in {"vector", "raster", "time"}:
        data_dir = os.path.join(gisdata.GOOD_DATA, ctype)

    settings = options.get("settings", "")
    if settings and "DJANGO_SETTINGS_MODULE" not in settings:
        settings = f"DJANGO_SETTINGS_MODULE={settings}"

    from geonode import settings as geonode_settings

    if not os.path.exists(geonode_settings.MEDIA_ROOT):
        info("media root not available, creating...")
        os.makedirs(geonode_settings.MEDIA_ROOT, exist_ok=True)

    sh(f"{settings} python -W ignore manage.py importlayers -v2 -hh {geonode_settings.SITEURL} {data_dir}")


@needs(["package"])
@cmdopts(
    [
        ("key=", "k", "The GPG key to sign the package"),
        ("ppa=", "p", "PPA this package should be published to."),
    ]
)
def deb(options):
    """
    Creates debian packages.

    Example uses:
        paver deb
        paver deb -k 12345
        paver deb -k 12345 -p geonode/testing
    """
    key = options.get("key", None)
    ppa = options.get("ppa", None)

    version, simple_version = versions()

    info(f"Creating package for GeoNode version {version}")

    # Get rid of any uncommitted changes to debian/changelog
    info("Getting rid of any uncommitted changes in debian/changelog")
    sh("git checkout package/debian/changelog")

    # Workaround for git-dch bug
    # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=594580
    sh(f"rm -rf {os.path.realpath('package')}/.git")
    sh(f"ln -s {os.path.realpath('.git')} {os.path.realpath('package')}")

    with pushd("package"):
        # Install requirements
        # sh('sudo apt-get -y install debhelper devscripts git-buildpackage')

        # sh(('git-dch --spawn-editor=snapshot --git-author --new-version=%s'
        #     ' --id-length=6 --ignore-branch --release' % (simple_version)))
        # In case you publish from Ubuntu Xenial (git-dch is removed from upstream)
        #  use the following line instead:
        # sh(('gbp dch --spawn-editor=snapshot --git-author --new-version=%s'
        #    ' --id-length=6 --ignore-branch --release' % (simple_version)))
        distribution = "bionic"
        # sh(('gbp dch --distribution=%s --force-distribution --spawn-editor=snapshot --git-author --new-version=%s'
        #    ' --id-length=6 --ignore-branch --release' % (distribution, simple_version)))

        deb_changelog = path("debian") / "changelog"
        for idx, line in enumerate(fileinput.input([deb_changelog], inplace=True)):
            if idx == 0:
                logger.info(f"geonode ({simple_version}) {distribution}; urgency=high", end="")
            else:
                print(line.replace("urgency=medium", "urgency=high"), end="")

        # Revert workaround for git-dhc bug
        sh("rm -rf .git")

        if key is None and ppa is None:
            print("A local installable package")
            sh("debuild -uc -us -A")
        elif key is None and ppa is not None:
            print("A sources package, signed by daemon")
            sh("debuild -S")
        elif key is not None and ppa is None:
            print("A signed installable package")
            sh(f"debuild -k{key} -A")
        elif key is not None and ppa is not None:
            print("A signed, source package")
            sh(f"debuild -k{key} -S")

    if ppa is not None:
        sh(f"dput ppa:{ppa} geonode_{simple_version}_source.changes")


@task
def publish(options):
    if "GPG_KEY_GEONODE" in os.environ:
        key = os.environ["GPG_KEY_GEONODE"]
    else:
        print("You need to set the GPG_KEY_GEONODE environment variable")
        return

    if "PPA_GEONODE" in os.environ:
        ppa = os.environ["PPA_GEONODE"]
    else:
        ppa = None

    call_task(
        "deb",
        options={
            "key": key,
            "ppa": ppa,
            # 'ppa': 'geonode/testing',
            # 'ppa': 'geonode/unstable',
        },
    )

    version, simple_version = versions()
    if ppa:
        sh("git add package/debian/changelog")
        sh(f'git commit -m "Updated changelog for version {version}"')
        sh(f"git tag -f {version}")
        sh(f"git push origin {version}")
        sh(f"git tag -f debian/{simple_version}")
        sh(f"git push origin debian/{simple_version}")
        # sh('git push origin master')
        sh("python setup.py sdist upload -r pypi")


def versions():
    import geonode
    from geonode.version import get_git_changeset

    raw_version = geonode.__version__
    version = geonode.get_version()
    timestamp = get_git_changeset()

    major, minor, revision, stage, edition = raw_version

    branch = "dev"

    if stage == "final":
        stage = "thefinal"

    if stage == "unstable":
        tail = f"{branch}{timestamp}"
    else:
        tail = f"{stage}{edition}"

    simple_version = f"{major}.{minor}.{revision}+{tail}"
    return version, simple_version


def kill(arg1, arg2):
    """Stops a proces that contains arg1 and is filtered by arg2"""
    from subprocess import Popen, PIPE

    # Wait until ready
    t0 = time.time()
    # Wait no more than these many seconds
    time_out = 30
    running = True

    while running and time.time() - t0 < time_out:
        if os.name == "nt":
            p = Popen(f'tasklist | find "{arg1}"', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)
        else:
            p = Popen(f"ps aux | grep {arg1}", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

        lines = p.stdout.readlines()

        running = False
        for line in lines:
            # this kills all java.exe and python including self in windows
            if (f"{arg2}" in str(line)) or (os.name == "nt" and f"{arg1}" in str(line)):
                running = True

                # Get pid
                fields = line.strip().split()

                info(f"Stopping {arg1} (process number {int(fields[1])})")
                if os.name == "nt":
                    kill = f'taskkill /F /PID "{int(fields[1])}"'
                else:
                    kill = f"kill -9 {int(fields[1])} 2> /dev/null"
                os.system(kill)

        # Give it a little more time
        time.sleep(1)

    if running:
        _procs = "\n".join([str(_l).strip() for _l in lines])
        raise Exception(f"Could not stop {arg1}: " f"Running processes are\n{_procs}")


def waitfor(url, timeout=300):
    started = False
    for a in range(timeout):
        try:
            resp = urlopen(url)
        except OSError:
            pass
        else:
            if resp.getcode() == 200:
                started = True
                break
        time.sleep(1)
    return started


def _copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            try:
                shutil.copytree(s, d, symlinks, ignore)
            except Exception:
                pass
        elif os.path.isfile(s):
            shutil.copy2(s, d)


def justcopy(origin, target):
    if os.path.isdir(origin):
        shutil.rmtree(target, ignore_errors=True)
        _copytree(origin, target)
    elif os.path.isfile(origin):
        if not os.path.exists(target):
            os.makedirs(target, exist_ok=True)
        shutil.copy(origin, target)


def str2bool(v):
    if v and len(v) > 0:
        return v.lower() in ("yes", "true", "t", "1")
    else:
        return False
