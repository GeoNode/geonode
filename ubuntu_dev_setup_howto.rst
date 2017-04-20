How to create a WorldMap dev setup in Ubuntu
============================================

git clone and submodules
------------------------

git clone git@github.com:cga-harvard/cga-worldmap.git cga-worldmap

cd cga-worldmap

git submodule update --init

vagrant setup
-------------

vagrant up

vagrant ssh

cd cga-worldmap

The rest of the procedure is in the vagrant box.

Install system requirements
---------------------------

sudo apt-get update

sudo apt-get install python-dev libxml2 libxml2-dev git postgresql-9.3 postgresql-server-dev-9.3 gdal-bin postgresql-9.3-postgis-2.1 python-virtualenv python-imaging libjpeg8 libjpeg62-dev libfreetype6 libfreetype6-dev libxslt1-dev ant default-jdk maven2


PostgreSQL/PostGIS configuration
--------------------------------

Run this as the postrgres user::

    sudo su postgres
    psql
    # create role worldmap with superuser login password 'worldmap';
    # create database worldmaplegacy with owner worldmap;
    # create database wmdata with owner worldmap;
    # \c worldmaplegacy
    # create extension postgis;
    # \c wmdata
    # create extension postgis;
    \q
    exit

Virtualenv
----------

Create and activate the virtualenv, and install WorldMap requirements::

    virtualenv env
    . env/bin/activate
    cd cga-worldmap/
    pip install -r shared/requirements.txt
    cp geonode/local_settings.py.tmpl geonode/local_settings.py
    paver build
    ./manage.py syncdb --all

Some hack
---------

Comment out the following lines in geonode.urls (unless you need DVN)::

    # Datatables API
    #(r'^datatables/', include('geonode.contrib.datatables.urls')),

    # Dataverse/GeoConnect API
    #(r'^dataverse/api/', include('geonode.contrib.dataverse_connect.urls')),
    #(r'^dataverse/api/tabular/', include('geonode.contrib.datatables.urls_dataverse')),

Run the development server
--------------------------

python manage.py runserver 0.0.0.0:8000
paver start_geoserver
