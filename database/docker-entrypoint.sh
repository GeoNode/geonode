#!/bin/bash

# Create .pgpass file based on env vars
echo "$DB_HOST:$DB_PORT:*:$DB_USER:$DB_PASSWORD" > ~/.pgpass
chmod 0600 ~/.pgpass

# Configure postgres access
export PGHOST=$DB_HOST
export PGPORT=$DB_PORT
export PGUSER=$DB_USER

# Check if DB is available and wait for it if necessary
until psql --no-password postgres -c "SELECT 1" > /dev/null 2>&1; do
  echo "Waiting for postgres server..."
  sleep 1
done

# Check if database was already bootstraped
# Database is considered bootstraped if it already exists
if psql --no-password -lqt postgres | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Database exists, skipping bootstrap"
else
    echo "Bootstraping database..."
    echo "------------------------"

    echo -n "Creating new database $DB_NAME..."
    psql --no-password postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER"
    echo "OK"

    echo -n "Generate minimal geonode configuration with DB parameters..."
    cat > /usr/src/app/geonode/local_settings.py << EOF
DATABASES = {
    'default': {
         'ENGINE'  : 'django.db.backends.postgresql_psycopg2',
         'HOST'    : '$DB_HOST',
         'PORT'    : '$DB_PORT',
         'NAME'    : '$DB_NAME',
         'USER'    : '$DB_USER',
         'PASSWORD': '$DB_PASSWORD',
     }
}
EOF
    echo "OK"

    echo "Launch genode DB bootstrap procedure..."
    # python manage.py makemigrations
    python manage.py migrate account --noinput
    python manage.py migrate --noinput

fi

