#!/bin/bash

# For Ubuntu 10.04
if [ -d "/usr/share/postgresql/8.4/contrib" ]
then
    POSTGIS_SQL_PATH=/usr/share/postgresql/8.4/contrib
    POSTGIS_SQL=postgis.sql
fi

# For Ubuntu 10.10 (with PostGIS 1.5)
if [ -d "/usr/share/postgresql/8.4/contrib/postgis-1.5" ]
then
    POSTGIS_SQL_PATH=/usr/share/postgresql/8.4/contrib/postgis-1.5
    POSTGIS_SQL=postgis.sql
    GEOGRAPHY=1
else
    GEOGRAPHY=0
fi

createdb -E UTF8 geonode && \
createlang -d genode plpgsql && \
psql -d geonode -f $POSTGIS_SQL_PATH/$POSTGIS_SQL && \
psql -d geonode -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql && \
psql -d geonode -c "GRANT ALL ON geometry_columns TO PUBLIC;" && \
psql -d geonode -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"

if ((GEOGRAPHY))
then
    psql -d geonode -c "GRANT ALL ON geography_columns TO PUBLIC;"
fi
