# GeoNode project bare installation

## Overview

Geonode project is the proper way to run a customized installation of Geonode. The repository of geonode-project contains a minimal set of files following the structure of a django-project. Geonode itself will be installed as a requirement of your project.
Inside the project structure is possible to extend, replace or modify all geonode components (e.g. css and other static files, templates, models..) and even register new django apps **without touching the original Geonode code**.

!!! Note 
    You can call your geonode project whatever you like following the naming conventions for python packages (generally lower case with underscores (_)). In the examples below, replace ``my_geonode`` with whatever you would like to name your project.

See also the [README](https://github.com/GeoNode/geonode-project/blob/master/README.md) file on geonode-project repository

The following steps will guide you to a new setup of GeoNode Project. All guides will first install and configure the system to run it in ``DEBUG`` mode (also known as ``DEVELOPMENT`` mode) and then by configuring an HTTPD server to serve GeoNode through the standard ``HTTP`` (``80``) port.

## Install the dependencies

The required dependencies are described in the following section: [prerequiesites guide](../prerequisites). Ensure you review this guide before proceeding with the GeoNode project installation.

## Geonode Project Installation

### Prepare the environment and clone GeoNode project

Prepare the environment

```bash
# Let's create the GeoNode project base folder and clone it
sudo mkdir -p /opt/geonode_projects/; sudo usermod -a -G www-data $USER; sudo chown -Rf $USER:www-data /opt/geonode_projects; sudo chmod -Rf 775 /opt/geonode_projects
```

Clone the source code

```bash
cd /opt/geonode_projects/
git clone https://github.com/GeoNode/geonode-project.git
```

This will clone the ``master`` branch. You will have to checkout the desidered branch or tag. 
As an example, if you want to generate a project for GeoNode 4.4.3 run the following:

```bash
git checkout -b 4.4.3
```

### Generate a custom GeoNode project

This is the most important part for the GeoNode project installation. Before building the project, you have to generate custom GeoNode project intance, using the `GeoNode Template`

!!! Note
    We will call our instance my_geonode. You can change the name at your convenience.

```bash
# Create and activate a Python environment called my_geonode_env
mkdir path/to/.venvs
python3 -m venv /path/to/.venvs/my_geonode_env
source /path/to/.venvs/my_geonode_env/bin/activate

# Install Django in the activated Python environment
pip install Django==5.2.8

cd /opt/geonode_projects
django-admin startproject --template=./geonode-project -e py,sh,md,rst,json,yml,ini,env,sample,properties -n monitoring-cron -n Dockerfile my_geonode
```

### Install the Python requrements
  
```bash
cd /opt/geonode_projects/my_geonode
pip install -r src/requirements.txt --upgrade
pip install -e src/ --upgrade

# Install GDAL Utilities for Python
pip install pygdal=="`gdal-config --version`.*"

# Dev scripts
mv .override_dev_env.sample src/.override_dev_env
mv src/manage_dev.sh.sample src/manage_dev.sh
mv src/paver_dev.sh.sample src/paver_dev.sh
```

### PostGIS database setup

In this section we are going to install the ``PostgreSQL`` packages along with the ``PostGIS`` extension. Those steps must be done **only** if you don't have the DB already installed on your system.

```bash
# Ubuntu 24.04 (focal)
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/pgdg.gpg >/dev/null

# Install PostgreSQL and PostGIS
sudo apt update
sudo apt install -y \
  postgresql-15 \
  postgresql-client-15 \
  postgresql-15-postgis-3 \
  postgresql-15-postgis-3-scripts
```

We now must create two databases, ``my_geonode`` and ``my_geonode_data``, belonging to the role ``my_geonode``.

!!! Warning
    This is our default configuration. You can use any database or role you need. The connection parameters must be correctly configured on settings, as we will see later in this section.

### Databases and Permissions

First, create the geonode user. GeoNode is going to use this user to access the database

```bash
sudo service postgresql start
sudo -u postgres createuser -P my_geonode
```

You will be prompted asked to set a password for the user. **Enter geonode as password**.

!!! Warning 
    This is a sample password used for the sake of simplicity. This password is very **weak** and should be changed in a production environment.

Create database ``my_geonode`` and ``my_geonode_data`` with owner ``my_geonode``

```bash
sudo -u postgres createdb -O my_geonode my_geonode
sudo -u postgres createdb -O my_geonode my_geonode_data
```

Next let's create PostGIS extensions

```bash
sudo -u postgres psql -d my_geonode -c 'CREATE EXTENSION postgis;'
sudo -u postgres psql -d my_geonode -c 'GRANT ALL ON geometry_columns TO PUBLIC;'
sudo -u postgres psql -d my_geonode -c 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
sudo -u postgres psql -d my_geonode -c 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO my_geonode;'

sudo -u postgres psql -d my_geonode_data -c 'CREATE EXTENSION postgis;'
sudo -u postgres psql -d my_geonode_data -c 'GRANT ALL ON geometry_columns TO PUBLIC;'
sudo -u postgres psql -d my_geonode_data -c 'GRANT ALL ON spatial_ref_sys TO PUBLIC;'
sudo -u postgres psql -d my_geonode_data -c 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO my_geonode;'
```

Final step is to change user access policies for local connections in the file ``pg_hba.conf``

```bash
sudo vim /etc/postgresql/15/main/pg_hba.conf
```

Scroll down to the bottom of the document. We want to make local connection ``trusted`` for the default user.

Make sure your configuration looks like the one below.

```bash
...
# DO NOT DISABLE!
# If you change this first entry you will need to make sure that the
# database superuser can access the database using some other method.
# Noninteractive access to all databases is required during automatic
# maintenance (custom daily cronjobs, replication, and similar tasks).
#
# Database administrative login by Unix domain socket
local   all             postgres                                trust

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     md5
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     peer
host    replication     all             127.0.0.1/32            md5
host    replication     all             ::1/128                 md5
```

!!! Warning 
    If your ``PostgreSQL`` database resides on a **separate/remote machine**, you'll have to **allow** remote access to the databases in the ``/etc/postgresql/15/main/pg_hba.conf`` to the ``geonode`` user and tell PostgreSQL to **accept** non-local connections in your ``/etc/postgresql/15/main/postgresql.conf`` file

Restart PostgreSQL to make the change effective.

```bash
sudo service postgresql restart
```

PostgreSQL is now ready. To test the configuration, try to connect to the ``my_geonode`` database as ``my_geonode`` role.

```bash
psql -U postgres my_geonode
# This should not ask for any password

psql -U my_geonode my_geonode
# This should ask for the password geonode

# Repeat the test with geonode_data DB
psql -U postgres my_geonode_data
psql -U my_geonode my_geonode_data
```

### Database migrations and data initialization

After the creation of the databases, you need to apply database migrations:

```bash
cd /opt/geonode_projects/my_project
# Run migrations for the my_geonode database
python manage.py migrate
# Run migrations for the my_geonode_data database
python manage.py migrate --database=datastore
```

### Install GeoServer

For installing GeoServer, please follow the steps from this section: [Install GeoServer](../vanilla-bare-installation#3-install-geoserver)

### Run GeoNode project in development mode

Now you have a completely working GeoNode instance installed which can be run by running the development server of Django.

To start GeoNode project in development mode run the following:

```bash
cd /opt/geonode_projects/my_geonode
python manage.py runserver
```

If you navigate to [http://localhost:8000](http://localhost:8000) you should see the `home` page of the default template of GeoNode project.

You can login as administrator by using the credentials below:
```bash
username: admin
password: admin
```

### Run GeoNode project in production

To setup GeoNode project in a production environment please refer to the corresponding guide from [Vanilla GeoNode installation](../vanilla-bare-installation/#4-web-server). 

**Be careful** to use the **new** paths and names everywhere:

- Everytime you'll find the keyword ``geonode``, you'll need to use your geonode custom name instead (in this example ``my_geonode``).

- Everytime you'll find paths pointing to ``/opt/geonode/``, you'll need to update them to point to your custom project instead (in this example ``/opt/geonode_projects/my_geonode``).

!!! Note
    Please keep in mind that the recommended way to setup a GeoNode instance (Vanilla or project) in a production environment is by using the `Docker installation`