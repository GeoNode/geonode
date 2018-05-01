import json
import logging
import os
import re

import docker

from invoke import run, task

BOOTSTRAP_IMAGE_CHEIP = 'codenvy/che-ip:nightly'


@task
def waitfordbs(ctx):
    print "**************************databases*******************************"
    ctx.run("/usr/bin/wait-for-databases {0}".format('db'), pty=True)


@task
def update(ctx):
    print "***************************initial*********************************"
    ctx.run("env", pty=True)
    pub_ip = _geonode_public_host_ip()
    print "Public Hostname or IP is {0}".format(pub_ip)
    pub_port = _geonode_public_port()
    print "Public PORT is {0}".format(pub_port)
    db_url = _update_db_connstring()
    geodb_url = _update_geodb_connstring()
    envs = {
        "public_fqdn": "{0}:{1}".format(pub_ip, pub_port),
        "public_host": "{0}".format(pub_ip),
        "dburl": db_url,
        "geodburl": geodb_url,
        "override_fn": "$HOME/.override_env"
    }
    ctx.run("echo export GEOSERVER_PUBLIC_LOCATION=\
http://{public_fqdn}/geoserver/ >> {override_fn}".format(**envs), pty=True)
    ctx.run("echo export SITEURL=\
http://{public_fqdn}/ >> {override_fn}".format(**envs), pty=True)
    ctx.run("echo export ALLOWED_HOSTS=\
\"\\\"['{public_fqdn}', '{public_host}', 'django', 'geonode',]\\\"\" \
>> {override_fn}".format(**envs), pty=True)
    ctx.run("echo export DATABASE_URL=\
{dburl} >> {override_fn}".format(**envs), pty=True)
    ctx.run("echo export GEODATABASE_URL=\
{geodburl} >> {override_fn}".format(**envs), pty=True)
    ctx.run("source $HOME/.override_env", pty=True)
    print "****************************final**********************************"
    ctx.run("env", pty=True)


@task
def migrations(ctx):
    print "**************************migrations*******************************"
    ctx.run("django-admin.py migrate --noinput --settings={0}".format(
        _localsettings()
    ), pty=True)


@task
def prepare(ctx):
    print "**********************prepare fixture***************************"
    ctx.run("rm -rf /tmp/default_oauth_apps_docker.json", pty=True)
    _prepare_oauth_fixture()


@task
def fixtures(ctx):
    print "**************************fixtures********************************"
    ctx.run("django-admin.py loaddata sample_admin \
--settings={0}".format(_localsettings()), pty=True)
    ctx.run("django-admin.py loaddata /tmp/default_oauth_apps_docker.json \
--settings={0}".format(_localsettings()), pty=True)
    ctx.run("django-admin.py loaddata geonode/base/fixtures/initial_data.json \
--settings={0}".format(_localsettings()), pty=True)


def _docker_host_ip():
    client = docker.from_env()
    ip_list = client.containers.run(BOOTSTRAP_IMAGE_CHEIP,
                                    network_mode='host'
                                    ).split("\n")
    if len(ip_list) > 1:
        print("Docker daemon is running on more than one \
address {0}".format(ip_list))
        print("Only the first address:{0} will be returned!".format(
            ip_list[0]
        ))
    else:
        print("Docker daemon is running at the following \
address {0}".format(ip_list[0]))
    return ip_list[0]


def _container_exposed_port(component, instname):
    client = docker.from_env()
    ports_dict = json.dumps(
        [c.attrs['Config']['ExposedPorts'] for c in client.containers.list(
            filters={
                'label': 'org.geonode.component={0}'.format(component),
                'status': 'running'
            }
        ) if '{0}'.format(instname) in c.name][0]
    )
    for key in json.loads(ports_dict):
        port = re.split('/tcp', key)[0]
    return port


def _update_db_connstring():
    user = os.getenv('GEONODE_DATABASE', 'geonode')
    pwd = os.getenv('GEONODE_DATABASE_PASSWORD', 'geonode')
    dbname = os.getenv('GEONODE_DATABASE', 'geonode')
    connstr = 'postgres://{0}:{1}@db:5432/{2}'.format(
        user,
        pwd,
        dbname
    )
    return connstr


def _update_geodb_connstring():
    geouser = os.getenv('GEONODE_GEODATABASE', 'geonode_data')
    geopwd = os.getenv('GEONODE_GEODATABASE_PASSWORD', 'geonode_data')
    geodbname = os.getenv('GEONODE_GEODATABASE', 'geonode_data')
    geoconnstr = 'postgis://{0}:{1}@db:5432/{2}'.format(
        geouser,
        geopwd,
        geodbname
    )
    return geoconnstr


def _localsettings():
    settings = os.getenv('DJANGO_SETTINGS_MODULE', 'geonode.settings')
    return settings


def _geonode_public_host_ip():
    gn_pub_hostip = os.getenv('GEONODE_LB_HOST_IP', '')
    if not gn_pub_hostip:
        gn_pub_hostip = _docker_host_ip()
    return gn_pub_hostip


def _geonode_public_port():
    gn_pub_port = os.getenv('GEONODE_LB_PORT', '')
    if not gn_pub_port:
        gn_pub_port = _container_exposed_port(
            'nginx',
            os.getenv('GEONODE_INSTANCE_NAME', 'geonode')
        )
    return gn_pub_port


def _prepare_oauth_fixture():
    pub_ip = _geonode_public_host_ip()
    print "Public Hostname or IP is {0}".format(pub_ip)
    pub_port = _geonode_public_port()
    print "Public PORT is {0}".format(pub_port)
    default_fixture = [
        {
            "model": "oauth2_provider.application",
            "pk": 1001,
            "fields": {
                "skip_authorization": True,
                "redirect_uris": "http://{0}:{1}/geoserver/index.html".format(
                    pub_ip, pub_port
                ),
                "name": "GeoServer",
                "authorization_grant_type": "authorization-code",
                "client_type": "confidential",
                "client_id": "Jrchz2oPY3akmzndmgUTYrs9gczlgoV20YPSvqaV",
                "client_secret": "\
rCnp5txobUo83EpQEblM8fVj3QT5zb5qRfxNsuPzCqZaiRyIoxM4jdgMiZKFfePBHYXCLd7B8NlkfDB\
Y9HKeIQPcy5Cp08KQNpRHQbjpLItDHv12GvkSeXp6OxaUETv3",
                "user": [
                    "admin"
                ]
            }
        }
    ]
    with open('/tmp/default_oauth_apps_docker.json', 'w') as fixturefile:
        json.dump(default_fixture, fixturefile)
