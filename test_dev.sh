#!/bin/bash
set -a
. ./.env_dev
set +a

# paver setup_data
sudo -u postgres dropdb test_geonode
coverage run --branch --source=geonode manage.py test -v 3 --keepdb $@
