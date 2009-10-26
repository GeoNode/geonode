from paver.easy import *
import os

options()

@task
def auto(options):
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
    sh('%s install geonode-webapp.pybundle' %pip)
    info("Python dependencies are now installed")
    #@@ output config???

@task
def place_artifacts(options):
    pass


