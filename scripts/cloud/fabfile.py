"""
This is a fabric script file that allows for remote deployment of
GeoNode and a downstream GeoNode project via ssh. 

To deploy a default GeoNode:
    fab -H user@hostname deploy_default_geonode

To deploy a GeoNode project from current directory:
    fab -H user@hostname deploy:'project'
       project - name of project (name of site directory in current dir)

This file currently gets GeoNode from GitHub, eventually will install
from repo or debian package (once release candidate phase or later)
"""
# Usage:
#     fab -H user@hostname 

import os, glob
from fabric.api import env, sudo, run, cd, local, put, prefix
from fabric.api import settings as fab_settings
from fabric.contrib.files import sed

INSTALLDIR = '/var/lib'
POSTGIS_VER = "1.5.3-2"
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
    sudo('apt-get install -y gcc python-pastescript python-dev libxml2-dev libxslt1-dev openjdk-6-jdk python-psycopg2')
    # Web server
    sudo('apt-get install -y apache2 tomcat6 libapache2-mod-wsgi maven2')
    sudo("a2enmod proxy_http")
    # Database
    sudo('apt-get install -y postgis=%s postgresql-9.1-postgis postgresql-server-dev-9.1' % POSTGIS_VER)
    create_postgis_template()
    #sed('/etc/postgresql/9.1/main/pg_hba.conf',
    #    'local   all             all                                     peer',
    #    'local   all             all                                     md5', use_sudo=True)

def create_postgis_template():
    # Create postgis template
    with fab_settings(warn_only=True):
        sudo('createdb -E UTF8 template_postgis', user='postgres')
        sudo('createlang -d template_postgis plpgsql', user='postgres')
        cstring = "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis'"
        sudo('psql -d postgres -c %s' % cstring, user='postgres')
        sudo('psql -d template_postgis -f /usr/share/postgresql/9.1/contrib/postgis-%s/postgis.sql' % POSTGIS_VER[:3], user='postgres')
        sudo('psql -d template_postgis -f /usr/share/postgresql/9.1/contrib/postgis-%s/spatial_ref_sys.sql' % POSTGIS_VER[:3], user='postgres')
        sudo('psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"', user='postgres')
        sudo('psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"', user='postgres')
        sudo('psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"', user='postgres')
        if POSTGIS_VER[:1] == '2':
            sudo('psql -d template_postgis -f /usr/share/postgresql/9.1/contrib/postgis-%s/rtpostgis.sql' % POSTGIS_VER[:3], user='postgres')

# Install GeoNode library
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
        sudo('cp setup/package/support/geonode.apache /etc/apache2/sites-available/geonode')
        sudo('rm -rf setup')
    sed('/etc/apache2/sites-available/geonode', 'REPLACE_WITH_SITEDIR', PYLIBS, use_sudo=True)
    sed('/etc/apache2/sites-available/geonode', '/var/www/geonode/wsgi/geonode.wsgi', PYLIBS+'/geonode/wsgi.py', use_sudo=True)
    # Use debian package instead
    #sudo('git branch deb;paver deb')
    #sudo('dpkg -i geonode/geonode*.deb')

# Deploy custom project from current local directory
def deploy_project(project):
    # Put apps....change settings to get project apps automagically
    put(project,PYLIBS,use_sudo=True)
    with fab_settings(warn_only=True):
        for projdir in filter(os.path.isdir,glob.glob('*')):
            if projdir != 'shared' and projdir != 'data':
                put(projdir,PYLIBS,use_sudo=True)
    put('requirements.txt',GEONODEDIR,use_sudo=True)
    with cd(GEONODEDIR), prefix(ACT):
        sudo('pip install -r requirements.txt')
        sudo('rm requirements.txt')
    put('%s/%s.apache' % (project,project),'/etc/apache2/sites-available/%s' % project, use_sudo=True)
    sed('/etc/apache2/sites-available/%s' % project, 'REPLACE_WITH_SITEDIR', PYLIBS, use_sudo=True)

def enable_site(project):
    with cd(PYLIBS), prefix(ACT):
        sudo('a2ensite %s; service apache2 restart' % project)
        sudo('mkdir /var/www/geonode; chown www-data:www-data /var/www/geonode')
        sudo('django-admin.py collectstatic --noinput --settings=%s.settings' % project)

# TODO - test/fix this function
def restore_data(project):
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
        sudo('django-admin.py cleardeadlayers --settings=%s.settings' % project)
        sudo('django-admin.py updatelayers --settings=%s.settings' % project)
        

def create_database(db,user,password):
    #sudo("dropdb %s" % db, user="postgres")
    #sudo("dropuser %s" % user, user="postgres")
    with fab_settings(warn_only=True):
        sudo("createuser -s %s" % user, user="postgres")
        sudo("createdb -O %s %s -T template_postgis" %(user,db), user="postgres")
        sudo("psql -c \"alter user %s with encrypted password '%s'\" " % (user,password), user="postgres")

def setup_pgsql(project):
    import sys
    sys.path.append('.')
    with cd(PYLIBS), fab_settings(warn_only=True):
        sudo('cd %s; ln -s settings_production.py local_settings.py' % project)
    exec('import ' + project + '.settings_production as settings')
    db = settings.DATABASES['default']['NAME']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    create_database(db,user,password)
    with prefix(ACT):
        sudo('django-admin.py syncdb --settings=%s.settings' % project)
    # Need to restore database and GeoServer data
    #put('data/%s.sql' % db, GEONODEDIR, use_sudo=True)
    #sudo('psql -d %s -f %s/%s.sql' % (db, GEONODEDIR, db), user='postgres')

def deploy(project):
    install_depend()
    deploy_geonode()
    deploy_project(project=project) 
    enable_site(project)
    setup_pgsql(project)

def deploy_default_geonode():
    install_depend()
    deploy_geonode()
    enable_site('geonode')
    # User needs to provide local_settings - where?
    setup_pgsql('geonode')

# TODO - Build Amazon Machine Instance
def build_ami():
    # Install ec2 tools
    sudo('apt-get install -y ec2-ami-tools ec2-api-tools')
    # bundle-vol then upload-bundle
