#!/bin/bash
set -a
. ./.env_dev
set +a

# paver setup_data
# dropdb -U postgres test_geonode
coverage run --branch --source=geonode manage.py test -v 3 --keepdb $@
