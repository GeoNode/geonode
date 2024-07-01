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
import os
import re
import ast
import json
import time
import docker
import socket
import ipaddress
import logging
import datetime
from pathlib import Path

from urllib.parse import urlparse, urlunparse
from invoke import task

BOOTSTRAP_IMAGE_CHEIP = "codenvy/che-ip:nightly"

logger = logging.getLogger(__name__)


@task
def waitfordbs(ctx):
    print("**************************databases*******************************")
    db_host = os.getenv("DATABASE_HOST", "db")
    ctx.run(f"/usr/bin/wait-for-databases {db_host}", pty=True)


@task
def update(ctx):
    print("***************************setting env*********************************")
    ctx.run("env", pty=True)
    pub_host = _geonode_public_host()
    print(f"Public Hostname is {pub_host}")
    pub_port = _geonode_public_port()
    print(f"Public PORT is {pub_port}")
    pub_protocol = "https" if pub_port == "443" else "http"
    if pub_protocol == "https" or pub_port == "80":
        pub_port = None
    db_url = _update_db_connstring()
    geodb_url = _update_geodb_connstring()
    geonode_docker_host = None
    for _cnt in range(1, 29):
        try:
            geonode_docker_host = str(socket.gethostbyname("geonode"))
            break
        except Exception:
            print(f"...waiting for NGINX to pop-up...{_cnt}")
            time.sleep(1)

    override_env = "$HOME/.override_env"
    if os.path.exists(override_env):
        os.remove(override_env)
    else:
        print(f"Can not delete the {override_env} file as it doesn't exists")

    if pub_port:
        siteurl = f"{pub_protocol}://{pub_host}:{pub_port}/"
        gs_pub_loc = f"http://{pub_host}:{pub_port}/geoserver/"
    else:
        siteurl = f"{pub_protocol}://{pub_host}/"
        gs_pub_loc = f"http://{pub_host}/geoserver/"
    envs = {
        "local_settings": str(_localsettings()),
        "siteurl": os.environ.get("SITEURL", siteurl),
        "geonode_docker_host": geonode_docker_host,
        "public_protocol": pub_protocol,
        "public_fqdn": str(pub_host) + str(f":{pub_port}" if pub_port else ""),
        "public_host": str(pub_host),
        "dburl": os.environ.get("DATABASE_URL", db_url),
        "geodburl": os.environ.get("GEODATABASE_URL", geodb_url),
        "static_root": os.environ.get("STATIC_ROOT", "/mnt/volumes/statics/static/"),
        "media_root": os.environ.get("MEDIA_ROOT", "/mnt/volumes/statics/uploaded/"),
        "geoip_path": os.environ.get("GEOIP_PATH", "/mnt/volumes/statics/geoip.db"),
        "monitoring": os.environ.get("MONITORING_ENABLED", False),
        "monitoring_host_name": os.environ.get("MONITORING_HOST_NAME", "geonode"),
        "monitoring_service_name": os.environ.get("MONITORING_SERVICE_NAME", "local-geonode"),
        "monitoring_data_ttl": os.environ.get("MONITORING_DATA_TTL", 7),
        "geonode_geodb_passwd": os.environ.get("GEONODE_GEODATABASE_PASSWORD", "geonode_data"),
        "default_backend_datastore": os.environ.get("DEFAULT_BACKEND_DATASTORE", "datastore"),
        "geonode_db_passwd": os.environ.get("GEONODE_DATABASE_PASSWORD", "geonode"),
        "geonode_geodb": os.environ.get("GEONODE_GEODATABASE", "geonode_data"),
        "db_url": os.environ.get("DATABASE_URL", "postgis://geonode:geonode@db:5432/geonode"),
        "geodb_url": os.environ.get("GEODATABASE_URL", "postgis://geonode:geonode@db:5432/geonode_data"),
        "geonode_db": os.environ.get("GEONODE_DATABASE", "geonode"),
        "gs_loc": os.environ.get("GEOSERVER_LOCATION", "http://geoserver:8080/geoserver/"),
        "gs_web_ui_loc": os.environ.get("GEOSERVER_WEB_UI_LOCATION", gs_pub_loc),
        "gs_pub_loc": os.environ.get("GEOSERVER_PUBLIC_LOCATION", gs_pub_loc),
        "gs_admin_pwd": os.environ.get("GEOSERVER_ADMIN_PASSWORD", "geoserver"),
        "override_fn": override_env,
    }
    try:
        current_allowed = ast.literal_eval(
            os.getenv("ALLOWED_HOSTS")
            or "['{public_fqdn}', '{public_host}', 'localhost', 'django', 'geonode',]".format(**envs)
        )
    except ValueError:
        current_allowed = []
    current_allowed.extend([str(pub_host), f"{pub_host}:{pub_port}"])
    allowed_hosts = [str(c) for c in current_allowed] + ['"geonode"', '"django"']

    ctx.run(
        "echo export DJANGO_SETTINGS_MODULE=\
{local_settings} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export MONITORING_ENABLED=\
{monitoring} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export MONITORING_HOST_NAME=\
{monitoring_host_name} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export MONITORING_SERVICE_NAME=\
{monitoring_service_name} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export MONITORING_DATA_TTL=\
{monitoring_data_ttl} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEOIP_PATH=\
{geoip_path} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEONODE_GEODATABASE_PASSWORD=\
{geonode_geodb_passwd} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export DEFAULT_BACKEND_DATASTORE=\
{default_backend_datastore} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEONODE_DATABASE_PASSWORD=\
{geonode_db_passwd} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEONODE_GEODATABASE=\
{geonode_geodb} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export DATABASE_URL=\
{db_url} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEODATABASE_URL=\
{geodb_url} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEONODE_DATABASE=\
{geonode_db} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEOSERVER_LOCATION=\
{gs_loc} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEOSERVER_WEB_UI_LOCATION=\
{gs_web_ui_loc} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEOSERVER_PUBLIC_LOCATION=\
{gs_pub_loc} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEOSERVER_ADMIN_PASSWORD=\
{gs_admin_pwd} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export SITEURL=\
{siteurl} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        'echo export ALLOWED_HOSTS=\
"\\"{}\\"" >> {override_fn}'.format(
            allowed_hosts, **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export DATABASE_URL=\
{dburl} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEODATABASE_URL=\
{geodburl} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export STATIC_ROOT=\
{static_root} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export MEDIA_ROOT=\
{media_root} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export GEOIP_PATH=\
{geoip_path} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export LOGIN_URL=\
{siteurl}account/login/ >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export LOGOUT_URL=\
{siteurl}account/logout/ >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export LOGIN_REDIRECT_URL=\
{siteurl} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(
        "echo export LOGOUT_REDIRECT_URL=\
{siteurl} >> {override_fn}".format(
            **envs
        ),
        pty=True,
    )
    ctx.run(f"source {override_env}", pty=True)
    print("****************************finalize env**********************************")
    ctx.run("env", pty=True)


@task
def migrations(ctx):
    print("**************************migrations*******************************")
    ctx.run(f"python manage.py migrate --noinput --settings={_localsettings()}", pty=True)
    ctx.run(
        f"python manage.py migrate --noinput --settings={_localsettings()} --database=datastore",
        pty=True,
    )
    try:
        ctx.run(
            f"python manage.py rebuild_index --noinput --settings={_localsettings()}",
            pty=True,
        )
    except Exception:
        pass


@task
def statics(ctx):
    print("**************************statics*******************************")
    try:
        static_root = os.environ.get("STATIC_ROOT", "/mnt/volumes/statics/static/")
        media_root = os.environ.get("MEDIA_ROOT", "/mnt/volumes/statics/uploaded/")
        assets_root = os.environ.get("ASSETS_ROOT", "/mnt/volumes/statics/assets/")

        ctx.run(f"mkdir -pv {static_root} {media_root} {assets_root}")
        ctx.run(
            f"python manage.py collectstatic --noinput --settings={_localsettings()}",
            pty=True,
        )
    except Exception:
        import traceback

        traceback.print_exc()


@task
def prepare(ctx):
    print("**********************prepare fixture***************************")
    ctx.run("rm -rf /tmp/default_oauth_apps_docker.json", pty=True)
    _prepare_oauth_fixture()
    ctx.run("rm -rf /tmp/default_site.json", pty=True)
    _prepare_site_fixture()


@task
def fixtures(ctx):
    print("**************************fixtures********************************")
    ctx.run(
        f"python manage.py loaddata sample_admin \
--settings={_localsettings()}",
        pty=True,
    )
    ctx.run(
        f"python manage.py loaddata /tmp/default_oauth_apps_docker.json \
--settings={_localsettings()}",
        pty=True,
    )
    ctx.run(
        f"python manage.py loaddata geonode/base/fixtures/initial_data.json \
--settings={_localsettings()}",
        pty=True,
    )


@task
def collectstatic(ctx):
    print("************************static artifacts******************************")
    ctx.run(
        f"django-admin collectstatic --noinput \
--settings={_localsettings()}",
        pty=True,
    )


@task
def monitoringfixture(ctx):
    if ast.literal_eval(os.environ.get("MONITORING_ENABLED", "False")):
        print("*******************monitoring fixture********************************")
        ctx.run("rm -rf /tmp/default_monitoring_apps_docker.json", pty=True)
        _prepare_monitoring_fixture()
        try:
            ctx.run(
                f"django-admin loaddata geonode/monitoring/fixtures/metric_data.json \
    --settings={_localsettings()}",
                pty=True,
            )
            ctx.run(
                f"django-admin loaddata geonode/monitoring/fixtures/notifications.json \
    --settings={_localsettings()}",
                pty=True,
            )
            ctx.run(
                f"django-admin loaddata /tmp/default_monitoring_apps_docker.json \
    --settings={_localsettings()}",
                pty=True,
            )
        except Exception as e:
            logger.error(f"ERROR installing monitoring fixture: {str(e)}")


@task
def updateadmin(ctx):
    print("***********************update admin details**************************")
    ctx.run("rm -rf /tmp/django_admin_docker.json", pty=True)
    _prepare_admin_fixture(
        os.environ.get("ADMIN_PASSWORD", "admin"),
        os.environ.get("ADMIN_EMAIL", "admin@example.org"),
    )
    ctx.run(
        f"django-admin loaddata /tmp/django_admin_docker.json \
--settings={_localsettings()}",
        pty=True,
    )


@task
def collectmetrics(ctx):
    print("************************collect metrics******************************")
    ctx.run(
        f"python -W ignore manage.py collect_metrics  \
--settings={_localsettings()} -n -t xml",
        pty=True,
    )


@task
def initialized(ctx):
    print("**************************init file********************************")
    static_root = os.environ.get("STATIC_ROOT", "/mnt/volumes/statics/static/")
    lockfile_dir = Path(static_root).parent  # quite ugly, we're assuming such dir exists and is writable
    ctx.run(f"date > {lockfile_dir}/geonode_init.lock")


def _docker_host_ip():
    try:
        client = docker.from_env(version="1.24")
        ip_list = client.containers.run(BOOTSTRAP_IMAGE_CHEIP, network_mode="host").split("\n")
    except Exception:
        import traceback

        traceback.print_exc()
        ip_list = [
            "127.0.0.1",
        ]
    if len(ip_list) > 1:
        print(
            f"Docker daemon is running on more than one \
address {ip_list}"
        )
        print(f"Only the first address:{ip_list[0]} will be returned!")
    else:
        print(
            f"Docker daemon is running at the following \
address {ip_list[0]}"
        )
    return ip_list[0]


def _is_valid_ip(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except Exception as e:
        return False


def _container_exposed_port(component, instname):
    port = "80"
    try:
        client = docker.from_env(version="1.24")
        ports_dict = json.dumps(
            [
                c.attrs["Config"]["ExposedPorts"]
                for c in client.containers.list(
                    filters={
                        "label": f"org.geonode.component={component}",
                        "status": "running",
                    }
                )
                if str(instname) in c.name
            ][0]
        )
        for key in json.loads(ports_dict):
            port = re.split("/tcp", key)[0]
    except Exception:
        import traceback

        traceback.print_exc()
    return port


def _update_db_connstring():
    connstr = os.getenv("DATABASE_URL", None)
    if not connstr:
        user = os.getenv("GEONODE_DATABASE_USER", "geonode")
        pwd = os.getenv("GEONODE_DATABASE_PASSWORD", "geonode")
        dbname = os.getenv("GEONODE_DATABASE", "geonode")
        dbhost = os.getenv("DATABASE_HOST", "db")
        dbport = os.getenv("DATABASE_PORT", 5432)
        connstr = f"postgis://{user}:{pwd}@{dbhost}:{dbport}/{dbname}"
    return connstr


def _update_geodb_connstring():
    geoconnstr = os.getenv("GEODATABASE_URL", None)
    if not geoconnstr:
        geouser = os.getenv("GEONODE_GEODATABASE_USER", "geonode_data")
        geopwd = os.getenv("GEONODE_GEODATABASE_PASSWORD", "geonode_data")
        geodbname = os.getenv("GEONODE_GEODATABASE", "geonode_data")
        dbhost = os.getenv("DATABASE_HOST", "db")
        dbport = os.getenv("DATABASE_PORT", 5432)
        geoconnstr = f"postgis://{geouser}:{geopwd}@{dbhost}:{dbport}/{geodbname}"
    return geoconnstr


def _localsettings():
    settings = os.getenv("DJANGO_SETTINGS_MODULE", "geonode.settings")
    return settings


def _geonode_public_host():
    gn_pub_hostip = os.getenv("GEONODE_LB_HOST_IP", None)
    if not gn_pub_hostip:
        gn_pub_hostip = _docker_host_ip()
    return gn_pub_hostip


def _geonode_public_host_ip():
    gn_pub_hostip = os.getenv("GEONODE_LB_HOST_IP", None)
    if not gn_pub_hostip or not _is_valid_ip(gn_pub_hostip):
        gn_pub_hostip = _docker_host_ip()
    return gn_pub_hostip


def _geonode_public_port():
    gn_pub_port = os.getenv("GEONODE_LB_PORT", "")
    if not gn_pub_port:
        gn_pub_port = _container_exposed_port("nginx", os.getenv("GEONODE_INSTANCE_NAME", "geonode"))
    elif gn_pub_port in ("80", "443"):
        gn_pub_port = None
    return gn_pub_port


def _prepare_oauth_fixture():
    upurl = urlparse(os.environ["SITEURL"])
    default_fixture = [
        {
            "model": "oauth2_provider.application",
            "pk": 1001,
            "fields": {
                "skip_authorization": True,
                "created": "2018-05-31T10:00:31.661Z",
                "updated": "2018-05-31T11:30:31.245Z",
                "algorithm": "RS256",
                "redirect_uris": f"{urlunparse(upurl)}geoserver/index.html",
                "name": "GeoServer",
                "authorization_grant_type": "authorization-code",
                "client_type": "confidential",
                "client_id": str(os.environ["OAUTH2_CLIENT_ID"]),
                "client_secret": str(os.environ["OAUTH2_CLIENT_SECRET"]),
                "user": ["admin"],
            },
        }
    ]
    with open("/tmp/default_oauth_apps_docker.json", "w") as fixturefile:
        json.dump(default_fixture, fixturefile)


def _prepare_site_fixture():
    upurl = urlparse(os.environ["SITEURL"])
    default_fixture = [
        {
            "model": "sites.site",
            "pk": 1,
            "fields": {"domain": str(upurl.hostname), "name": str(upurl.hostname)},
        }
    ]
    with open("/tmp/default_site.json", "w") as fixturefile:
        json.dump(default_fixture, fixturefile)


def _prepare_monitoring_fixture():
    # upurl = urlparse(os.environ['SITEURL'])
    # net_scheme = upurl.scheme
    # net_loc = upurl.netloc
    pub_ip = _geonode_public_host_ip()
    print(f"Public Hostname or IP is {pub_ip}")
    pub_port = _geonode_public_port()
    print(f"Public PORT is {pub_port}")
    try:
        geonode_ip = socket.gethostbyname("geonode")
    except Exception:
        geonode_ip = pub_ip
    try:
        geoserver_ip = socket.gethostbyname("geoserver")
    except Exception:
        geoserver_ip = pub_ip
    d = "1970-01-01 00:00:00"
    default_fixture = [
        {
            "fields": {
                "active": True,
                "ip": str(geonode_ip),
                "name": str(os.environ["MONITORING_HOST_NAME"]),
            },
            "model": "monitoring.host",
            "pk": 1,
        },
        {
            "fields": {"active": True, "ip": str(geoserver_ip), "name": "geoserver"},
            "model": "monitoring.host",
            "pk": 2,
        },
        {
            "fields": {
                "name": str(os.environ["MONITORING_SERVICE_NAME"]),
                "url": str(os.environ["SITEURL"]),
                "notes": "",
                "last_check": d,
                "active": True,
                "host": 1,
                "check_interval": "00:01:00",
                "service_type": 1,
            },
            "model": "monitoring.service",
            "pk": 1,
        },
        {
            "fields": {
                "name": "geoserver-hostgeonode",
                "url": str(os.environ["SITEURL"]),
                "notes": "",
                "last_check": d,
                "active": True,
                "host": 1,
                "check_interval": "00:01:00",
                "service_type": 3,
            },
            "model": "monitoring.service",
            "pk": 2,
        },
        {
            "fields": {
                "name": "geoserver-hostgeoserver",
                "url": str(os.environ["GEOSERVER_PUBLIC_LOCATION"]),
                "notes": "",
                "last_check": d,
                "active": True,
                "host": 2,
                "check_interval": "00:01:00",
                "service_type": 4,
            },
            "model": "monitoring.service",
            "pk": 3,
        },
        {
            "fields": {
                "name": "default-geoserver",
                "url": "http://geoserver:8080/geoserver/",
                "notes": "",
                "last_check": d,
                "active": True,
                "host": 2,
                "check_interval": "00:01:00",
                "service_type": 2,
            },
            "model": "monitoring.service",
            "pk": 4,
        },
    ]
    with open("/tmp/default_monitoring_apps_docker.json", "w") as fixturefile:
        json.dump(default_fixture, fixturefile)


def _prepare_admin_fixture(admin_password, admin_email):
    from django.contrib.auth.hashers import make_password

    d = datetime.datetime.now()
    mdext_date = f"{d.isoformat()[:23]}Z"
    default_fixture = [
        {
            "fields": {
                "date_joined": mdext_date,
                "email": admin_email,
                "first_name": "",
                "groups": [],
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
                "last_login": mdext_date,
                "last_name": "",
                "password": make_password(admin_password),
                "user_permissions": [],
                "username": "admin",
            },
            "model": "people.Profile",
            "pk": 1000,
        }
    ]
    with open("/tmp/django_admin_docker.json", "w") as fixturefile:
        json.dump(default_fixture, fixturefile)
