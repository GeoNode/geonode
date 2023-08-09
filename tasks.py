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
import logging
import datetime

from urllib.parse import urlparse
from invoke import task

BOOTSTRAP_IMAGE_CHEIP = "codenvy/che-ip:nightly"

logger = logging.getLogger(__name__)


@task
def waitfordbs(ctx):
    print("**************************databases*******************************")
    db_host = os.getenv("DATABASE_HOST", "db")
    ctx.run(f"/usr/bin/wait-for-databases {db_host}", pty=True)


@task
def waitforgeoserver(ctx):
    print("****************************geoserver********************************")
    while not _gs_service_availability(f"{os.environ['GEOSERVER_LOCATION']}ows"):
        print("Wait for GeoServer API availability...")
    print("GeoServer is available for HTTP calls!")


@task
def update(ctx):
    print("***************************setting env*********************************")
    ctx.run("env", pty=True)
    pub_ip = _geonode_public_host_ip()
    print(f"Public Hostname or IP is {pub_ip}")
    pub_port = _geonode_public_port()
    print(f"Public PORT is {pub_port}")
    pub_protocol = "https" if pub_port == "443" else "http"
    if pub_protocol == "https" or pub_port == "80":
        pub_port = None
    db_url = _update_db_connstring()
    geodb_url = _update_geodb_connstring()
    service_ready = False
    while not service_ready:
        try:
            socket.gethostbyname("geonode")
            service_ready = True
        except Exception:
            time.sleep(10)

    override_env = "$HOME/.override_env"
    if os.path.exists(override_env):
        os.remove(override_env)
    else:
        print(f"Can not delete the {override_env} file as it doesn't exists")

    if pub_port:
        siteurl = f"{pub_protocol}://{pub_ip}:{pub_port}/"
        gs_pub_loc = f"http://{pub_ip}:{pub_port}/geoserver/"
    else:
        siteurl = f"{pub_protocol}://{pub_ip}/"
        gs_pub_loc = f"http://{pub_ip}/geoserver/"
    envs = {
        "local_settings": str(_localsettings()),
        "siteurl": os.environ.get("SITEURL", siteurl),
        "geonode_docker_host": str(socket.gethostbyname("geonode")),
        "public_protocol": pub_protocol,
        "public_fqdn": str(pub_ip) + str(f":{pub_port}" if pub_port else ""),
        "public_host": str(pub_ip),
        "dburl": os.environ.get("DATABASE_URL", db_url),
        "geodburl": os.environ.get("GEODATABASE_URL", geodb_url),
        "static_root": os.environ.get("STATIC_ROOT", "/mnt/volumes/statics/static/"),
        "media_root": os.environ.get("MEDIA_ROOT", "/mnt/volumes/statics/uploaded/"),
        "geoip_path": os.environ.get("GEOIP_PATH", "/mnt/volumes/statics/geoip.db"),
        "monitoring": os.environ.get("MONITORING_ENABLED", True),
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
    current_allowed.extend([str(pub_ip), f"{pub_ip}:{pub_port}"])
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
    ctx.run(f"python manage.py migrate --noinput --settings={_localsettings()} --database=datastore", pty=True)
    try:
        ctx.run(f"python manage.py rebuild_index --noinput --settings={_localsettings()}", pty=True)
    except Exception:
        pass


@task
def statics(ctx):
    print("**************************statics*******************************")
    try:
        ctx.run("mkdir -p /mnt/volumes/statics/{static,uploads}")
        ctx.run(f"python manage.py collectstatic --noinput --settings={_localsettings()}", pty=True)
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
    # Updating OAuth2 Service Config
    new_ext_ip = os.environ["SITEURL"]
    client_id = os.environ["OAUTH2_CLIENT_ID"]
    client_secret = os.environ["OAUTH2_CLIENT_SECRET"]
    oauth_config = "/geoserver_data/data/security/filter/geonode-oauth2/config.xml"
    ctx.run(f'sed -i "s|<cliendId>.*</cliendId>|<cliendId>{client_id}</cliendId>|g" {oauth_config}', pty=True)
    ctx.run(
        f'sed -i "s|<clientSecret>.*</clientSecret>|<clientSecret>{client_secret}</clientSecret>|g" {oauth_config}',
        pty=True,
    )
    ctx.run(
        f'sed -i "s|<userAuthorizationUri>.*</userAuthorizationUri>|<userAuthorizationUri>{new_ext_ip}o/authorize/</userAuthorizationUri>|g" {oauth_config}',  # noqa
        pty=True,
    )
    ctx.run(
        f'sed -i "s|<redirectUri>.*</redirectUri>|<redirectUri>{new_ext_ip}geoserver/index.html</redirectUri>|g" {oauth_config}',  # noqa
        pty=True,
    )
    ctx.run(
        f'sed -i "s|<logoutUri>.*</logoutUri>|<logoutUri>{new_ext_ip}account/logout/</logoutUri>|g" {oauth_config}',
        pty=True,
    )


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
        f"django-admin.py collectstatic --noinput \
--settings={_localsettings()}",
        pty=True,
    )


@task
def geoserverfixture(ctx):
    print("********************geoserver fixture********************************")
    _geoserver_info_provision(f"{os.environ['GEOSERVER_LOCATION']}rest/")


@task
def monitoringfixture(ctx):
    print("*******************monitoring fixture********************************")
    ctx.run("rm -rf /tmp/default_monitoring_apps_docker.json", pty=True)
    _prepare_monitoring_fixture()
    try:
        ctx.run(
            f"django-admin.py loaddata /tmp/default_monitoring_apps_docker.json \
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
        os.environ.get("ADMIN_PASSWORD", "admin"), os.environ.get("ADMIN_EMAIL", "admin@example.org")
    )
    ctx.run(
        f"django-admin.py loaddata /tmp/django_admin_docker.json \
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
    ctx.run("date > /mnt/volumes/statics/geonode_init.lock")


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


def _container_exposed_port(component, instname):
    port = "80"
    try:
        client = docker.from_env(version="1.24")
        ports_dict = json.dumps(
            [
                c.attrs["Config"]["ExposedPorts"]
                for c in client.containers.list(
                    filters={"label": f"org.geonode.component={component}", "status": "running"}
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
    user = os.getenv("GEONODE_DATABASE", "geonode")
    pwd = os.getenv("GEONODE_DATABASE_PASSWORD", "geonode")
    dbname = os.getenv("GEONODE_DATABASE", "geonode")
    dbhost = os.getenv("DATABASE_HOST", "db")
    dbport = os.getenv("DATABASE_PORT", 5432)
    connstr = f"postgis://{user}:{pwd}@{dbhost}:{dbport}/{dbname}"
    return connstr


def _update_geodb_connstring():
    geouser = os.getenv("GEONODE_GEODATABASE", "geonode_data")
    geopwd = os.getenv("GEONODE_GEODATABASE_PASSWORD", "geonode_data")
    geodbname = os.getenv("GEONODE_GEODATABASE", "geonode_data")
    dbhost = os.getenv("DATABASE_HOST", "db")
    dbport = os.getenv("DATABASE_PORT", 5432)
    geoconnstr = f"postgis://{geouser}:{geopwd}@{dbhost}:{dbport}/{geodbname}"
    return geoconnstr


def _localsettings():
    settings = os.getenv("DJANGO_SETTINGS_MODULE", "geonode.settings")
    return settings


def _gs_service_availability(url):
    import requests

    try:
        r = requests.request("get", url, verify=False)
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.error(f"GeoServer connection error is {e}")
        return False
    except requests.exceptions.HTTPError as er:
        logger.error(f"GeoServer HTTP error is {er}")
        return False
    else:
        logger.info("GeoServer API are available!")
        return True


def _geonode_public_host_ip():
    gn_pub_hostip = os.getenv("GEONODE_LB_HOST_IP", None)
    if not gn_pub_hostip:
        gn_pub_hostip = _docker_host_ip()
    return gn_pub_hostip


def _geonode_public_port():
    gn_pub_port = os.getenv("GEONODE_LB_PORT", "")
    if not gn_pub_port:
        gn_pub_port = _container_exposed_port("nginx", os.getenv("GEONODE_INSTANCE_NAME", "geonode"))
    elif gn_pub_port in ("80", "443"):
        gn_pub_port = None
    return gn_pub_port


def _geoserver_info_provision(url):
    from django.conf import settings
    from geoserver.catalog import Catalog

    print("Setting GeoServer Admin Password...")
    cat = Catalog(url, username=settings.OGC_SERVER_DEFAULT_USER, password=settings.OGC_SERVER_DEFAULT_PASSWORD)
    headers = {"Content-type": "application/xml", "Accept": "application/xml"}
    data = f"""<?xml version="1.0" encoding="UTF-8"?>
<userPassword>
    <newPassword>{(os.getenv('GEOSERVER_ADMIN_PASSWORD', 'geoserver'))}</newPassword>
</userPassword>"""

    response = cat.http_request(f"{cat.service_url}/security/self/password", method="PUT", data=data, headers=headers)
    print(f"Response Code: {response.status_code}")
    if response.status_code == 200:
        print("GeoServer admin password updated SUCCESSFULLY!")
    else:
        logger.warning(f"WARNING: GeoServer admin password *NOT* updated: code [{response.status_code}]")


def _prepare_oauth_fixture():
    upurl = urlparse(os.environ["SITEURL"])
    net_scheme = upurl.scheme
    pub_ip = _geonode_public_host_ip()
    print(f"Public Hostname or IP is {pub_ip}")
    pub_port = _geonode_public_port()
    print(f"Public PORT is {pub_port}")
    default_fixture = [
        {
            "model": "oauth2_provider.application",
            "pk": 1001,
            "fields": {
                "skip_authorization": True,
                "created": "2018-05-31T10:00:31.661Z",
                "updated": "2018-05-31T11:30:31.245Z",
                "algorithm": "RS256",
                "redirect_uris": f"{net_scheme}://{pub_ip}:{pub_port}/geoserver/index.html"
                if pub_port
                else f"{net_scheme}://{pub_ip}/geoserver/index.html",
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
        {"model": "sites.site", "pk": 1, "fields": {"domain": str(upurl.hostname), "name": str(upurl.hostname)}}
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
            "fields": {"active": True, "ip": str(geonode_ip), "name": str(os.environ["MONITORING_HOST_NAME"])},
            "model": "monitoring.host",
            "pk": 1,
        },
        {"fields": {"active": True, "ip": str(geoserver_ip), "name": "geoserver"}, "model": "monitoring.host", "pk": 2},
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
