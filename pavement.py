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
from shutil import move
import zipfile
import tarfile
import urllib


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
            'http://bitbucket.org/ianb/pip/get/2cb1db7b2baf.gz#egg=pip',
            'jstools',
            'virtualenv'
        ],
        dest_dir='./',
        install_paver=True,
        script_name='bootstrap.py',
        paver_command_line='post_bootstrap'
    ),
    deploy=Bunch(
        pavement=path('shared/package/pavement.py'),
        req_file=path('shared/package/deploy-libs.txt'),
        packages_to_install=['pip'],
        dest_dir='./',
        install_paver=True,
        paver_command_line='post_bootstrap'      
    ),
    host=Bunch(
        bind='localhost'
    )
)

venv = os.environ.get('VIRTUAL_ENV')
bundle = path('shared/geonode.pybundle')
dl_cache = "--download-cache=./build"
dlname = 'geonode.bundle'
gs_data = "gs-data"
geoserver_target = path('src/geoserver-geonode-ext/target/geoserver-geonode-dev.war')
geonetwork_target = path('webapps/geonetwork.war')
def geonode_client_target(): return options.deploy.out_dir / "geonode-client.zip"

deploy_req_txt = """
# NOTE... this file is generated
-r %(venv)s/shared/core-libs.txt
-e %(venv)s/src/GeoNodePy
""" % locals()

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
def install_deps(options):
    """Installs all the python deps from a requirements file"""
    if bundle.exists():
        info('using to install python deps bundle')
        call_task('install_bundle')
    else:
        info('Installing from requirements file. '\
             'Use "paver bundle_deps" to create an install bundle')
        pip_install("-r shared/%s" % options.config.corelibs)
        if options.config.platform == "win32":
            info("You will need to install 'PIL' and 'ReportLab' "\
                 "separately to do PDF generation")


@task
def bundle_deps(options):
    """
    Create a pybundle of all python dependencies.  If created, this
    will be the default for installing python deps.
    """
    pip_bundle("-r shared/core-libs.txt %s" % bundle)


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
    pip = path(options.config.bin) / "pip"
    sh('%s install -e %s' %(pip, path("src/GeoNodePy")))


#TODO Move svn urls out to a config file

def grab(src, dest):
    from urllib import urlretrieve
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
    """Prepare a testing instance of GeoServer."""
    with pushd('src/geoserver-geonode-ext'):
        sh("mvn clean install")

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
    schema_url = deployed_url / "xml" / "schemas" / "iso19139.geonode"

    if getattr(options, 'clean', False):
        deployed_url.rmtree()
    grab(src_url, dst_url)
    if not dst_war.exists():
        zip_extractall(zipfile.ZipFile(dst_url), webapps)
    if not deployed_url.exists():
        zip_extractall(zipfile.ZipFile(dst_war), deployed_url)

    # Update the ISO 19139 profile to the latest version
    path(schema_url).rmtree()
    info("Copying GeoNode ISO 19139 profile to %s" %schema_url)
    path("gn_schema").copytree(schema_url)

    src_url = str(options.config.parser.get('geonetwork', 'intermap_war_url'))
    dst_url = webapps / "intermap.war"

    grab(src_url, dst_url)

@task
@needs([
    'setup_geoserver',
    'setup_geonetwork'
])
def setup_webapps(options):
    pass

@task
@needs([
    'install_deps',
    'setup_webapps',
    'build_js', 
    'generate_geoserver_token',
    'sync_django_db'
])
def build(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    info("""GeoNode development environment successfully set up.\nIf you have not set up an administrative account, please do so now.\nUse "paver host" to start up the server.""") 


@task
@needs(['js_dependencies'])
def build_js(options):
    """
    Concatenate and compress application client javascript
    """
    with pushd('src/geonode-client/build/'):
       path("geonode-client").rmtree()
       os.makedirs("geonode-client")
       path("../externals/ext").copytree("geonode-client/ext")
       os.makedirs("geonode-client/gx")
       path("../externals/geoext/geoext/resources").copytree("geonode-client/gx/theme")
       os.makedirs("geonode-client/gxp")
       path("../externals/gxp/src/theme").copytree("geonode-client/gxp/theme")
       os.makedirs("geonode-client/PrintPreview")
       path("../externals/PrintPreview/resources").copytree("geonode-client/PrintPreview/theme")
       os.makedirs("geonode-client/ol") #need to split this off b/c of dumb hard coded OL paths
       path("../externals/openlayers/theme").copytree("geonode-client/ol/theme")
       path("../externals/openlayers/img").copytree("geonode-client/ol/img")
       os.makedirs("geonode-client/gn")
       path("../src/theme/").copytree("geonode-client/gn/theme/")
       path("../src/script/ux").copytree("geonode-client/gn/ux")

       sh("jsbuild -o geonode-client/ all.cfg") 
       move("geonode-client/OpenLayers.js","geonode-client/ol/")
       move("geonode-client/GeoExt.js","geonode-client/gx/")
       move("geonode-client/gxp.js","geonode-client/gxp/")
       move("geonode-client/GeoNode.js","geonode-client/gn/")
       move("geonode-client/GeoExplorer.js","geonode-client/gn/")
       move("geonode-client/PrintPreview.js","geonode-client/PrintPreview/")
       move("geonode-client/ux.js","geonode-client/gn/")
       
    info('GeoNode Client Javascript is done building')
    

@task
def js_dependencies(options):
    """
    Fetch dependencies for the JavaScript build
    """
    grab("http://extjs.cachefly.net/ext-3.2.1.zip", "shared/ext-3.2.1.zip")
    path("src/geonode-client/externals/ext").rmtree()
    zip_extractall(zipfile.ZipFile("shared/ext-3.2.1.zip"), "src/geonode-client/externals/")
    path("src/geonode-client/externals/ext-3.2.1").rename("src/geonode-client/externals/ext")


@task
def sync_django_db(options):
    sh("django-admin.py syncdb --settings=geonode.settings --noinput")

@task
def generate_geoserver_token(options):
    gs_token_file = 'geoserver_token'
    if not os.path.exists(gs_token_file):
        from random import choice
        import string
        chars = string.letters + string.digits + "-_!@#$*"
        token = ''
        for i in range(32):
            token += choice(chars)
        tf = open('geoserver_token', 'w')
        tf.write(token)
        tf.close()

@task
def package_dir(options):
    """
    Adds a packaging directory
    """
    if not options.deploy.out_dir.exists():
        options.config.package_dir.mkdir()


@task
@needs('package_dir', 'build_js')
def package_client(options):
    """
    Package compressed client resources (JavaScript, CSS, images).
    """
    # build_dir = options.deploy.out_dir
    zip = zipfile.ZipFile(geonode_client_target(),'w') #create zip in write mode

    with pushd('src/geonode-client/build/'):
        for file in path("geonode-client/").walkfiles():
            print(file)
            zip.write(file)

    zip.close()


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
    """Package (Python, Django) web application and dependencies."""
    with pushd('src/GeoNodePy'):
        sh('python setup.py egg_info sdist')
        
    req_file = options.deploy.req_file
    req_file.write_text(deploy_req_txt)
    pip_bundle("-r %s %s/geonode-webapp.pybundle" % (req_file, options.deploy.out_dir))


@task
@needs(
    'build',
    'package_geoserver',
    'package_geonetwork',
    'package_webapp',
    'package_client',
    'package_bootstrap'
)
def package_all(options):
    info('all is packaged, ready to deploy')


def create_version_name():
    # we'll use the geonodepy version as our "official" version number
    # for now
    slug = "GeoNode-%s-%s" % (
        pkg_resources.get_distribution('GeoNodePy').version,
        date.today().isoformat()
    )

    return slug

@task
def make_devkit(options):
    import virtualenv
    from urllib import urlretrieve

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

    full_path_pip = options.config.bin / 'pip'

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
        sh("%s install sphinx" % (options.config.bin / 'pip'))

        # have to reload doctools so it will realize sphinx is now
        # available
        sys.modules['paver.doctools'] = reload(sys.modules['paver.doctools'])


@task
@cmdopts([
    ('bind=', 'b', 'IP address to bind to. Default is localhost.')
])
def host(options):
    jettylog = open("jetty.log", "w")
    djangolog = open("django.log", "w")
    with pushd("src/geoserver-geonode-ext"):
        os.environ["MAVEN_OPTS"] = " ".join([
            "-XX:CompileCommand=exclude,net/sf/saxon/event/ReceivingContentHandler.startElement",
            "-Djetty.host=" + options.host.bind,
            "-Xmx512M",
            "-XX:MaxPermSize=128m"
        ])
        mvn = subprocess.Popen(
            ["mvn", "jetty:run"],
            stdout=jettylog,
            stderr=jettylog
        )
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
            urllib.urlopen("http://" + options.host.bind + ":8001/geoserver/web/")
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
        #sh("django-admin.py updatelayers --settings=geonode.settings")
        
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
    corelibs = "core-libs.txt"

    if sys.platform == "win32":
        corelibs = "py-base-libs.txt"
        scripts = "Scripts"
    elif sys.platform == "darwin":
        pip_flags = "ARCHFLAGS='-arch i386'"
        
    options.config.bin = path(scripts)
    options.config.corelibs = corelibs
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
