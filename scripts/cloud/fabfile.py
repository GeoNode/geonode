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

import os
import glob
from fabric.api import sudo, run, cd, put, prefix
from fabric.api import settings as fab_settings
from fabric.context_managers import settings, hide
from fabric.contrib.files import sed
import datetime

INSTALLDIR = '/var/lib'
POSTGIS_VER = "1.5.3-2"
GEONODE_BRANCH = 'dev'
GEONODE_GIT_URL = 'git://github.com/GeoNode/geonode.git'
ADMIN_USER = 'geonode'  # Matches user in ubuntu packages
ADMIN_PASSWORD = 'adm1n'
ADMIN_EMAIL = 'admin@admin.admin'
UBUNTU_VERSION = "precise"
ARCH = 'x86_64'
VERSION = '2.0a0'
MAKE_PUBLIC = True
AMI_BUCKET = 'geonode-ami-dev'
AWS_USER_ID = os.environ['AWS_USER_ID']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
KEY_BASE = os.environ['EC2_KEY_BASE']
KEY_PATH = '~/.ssh/'  # trailing slash please

# Derived variables
GEONODEDIR = f"{INSTALLDIR}/geonode"
PYLIBS = f"{GEONODEDIR}/lib/python2.7/site-packages"
ACT = f"source {GEONODEDIR}/bin/activate"


# Install GeoNode dependencies
def install_depend():
    sudo(f'cd {INSTALLDIR}; virtualenv geonode --system-site-packages;')
    sudo('apt-get install -y gcc python-pastescript python-dev libxml2-dev libxslt1-dev openjdk-6-jdk '
         'python-psycopg2 imagemagick')
    # Web server
    sudo('apt-get install -y apache2 tomcat6 libapache2-mod-wsgi maven2')
    sudo("a2enmod proxy_http")
    # Database
    sudo(f'apt-get install -y postgis={POSTGIS_VER} postgresql-9.1-postgis postgresql-server-dev-9.1')
    create_postgis_template()
    # sed('/etc/postgresql/9.1/main/pg_hba.conf',
    #    'local   all             all                                     peer',
    #    'local   all             all                                     md5', use_sudo=True)


def create_postgis_template():
    # Create postgis template
    with fab_settings(warn_only=True):
        sudo('createdb -E UTF8 template_postgis', user='postgres')
        sudo('createlang -d template_postgis plpgsql', user='postgres')
        cstring = "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis'"
        sudo(f'psql -d postgres -c {cstring}', user='postgres')
        sudo(f'psql -d template_postgis -f /usr/share/postgresql/9.1/contrib/postgis-{POSTGIS_VER[:3]}/postgis.sql', user='postgres')
        sudo(f'psql -d template_postgis -f /usr/share/postgresql/9.1/contrib/postgis-{POSTGIS_VER[:3]}/spatial_ref_sys.sql', user='postgres')
        sudo('psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"', user='postgres')
        sudo('psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"', user='postgres')
        sudo('psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"', user='postgres')
        if POSTGIS_VER[:1] == '2':
            sudo(f'psql -d template_postgis -f /usr/share/postgresql/9.1/contrib/postgis-{POSTGIS_VER[:3]}/rtpostgis.sql', user='postgres')


# Install GeoNode library
def deploy_geonode():
    sudo('apt-get install -y python-virtualenv')
    with cd(GEONODEDIR), prefix(ACT):
        # Fetch from GitHub
        sudo('apt-get install -y git')
        sudo('rm -rf setup')
        sudo(f'git clone -b {GEONODE_BRANCH} {GEONODE_GIT_URL} setup')
        # Install requirements, setup
        sudo('pip install -e setup')
        sudo(f'cp -r setup/geonode {PYLIBS}')
        sudo('cp setup/package/support/geonode.apache /etc/apache2/sites-available/geonode')
        sudo('rm -rf setup')
    sed('/etc/apache2/sites-available/geonode', 'REPLACE_WITH_SITEDIR', PYLIBS, use_sudo=True)
    sed('/etc/apache2/sites-available/geonode', '/var/www/geonode/wsgi/geonode.wsgi', f"{PYLIBS}/geonode/wsgi.py",
        use_sudo=True)
    # Fix geoserver auth config file
    sed('/usr/share/geoserver/data/security/auth/geonodeAuthProvider/config.xml', 'localhost:8000',
        'localhost', use_sudo=True)
    # Use debian package instead
    # sudo('git branch deb;paver deb')
    # sudo('dpkg -i geonode/geonode*.deb')


# Deploy custom project from current local directory
def deploy_project(project):
    # Put apps....change settings to get project apps automagically
    put(project, PYLIBS, use_sudo=True)
    with fab_settings(warn_only=True):
        for projdir in filter(os.path.isdir, glob.glob('*')):
            if projdir != 'shared' and projdir != 'data':
                put(projdir, PYLIBS, use_sudo=True)
    put('requirements.txt', GEONODEDIR, use_sudo=True)
    with cd(GEONODEDIR), prefix(ACT):
        sudo('pip install -r requirements.txt --upgrade')
        sudo('rm requirements.txt')
    put(f'{project}/{project}.apache', f'/etc/apache2/sites-available/{project}', use_sudo=True)
    sed(f'/etc/apache2/sites-available/{project}', 'REPLACE_WITH_SITEDIR', PYLIBS, use_sudo=True)
    with cd(os.path.join(PYLIBS, project)):
        sudo('ln -s settings_production.py local_settings.py')


def enable_site(project):
    with cd(PYLIBS), prefix(ACT):
        sudo(f'a2ensite {project}; service apache2 restart')
        sudo('mkdir /var/www/geonode; chown www-data:www-data /var/www/geonode')
        sudo(f'django-admin.py collectstatic --noinput --settings={project}.settings')


# TODO - test/fix this function
def restore_data(project):
    # Restore geoserver data
    gsdir = '/var/lib/tomcat6/webapps/geoserver'
    put('data/geoserver-data.tar', f"{gsdir}/geoserver-data.tar", use_sudo=True)
    with cd(gsdir):
        sudo('rm -rf data')
        sudo('tar xvf geoserver-data.tar')
        sudo('chown -R tomcat6:tomcat6 data')
    run('rm geoserver-data.tar')
    sudo('service tomcat6 restart')
    with prefix(ACT):
        sudo(f'django-admin.py cleardeadlayers --settings={project}.settings')
        sudo(f'django-admin.py updatelayers --settings={project}.settings')


def create_database(db, user, password):
    # sudo("dropdb %s" % db, user="postgres")
    # sudo("dropuser %s" % user, user="postgres")
    with fab_settings(warn_only=True):
        sudo(f"createuser -s {user}", user="postgres")
        sudo(f"createdb -O {user} {db} -T template_postgis", user="postgres")
        sudo(f"psql -c \"alter user {user} with encrypted password '{password}'\" ", user="postgres")


def setup_pgsql(project):
    import sys
    sys.path.append('.')
    exec(f'import {project}.settings_production as settings')
    db = settings.DATABASES['default']['NAME']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    create_database(db, user, password)
    with prefix(ACT):
        sudo(f'django-admin.py migrate --settings={project}.settings')
    # Need to restore database and GeoServer data
    # put('data/%s.sql' % db, GEONODEDIR, use_sudo=True)
    # sudo('psql -d %s -f %s/%s.sql' % (db, GEONODEDIR, db), user='postgres')


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
        sudo('cd build.geonode.org/geonode/latest;dpkg -i geonode_2.0.0*.deb', shell=True)
    sudo('apt-get install -f -y')


def change_admin_password():
    put('../misc/changepw.py', '/home/ubuntu/')
    run(f"perl -pi -e 's/replace.me.admin.user/{ADMIN_USER}/g' ~/changepw.py")
    run(f"perl -pi -e 's/replace.me.admin.pw/{ADMIN_PASSWORD}/g' ~/changepw.py")
    sudo('source /var/lib/geonode/bin/activate;cat ~/changepw.py | django-admin.py shell --settings=geonode.settings')
    run('rm ~/changepw.py')


def geonode_updateip(server_name="demo.geonode.org"):
    sudo(f'geonode-updateip {server_name}')


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
    sudo(f'rm -f ~/.ssh/*{KEY_BASE}.pem')
    put(f'{KEY_PATH}*{KEY_BASE}*', '/home/ubuntu/.ssh/', mode=0o400)


def install_ec2_tools():
    sudo(f'add-apt-repository "deb http://us-east-1.ec2.archive.ubuntu.com/ubuntu/ {UBUNTU_VERSION} multiverse"')
    sudo(f'add-apt-repository "deb http://us-east-1.ec2.archive.ubuntu.com/ubuntu/ {UBUNTU_VERSION}-updates multiverse"')
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
        sudo(f'export AWS_USER_ID={AWS_USER_ID}')
        sudo(f'export AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY_ID}')
        sudo(f'export AWS_SECRET_ACCESS_KEY={AWS_SECRET_ACCESS_KEY}')
    sudo(f'export ARCH={ARCH}')
    prefix = f"geonode-{VERSION}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    excludes = '/mnt,/root/.ssh,/home/ubuntu/.ssh,/tmp'
    sudo(f"ec2-bundle-vol -r {ARCH} -d /mnt -p {prefix} -u {AWS_USER_ID} -k ~/.ssh/pk-*.pem -c ~/.ssh/cert-*.pem -e {excludes}")
    sudo(f"ec2-upload-bundle -b {AMI_BUCKET} -m /mnt/{prefix}.manifest.xml -a {AWS_ACCESS_KEY_ID} -s {AWS_SECRET_ACCESS_KEY}")
    output = sudo(f'ec2-register --name "{AMI_BUCKET}/{prefix}" "{AMI_BUCKET}/{prefix}.manifest.xml" -K ~/.ssh/pk-*.pem -C ~/.ssh/cert-*.pem')
    ami_id = output.split('\t')[1]
    if MAKE_PUBLIC:
        sudo(f"ec2-modify-image-attribute -l -a all -K ~/.ssh/pk-*.pem -C ~/.ssh/cert-*.pem {ami_id}")
    print(f"AMI {ami_id} Ready for Use")


def install_sample_data():
    run('geonode loaddata sample_admin.json')
    run('geonode importlayers `python -c "import gisdata; print gisdata.GOOD_DATA"` -v 3')
    # Fix permissions issue on the newly created thumbs dir
    sudo('chmod -R 7777 /var/www/geonode/uploaded/thumbs/')
