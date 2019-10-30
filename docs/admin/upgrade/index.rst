Upgrade from 2.8.x
==================



Upgrade from 2.7.x
==================

Upgrade from 2.6.x
==================

Upgrade from 2.4.x
==================

These are the notes of a migration from 2.4.x to 2.10.1.
These notes could possibly works also when migrating from 2.6.x, 2.7.x, 2.8.x but were not tested in that scenarios.
You should run this procedure on your local machine and once you successfully migrated the database move the backup to your GeoNode 2.10.1 production instance.

PostgreSQL
----------

Create a role and a database for Django GeoNode 2.4:

.. code-block:: sql

    create role user with superuser login with password '***';
    create database gn_24 with owner user;
    \c gn_24
    create extension postgis;

Restore backup from your production backup:

.. code-block:: shell

    psql gn_24 < gn_24.sql

Run GeoNode migrations
----------------------

Activate your GeoNode virtualenv and set the env vars:

.. code-block:: sql

    . env/bin/Activate
    export vars_210

Here are the variables to export - update them to your environment settings:

.. code-block:: shell

    export DATABASE_URL=postgis://user:***@localhost:5432/dbname
    export DEFAULT_BACKEND_DATASTORE=data
    export GEODATABASE_URL=postgis://user:***@localhost:5432/geonode_data
    export ALLOWED_HOSTS="['localhost', '192.168.100.10']"
    export STATIC_ROOT=~/www/geonode/static/
    export GEOSERVER_LOCATION=http://localhost:8080/geoserver/
    export GEOSERVER_PUBLIC_LOCATION=http://localhost:8080/geoserver/
    export GEOSERVER_ADMIN_PASSWORD=geoserver
    export SESSION_EXPIRED_CONTROL_ENABLED=False

Downgrade psycopg2:

.. code-block:: shell

    pip install psycopg2==2.7.7

Apply migrations and apply basic fixtures:

.. code-block:: shell

    cd wfp-geonode
    ./manage.py migrate --fake-initial
    paver sync


Regenerate from scratch the upload application tables in the database:

.. code-block:: sql

    delete from django_migrations where app = 'upload';
    drop table upload_upload cascade;
    drop table upload_uploadfile;

Regenerate upload tables with migrate:

.. code-block:: shell

    ./manage.py migrate upload

Upgrade psycopg2:

.. code-block:: shell

    pip install -r geonode/requirements.txt

Create superuser
----------------

To create a superuser you should drop the following constraints (they can be re-enabled if needed):

.. code-block:: sql

    alter table people_profile alter column last_login drop not null;

.. code-block:: shell

    ./manage createsuperuser

Fixes on database
-----------------

For some reason some resources were unpublished:

.. code-block:: sql

    UPDATE base_resourcebase SET is_published = true;

Remove a foreign key from account_account which is not used anymore (GeoNode dev team: maybe even better let's remove all of the account tables, I think they are stale now):

.. code-block:: sql

    ALTER TABLE account_account DROP CONSTRAINT user_id_refs_id_726cb6b4;
    ALTER TABLE account_signupcode DROP CONSTRAINT "inviter_id_refs_id_49a7c0d9";

Fix the remote service layers by running this script:

.. code-block:: shell

    python migration/fixes_remote_layers.py
