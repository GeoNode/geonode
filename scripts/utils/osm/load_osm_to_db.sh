#!/bin/bash

set -e

if [[ "$#" -ne 1 ]]; then
    echo Provide database host as parameter\! Exiting.
    exit 1
fi

DBHOST=$1
BINARIES=(wget psql osm2pgsql shp2pgsql)
DBNAME="osm"
WORKSPACE="osm"
DATASTORE="osm"
CONN="-h $DBHOST -W"
PCONN="-U postgres $CONN"
GCONN="-U geonode $CONN -d $DBNAME"

echo Check if required binaries are in path...
for bin in ${BINARIES[@]}; do
    which $bin &>/dev/null || ( echo $bin missing\! Exiting. && exit 1 )
done
echo All required binaries are in path\!

if [[ ! -f philippines-latest.osm.pbf ]]; then
    echo Download the OpenStreetMap subset definition file for the Philippines...
    wget -c http://download.geofabrik.de/asia/philippines-latest.osm.pbf
fi

echo Create osm database if it doesn\'t exist...
echo Enter postgres db user password if asked...
psql $PCONN -tc "SELECT 1 FROM pg_database WHERE datname = '$DBNAME'" | grep -q 1 || psql $PCONN -c "CREATE DATABASE $DBNAME"

echo Create extensions if they don\'t exist...
psql $PCONN -d $DBNAME -c "CREATE EXTENSION IF NOT EXISTS postgis"
psql $PCONN -d $DBNAME -c "CREATE EXTENSION IF NOT EXISTS hstore"

echo Grant all privileges on database osm to geonode user...
psql $PCONN -c "GRANT ALL PRIVILEGES ON DATABASE $DBNAME TO geonode"

echo Enter geonode db user password if asked...
echo Import OSM to PostGIS...
osm2pgsql -cks -C 512 -H $DBHOST -U geonode -W -d $DBNAME philippines-latest.osm.pbf

if [[ ! -d ne_10m_admin_0_boundary_lines_land ]]; then
    echo Download ne_10m_admin_0_boundary_lines_land...
    wget -c http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_boundary_lines_land.zip
    unzip -o ne_10m_admin_0_boundary_lines_land.zip -d ne_10m_admin_0_boundary_lines_land
fi

if [[ ! -d ne_10m_admin_1_states_provinces_lines ]]; then
    echo Download ne_10m_admin_1_states_provinces_lines...
    wget -c http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_1_states_provinces_lines.zip
    unzip -o ne_10m_admin_1_states_provinces_lines.zip -d ne_10m_admin_1_states_provinces_lines
fi

echo Load boundary shapefiles to database...
shp2pgsql -g geom -s 4326 -I -D ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land.shp admin0 | psql $GCONN
shp2pgsql -g geom -s 4326 -I -D ne_10m_admin_1_states_provinces_lines/ne_10m_admin_1_states_provinces_lines.shp admin1 | psql $GCONN

echo Transform boundary layers from 4326 to 900913...
psql $GCONN -c "ALTER TABLE admin0 ALTER COLUMN geom TYPE geometry(MULTILINESTRING,900913) USING st_transform(geom,900913)"
psql $GCONN -c "ALTER TABLE admin1 ALTER COLUMN geom TYPE geometry(MULTILINESTRING,900913) USING st_transform(geom,900913)"

if [[ ! -d water-polygons-split-3857 ]]; then
    echo Download oceans shapefile...
    wget -c http://data.openstreetmapdata.com/water-polygons-split-3857.zip
    unzip -o water-polygons-split-3857.zip
fi

echo Load oceans shapefile to database...
shp2pgsql -g geom -s 900913 -I -D ./water-polygons-split-3857/water_polygons.shp ocean | psql $GCONN

if [[ ! -f createDBObjects.sql ]]; then
    echo Download createDBobjects.sql...
    wget -c https://raw.githubusercontent.com/boundlessgeo/OSM/master/createDBobjects.sql
fi

echo Create database objects...
psql $GCONN -f createDBobjects.sql

echo Get geoserver settings...
SETTINGS=$( python get_geoserver_settings.py | tail -1 )
GUSER=$( echo $SETTINGS | awk '{print $1}' )
GPASS=$( echo $SETTINGS | awk '{print $2}' )
GSURL=$( echo $SETTINGS | awk '{print $3}' )
DHOST=$( echo $SETTINGS | awk '{print $4}' )
DPORT=$( echo $SETTINGS | awk '{print $5}' )
DUSER=$( echo $SETTINGS | awk '{print $6}' )
DPASS=$( echo $SETTINGS | awk '{print $7}' )

echo Create osm workspace...
sed "s/%%%workspace%%%/${WORKSPACE}/g" osm-workspace-template.json >osm-workspace.json
curl -v -u $GUSER:$GPASS -XPOST -d@osm-workspace.json -H "Content-type: application/json" "http://localhost:8080/geoserver/rest/workspaces.json"

echo Create osm datastore...
sed "s/%%%workspace%%%/${WORKSPACE}/g; s/%%%datastore%%%/${DATASTORE}/g; s/%%%host%%%/${DHOST}/g; s/%%%port%%%/${DPORT}/g; s/%%%user%%%/${DUSER}/g; s/%%%passwd%%%/${DPASS}/g;" osm-datastore-template.json >osm-datastore.json
curl -v -u $GUSER:$GPASS -XPOST -d@osm-datastore.json -H "Content-type: application/json" "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/datastores.json"

if [[ ! -d sld ]]; then
    echo Download SLD scripts...
    wget -c https://github.com/boundlessgeo/OSM/raw/master/sld.zip
    unzip -o sld.zip
fi

echo Run SLD_create.sh script...
if [[ ! -f sld/layergroup_template.xml ]]; then
    cp sld/layergroup.xml sld/layergroup_template.xml
fi
sed "s/<workspace>osm<\/workspace>/<workspace>${WORKSPACE}<\/workspace>/g" sld/layergroup_template.xml >sld/layergroup.xml
if [[ ! -f sld/SLD_create_template.sh ]]; then
    cp sld/SLD_create.sh sld/SLD_create_template.sh
fi
sed "s/login=admin:geoserver/login=${GUSER}:${GPASS}/g; s/workspace=osm/workspace=$WORKSPACE/g; s/store=openstreetmap/store=$DATASTORE/g; s/http:\/\/localhost:8080\/geoserver\/rest\/layergroups/http:\/\/localhost:8080\/geoserver\/rest\/workspaces\/\$workspace\/layergroups/g;" sld/SLD_create_template.sh >sld/SLD_create.sh
cd sld
bash -x ./SLD_create.sh
cd ..

echo Run updatelayers on workspace...
python ../../../manage.py updatelayers -w $WORKSPACE

echo Apply proper permissions to osm layers...
python osm_permissions.py
