from __future__ import with_statement

from paver import svn
from paver.easy import *
from paver.easy import options
from paver.path25 import pushd
import functools
import os
import sys
import time
import socket
import ConfigParser
import paver.doctools
import paver.misctasks
import pkg_resources
import subprocess
from shutil import move
import zipfile
import tarfile
import urllib


assert sys.version_info[0] >= 2 and sys.version_info[1] >= 6, \
       SystemError("GeoNode Build requires python 2.6.2 or better")


options(
    config=Bunch(
        ini=path('shared/build.ini'),
        package_dir = path('shared/package')
    ),
    minilib=Bunch(extra_files=['virtual', 'doctools', 'misctasks']),
    sphinx=Bunch(
        docroot='docs',
        builddir="_build",
        sourcedir="./"
    ),
    virtualenv=Bunch(
        packages_to_install=[
            'http://bitbucket.org/ianb/pip/get/2cb1db7b2baf.gz#egg=pip',
            'urlgrabber',
            'jstools',
            'virtualenv'
        ],
        dest_dir='./',
        install_paver=True,
        script_name='bootstrap.py',
        no_site_packages=True,
        paver_command_line='post_bootstrap'
    ),
    deploy=Bunch(
        pavement=path('shared/package/pavement.py'),
        req_file=path('shared/package/deploy-libs.txt'),
        packages_to_install=['pip'],
        dest_dir='./',
        install_paver=True,
        no_site_packages=True,
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
            sh('wget http://capra.opengeo.org/repo/%s.zip' % dlname)
            path(dlname + '.zip').copy(bpath)
    else:
        info("Skipping download. 'rm bundle  %s' if you need a fresh download. " % bundle)


@task
def install_25_deps(options):
    """Fetch python 2_5-specific dependencies (not maintained)"""
    pass

    
@task
def post_bootstrap(options):
    """installs the current package"""
    pip = path(options.config.bin) / "pip"
    sh('%s install -e %s' %(pip, path("src/GeoNodePy")))


#TODO Move svn urls out to a config file

@task
def setup_gs_data(options):
    """Fetch a data directory to use with GeoServer for testing."""
    from urlgrabber.grabber import urlgrab
    from urlgrabber.progress import text_progress_meter
    src_url = options.config.parser.get('geoserver', 'gs_data_url')
    shared = path("./shared")
    if not shared.exists():
        shared.mkdir()
    dst_url = shared / "geonode-geoserver-data.zip"
    if not dst_url.exists() or getattr(options, 'clean', False):
        urlgrab(src_url, dst_url, progress_obj=text_progress_meter())
    if not path(gs_data).exists():
        path(gs_data).rmtree()
        unzip_file(dst_url, gs_data)


@task
@needs(['setup_gs_data'])
def setup_geoserver(options):
    """Prepare a testing instance of GeoServer."""
    with pushd('src/geoserver-geonode-ext'):
        sh("mvn install")

@task
def setup_geonetwork(options):
    """Fetch the geonetwork.war and intermap.war to use with GeoServer for testing."""
    from urlgrabber.grabber import urlgrab
    from urlgrabber.progress import text_progress_meter
    src_url = options.config.parser.get('geonetwork', 'geonetwork_war_url')
    # where to download the war files. If changed change also
    # src/geoserver-geonode-ext/jetty.xml accordingly
    webapps = path("./webapps")
    if not webapps.exists():
        webapps.mkdir()
    dst_url = webapps / "geonetwork.war"
    if not dst_url.exists() or getattr(options, 'clean', False):
        urlgrab(src_url, dst_url, progress_obj=text_progress_meter())
    src_url = options.config.parser.get('geonetwork', 'intermap_war_url')
    dst_url = webapps / "intermap.war"
    if not dst_url.exists() or getattr(options, 'clean', False):
        urlgrab(src_url, dst_url, progress_obj=text_progress_meter())


@task
@needs([
    'install_deps',
    'setup_geoserver', 
    'build_js', 
    'setup_geonetwork',
    'sync_django_db'
])
def build(options):
    """Get dependencies and generally prepare a GeoNode development environment."""
    info("""GeoNode development environment successfully set up; use "paver host" to start up the server.""") 


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
       svn.export("../externals/geoext/resources", "geonode-client/gx/theme")
       os.makedirs("geonode-client/PrintPreview")
       svn.export("../externals/PrintPreview/resources", "geonode-client/PrintPreview/theme")
       os.makedirs("geonode-client/ol") #need to split this off b/c of dumb hard coded OL paths
       svn.export("../externals/openlayers/theme", "geonode-client/ol/theme")
       os.makedirs("geonode-client/gn")
       svn.export("../src/theme/", "geonode-client/gn/theme/")

       sh("jsbuild -o geonode-client/ all.cfg") 
       move("geonode-client/OpenLayers.js","geonode-client/ol/")
       move("geonode-client/GeoExt.js","geonode-client/gx/")
       move("geonode-client/GeoNode.js","geonode-client/gn/")
       move("geonode-client/PrintPreview.js","geonode-client/PrintPreview/")
       move("geonode-client/ux.js","geonode-client/gn/")


@task
def capra_js(options):
    """Compress the JavaScript resources used by the CAPRA GeoNode extensions."""
    with pushd('src/capra-client/build/'):
       path("capra-client").rmtree()
       path("capra-client/").makedirs()
       sh("jsbuild -o capra-client/ all.cfg") 


@task
def sync_django_db(options):
    if not path("development.db").exists():
        sh("django-admin.py syncdb --settings=capra.settings --noinput")


@task
def package_dir(options):
    """
    Adds a packaging directory
    """
    if not options.deploy.out_dir.exists():
        options.config.package_dir.mkdir()


@task
@needs('package_dir', 'concat_js', 'capra_js')
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
@needs('package_dir', 'setup_geoserver')
def package_geoserver(options):
    """Package GeoServer WAR file with appropriate extensions."""
    path('src/geoserver-geonode-ext/target/geoserver-geonode-dev.war').copy(options.deploy.out_dir)


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
    'package_webapp',
    'package_client',
    'package_bootstrap'
)
def package_all(options):
    info('all is packaged, ready to deploy')


def create_version_name(svn_version=True):
    # we'll use the geonodepy version as our "official" version number
    # for now
    slug = "GeoNode-%s" %pkg_resources.get_distribution('GeoNodePy').version
    if svn_version:
        # this assumes releaser know what branch is being released
        revision = svn.info()['revision']
        slug += "rev" + revision
    return slug

        
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

    # This part of the build is svn specific...

    if not hasattr(options, 'skip_packaging'):
        call_task("package_all")
    if hasattr(options, 'name'):
        pkgname = options.name
    else:
        pkgname = create_version_name(not getattr(options, 'no_svn', False))
        if hasattr(options, 'append_to'):
            pkgname += options.append_to

    def excludable(f):
        return f.find(".svn") != -1
            
    svninfo = svn.info()
    with pushd('shared'):
        out_pkg = path(pkgname)
        out_pkg.rmtree()
        path('./package').copytree(out_pkg)
        infofile = out_pkg / "version.txt"
        infofile.write_text("%s@%s" % (svninfo["url"], svninfo["revision"]))

        tar = tarfile.open("%s.tar.gz" % out_pkg, "w:gz")
        with pushd(out_pkg):
            for file in path(".").walkfiles():
                if not excludable(file):
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
@needs('install_sphinx_conditionally', 'checkup_spec')
def html(options):
    call_task('paver.doctools.html')

@task
@cmdopts([
    ('bind=', 'b', 'IP address to bind to. Default is localhost.')
])
def host(options):
    jettylog = open("jetty.log", "w")
    djangolog = open("django.log", "w")
    with pushd("src/geoserver-geonode-ext"):
        os.environ["MAVEN_OPTS"] = "-Xmx512M -Djetty.host=" + options.host.bind
        mvn = subprocess.Popen(
            ["mvn", "jetty:run"],
            stdout=jettylog,
            stderr=jettylog
        )
    django = subprocess.Popen([
            "django-admin.py", 
            "runserver",
            "--settings=capra.settings",
            options.host.bind + ":8000"
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

    info("Logging servlet output to jetty.log and django output to django.log...")
    info("Jetty is starting up, please wait...")
    socket.setdefaulttimeout(1)
    while not jetty_is_up():
        time.sleep(2)

    sh("django-admin.py updatelayers --settings=capra.settings")
    info("Development GeoNode is running at http://" + options.host.bind + ":8000/")
    info("The GeoNode is an unstoppable machine")
    info("Press CTRL-C to shut down")

    try: 
        django.wait()
    except KeyboardInterrupt:
        info("Shutting down...")
        django.terminate()
        mvn.terminate()
        django.wait()
        mvn.wait()
        sys.exit()


@task
def test(options):
    sh("django-admin.py test --settings=capra.settings")


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
