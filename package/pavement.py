from paver.easy import *
import os

options()

@task
def auto(options):
    # read in config file for artifact locations
    pass

wsgi_config = \
"""

"""

@task
def post_bootstrap(options):
    if sys.platform == 'win32':
        bin = "Scripts"
    else:
        bin = "bin"
    pip = path(bin) / "pip"
    cmd = '%s install geonode-webapp.pybundle' %pip
    if sys.platform == 'darwin':
        cmd = "ARCHFLAGS='-arch i386' " + cmd
    sh(cmd)
    info("Python dependencies are now installed")
    #@@ output config???


@task
def place_artifacts(options):
    pass


