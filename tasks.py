# -*- coding: utf-8 -*-
import os
import re
import ast
import json
import time
import socket
import logging
import datetime
from pathlib import Path

from urllib.parse import urlparse, urlunparse
from invoke import task

logger = logging.getLogger(__name__)


@task
def update(ctx):
    print("***************************setting env*********************************")
    pub_host = _geonode_public_host()
    print(f"Public Hostname or IP is {pub_host}")
    pub_port = _geonode_public_port()
    print(f"Public PORT is {pub_port}")
    
    pub_protocol = "https" if pub_port == "443" else "http"
    if pub_protocol == "https" or pub_port == "80":
        pub_port = None
        
    db_url = _update_db_connstring()
    geodb_url = _update_geodb_connstring()
    
    geonode_docker_host = None
    for _cnt in range(1, 60):
        try:
            geonode_docker_host = str(socket.gethostbyname("nginx"))
            break
        except Exception:
            if _cnt % 4 == 0:
                print(f"...waiting for NGINX to pop-up...{_cnt // 4}")
            time.sleep(0.25)
            
    if not geonode_docker_host:
        geonode_docker_host = "127.0.0.1"

    override_env = os.path.expandvars("$HOME/.override_env")
    if os.path.exists(override_env):
        try:
            os.remove(override_env)
        except OSError:
            pass

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
        "asset_root": os.environ.get("ASSETS_ROOT", "/mnt/volumes/statics/assets/"),
        "geoip_path": os.environ.get("GEOIP_PATH", "/mnt/volumes/statics/geoip.db"),
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
            os.getenv("ALLOWED_HOSTS") or "['{public_fqdn}', '{public_host}', 'localhost', 'django', 'geonode',]".format(**envs)
        )
    except ValueError:
        current_allowed = []
    current_allowed.extend([str(pub_host), f"{pub_host}:{pub_port}"])
    allowed_hosts = [str(c) for c in current_allowed] + ['"nginx"', '"django"']

    # Preserved 100% original string format to avoid parsing errors
    content = f"""export DJANGO_SETTINGS_MODULE={envs['local_settings']}
    export GEONODE_GEODATABASE_PASSWORD={envs['geonode_geodb_passwd']}
    export DEFAULT_BACKEND_DATASTORE={envs['default_backend_datastore']}
    export GEONODE_DATABASE_PASSWORD={envs['geonode_db_passwd']}
    export GEONODE_GEODATABASE={envs['geonode_geodb']}
    export DATABASE_URL={envs['db_url']}
    export GEODATABASE_URL={envs['geodb_url']}
    export GEONODE_DATABASE={envs['geonode_db']}
    export GEOSERVER_LOCATION={envs['gs_loc']}
    export GEOSERVER_WEB_UI_LOCATION={envs['gs_web_ui_loc']}
    export GEOSERVER_PUBLIC_LOCATION={envs['gs_pub_loc']}
    export GEOSERVER_ADMIN_PASSWORD={envs['gs_admin_pwd']}
    export SITEURL={envs['siteurl']}
    export ALLOWED_HOSTS="\\"{allowed_hosts}\\""
    export DATABASE_URL={envs['dburl']}
    export GEODATABASE_URL={envs['geodburl']}
    export STATIC_ROOT={envs['static_root']}
    export MEDIA_ROOT={envs['media_root']}
    export GEOIP_PATH={envs['geoip_path']}
    export LOGIN_URL={envs['siteurl']}account/login/
    export LOGOUT_URL={envs['siteurl']}account/logout/
    export LOGIN_REDIRECT_URL={envs['siteurl']}
    export LOGOUT_REDIRECT_URL={envs['siteurl']}"""

    ctx.run(f'echo "{content}" >> {envs["override_fn"]}', pty=True)
    ctx.run(f"source {override_env}", pty=True)


@task
def migrations(ctx):
    print("**************************migrations*******************************")
    settings = _localsettings()
    ctx.run(
        f"source $HOME/.override_env && "
        f"python manage.py migrate --noinput --settings={settings} && "
        f"python manage.py migrate dynamic_models --noinput --settings={settings} --database=datastore",
        pty=True,
    )


@task
def statics(ctx):
    print("**************************statics*******************************")
    try:
        static_root = os.environ.get("STATIC_ROOT", "/mnt/volumes/statics/static/")
        media_root = os.environ.get("MEDIA_ROOT", "/mnt/volumes/statics/uploaded/")
        assets_root = os.environ.get("ASSETS_ROOT", "/mnt/volumes/statics/assets/")

        ctx.run(
            f"source $HOME/.override_env && "
            f"mkdir -pv {static_root} {media_root} {assets_root} && "
            f"python manage.py collectstatic --noinput --settings={_localsettings()}",
            pty=True,
        )
    except Exception:
        import traceback
        traceback.print_exc()


@task
def prepare(ctx):
    print("**********************prepare fixture***************************")
    for path in ["/tmp/default_oauth_apps_docker.json", "/tmp/default_site.json"]:
        try:
            os.remove(path)
        except OSError:
            pass
            
    _prepare_oauth_fixture()
    _prepare_site_fixture()


@task
def fixtures(ctx):
    print("**************************fixtures********************************")
    settings = _localsettings()
    
    base_cmd = (
        f"source $HOME/.override_env && "
        f"python manage.py loaddata sample_admin --settings={settings} && "
        f"python manage.py loaddata /tmp/default_oauth_apps_docker.json --settings={settings} && "
        f"python manage.py loaddata /tmp/default_site.json --settings={settings} && "
        f"python manage.py loaddata initial_data.json --settings={settings}"
    )
    ctx.run(base_cmd, pty=True)

    from django.conf import settings as django_settings
    project_fixtures = getattr(django_settings, "PROJECT_FIXTURES", [])

    if project_fixtures:
        fixture_cmds = [
            f"python manage.py loaddata {fix} --settings={settings}" 
            for fix in project_fixtures if fix
        ]
        if fixture_cmds:
            try:
                ctx.run("source $HOME/.override_env && " + " && ".join(fixture_cmds), pty=True)
            except Exception as e:
                print(f"Warning: Failed to load project fixtures: {e}")


@task
def updateadmin(ctx):
    print("***********************update admin details**************************")
    try:
        os.remove("/tmp/django_admin_docker.json")
    except OSError:
        pass
        
    _prepare_admin_fixture(
        os.environ.get("ADMIN_PASSWORD", "admin"),
        os.environ.get("ADMIN_EMAIL", "admin@example.org"),
    )
    ctx.run(
        f"source $HOME/.override_env && "
        f"django-admin loaddata /tmp/django_admin_docker.json --settings={_localsettings()}",
        pty=True,
    )


@task
def initialized(ctx):
    print("**************************init file********************************")
    static_root = os.environ.get("STATIC_ROOT", "/mnt/volumes/statics/static/")
    lockfile = Path(static_root).parent / "geonode_init.lock"
    
    try:
        lockfile.write_text(datetime.datetime.now().ctime() + "\n")
    except Exception:
        ctx.run(f"date > {lockfile}")


def _docker_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def _container_exposed_port(component, instname):
    port = "80"
    try:
        client = docker.from_env(version="1.24")
        for c in client.containers.list(filters={"label": f"org.geonode.component={component}", "status": "running"}):
            if str(instname) in c.name:
                exposed_ports = c.attrs["Config"].get("ExposedPorts", {})
                for key in exposed_ports:
                    return re.split("/tcp", key)[0]
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
    return os.getenv("DJANGO_SETTINGS_MODULE", "geonode_project.settings")


def _geonode_public_host():
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
