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
def post_bootstrap(options):
    if sys.platform == 'win32':
        bin = "Scripts"
    else:
        bin = "bin"
    cmd = '%s install geonode-webapp.pybundle' %(path(bin) / "pip")
    if sys.platform == 'darwin':
        cmd = "ARCHFLAGS='-arch i386' " + cmd
    sh(cmd)
    call_task('generate_geoserver_token')
    info("Python dependencies are now installed")
    #@@ output config???

@task
def place_artifacts(options):
    pass


