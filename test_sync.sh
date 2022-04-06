#!/bin/bash
set -e
set -a
. ./.env_test
set +a

export ASYNC_SIGNALS=False

paver setup_data
coverage run --branch --source=geonode manage.py test -v 3 --keepdb $@
