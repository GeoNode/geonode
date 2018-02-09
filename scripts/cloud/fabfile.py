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
from fabric.context_managers import settings, hide
from fabric.contrib.files import sed
from subprocess import Popen, PIPE
import datetime

INSTALLDIR = '/var/lib'
POSTGIS_VER = "1.5.3-2"
GEONODE_BRANCH = 'dev'
GEONODE_GIT_URL = 'git://github.com/GeoNode/geonode.git'
ADMIN_USER='geonode' # Matches user in ubuntu packages
ADMIN_PASSWORD='adm1n'
ADMIN_EMAIL='admin@admin.admin'
UBUNTU_VERSION = "precise"
ARCH='x86_64'
VERSION='2.0a0'
MAKE_PUBLIC=True
AMI_BUCKET = 'geonode-ami-dev'
AWS_USER_ID=os.environ['AWS_USER_ID']
AWS_ACCESS_KEY_ID=os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY=os.environ['AWS_SECRET_ACCESS_KEY']
KEY_BASE=os.environ['EC2_KEY_BASE']
KEY_PATH='~/.ssh/' # trailing slash please

# Derived variables
GEONODEDIR = INSTALLDIR + '/geonode'
PYLIBS = GEONODEDIR + '/lib/python2.7/site-packages'
ACT = 'source ' + GEONODEDIR + '/bin/activate'

# Install GeoNode dependencies
def install_depend():
    sudo('cd %s; virtualenv geonode --system-site-packages;' % INSTALLDIR)
    sudo('apt-get install -y gcc python-pastescript python-dev libxml2-dev libxslt1-dev openjdk-6-jdk python-psycopg2 imagemagick')
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
    sudo('apt-get install -y python-virtualenv')
    with cd(GEONODEDIR), prefix(ACT):
        # Fetch from GitHub
        sudo('apt-get install -y git')
        sudo('rm -rf setup')
        sudo('git clone -b %s %s setup' % (GEONODE_BRANCH, GEONODE_GIT_URL))
        # Install requirements, setup
        sudo('pip install -e setup')
        sudo('cp -r setup/geonode %s' % PYLIBS )
        sudo('cp setup/package/support/geonode.apache /etc/apache2/sites-available/geonode')
        sudo('rm -rf setup')
    sed('/etc/apache2/sites-available/geonode', 'REPLACE_WITH_SITEDIR', PYLIBS, use_sudo=True)
    sed('/etc/apache2/sites-available/geonode', '/var/www/geonode/wsgi/geonode.wsgi', PYLIBS+'/geonode/wsgi.py', use_sudo=True)
    # Fix geoserver auth config file
    sed('/usr/share/geoserver/data/security/auth/geonodeAuthProvider/config.xml','localhost:8000','localhost', use_sudo=True)
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
        sudo('pip install -r requirements.txt --no-deps')
        sudo('rm requirements.txt')
    put('%s/%s.apache' % (project,project),'/etc/apache2/sites-available/%s' % project, use_sudo=True)
    sed('/etc/apache2/sites-available/%s' % project, 'REPLACE_WITH_SITEDIR', PYLIBS, use_sudo=True)
    with cd(os.path.join(PYLIBS,project)):
        sudo('ln -s settings_production.py local_settings.py')

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
    exec('import %s.settings_production as settings' % project)
    db = settings.DATABASES['default']['NAME']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    create_database(db,user,password)
    with prefix(ACT):
        sudo('django-admin.py migrate --settings=%s.settings' % project)
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

def deploy_geonode_testing_package():
    sudo('add-apt-repository -y ppa:geonode/testing')
    sudo('apt-get update')
    sudo('apt-get install -f -y geonode')

def deploy_geonode_snapshot_package():
    sudo('add-apt-repository -y ppa:geonode/snapshots')
    sudo('apt-get update')
    sudo('apt-get install -f -y geonode')

def deploy_geonode_unstable_package():
    sudo('add-apt-repository -y ppa:geonode/unstable')
    sudo('apt-get update')
    sudo('apt-get install -f -y geonode')

def deploy_geonode_dev_deb():
    sudo('add-apt-repository -y ppa:geonode/unstable')
    sudo('apt-get update')
    sudo('wget -e robots=off --wait 0.25 -r -l1 --no-parent -A.deb http://build.geonode.org/geonode/latest/')
    with settings(warn_only=True):
        sudo('cd build.geonode.org/geonode/latest;dpkg -i geonode_2.0.0*.deb',shell=True)
    sudo('apt-get install -f -y')

def change_admin_password():
    put('../misc/changepw.py', '/home/ubuntu/')
    run("perl -pi -e 's/replace.me.admin.user/%s/g' ~/changepw.py" % ADMIN_USER)
    run("perl -pi -e 's/replace.me.admin.pw/%s/g' ~/changepw.py" % ADMIN_PASSWORD)
    sudo('source /var/lib/geonode/bin/activate;cat ~/changepw.py | django-admin.py shell --settings=geonode.settings')
    run('rm ~/changepw.py')

def geonode_updateip(server_name="demo.geonode.org"):
    sudo ('geonode-updateip %s' % server_name)

def set_temp_hosts_entry(server_name="demo.geonode.org"):
    sudo("IP=`wget -qO- http://instance-data/latest/meta-data/public-ipv4`; echo $IP demo.geonode.org >> /etc/hosts")

def remove_temp_hosts_entry():
    sudo("sed '$d' /etc/hosts > temp; mv temp /etc/hosts")

def update_geoserver_geonode_auth():
    sudo('perl -pi -e "s/:8000//g" /usr/share/geoserver/data/security/auth/geonodeAuthProvider/config.xml')
    sudo('/etc/init.d/tomcat7 restart')



def update_instance():
    put('../misc/update-instance', '/home/ubuntu/')
    sudo('mv /home/ubuntu/update-instance /etc/init.d')
    sudo('chmod +x /etc/init.d/update-instance')
    sudo('sudo update-rc.d -f update-instance start 20 2 3 4 5 .')

def cleanup_temp():
    # ToDo: Update as necessary
    sudo("rm -f /root/.*hist* $HOME/.*hist*")
    sudo("rm -f /var/log/*.gz")

def copy_keys():
    sudo('rm -f ~/.ssh/*%s.pem' % (KEY_BASE))
    put(('%s*%s*' % (KEY_PATH, KEY_BASE)), '/home/ubuntu/.ssh/', mode=0400)
    pass

def install_ec2_tools():
    sudo('add-apt-repository "deb http://us-east-1.ec2.archive.ubuntu.com/ubuntu/ %s multiverse"' % (UBUNTU_VERSION))
    sudo('add-apt-repository "deb http://us-east-1.ec2.archive.ubuntu.com/ubuntu/ %s-updates multiverse"' % (UBUNTU_VERSION))
    sudo('apt-get -y update')
    sudo('apt-get install -y ec2-ami-tools')
    sudo('apt-get install -y ec2-api-tools')

def build_geonode_ami():
    deploy_geonode_dev_deb()
    change_admin_password()
    cleanup_temp()
    copy_keys()
    update_instance()
    install_ec2_tools()
    with hide('running', 'stdout', 'stderr'):
        sudo('export AWS_USER_ID=%s' % AWS_USER_ID)
        sudo('export AWS_ACCESS_KEY_ID=%s' % AWS_ACCESS_KEY_ID)
        sudo('export AWS_SECRET_ACCESS_KEY=%s' % AWS_SECRET_ACCESS_KEY)
    sudo('export ARCH=%s' % ARCH)
    prefix = 'geonode-%s-%s' % (VERSION, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    excludes = '/mnt,/root/.ssh,/home/ubuntu/.ssh,/tmp'
    sudo("ec2-bundle-vol -r %s -d /mnt -p %s -u %s -k ~/.ssh/pk-*.pem -c ~/.ssh/cert-*.pem -e %s" % (ARCH, prefix, AWS_USER_ID, excludes))
    sudo("ec2-upload-bundle -b %s -m /mnt/%s.manifest.xml -a %s -s %s" % (AMI_BUCKET, prefix, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY))
    output = sudo('ec2-register --name "%s/%s" "%s/%s.manifest.xml" -K ~/.ssh/pk-*.pem -C ~/.ssh/cert-*.pem' % (AMI_BUCKET, prefix, AMI_BUCKET, prefix))
    ami_id = output.split('\t')[1]
    if MAKE_PUBLIC:
        sudo("ec2-modify-image-attribute -l -a all -K ~/.ssh/pk-*.pem -C ~/.ssh/cert-*.pem %s" % (ami_id))
    print "AMI %s Ready for Use" % (ami_id)

def install_sample_data():
    run('geonode loaddata sample_admin.json')
    run('geonode importlayers `python -c "import gisdata; print gisdata.GOOD_DATA"` -v 3')
    # Fix permissions issue on the newly created thumbs dir
    sudo('chmod -R 7777 /var/www/geonode/uploaded/thumbs/')
