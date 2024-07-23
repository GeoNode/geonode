#!/bin/bash
set -e

function create_geonode_user_and_database() {
	local db=$1
	local geonode_user="${GEONODE_DATABASE_USER:-$db}"
	local geonode_password="$GEONODE_DATABASE_PASSWORD"
	echo "  Creating user and database '$db' with Geonode user: $geonode_user"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
		CREATE USER $geonode_user;
		ALTER USER $geonode_user with encrypted password '$geonode_password';
		ALTER USER $geonode_user CREATEDB;
		CREATE DATABASE $db;
		GRANT CREATE ON SCHEMA public TO $geonode_user;
		GRANT USAGE ON SCHEMA public TO $geonode_user;
		GRANT ALL PRIVILEGES ON DATABASE $db TO $geonode_user;
EOSQL
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db" -c "GRANT ALL ON SCHEMA public TO $geonode_user;"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $geonode_user;"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $geonode_user;"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db" -c "GRANT INSERT, SELECT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $geonode_user;"
}

function create_geonode_user_and_geodatabase() {
	local geodb=$1
	local geonode_geodb_user="${GEONODE_GEODATABASE_USER:-$geodb}"
	local geonode_geodb_password="$GEONODE_GEODATABASE_PASSWORD"

	echo "  Creating user and database '$geodb' with Geonode GeoDB user: $geonode_geodb_user"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
		CREATE USER $geonode_geodb_user;
		ALTER USER $geonode_geodb_user with encrypted password '$geonode_geodb_password';
		ALTER USER $geonode_geodb_user CREATEDB;
		CREATE DATABASE $geodb;
		GRANT CREATE ON SCHEMA public TO $geonode_geodb_user;
		GRANT USAGE ON SCHEMA public TO $geonode_geodb_user;
		GRANT ALL PRIVILEGES ON DATABASE $geodb TO $geonode_geodb_user;
EOSQL
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$geodb" -c "GRANT ALL ON SCHEMA public TO $geonode_geodb_user;"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$geodb" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $geonode_geodb_user;"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$geodb" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $geonode_geodb_user;"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$geodb" -c "GRANT INSERT, SELECT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $geonode_geodb_user;"
}

function update_database_with_postgis() {
    local db=$1
    echo "  Updating databse '$db' with extension"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<-EOSQL
		CREATE EXTENSION IF NOT EXISTS postgis;
		GRANT ALL ON geometry_columns TO PUBLIC;
		GRANT ALL ON spatial_ref_sys TO PUBLIC;
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
	update_database_with_postgis $GEONODE_GEODATABASE
	echo "Geonode geodatabase created"
fi
