#!/bin/bash

# This script should receive super user credentials for database access in order to create database for geonode and
# geoserver. So $DB_USER and $DB_PASSWORD should correspond to user that can create database.
# This script will create following databases: $GEONODE_DB_NAME and $GEOSERVER_DB_NAME if they not exists.

# Create .pgpass file based on env vars
echo "$DB_HOST:$DB_PORT:*:$DB_ADMIN_USER:$DB_ADMIN_PASSWORD" > ~/.pgpass
chmod 0600 ~/.pgpass

# Configure postgres access
export PGHOST=$DB_HOST
export PGPORT=$DB_PORT
export PGUSER=$DB_ADMIN_USER

# Check if DB is available and wait for it if necessary
until psql --no-password postgres -c "SELECT 1" > /dev/null 2>&1; do
  echo "Waiting for postgres server..."
  sleep 1
done

# Check if geonode database and user was already bootstraped
# Database is considered bootstraped if it already exists
if psql --no-password -lqt postgres | cut -d \| -f 1 | grep -qw $DB_GEONODE_NAME; then
    echo "Geonode database exists, skipping bootstrap"
else
    echo "Bootstraping Geonode database..."
    echo "--------------------------------"

    echo -n "Creating new role $DB_GEONODE_USER..."
    psql --no-password postgres -q -c "CREATE ROLE $DB_GEONODE_USER WITH LOGIN UNENCRYPTED PASSWORD '$DB_GEONODE_PASSWORD';"
    echo "OK"

    echo -n "Creating new database $DB_NAME..."
    psql --no-password postgres -q -c "CREATE DATABASE $DB_GEONODE_NAME OWNER $DB_GEONODE_USER"
    echo "OK"

    echo "Launch genode DB bootstrap procedure..."
    # python manage.py makemigrations
    python manage.py migrate account --noinput
    python manage.py migrate --noinput

    echo " Populate db with admin:admin account and some categories"
    paver sync

fi

# Check if geoserver database exists
if psql --no-password -lqt postgres | cut -d \| -f 1 | grep -qw $DB_GEOSERVER_NAME; then
    echo "Geoserver database exists, skipping bootstrap"
else
    echo "Bootstraping Geoserver database..."
    echo "----------------------------------"

    echo -n "Creating new role $DB_GEOSERVER_USER..."
    psql --no-password postgres -q -c "CREATE ROLE $DB_GEOSERVER_USER WITH LOGIN UNENCRYPTED PASSWORD '$DB_GEOSERVER_PASSWORD'"
    echo "OK"

    echo -n "Creating new database $DB_NAME..."
    psql --no-password postgres -q -c "CREATE DATABASE $DB_GEOSERVER_NAME OWNER $DB_GEOSERVER_USER"
    echo "OK"

    echo -n "Adding postgis extension..."
    psql --no-password $DB_GEOSERVER_NAME -q -c "CREATE EXTENSION postgis"
    echo "OK"
fi