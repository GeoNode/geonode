#!/bin/bash

export BACKEND=geonode.geoserver
export DOCKER_COMPOSE_VERSION=1.19.0
export GEOSERVER_SERVER_URL=http://localhost:8080/geoserver/
export GEOSERVER_SERVER_PORT=8080
export ON_TRAVIS=True
export TEST_RUNNER_KEEPDB=True
export TEST_RUN_INTEGRATION=True
export TEST_RUN_INTEGRATION_SERVER=True
export TEST_RUN_INTEGRATION_UPLOAD=False
export TEST_RUN_INTEGRATION_MONITORING=False
export TEST_RUN_INTEGRATION_CSW=True
export TEST_RUN_INTEGRATION_BDD=False
export MONITORING_ENABLED=False
export SESSION_EXPIRED_CONTROL_ENABLED=True
export CELERY_ALWAYS_EAGER=True
export DATABASE_URL=postgis://geonode:geonode@localhost:5432/upload_test
export GEODATABASE_URL=postgis://geonode:geonode@localhost:5432/upload_test
export DEFAULT_BACKEND_DATASTORE=datastore

echo "Initialize DB";
chmod +x scripts/misc/create_dbs_travis.sh;
scripts/misc/create_dbs_travis.sh before_script;

paver run_tests --coverage --local false
