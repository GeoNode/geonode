#!/bin/bash
set -e
set -a
. ./.env_dev
set +a

coverage run --branch --source=geonode manage.py test -v 3 --keepdb  $@
