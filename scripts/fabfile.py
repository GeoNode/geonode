"""
This is a fabric script file that allows for remote deployment of
GeoNode and a downstream GeoNode project via ssh. 

To deploy GeoNode:
    fab -H user@hostname deploy_geonode
To deploy GeoNode project:
    fab -H user@hostname deploy_project
To deploy GeoNode and a GeoNode project:
    fab -H user@hostname deploy

This file currently gets GeoNode from GitHub, eventually will install
from repo or debian package (once release candidate phase or later)
"""
# Usage:
#     fab -H user@hostname 

from fabric.api import env, sudo, run, cd, local, put, prefix
from fabric.api import settings as fab_settings

# Project info
PROJECT = 'PROJNAME'
PROJECT_DIRS = ['PROJNAME','APP1']

INSTALLDIR = '/var/lib'
GEONODE_BRANCH = 'dev'
GEONODE_GIT_URL = 'git://github.com/GeoNode/geonode.git'

# Derived variables
GEONODEDIR = INSTALLDIR + '/geonode'
PYLIBS = GEONODEDIR + '/lib/python2.7/site-packages'
ACT = 'source ' + GEONODEDIR + '/bin/activate'

# Install GeoNode dependencies
def install_depend():
    sudo('apt-get install -y python-virtualenv')
    sudo('cd %s; virtualenv geonode --system-site-packages;' % INSTALLDIR)
    sudo('apt-get install -y gcc python-pastescript python-dev libxml2-dev libxslt1-dev openjdk-6-jdk')
    # Web server
    sudo('apt-get install -y apache2 tomcat6 libapache2-mod-wsgi maven2')
    # Database
    sudo('apt-get install -y postgresql-9.1-postgis postgresql-server-dev-9.1')

# Install GeoNode
def deploy_geonode():
    with cd(GEONODEDIR), prefix(ACT):
        # Fetch from GitHub
        sudo('apt-get install -y git')
        sudo('rm -rf setup')
        sudo('git clone -b %s %s setup' % (GEONODE_BRANCH, GEONODE_GIT_URL))
        # Install requirements, setup
        sudo('pip install -e setup')
        sudo('cd setup; paver setup')
        sudo('cp -r setup/geonode %s' % PYLIBS )
        sudo('cp setup/geoserver-geonode-ext/target/geoserver.war /var/lib/tomcat6/webapps/')
        sudo('rm -rf setup')
        # Use debian package instead
        #sudo('git branch deb;paver deb')
        #sudo('dpkg -i geonode/geonode*.deb')

def deploy_project():
    #run('git clone -b %s %s %S' % (BRANCH, GIT_URL, PROJECT))
    # Put apps....change settings to get project apps automagically
    for projdir in PROJECT_DIRS:
        put(projdir,PYLIBS,use_sudo=True)
    put('requirements.txt',GEONODEDIR,use_sudo=True)
    with cd(GEONODEDIR), prefix(ACT):
        sudo('pip install -r requirements.txt')
        sudo('rm requirements.txt')

def restore_data():
    # Restore geoserver data
    gsdir = '/var/lib/tomcat6/webapps/geoserver'
    put('data/geoserver-data.tar', gsdir+'/geoserver-data.tar', use_sudo=True)
    with cd(gsdir):
        sudo('rm -rf data')
        sudo('tar xvf geoserver-data.tar')
        sudo('chown -R tomcat6:tomcat6 data')
    run('rm geoserver-data.tar')
    sudo('service tomcat6 restart')
    with prefix(ACT):
        sudo('django-admin.py cleardeadlayers --settings=%s.settings' % PROJECT)
        sudo('django-admin.py updatelayers --settings=%s.settings' % PROJECT)
        
def setup_apache():
    with cd(PYLIBS), prefix(ACT):
        sudo("sed 's/{{ PYLIBS }}/%s/g' %s/%s.apache > /etc/apache2/sites-available/%s" % (PYLIBS.replace('/','\/'), PROJECT, PROJECT, PROJECT))
        sudo("a2enmod proxy_http")
        sudo('a2ensite %s; service apache2 restart' % PROJECT)
        sudo('mkdir /var/www/geonode; chown www-data:www-data /var/www/geonode')
        sudo('django-admin.py collectstatic --noinput --settings=%s.settings' % PROJECT)

def setup_pgsql():
    import sys
    sys.path.append('.')
    exec('import ' + PROJECT + '.local_settings as settings')
    db = settings.DATABASES['default']['NAME']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    #sudo("dropdb %s" % db, user="postgres")
    #sudo("dropuser %s" % user, user="postgres")
    with fab_settings(warn_only=True):
        sudo("createuser -SDR %s" % user, user="postgres")
        sudo("createdb -O %s %s -T template_postgis" %(user,db), user="postgres")
        sudo("psql -c \"alter user %s with encrypted password '%s'\" " % (user,password), user="postgres")
    with prefix(ACT):
        sudo('django-admin.py syncdb --settings=%s.settings' % PROJECT)
        sudo('django-admin.py migrate --settings=%s.settings' % PROJECT)
    # Need to restore database and GeoServer data
    #put('data/%s.sql' % db, GEONODEDIR, use_sudo=True)
    #sudo('psql -d %s -f %s/%s.sql' % (db, GEONODEDIR, db), user='postgres')

def deploy():
    install_depend()
    deploy_geonode()
    deploy_project() 
    setup_apache()
    setup_pgsql()

# TODO - Build Amazon Machine Instance
def build_ami():
    # Install ec2 tools
    sudo('apt-get install -y ec2-ami-tools ec2-api-tools')
    # bundle-vol then upload-bundle

