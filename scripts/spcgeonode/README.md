# SPCgeonode [![CircleCI](https://circleci.com/gh/olivierdalang/geonode.svg?style=svg)](https://circleci.com/gh/olivierdalang/geonode)

SPCgeonode is a setup for Geonode deployement at SPC. It makes it easy to deploy a production ready Geonode. The setup aims for simplicity over flexibility, so that it will only apply for typical small scale Geonode installations.

The setup is also usable for Geonode developement or customization.


## Prerequisites

Make sure you have a version of Docker (tested with 17.12) and docker-compose.

- Linux : https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-from-a-package and https://docs.docker.com/compose/install/#install-compose 
- Windows : https://store.docker.com/editions/community/docker-ce-desktop-windows
- Mac : https://store.docker.com/editions/community/docker-ce-desktop-mac

## Usage

All the following commands happen from this folder :

```
cd /path/to/geonode/scripts/spcgeonode
```

### Development

To start only the main services (should be enough for developement) :
```
docker-compose up --build -d django geoserver postgres nginx
```

To start the whole stack :
```
docker-compose up --build -d
```

If not familiar with Docker, read below to know how to see what's happening. On first start, the containers will restart serveral times. Once everything started, you should be able to open http://127.0.0.1 in your browser. See how to edit the configuration below if you install on another computer.

### Production (using composer)

Using a text editor, edit the `.env` file (you can also override those with environment variables) :
```
# General configuration
nano .env
```

When ready, start the stack using this commands :
```
# Run the stack
docker-compose -f docker-compose.yml up -d --build
```

Alternatively, you can pull the images from dockerhub instead of rebuilding (only applies if you haven't changed the docker setup) :
```
# Pull the images and run the stack
docker-compose -f docker-compose.yml pull
docker-compose -f docker-compose.yml up -d
```

If not familiar with Docker, read below to know how to see what's happening. On first start, the containers will restart serveral times. Once everything started, you should be able to open http://your_http_host or https://your_https_host in your browser.

### Upgrade

If at some point you want to update the SPCgeonode setup (this will work only if you didn't do modifications, if you did, you need to merge them) :
```
# Get the update setup
git pull

# Upgrade the stack
docker-compose -f docker-compose.yml up -d --build
```

### Developpement vs Production

Difference of dev setup vs prod setup:

- Django source is mounted on the host and uwsgi does live reload (so that edits to the python code is reloaded live)
- Django static and media folder, Geoserver's data folder and Certificates folder are mounted on the host (just to easily see what's happening)
- Django debug is set to True
- Postgres's port 5432 is exposed (to allow debugging using pgadmin)
- Nginx debug mode is acticated (not really sure what this changes)
- Docker tags are set to dev instead of latest

### Releases


To make a release :

- checkout spcgeonode-release
- merge spcgeonode
- replace the version tag in docker-compose.yml with the version (format `x.x.x`)
- commit
- create a git tag (format `spc/x.x.x`)
- push spcgeonode-release with tags

This will trigger an automatic build on docker hub.

If you need to manually publish the image (e.g. dockerhub build fail) :

```
docker login
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml push
```

## FAQ

### Docker-primer - How to see what's happening ?

If not familiar with Docker, here are some useful commands :

- `docker ps` : list all containers and their status
- `docker-compose logs -f` : show live stdout from all containers
- `docker-compose logs -f django` : show live stdout from a specific container (replace `django` by `geoserver`, `postgres`, etc.)
- `docker-compose down -v` : brings the stack down including volumes, allowing you to restart from scratch **THIS WILL ERASE ALL DATA !!**

### During startup, a lot of container crash and restart, is it normal ?

This is the normal startup process. Due to the nature of the setup, the containers are very interdependant. Startup from scratch can take approx. 5-10 minutes, during which all containers may restart a lot of times.

In short, Django will restart until Postgres is up so it can migrate the database. Geoserver will restart until Django has configured OAuth so it can get OAuth2 configuration. Django will restart until Geoserver is running so it can reinitialize the master password.

### Backups

*Backups* are made using [RClone](https://rclone.org/docs/). RClone is a flexible file syncing tool that supports all commons cloud provider, regular file transfer protocols as well as local filesystem. It should be able to accomodate almost any setup.

The only available configuration provided with the setup assumes Amazon S3 is being used, in which case you need to replace the following parts of the `rclone.backup.config` file : `YOUR_S3_ACCESS_KEY_HERE`,`YOUR_S3_SECRET_KEY_HERE`,`YOUR_S3_REGION_HERE` and `THE_NAME_OF_YOUR_BUCKET_HERE` (watch [this](https://www.youtube.com/watch?v=BLTy2tQXQLY) to learn how to get these keys).

Also consider enabling *versionning* on the Bucket, so that if data won't get lost if deleted accidentally in GeoNode.

If you want to setup backups using another provider, check the [RClone documentation](https://rclone.org/docs/). It should be easy to add any RClone supported provider to SPCgeonode.

### How to migrate from an existing standard Geonode install

This section lists the steps done to migrate from an apt-get install of Geonode 2.4.1 (with Geoserver 2.7.4) to a fresh SPCGeonode 0.1 install. It is meant as a guide only as some steps may need some tweaking depending on your installation. Do not follow these steps if you don't understand what you're doing.

#### Prerequisites

- access to the original server
- a new server for the install (can be the same than the first one if you don’t fear losing all data) - ideally linux but should be OK as long as it runs docker (64bits)
- an external hard-drive to copy data over

#### On the old server

```
# Move to the external hard drive
cd /path/to/your/external/drive

# Find the current database password (look for DATABASE_PASSWORD, in my case it was XbFAyE4w)
more /etc/geonode/local_settings.py

# Dump the database content (you will be prompted several time for the password above)
pg_dumpall --host=127.0.0.1 --username=geonode --file=pg_dumpall.custom

# Copy all uploaded files
cp -r /var/www/geonode/uploaded uploaded

# Copy geoserver data directory
cp -r /usr/share/geoserver/data geodatadir
```

#### On the new server

Setup SPCGeonode by following the prerequisite and production steps on https://github.com/olivierdalang/SPCgeonode/tree/release up to (but not including) run the stack.

Then run these commands :

```
# Prepare the stack (without running)
docker-compose -f docker-compose.yml pull --no-parallel
docker-compose -f docker-compose.yml up --no-start

# Start the database
docker-compose -f docker-compose.yml up -d postgres

# Initialize geoserver (to create the geodatadir - this will fail because Django/Postgres arent started yet - but this is expected)
docker-compose -f docker-compose.yml run --rm geoserver exit 0

# Go to the external drive
cd /path/to/drive/

# Restore the dump (this can take a while if you have data in postgres)
cat pg_dumpall.custom | docker exec -i spcgeonode_postgres_1 psql -U postgres
# Rename the database to postgres
docker exec -i spcgeonode_postgres_1 dropdb -U postgres postgres
docker exec -i spcgeonode_postgres_1 psql -d template1 -U postgres -c "ALTER DATABASE geonode RENAME TO postgres;"

# Restore the django uploaded files
docker cp uploaded/. spcgeonode_django_1:/spcgeonode-media/

# Restore the workspaces and styles of the geoserver data directory
docker cp geodatadir/styles/. spcgeonode_geoserver_1:/spcgeonode-geodatadir/styles
docker cp geodatadir/workspaces/. spcgeonode_geoserver_1:/spcgeonode-geodatadir/workspaces
docker cp geodatadir/data/. spcgeonode_geoserver_1:/spcgeonode-geodatadir/data

# Back to SPCgeonode
cd /path/to/SPCgeonode

# Fix some inconsistency that prevents migrations (public.layers_layer shouldn’t have service_id column)
docker exec -i spcgeonode_postgres_1 psql -U postgres -c "ALTER TABLE public.layers_layer DROP COLUMN service_id;"

# Migrate with fake initial
docker-compose -f docker-compose.yml run --rm --entrypoint "" django python manage.py migrate --fake-initial

# Create the SQL diff to fix the schema # TODO : upstream some changes to django-extensions for this to work directly
docker-compose -f docker-compose.yml run --rm --entrypoint "" django /bin/sh -c "DJANGO_COLORS="nocolor" python manage.py sqldiff -ae" >> fix.sql

# Manually fix the SQL command until it runs (you can also drop the tables that have no model)
nano fix.sql

# Apply the SQL diff (review the sql file first as this may delete some important tables)
cat fix.sql | docker exec -i spcgeonode_postgres_1 psql -U postgres

# This time start the stack
docker-compose -f docker-compose.yml up -d
```

One last step was to connect to the GeoServer administration and change the PostGIS store host to ‘postgres’ instead of localhost.

### On windows, I have error like `standard_init_linux.go:190: exec user process caused "no such file or directory"`

This may be due to line endings. When checking out files, git optionnaly converts line endings to match the platform, which doesn't work well it `.sh` files.

To fix, use `git config --global core.autocrlf false` and checkout again.
