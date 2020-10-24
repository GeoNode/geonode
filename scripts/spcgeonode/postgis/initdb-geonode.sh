#!/bin/bash
set -e

function create_geonode_user_and_database() {
	local db=$1
	echo "  Creating user and database '$db'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE USER $db;
		ALTER USER $db with encrypted password '$GEONODE_DATABASE_PASSWORD';
	    CREATE DATABASE $db;
	    GRANT ALL PRIVILEGES ON DATABASE $db TO $db;
EOSQL
}

function create_geonode_user_and_geodatabase() {
	local geodb=$1
	echo "  Creating user and database '$geodb'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE USER $geodb;
		ALTER USER $geodb with encrypted password '$GEONODE_GEODATABASE_PASSWORD';
	    CREATE DATABASE $geodb;
	    GRANT ALL PRIVILEGES ON DATABASE $geodb TO $geodb;
EOSQL
}

function update_database_with_postgis() {
    local db=$1
    echo "  Updating databse '$db' with extension"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL
}

function update_geodatabase_with_postgis() {
	local geonode_data=$1
	echo "  Updating geodatabase '$geonode_data' with extension"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$geonode_data" <<-EOSQL
		CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL
}

if [ -n "$GEONODE_DATABASE" ]; then
	echo "Geonode database creation requested: $GEONODE_DATABASE"
	create_geonode_user_and_database $GEONODE_DATABASE
    update_database_with_postgis $GEONODE_DATABASE
	echo "Geonode database created"
fi

if [ -n "$GEONODE_GEODATABASE" ]; then
	echo "Geonode geodatabase creation requested: $GEONODE_GEODATABASE"
	create_geonode_user_and_geodatabase $GEONODE_GEODATABASE
	update_geodatabase_with_postgis $GEONODE_GEODATABASE
	echo "Geonode geodatabase created"
fi
