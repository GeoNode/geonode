#!/bin/bash

set -e

echo Get geoserver settings...
SETTINGS=$( python get_geoserver_settings.py | tail -1 )
GUSER=$( echo $SETTINGS | awk '{print $1}' )
GPASS=$( echo $SETTINGS | awk '{print $2}' )
GSURL=$( echo $SETTINGS | awk '{print $3}' )
DHOST=$( echo $SETTINGS | awk '{print $4}' )
DPORT=$( echo $SETTINGS | awk '{print $5}' )
DUSER=$( echo $SETTINGS | awk '{print $6}' )
DPASS=$( echo $SETTINGS | awk '{print $7}' )
DATASTORE=$( echo $SETTINGS | awk '{print $8}' )
DBNAME=$( echo $SETTINGS | awk '{print $9}' )

Q="'"
echo Get postgres settings...
source settings.sh

PCONN="-U postgres -h $DHOST -d $DBNAME"

echo Importing lidar_coverage from $DATASTORE

PGPASSWORD=$POSTGRES_PW psql $PCONN << EOF
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
DROP SERVER IF EXISTS "$DATASTORE" CASCADE;
CREATE SERVER "$DATASTORE" FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', dbname $Q$DATASTORE$Q, port $Q$DPORT$Q);
CREATE USER MAPPING FOR "$DUSER" SERVER "$DATASTORE"
OPTIONS (user $Q$DUSER$Q, password $Q$DPASS$Q);
DROP FOREIGN TABLE IF EXISTS lidar_coverage;
CREATE FOREIGN TABLE IF NOT EXISTS lidar_coverage (
uid             integer,
block_name      varchar(254),
adjusted_l      varchar(254),
sensor          varchar(254),
processor       varchar(254),
flight_num      varchar(254),
mission_na      varchar(254),
date_flown      timestamp without time zone,
x_shift_m       varchar(254),
y_shift_m       varchar(254),
z_shift_m       varchar(254),
height_dif      varchar(254),
rmse_val_m      varchar(254),
cal_ref_pt      varchar(254),
val_ref_pt      varchar(254),
floodplain      varchar(254),
pl1_suc         varchar(254),
pl2_suc         varchar(254)
)
SERVER "$DATASTORE"
OPTIONS (table_name 'lidar_coverage');
GRANT ALL PRIVILEGES ON lidar_coverage TO "$DUSER";
ALTER FOREIGN TABLE public.lidar_coverage OWNER TO "$DUSER";
EOF
echo Created lidar_coverage table on "$DBNAME"
