from __future__ import with_statement
from paver import svn
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
from shutil import move, copy
import zipfile
import tarfile
import urllib
from urllib import urlretrieve
import glob

assert sys.version_info >= (2,6), \
    SystemError("GeoNode Build requires python 2.6 or better")


options(
    config=Bunch(
        ini=path('shared/build.ini'),
        package_dir = path('shared/package')
    ),
    minilib=Bunch(extra_files=['virtual', 'doctools', 'misctasks']),
    sphinx=Bunch(
        docroot='docs',
        builddir="_build",
        sourcedir="source"
    ),
    virtualenv=Bunch(
        packages_to_install=[
            'pip',
            'jstools',
            'virtualenv'
        ],
        dest_dir='./',
        install_paver=True,
        script_name='bootstrap.py',
        paver_command_line='post_bootstrap'
    ),
    deploy=Bunch(
        req_file=path('shared/package/requirements.txt'),
        packages_to_install=['pip'],
        dest_dir='./',
        ),
    host=Bunch(
        bind='localhost'
    )
)

venv = os.environ.get('VIRTUAL_ENV')
bundle = path('shared/geonode.pybundle')
dl_cache = "--download-cache=./build"
dlname = 'geonode.bundle'

geoserver_target = path('webapps/geoserver.war')
geoserver_zip="geoserver.war"
geoserver_war_url = "http://worldmap.harvard.edu/media/geoserver/"

gs_data = "webapps/gs-data"
gs_data_url="http://worldmap.harvard.edu/media/geoserver/geonode-geoserver-data.zip"

def geonode_client_target(): return options.deploy.out_dir / "geonode-client.zip"
geonode_client_target_war = path('webapps/geonode-client.war')

deploy_req_txt = """
# NOTE... this file is generated
-r %s/shared/requirements.txt
-e %s/src/GeoNodePy
""" % (os.getcwd(), os.getcwd())

@task
def auto(options):
    cp = ConfigParser.ConfigParser()
    cp.read(options.config.ini)
    options.config.parser = cp

    # set a few vars from the config ns
    package_dir = options.deploy.out_dir = options.config.package_dir
    options.deploy.script_name=package_dir / 'bootstrap.py'

    # set windows dependent opts
    platform_options(options)

@task
def fix_geos_version(options):
    import fileinput
    oldline = "ver = geos_version()"
    newline = "ver = geos_version().decode().split(' ')[0]"
    for line in fileinput.input(path(os.environ['VIRTUAL_ENV']) / 'lib/python2.7/site-packages/django/contrib/gis/geos/libgeos.py', inplace=True):
        if oldline in line and newline not in line:
            line = line.replace(oldline,newline)
        print line,


@task
def install_deps(options):
    """Installs all the python deps from a requirements file"""
    if bundle.exists():
        info('using to install python deps bundle')
        call_task('install_bundle')
    else:
        info('Installing from requirements file. ' \
             'Use "paver bundle_deps" to create an install bundle')
        pip_install("-r shared/%s" % options.config.corelibs)
        pip_install("-r shared/%s" % options.config.devlibs)
        pip_install('-e %s' %(path(".")))
        if options.config.platform == "win32":
            info("You will need to install 'PIL' and 'ReportLab' " \
                 "separately to do PDF generation")

@task
def bundle_deps(options):
    """
    Create a pybundle of all python dependencies.  If created, this
    will be the default for installing python deps.
    """
    pip_bundle("-r shared/requirements.txt %s" % bundle)


@task
@needs(['download_bundle'])
def install_bundle(options):
    """
    Installs a bundle of dependencies located at %s.
    """ % bundle

    info('install the bundle')
    pip_install(bundle)


@task
def download_bundle(options):
    """
    Downloads zipped bundle of python dependencies to %s. Does not overwrite.
    """ % bundle

    bpath = bundle.abspath()
    if not bundle.exists():
        with pushd('shared'):
            grab("http://dev.capra.opengeo.org/repo/%s.zip" % dlname, bpath)
    else:
        info("Skipping download. 'rm bundle  %s' if you need a fresh download. " % bundle)


@task
def install_25_deps(options):
    """Fetch python 2_5-specific dependencies (not maintained)"""
    pass


@task
@needs(['install_deps'])
def post_bootstrap(options):
    """installs the current package"""
    pip = "pip"
    sh('%s install -e %s' %(pip, path("src/GeoNodePy")))


#TODO Move svn urls out to a config file

def grab(src, dest):
    urlretrieve(str(src), str(dest))

@task
def setup_gs_data(options):
    """Fetch a data directory to use with GeoServer for testing."""
    src_url = str(options.config.parser.get('geoserver', 'gs_data_url'))
    shared = path("./shared")
    if not shared.exists():
        shared.mkdir()

    dst_url = shared / "geonode-geoserver-data.zip"
    grab(src_url, dst_url)

    if getattr(options, 'clean', False): path(gs_data).rmtree()
    if not path(gs_data).exists(): unzip_file(dst_url, gs_data)


@task
@needs(['setup_gs_data'])
def setup_geoserver(options):
    war_zip_file = geoserver_zip
    src_url = str(geoserver_war_url + war_zip_file)
    info("geoserver url: %s" %src_url)
    # where to download the war files. If changed change also
    # src/geoserver-geonode-ext/jetty.xml accordingly

    webapps = path("./webapps")
    if not webapps.exists():
        webapps.mkdir()

    dst_url = webapps / war_zip_file
    dst_war = webapps / "geoserver.war"
    deployed_url = webapps / "geoserver"

    if getattr(options, 'clean', False):
        deployed_url.rmtree()

    if not dst_war.exists():
        info("getting geoserver.war")
        grab(src_url, dst_url)
        zip_extractall(zipfile.ZipFile(dst_url), webapps)
    if not deployed_url.exists():
        zip_extractall(zipfile.ZipFile(dst_war), deployed_url)

@task
def setup_geonetwork(options):
    """Fetch the geonetwork.war and intermap.war to use with GeoServer for testing."""
    war_zip_file = options.config.parser.get('geonetwork', 'geonetwork_zip')
    src_url = str(options.config.parser.get('geonetwork', 'geonetwork_war_url') +  war_zip_file)
    info("geonetwork url: %s" %src_url)
    # where to download the war files. If changed change also
    # src/geoserver-geonode-ext/jetty.xml accordingly

    webapps = path("./webapps")
    if not webapps.exists():
        webapps.mkdir()

    dst_url = webapps / war_zip_file
    dst_war = webapps / "geonetwork.war"
    deployed_url = webapps / "geonetwork"

    if getattr(options, 'clean', False):
        deployed_url.rmtree()

    if not dst_war.exists():
        info("getting geonetwork.war")
        grab(src_url, dst_url)
        zip_extractall(zipfile.ZipFile(dst_url), webapps)
    if not deployed_url.exists():
        zip_extractall(zipfile.ZipFile(dst_war), deployed_url)

    src_url = str(options.config.parser.get('geonetwork', 'intermap_war_url'))
    dst_url = webapps / "intermap.war"

    if not dst_url.exists():
        grab(src_url, dst_url)

@task
@needs([
    'setup_geoserver',
    'setup_geonetwork',
    'setup_geonode_client'
])
def setup_webapps(options):
    pass


@task
@needs([
    'install_deps',
    'fix_geos_version',
    'setup_webapps',
    'sync_django_db',
    'package_client'
])
def build(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    info("""GeoNode development environment successfully set up.\nIf you have not set up an administrative account, please do so now.\nUse "paver host" to start up the server.""")


@task
@needs([
    'install_deps',
    'setup_geonode_client',
    'sync_django_db',
    'package_client'
])
def fastbuild(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    info("""GeoNode development environment successfully set up minus GeoServer and Geonetwork.\nIf you have not set up an administrative account, please do so now.\nUse "paver host" to start up the server.""")


@task
def setup_geonode_client(options):
    """
    Fetch geonode-client
    """
    static = path("./geonode/static/geonode")
    if not static.exists():
        static.mkdir()

    sh("git submodule update --init")

    with pushd("src/geonode-client/"):
        sh("ant clean zip")

    src_zip = "src/geonode-client/build/geonode-client.zip"
    zip_extractall(zipfile.ZipFile(src_zip), static)


@task
def sync_django_db(options):
    sh("django-admin.py syncdb --settings=geonode.settings --noinput")
    try:
        from geonode import settings
        if settings.USE_GAZETTEER and settings.GAZETTEER_DB_ALIAS:
            sh("django-admin.py syncdb --database=%s --settings=geonode.settings --noinput" % settings.GAZETTEER_DB_ALIAS)
            sh("django-admin.py migrate gazetteer --database=%s --settings=geonode.settings --noinput" % settings.GAZETTEER_DB_ALIAS)
    except Exception as e:
        info("""
******CREATION OF GAZETTEER TABLE FAILED - if you want the gazetteer data saved
in the geodata store database instead of the default database, unescape the
DATABASE_ROUTERS and GAZETTEER_DB_ALIAS settings in your settings file
and modify the default values if necessary - but re-escape them before
running unit tests""")
    sh("django-admin.py migrate --settings=geonode.settings --noinput")


@task
def package_dir(options):
    """
    Adds a packaging directory
    """
    if not options.deploy.out_dir.exists():
        options.config.package_dir.mkdir()


@task
@needs('package_dir', 'setup_geonode_client')
@cmdopts([
    ('use_war', 'w', 'Use a war to deploy geonode-client')
])
def package_client(options):
    """Package compressed client resources (JavaScript, CSS, images)."""

    if(hasattr(options, 'use_war')):
        geonode_client_target_war.copy(options.deploy.out_dir)
    else:
        # Extract static files to static_location
        geonode_media_dir = path("./geonode/media")
        static_location = geonode_media_dir / "static"

        dst_zip = "src/geonode-client/build/geonode-client.zip"

        zip_extractall(zipfile.ZipFile(dst_zip), static_location)
        os.remove(dst_zip)

@task
@needs('package_dir', 'setup_geoserver')
def package_geoserver(options):
    """Package GeoServer WAR file with appropriate extensions."""
    geoserver_target.copy(options.deploy.out_dir)


@task
@needs('package_dir', 'setup_geonetwork')
def package_geonetwork(options):
    """Package GeoNetwork WAR file for deployment."""
    geonetwork_target.copy(options.deploy.out_dir)


@task
@needs('package_dir')
def package_webapp(options):

    sh("django-admin.py collectstatic -v0 --settings=geonode.settings --noinput")

    """Package (Python, Django) web application and dependencies."""
    sh('python setup.py egg_info sdist')

    req_file = path(os.getcwd()) / options.deploy.req_file
    req_file.write_text(deploy_req_txt)
    pip_bundle("-r %s %s/geonode-webapp.pybundle" % (req_file, path(os.getcwd()) / options.deploy.out_dir))


@task
@needs(
    'build',
    'package_geoserver',
    'package_geonetwork',
    'package_webapp',
    'package_bootstrap'
)
def package_all(options):
    info('all is packaged, ready to deploy')


def create_version_name():
    # we'll use the geonodepy version as our "official" version number
    # for now
    slug = "GeoNode-%s" % (
        pkg_resources.get_distribution('GeoNodePy').version,
        date.today().isoformat()
    )

    return slug

@task
def make_devkit(options):
    import virtualenv

    (path("package") / "devkit" / "share").makedirs()
    pip_bundle("package/devkit/share/geonode-core.pybundle -r shared/devkit.requirements")
    script = virtualenv.create_bootstrap_script("""
import os, subprocess, zipfile

def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'

    installer_base = os.path.abspath(os.path.dirname(__file__))

    def pip(*args):
        subprocess.call([os.path.join(home_dir, bin, "pip")] + list(args))

    pip("install", os.path.join(installer_base, "share", "geonode-core.pybundle"))
    setup_jetty(source=os.path.join(installer_base, "share"), dest=os.path.join(home_dir, "share"))

def setup_jetty(source, dest):
    jetty_zip = os.path.join(source, "jetty-distribution-7.0.2.v20100331.zip")
    jetty_dir = os.path.join(dest, "jetty-distribution-7.0.2.v20100331")

    zipfile.ZipFile(jetty_zip).extractall(dest)
    shutil.rmtree(os.path.join(jetty_dir, "contexts"))
    shutil.rmtree(os.path.join(jetty_dir, "webapps"))
    os.mkdir(os.path.join(jetty_dir, "contexts"))
    os.mkdir(os.path.join(jetty_dir, "webapps"))

    deployments = [
        ('geoserver', 'geoserver-geonode-dev.war'),
        ('geonetwork', 'geonetwork.war'),
        ('media', 'geonode-client.zip')
    ]

    for context, archive in deployments:
        src = os.path.join(source, archive)
        dst = os.path.join(jetty_dir, "webapps", context)
        zipfile.ZipFile(src).extractall(dst)
""")

    open((path("package")/"devkit"/"go-geonode.py"), 'w').write(script)
    urlretrieve(
        "http://download.eclipse.org/jetty/7.0.2.v20100331/dist/jetty-distribution-7.0.2.v20100331.zip",
        "package/devkit/share/jetty-distribution-7.0.2.v20100331.zip"
    )
    urlretrieve(
        "http://pypi.python.org/packages/source/p/pip/pip-0.7.1.tar.gz",
        "package/devkit/share/pip-0.7.1.tar.gz"
    )
    geoserver_target.copy("package/devkit/share")
    geonetwork_target.copy("package/devkit/share")
    geonode_client_target().copy("package/devkit/share")

@task
@cmdopts([
    ('name=', 'n', 'Release number or name'),
    ('no_svn', 'D', 'Do not append svn version number as part of name '),
    ('append_to=', 'a', 'append to release name'),
    ('skip_packaging', 'y', 'Do not call package_all when creating a release'),
    ])
def make_release(options):
    """
    Creates a tarball to use for building the system elsewhere
    (production, distribution, etc)
    """

    if not hasattr(options, 'skip_packaging'):
        call_task("package_all")
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
def checkup_spec(options):
    parser = options.config.parser
    svn.checkup(parser.get('doc', 'spec_url'), path('docs') / 'spec')


def pip(*args):
    try:
        pkg_resources.require('pip>=0.6')
    except :
        error("**ATTENTION**: Update your 'pip' to at least 0.6")
        raise

    full_path_pip =  'pip'

    sh("%(env)s %(cmd)s %(args)s" % {
        "env": options.config.pip_flags,
        "cmd": full_path_pip,
        "args": " ".join(args)
    })

pip_install = functools.partial(pip, 'install', dl_cache)
pip_bundle = functools.partial(pip, 'bundle', dl_cache)


@task
@needs('package_dir')
def package_bootstrap(options):
    """Create a bootstrap script for deployment"""

    try:
        from paver.virtual import bootstrap
        options.virtualenv = options.deploy
        call_task("paver.virtual.bootstrap")
    except ImportError, e:
        info("VirtualEnv must be installed to enable 'paver bootstrap'. If you " +
             "need this command, run: pip install virtualenv")


@task
def install_sphinx_conditionally(options):
    """if no sphinx, install it"""
    try:
        import sphinx
    except ImportError:
        sh("%s install sphinx" % ('pip'))

        # have to reload doctools so it will realize sphinx is now
        # available
        sys.modules['paver.doctools'] = reload(sys.modules['paver.doctools'])

@task
@needs('package_client')
@cmdopts([
    ('bind=', 'b', 'IP address to bind to. Default is localhost.')
])
def start_django(options):
    djangolog = open("django.log", "w")
    django = subprocess.Popen([
                                  "paster",
                                  "serve",
                                  "--reload",
                                  "shared/dev-paste.ini"
                              ],
                              stdout=djangolog,
                              stderr=djangolog
    )

    def django_is_up():
        try:
            urllib.urlopen("http://" + options.host.bind + ":8000")
            return True
        except Exception, e:
            return False

    socket.setdefaulttimeout(1)

    info("Django is starting up, please wait...")
    while not django_is_up():
        time.sleep(2)

    try:
        info("Django/Worldmap is running at http://" + options.host.bind + ":8000/")
        info("Press CTRL-C to shut down")
        django.wait()
        info("Django process terminated, see log for details.")
    finally:
        info("Shutting down...")
        try:
            django.terminate()
        except:
            pass

        django.wait()
        sys.exit()

@task
@cmdopts([
    ('bind=', 'b', 'IP address to bind to. Default is localhost.')
])
def start_geoserver(options):
    jettylog = open("jetty.log", "w")
    from geonode import settings

    url = "http://localhost:8080/geoserver/"
    if settings.GEOSERVER_BASE_URL != url:
        print 'your GEOSERVER_BASE_URL does not match %s' % url
        sys.exit(1)


    jettylog = open("jetty.log", "w")
    with pushd("src/geoserver-geonode-ext"):
        os.environ["MAVEN_OPTS"] = " ".join([
            "-XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement",
            "-Xmx512M",
            "-XX:MaxPermSize=256m"
        ])
        mvn = subprocess.Popen(
            ["mvn", "jetty:run"],
            stdout=jettylog,
            stderr=jettylog
        )


    def jetty_is_up():
        try:
            urllib.urlopen("http://" + options.host.bind + ":8080/geoserver/web/")
            return True
        except Exception, e:
            return False

    socket.setdefaulttimeout(1)

    info("Logging servlet output to jetty.log...")
    info("Jetty is starting up, please wait...")
    while not jetty_is_up():
        time.sleep(2)

    try:
        info("Development GeoServer/GeoNetwork is running")
        info("Press CTRL-C to shut down")
        mvn.wait()
        info("GeoServer process terminated, see log for details.")
    finally:
        info("Shutting down...")
        try:
            mvn.terminate()
        except:
            pass
        mvn.wait()
        sys.exit()


@task
@needs('package_client')
@cmdopts([
    ('bind=', 'b', 'IP address to bind to. Default is localhost.')
])
def host(options):
    jettylog = open("jetty.log", "w")
    djangolog = open("django.log", "w")
    from geonode import settings

    url = "http://localhost:8080/geoserver/"
    if settings.GEOSERVER_BASE_URL != url:
        print 'your GEOSERVER_BASE_URL does not match %s' % url
        sys.exit(1)


    jettylog = open("jetty.log", "w")
    with pushd("src/geoserver-geonode-ext"):
        os.environ["MAVEN_OPTS"] = " ".join([
            "-XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement",
            "-Xmx512M",
            "-XX:MaxPermSize=256m"
        ])
        mvn = subprocess.Popen(
            ["mvn", "jetty:run"],
            stdout=jettylog,
            stderr=jettylog
        )


    socket.setdefaulttimeout(1)
    django = subprocess.Popen([
                                  "paster",
                                  "serve",
                                  "--reload",
                                  "shared/dev-paste.ini"
                              ],
                              stdout=djangolog,
                              stderr=djangolog
    )

    def jetty_is_up():
        try:
            urllib.urlopen("http://" + options.host.bind + ":8080/geoserver/web/")
            return True
        except Exception, e:
            return False

    def django_is_up():
        try:
            urllib.urlopen("http://" + options.host.bind + ":8000")
            return True
        except Exception, e:
            return False

    socket.setdefaulttimeout(1)

    info("Django is starting up, please wait...")
    while not django_is_up():
        time.sleep(2)

    info("Logging servlet output to jetty.log and django output to django.log...")
    info("Jetty is starting up, please wait...")
    while not jetty_is_up():
        time.sleep(2)

    try:
        sh("django-admin.py updatelayers --settings=geonode.settings")

        info("Development GeoNode is running at http://" + options.host.bind + ":8000/")
        info("The GeoNode is an unstoppable machine")
        info("Press CTRL-C to shut down")
        django.wait()
        info("Django process terminated, see log for details.")
    finally:
        info("Shutting down...")
        try:
            django.terminate()
        except:
            pass
        try:
            mvn.terminate()
        except:
            pass

        django.wait()
        mvn.wait()
        sys.exit()




@task
def test(options):
    sh("django-admin.py test --settings=geonode.settings")


def platform_options(options):
    "Platform specific options"
    options.config.platform = sys.platform

    # defaults:
    pip_flags = ""
    scripts = "bin"
    corelibs = "requirements.txt"
    devlibs = "dev-requirements.txt"

    if sys.platform == "win32":
        scripts = "Scripts"
    elif sys.platform == "darwin":
        pip_flags = "ARCHFLAGS='-arch i386'"

    options.config.bin = path(scripts)
    options.config.corelibs = corelibs
    options.config.devlibs = devlibs
    options.config.pip_flags = pip_flags

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
