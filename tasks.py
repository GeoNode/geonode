import json
import os
import ast

from invoke import task

BOOTSTRAP_IMAGE_CHEIP = 'codenvy/che-ip:nightly'


@task
def waitfordbs(ctx):
    print("**************************databases*******************************")
    ctx.run("/usr/bin/wait-for-databases {0}".format('db'), pty=True)


@task
def update(ctx):
    print("***************************initial*********************************")
    ctx.run("env", pty=True)
    pub_ip = _geonode_public_host_ip()
    print("Public Hostname or IP is {0}".format(pub_ip))
    pub_port = _geonode_public_port()
    print("Public PORT is {0}".format(pub_port))
    pub_protocol = 'https' if pub_port == '443' else 'http'
    if pub_protocol == 'https' or pub_port == '80':
        pub_port = None
    db_url = _update_db_connstring()
    geodb_url = _update_geodb_connstring()
    override_env = "$HOME/.override_env"
    envs = {
        "public_protocol": pub_protocol,
        "public_fqdn": "{0}{1}".format(pub_ip, ':' + pub_port if pub_port else ''),
        "public_host": "{0}".format(pub_ip),
        "dburl": db_url,
        "geodburl": geodb_url,
        "override_fn": override_env
    }
    if os.environ.get(
        'GEONODE_LB_HOST_IP'
    ) and os.environ.get(
        'GEONODE_LB_PORT'
    ):
        ctx.run("echo export GEOSERVER_PUBLIC_LOCATION=\
{public_protocol}://{public_fqdn}/geoserver/ >> {override_fn}".format(**envs), pty=True)
        ctx.run("echo export GEOSERVER_WEB_UI_LOCATION=\
{public_protocol}://{public_fqdn}/geoserver/ >> {override_fn}".format(**envs), pty=True)
        ctx.run("echo export SITEURL=\
{public_protocol}://{public_fqdn}/ >> {override_fn}".format(**envs), pty=True)

    try:
        current_allowed = ast.literal_eval(
            os.getenv('ALLOWED_HOSTS') or "[\
'{public_fqdn}', '{public_host}', 'localhost', 'django', 'geonode',\
]".format(**envs))
    except ValueError:
        current_allowed = []
    current_allowed.extend(
        ['{}'.format(pub_ip), '{}:{}'.format(pub_ip, pub_port)]
    )
    allowed_hosts = ['"{}"'.format(c) for c in current_allowed]
    for host in ['django', 'geonode']:
        if host not in allowed_hosts:
            allowed_hosts.extend(['{}'.format(host)])

    ctx.run('echo export ALLOWED_HOSTS="\\"{}\\"" >> {}'.format(
        allowed_hosts, override_env
    ), pty=True)

    if not os.environ.get('DATABASE_URL'):
        ctx.run("echo export DATABASE_URL=\
{dburl} >> {override_fn}".format(**envs), pty=True)
    if not os.environ.get('GEODATABASE_URL'):
        ctx.run("echo export GEODATABASE_URL=\
{geodburl} >> {override_fn}".format(**envs), pty=True)
    ctx.run("source $HOME/.override_env", pty=True)
    print("****************************final**********************************")
    ctx.run("env", pty=True)


@task
def migrations(ctx):
    print("**************************migrations*******************************")
    ctx.run("django-admin.py migrate --noinput --settings={0}".format(
        _localsettings()
    ), pty=True)


@task
def statics(ctx):
    print("**************************migrations*******************************")
    ctx.run('mkdir -p /mnt/volumes/statics/{static,uploads}')
    ctx.run("python manage.py collectstatic --noinput --clear --settings={0}".format(
        _localsettings()
    ), pty=True)


@task
def prepare(ctx):
    print("**********************prepare fixture***************************")
    ctx.run("rm -rf /tmp/default_oauth_apps_docker.json", pty=True)
    _prepare_oauth_fixture()


@task
def fixtures(ctx):
    print("**************************fixtures********************************")
    ctx.run("django-admin.py loaddata sample_admin \
--settings={0}".format(_localsettings()), pty=True)
    ctx.run("django-admin.py loaddata /tmp/default_oauth_apps_docker.json \
--settings={0}".format(_localsettings()), pty=True)
    ctx.run("django-admin.py loaddata geonode/base/fixtures/initial_data.json \
--settings={0}".format(_localsettings()), pty=True)


@task
def initialized(ctx):
    print("**************************init file********************************")
    ctx.run('date > /mnt/volumes/statics/geonode_init.lock')


@task
def devrequirements(ctx):
    print("*********************install dev requirements**********************")
    ctx.run('pip install -r requirements_dev.txt --upgrade')


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
    gn_pub_hostip = os.getenv('GEONODE_LB_HOST_IP', 'localhost')
    return gn_pub_hostip


def _geonode_public_port():
    gn_pub_port = os.getenv('GEONODE_LB_PORT', '80')
    return str(gn_pub_port)


def _prepare_oauth_fixture():
    pub_ip = _geonode_public_host_ip()
    print("Public Hostname or IP is {0}".format(pub_ip))
    pub_port = _geonode_public_port()
    print("Public PORT is {0}".format(pub_port))
    pub_protocol = 'https' if pub_port == '443' else 'http'
    if pub_protocol == 'https' or pub_port == '80':
        pub_port = None
    default_fixture = [
        {
            "model": "oauth2_provider.application",
            "pk": 1001,
            "fields": {
                "skip_authorization": True,
                "created": "2018-05-31T10:00:31.661Z",
                "updated": "2018-05-31T11:30:31.245Z",
                "algorithm": "RS256",
                "redirect_uris": "{0}://{1}{2}/geoserver/index.html".format(
                    pub_protocol, pub_ip, ':' + pub_port if pub_port else ''
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
