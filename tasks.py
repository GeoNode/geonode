import json
import logging
import os
import re

import docker

from invoke import run, task

BOOTSTRAP_IMAGE_CHEIP = 'codenvy/che-ip:nightly'


@task
def update(ctx):
    print "***************************initial*********************************"
    ctx.run("env", pty=True)
    pub_ip = _docker_host_ip()
    print "Public IP is {0}".format(pub_ip)
    pub_port = _nginx_exposed_port()
    print "Public PORT is {0}".format(pub_port)
    envs = {
        "sitedomain": "{0}:{1}".format(pub_ip, pub_port),
        "override_fn": "$HOME/.override_env"
    }
    ctx.run("echo export GEOSERVER_PUBLIC_LOCATION=\
http://{sitedomain}/geoserver/ >> {override_fn}".format(**envs), pty=True)
    ctx.run("echo export SITEURL=\
http://{sitedomain}/ >> {override_fn}".format(**envs), pty=True)
    ctx.run("echo export ALLOWED_HOSTS=\
['{sitedomain}',] >> {override_fn}".format(**envs), pty=True)
    ctx.run("source $HOME/.override_env", pty=True)
    print "****************************final**********************************"
    ctx.run("env", pty=True)


@task
def migrations(ctx):
    print "**************************migrations*******************************"
    ctx.run("django-admin.py migrate --noinput", pty=True)


@task
def prepare(ctx):
    print "**********************prepare fixture***************************"
    ctx.run("rm -rf /tmp/default_oauth_apps_docker.json", pty=True)
    _prepare_oauth_fixture()


@task
def fixtures(ctx):
    print "**************************fixtures********************************"
    ctx.run("django-admin.py loaddata sample_admin", pty=True)
    ctx.run("django-admin.py loaddata /tmp/default_oauth_apps_docker.json",
            pty=True
            )
    ctx.run("django-admin.py loaddata geonode/base/fixtures/initial_data.json",
            pty=True
            )


def _docker_host_ip():
    client = docker.from_env()
    ip = client.containers.run(BOOTSTRAP_IMAGE_CHEIP, network_mode='host')
    print("Docker daemon is running at the following \
address {0}".format(ip))
    return ip.replace("\n", "")


def _nginx_exposed_port():
    client = docker.from_env()
    ports_dict = json.dumps(
        [c.attrs['Config']['ExposedPorts'] for c in client.containers.list(
        ) if c.status in 'running' and 'nginx4' in c.name][0]
    )
    for key in json.loads(ports_dict):
        port = re.split('/tcp', key)[0]
    return port


def _prepare_oauth_fixture():
    pub_ip = _docker_host_ip()
    print "Public IP is {0}".format(pub_ip)
    pub_port = _nginx_exposed_port()
    print "Public PORT is {0}".format(pub_port)
    default_fixture = [
        {
            "model": "oauth2_provider.application",
            "pk": 1001,
            "fields": {
                "skip_authorization": True,
                "redirect_uris": "http://{0}:{1}/geoserver".format(
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
