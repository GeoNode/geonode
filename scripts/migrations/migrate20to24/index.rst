Procedure to migrate a GeoNode 2.0 instance to 2.4
==================================================

To migrate your GeoNode 2.0 instance to a fresh 2.4 instance the following steps are needed:

* backup everything
* database migration first part
* migrate GeoServer data directory
* database migration second part
* restore Django media files

Backup everything
-----------------

Things to backup before proceeding with the other steps (the scripts will not alter them, but just in case):

* GeoNode Django database
* GeoNode uploads database
* GeoServer data directory
* Django media files

Database migration first part
-----------------------------

Warning 1
+++++++++

This procedure works only with GeoNode using a Postgres database.

Warning 2
+++++++++

Some of the tables is not being migrated as we don't use those features:

* actstream
* agon_ratings
* announcements
* dialogos
* notifications
* messages

In case you update the scripts, pull requests are very welcome :)

Warning 3
+++++++++

Thumbnails for maps must be generated manually clicking on the "Set Thumbnail" button from the "Edit Map" form in the map detail page.

Warning 4
+++++++++

Link for map and document details page are not kept. We would need to add a slug field in the resourcebase table for this purpose and this is under discussion (maybe there will be this schema change for 2.4.1, therefore if you need this wait for that release, the migration procedure will be updated).

Database migration steps
++++++++++++++++++++++++

The migration scripts must be run from the server.

As a first step, install GeoNode on the server and create a fresh database using the syncdb command. Make sure that both the fresh database and the old one are on your Postgres server (don't forget to make a backup of the Postgres GeoNode 2.0 database before going on with this!).

For the purpose of these instructions, we will suppose that your Postgres server is your localhost, and that it will contain the two databases (GeoNode 2.0, referred as db20, and GeoNode 2.4, referred as db24) with the following credentials::

    [db20]
    dbname = geonode_20
    host = localhost
    user = geonode
    password = secret

    [db24]
    dbname = geonode_24
    host = localhost
    user = geonode
    password = secret

Make a copy of the gn_migration.cfg.tmpl file and edit it accordingly to your database and virtual environment settings::

    $ cd scripts/migrations/migrate20to24/
    $ cp gn_migration.cfg.tmpl gn_migration.cfg
    $ vi gn_migration.cfg

You will need to set the settings relative to your GeoNode path::

    [path]
    geonode_path = /home/capooti/git/github/geonode
    settings_path = geonode.local_settings

Now run the first migration script, migrate.sh::

    $ ./migrate.sh

Migrate GeoServer data directory
--------------------------------

Copy GeoServer data directory to the GeoServer instance included with GeoNode 2.4.
Login with the GeoServer admin user to check if everything is working properly.

Database migration second part
------------------------------

Run the second migration script::

    $ ./migrate2.sh

Consideration on permissions migration
++++++++++++++++++++++++++++++++++++++

GeoNode 2.0 gives the user the opportunity to assign a resource permission to the GeoNode authenticated users.

For this purpose and to migrate corresponding permissions, the migration script creates a "authenticated" group, and each user is assigned to it.

Don't forget to add to this group newly created users (in the near future we will implement a "add new user to this group" checkbox).

Restore Django media files
--------------------------

Restore the Django media files from backup.

